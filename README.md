# V100 x2 + Strata + Qwen3.8-Flash-Next

Experimental Docker-first deployment and benchmark harness for running the original Qwen3.8-Flash-Next IQ2_XS model on a Lenovo ThinkStation P520 with two Tesla V100 16 GB GPUs.

## Current validated state

Host:

- Lenovo ThinkStation P520
- Xeon W-2135, 6C/12T
- 64 GB DDR4-2400 ECC
- Tesla V100-SXM2 16 GB x2 (sm_70)
- Ubuntu Server 26.04.1
- Docker 29.1.3
- NVIDIA Container Toolkit 1.20.0
- NVIDIA driver 580.178.04
- no host CUDA toolkit required

Runtime:

- image: `strata-v100:0.1.31`
- Strata 0.1.31 pinned to commit `9259cad4cfa3543cd3b8decab5962672b968c649`
- CUDA Toolkit 12.9.1 inside the image
- `CMAKE_CUDA_ARCHITECTURES=70`
- text-only / vision disabled
- `STRATA_PROMPT_ATTN_OLD=1` retained for the conservative Volta prompt-attention path
- the W-2135 does not satisfy Strata's AVX-512 IQ fast-path requirements, so IQ expert CPU work uses AVX2

The current preferred topology is **two independent 128K mmap agents**, one per V100.

## Model

Current model:

- **Original Qwen3.8-Flash-Next IQ2_XS**
- source: `ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF`
- pinned revision: `ed59f92082b1e93c0e96d60a8b11aab089b52f09`
- two GGUF shards, approximately 64 GB total
- native Strata pack approximately 1.5 GB
- no `experts.bin` in the native pack
- expert slices are mmap-read directly from the GGUF shards
- shared MTP data is reused read-only from `/srv/models/strata-data/mtp`

IQ2_XS is a higher-precision quantization than the earlier Coder IQ1_M baseline. A direct model-quality benchmark has **not** been run, so this repository does not claim a measured quality delta.

## Storage layout

The old Coder IQ1_M model under `/srv/models/strata-data/models/coder-IQ1_M` was removed after the IQ2_XS deployment was validated.

The IQ2_XS data now physically lives on the dedicated model NVMe:

```text
/srv/models/strata-iq2xs/
├── config/
├── logs/
├── model/
└── pack/

/srv/models/strata-data/mtp/
└── ... shared MTP data ...
```

For compatibility with the already validated containers and scripts, the original path is a symlink:

```text
/home/loopwhile/models/strata-iq2xs -> /srv/models/strata-iq2xs
```

The copy was verified with SHA-256 across all 19 files before the old 65 GB copy under `/home` was deleted. The preserved `strata-iq2xs-single-mmap` container was then started successfully through the symlink and reported the model as loaded with `n_ctx=131072`.

## Day-to-day server startup

The validated containers already exist. **Do not recreate or remove them for normal startup.**

The main serving topology is:

```text
Agent A                              Agent B
host GPU 0                           host GPU 1
V100 16 GB                           V100 16 GB
128K context                         128K context
127.0.0.1:8080                       127.0.0.1:8081
CPUs 0-2,6-8                         CPUs 3-5,9-11
mmap experts                         mmap experts
        \                           /
         \-- shared IQ2_XS + MTP --/
```

Start both validated agents after a reboot:

```bash
cd ~/v100-x2-strata-qwen3.8-flash-next

docker start strata-iq2xs-agent-a strata-iq2xs-agent-b
```

Check status:

```bash
docker ps --filter name=strata-iq2xs-agent   --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

curl -fsS http://127.0.0.1:8080/health
echo
curl -fsS http://127.0.0.1:8081/health
echo
```

Check the OpenAI-compatible model endpoints:

```bash
curl -fsS http://127.0.0.1:8080/v1/models
echo
curl -fsS http://127.0.0.1:8081/v1/models
echo
```

Follow logs:

```bash
docker logs -f --tail 50 strata-iq2xs-agent-a
```

and, in another terminal:

```bash
docker logs -f --tail 50 strata-iq2xs-agent-b
```

Stop both without deleting them:

```bash
docker stop strata-iq2xs-agent-a strata-iq2xs-agent-b
```

### Preserved alternate containers

These validated containers are also intentionally preserved:

```text
strata-iq2xs-single-mmap
strata-iq2xs-mgpu
```

Do not run these at the same time as the dual-agent topology because they compete for the same GPUs and/or port 8080.

Single-V100 mmap:

```bash
docker start strata-iq2xs-single-mmap
docker logs -f --tail 50 strata-iq2xs-single-mmap
docker stop strata-iq2xs-single-mmap
```

Two-GPU single-server baseline:

```bash
docker start strata-iq2xs-mgpu
docker logs -f --tail 50 strata-iq2xs-mgpu
docker stop strata-iq2xs-mgpu
```

## Provisioning scripts

The current IQ2_XS workflow was built with:

```text
scripts/40-download-original-iq2xs.sh
scripts/41-docker-pack-original-iq2xs-native.sh
scripts/42-prepare-original-iq2xs-multigpu-128k.sh
scripts/43-run-original-iq2xs-multigpu-128k.sh
scripts/44-bench-original-iq2xs-multigpu.sh
scripts/45-prepare-original-iq2xs-single-mmap.sh
scripts/46-run-original-iq2xs-single-mmap.sh
scripts/47-bench-original-iq2xs-single-mmap.sh
scripts/48-prepare-original-iq2xs-dual-mmap.sh
scripts/49-run-original-iq2xs-dual-mmap.sh
scripts/50-smoke-original-iq2xs-dual-mmap.sh
scripts/51-bench-original-iq2xs-dual-mmap.sh
scripts/52-bench-v100-contract-c2-performance.sh
```

`scripts/49-run-original-iq2xs-dual-mmap.sh` is an initial container-creation script. It intentionally refuses to replace existing agent containers. For routine boots, use `docker start` as shown above.

The earlier Coder IQ1_M scripts and results remain useful as historical references, but IQ1_M is no longer the active model deployment.

## Validated performance

### Two-GPU single Strata server

The preserved `strata-iq2xs-mgpu` configuration uses both V100s for one server.

Observed results:

| Prompt | Prefill | Decode |
|---|---:|---:|
| ~32K | 1329.6 tok/s | 44.9 tok/s |
| ~64K | 1398.9 tok/s | 43.9 tok/s |
| ~125K | 1331.3 tok/s | 48.1 tok/s |

This topology used a full expert arena in host RAM and is retained as the single-server performance baseline.

### One-V100 mmap server

The preserved `strata-iq2xs-single-mmap` configuration uses one V100, mmap experts, and no host expert arena.

A 32K run measured approximately:

- prefill: 723.8 tok/s
- decode: 17.6 tok/s
- expert-cache hit rate: 82.2%

### Dual independent 128K mmap agents

The current serving topology is:

- Agent A: host GPU0, port 8080, CPUs `0-2,6-8`
- Agent B: host GPU1, port 8081, CPUs `3-5,9-11`
- both configured for `131072` context
- KV cache INT8
- `kv_resident=32768`
- mmap experts
- 7283 expert-cache slots per agent, approximately 9.75 GiB VRAM
- no `experts.bin`

Earlier diagnostic runs established concurrent 32K, 64K and ~125K operation. The clean 32K concurrent diagnostic had zero prefix reuse and measured approximately 746.8 / 762.6 prefill tok/s for A/B.

## Formal C2 128K result

The repository includes an adapted direct-Strata implementation of the frozen `v100-llm-test` performance C2 contract:

```bash
bash scripts/52-bench-v100-contract-c2-performance.sh
```

Contract:

- workload: `V100-PERFORMANCE-C2-128K-v1`
- manifest SHA256: `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`
- context: 131072 per request
- output reserve: 4096
- minimum output: 1024
- independent Project A + Project B prompts
- no full-size warmup
- exactly one measured batch
- fresh Strata processes before measurement
- 8 internal Strata context cells reserved by the adapted harness

Successful run on 2026-10-01:

| Metric | Agent A | Agent B |
|---|---:|---:|
| Prompt tokens | 126,967 | 126,968 |
| Output tokens | 1,402 | 1,446 |
| TTFT | 181.762 s | 178.345 s |
| Prefill | **700.5 tok/s** | **714.0 tok/s** |
| Decode | **21.2 tok/s** | **22.5 tok/s** |
| Prefix `cache_n` | 0 | 0 |
| `cached_tokens` | 0 | 0 |
| Expert-cache hit | 88.6% | 89.3% |
| Request wall time | 247.918 s | 242.537 s |

Batch-level result:

```text
submission_skew_s = 0.003766
batch_wall_s      = 247.933
decode_overlap_s  = 60.771
both_busy_samples = 299
both_answering    = 299

mechanical_pass = true
active_overlap  = true
post_health     = true
```

Local result directory from that run:

```text
results/c2-v100-contract-20261001-194809
```

The evidence was also copied into the separate `v100-llm-test` result archive as:

```text
EXP-V100-Q38-STRATA-IQ2XS-2GPU2-C2-PERF-20261001-001
```

with the copied `summary.json` SHA256:

```text
793ed441f305541934ee252829ef7eebe7e127443e24386df7e6e440d1698cbc
```

### Cache interpretation

The successful C2 result is specifically **prefix-cache-free**:

```text
A: cache_n=0, cached_tokens=0
B: cache_n=0, cached_tokens=0
```

Therefore the 700.5 / 714.0 tok/s prefill measurements are not explained by reused conversation/KV prefixes.

This does **not** mean the system is cache-free overall:

- Strata's reported `expert_hit_rate` is the decode expert-cache hit rate, not prefix-cache reuse.
- Each agent pre-fills its GPU expert cache from the routing profile.
- mmap expert reads can benefit from the Linux filesystem page cache.
- prompt working buffers can borrow expert-cache VRAM.

These cache layers must not be conflated.

## Stability note

During an earlier attempt at the same cold-prefix dual long-context workload, the host abruptly reset while both agents were still in prefill above 100K prompt tokens.

Post-reboot diagnostics did not show evidence of:

- host OOM
- a new NVIDIA Xid at the crash time
- a logged kernel panic
- a logged MCE
- a logged thermal trip

The later formal C2 run shown above completed successfully under the same class of dual 127K fresh-prefix load and passed post-run health checks.

Therefore:

- dual independent 128K IQ2_XS serving is demonstrated;
- a full concurrent 127K-prefix + 1K-plus-output C2 run is demonstrated;
- the earlier reset was not reproduced by the successful rerun;
- universal stability under every sustained 128K x2 workload is not claimed.

## Build image

Rebuild only when intentionally changing the Strata/CUDA image:

```bash
git pull --ff-only
bash scripts/20-docker-build-v100.sh
```

The image build is Docker-contained. Do not install a host CUDA toolkit for this deployment.

## Safety / preservation policy

The following containers are validated baselines and should not be deleted casually:

```text
strata-iq2xs-mgpu
strata-iq2xs-single-mmap
strata-iq2xs-agent-a
strata-iq2xs-agent-b
```

Normal operations should use `docker start`, `docker stop`, or `docker restart`. Avoid `docker rm -f` unless deliberately replacing a baseline after its configuration and results have been preserved.

The formal C2 script intentionally restarts the two existing agents to clear process-local request/prefix state before its one measured batch.

## References

- Strata: https://github.com/Niko1221/Strata
- Volta issue: https://github.com/Niko1221/Strata/issues/236
- V100 experimental PR: https://github.com/Niko1221/Strata/pull/130
- V100 multi-GPU measurements: https://github.com/Niko1221/Strata/pull/139
- Multi-GPU docs: https://github.com/Niko1221/Strata/blob/main/docs/MULTI_GPU.md
