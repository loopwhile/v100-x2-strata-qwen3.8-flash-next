# V100 x2 + Strata + Qwen3.8-Flash-Next

Experimental Docker-first deployment and benchmark harness for running and comparing the original Qwen3.8-Flash-Next quantizations on a Lenovo ThinkStation P520 with two Tesla V100 16 GB GPUs. IQ2_XS remains the preferred deployment; IQ3_XXS and IQ3_S are also measured below.

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

Preferred deployment:

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
scripts/53-bench-q4-v100-contract-c2-performance.sh
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

## IQ3_XXS and IQ3_S formal C2 128K comparison

On 2026-10-04, the same frozen `V100-PERFORMANCE-C2-128K-v1` workload was
run against original Qwen3.8-Flash-Next IQ3_XXS and IQ3_S native packs.

The comparison kept the following controls aligned with the IQ2_XS C2 run:

- Strata 0.1.31, commit `9259cad4cfa3543cd3b8decab5962672b968c649`
- two independent one-V100 agents
- Agent A on GPU0 / CPUs `0-2,6-8`; Agent B on GPU1 / CPUs `3-5,9-11`
- 131072-token context per request
- INT8 KV with `kv_resident=32768`
- GGUF-in-place `--mmap-experts`, with no `experts.bin`
- `--prefill auto`
- `--spec 4 --spec-min-p 0.5`
- shared existing MTP data
- `STRATA_PROMPT_ATTN_OLD=1`
- fresh Strata processes, no full-size warmup
- prefix `cache_n=0` and `cached_tokens=0`
- the same frozen manifest SHA256:
  `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`

The C2 harness now accepts `--expected-model-a` and `--expected-model-b` so
the same workload runner can validate non-IQ2_XS model names without changing
the frozen workload or its materialization.

### IQ3_XXS result

Successful run on 2026-10-04:

| Metric | Agent A | Agent B |
|---|---:|---:|
| Prompt tokens | 126,967 | 126,968 |
| Output tokens | 1,627 | 2,506 |
| TTFT | 206.324 s | 202.460 s |
| Prefill | **617.1 tok/s** | **629.0 tok/s** |
| Decode | **10.9 tok/s** | **12.0 tok/s** |
| Prefix `cache_n` | 0 | 0 |
| `cached_tokens` | 0 | 0 |
| Expert-cache hit | 74.8% | 77.5% |
| File-tier reads reported by Strata | 352,725.5 MB | 481,364.7 MB |
| Request wall time | 355.536 s | 411.259 s |

Batch-level result:

~~~text
submission_skew_s = 0.003845
batch_wall_s      = 411.269
decode_overlap_s  = 149.212
both_busy_samples = 734
both_answering    = 734

mechanical_pass = true
active_overlap  = true
post_health     = true
~~~

Local result directory:

~~~text
results/c2-iq3xxs-v100-contract-20261004-151015
~~~

### IQ3_S result

Successful run on 2026-10-04:

| Metric | Agent A | Agent B |
|---|---:|---:|
| Prompt tokens | 126,967 | 126,968 |
| Output tokens | 1,872 | 1,515 |
| TTFT | 213.225 s | 209.501 s |
| Prefill | **597.0 tok/s** | **607.8 tok/s** |
| Decode | **10.1 tok/s** | **11.4 tok/s** |
| Prefix `cache_n` | 0 | 0 |
| `cached_tokens` | 0 | 0 |
| Expert-cache hit | 74.0% | 78.2% |
| File-tier reads reported by Strata | 483,553.9 MB | 331,848.4 MB |
| Request wall time | 398.902 s | 342.008 s |

Batch-level result:

~~~text
submission_skew_s = 0.003909
batch_wall_s      = 398.911
decode_overlap_s  = 128.779
both_busy_samples = 633
both_answering    = 633

mechanical_pass = true
active_overlap  = true
post_health     = true
~~~

Local result directory:

~~~text
results/c2-iq3s-v100-contract-20261004-145554
~~~

### Quantization comparison

Averaging the two agents' engine-reported rates gives:

| Model | Avg prefill | Avg decode | Avg expert hit |
|---|---:|---:|---:|
| IQ2_XS | **707.3 tok/s** | **21.85 tok/s** | **88.95%** |
| IQ3_XXS | **623.1 tok/s** | **11.45 tok/s** | **76.15%** |
| IQ3_S | **602.4 tok/s** | **10.75 tok/s** | **76.10%** |

Relative to IQ2_XS under this C2 topology:

- IQ3_XXS prefill was about 11.9% lower and decode about 47.6% lower.
- IQ3_S prefill was about 14.8% lower and decode about 50.8% lower.
- Both IQ3 variants averaged about 76.1% expert-cache hit rate, roughly 12.8
  percentage points below IQ2_XS.
- IQ3_XXS was only about 3.4% faster in average prefill and 6.5% faster in
  average decode than IQ3_S in these single measured batches.

The similar IQ3_XXS and IQ3_S expert-hit rates, together with their much lower
decode throughput than IQ2_XS, are consistent with an expert-residency /
miss-path bottleneck once the working set grows beyond the IQ2_XS case. This
benchmark does not isolate that mechanism as the sole cause.

Host-memory exhaustion was not observed in either IQ3 run. The IQ3_S run ended
with about 49 GiB available RAM and 4.8 MiB of swap in use; the IQ3_XXS run
ended with about 49 GiB available and 29.6 MiB of swap in use. End-of-run GPU
temperatures were 53/46 C for IQ3_S and 51/48 C for IQ3_XXS, so these completed
runs do not show evidence of thermal throttling as the dominant limitation.

The reported `file_mb` counters can greatly exceed the physical GGUF size and
should be treated as Strata's cumulative file-tier traffic metric, not as the
size of the model or a direct measurement of physical NVMe bytes read.

Storage is one remaining uncontrolled variable in the cross-quant comparison:
IQ3_XXS was stored under `/srv/models/strata-iq3xxs` on the dedicated model
NVMe, while IQ3_S was stored under `/models/strata-iq3s` on the root NVMe.
Therefore the table is a controlled workload/runtime comparison, but not a
strict quant-only storage A/B.

Under the current Strata 0.1.31 dual-agent topology, IQ2_XS remains the
preferred performance configuration. No direct model-quality benchmark has
been run, so these measurements make no quality claim for IQ2_XS, IQ3_XXS, or
IQ3_S.

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

## Experimental UD-Q4_K_XL result

Strata 0.1.31 was also tested with Unsloth's
`Qwen3.8-Flash-Next-UD-Q4_K_XL` on the same V100 x2 host.

The downloaded model consisted of four GGUF shards, approximately 104 GB total.
A native Strata pack of approximately 1.4 GB was generated with
`tools/iq_pack.py --compat-bf16`.

No `experts.bin` was created. Routed experts were mmap-read directly from the
original GGUF shards.

The validated experimental topology was:

- Agent A: Tesla V100 16 GB GPU0, CPUs `0-2,6-8`
- Agent B: Tesla V100 16 GB GPU1, CPUs `3-5,9-11`
- 131072-token context per agent
- INT8 KV
- `kv_resident=32768`
- `--mmap-experts`
- `--resident-budget-gib 16` per agent
- 2692 GPU expert-cache slots per agent
- approximately 7.85 GiB of expert-cache VRAM per agent
- shared existing MTP data

Both independent 128K agents loaded successfully and completed concurrent
inference.

### Q4 formal C2 128K result

The same frozen `V100-PERFORMANCE-C2-128K-v1` workload used for the IQ2_XS
measurement was run once against the Q4 dual-agent topology.

Contract:

- manifest SHA256: `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`
- context: 131072 per request
- output reserve: 4096
- minimum output: 1024
- independent Project A + Project B prompts
- no full-size warmup
- exactly one measured batch
- fresh Strata processes before measurement

Successful run on 2026-10-02:

| Metric | Agent A | Agent B |
|---|---:|---:|
| Prompt tokens | 126,967 | 126,968 |
| Output tokens | 1,924 | 1,341 |
| TTFT | 850.706 s | 851.149 s |
| Prefill | **149.4 tok/s** | **149.4 tok/s** |
| Decode | **3.1 tok/s** | **3.3 tok/s** |
| Prefix `cache_n` | 0 | 0 |
| `cached_tokens` | 0 | 0 |
| Expert-cache hit | 58.9% | 65.2% |
| RAM-tier blobs | 204,108 | 157,410 |
| File-tier blobs | 213,743 | 115,566 |
| File-tier reads | 615,572.4 MB | 294,972.1 MB |
| Request wall time | 1471.416 s | 1257.075 s |

Batch-level result:

~~~text
submission_skew_s = 0.003769
batch_wall_s      = 1471.425
decode_overlap_s  = 405.926
both_busy_samples = 1974
both_answering    = 1974

mechanical_pass = true
active_overlap  = true
post_health     = true
~~~

The Q4 run therefore demonstrated that `UD-Q4_K_XL` can technically run as two
independent 128K Strata agents on two Tesla V100 16 GB GPUs.

Performance, however, was substantially below the validated IQ2_XS topology.

For the same formal C2 workload:

| Model | Prefill A/B | Decode A/B | Batch wall |
|---|---:|---:|---:|
| IQ2_XS | 700.5 / 714.0 tok/s | 21.2 / 22.5 tok/s | 247.933 s |
| UD-Q4_K_XL | 149.4 / 149.4 tok/s | 3.1 / 3.3 tok/s | 1471.425 s |

Relative to IQ2_XS, the Q4 experiment was approximately:

- 4.7x slower in long-context prefill
- 6.4-6.8x slower in decode
- 5.9x longer in total batch wall time
- approximately 14.2 minutes TTFT per request

The Q4 topology also placed substantial pressure on the 64 GB host memory.
With two 16 GiB resident expert tiers, the 4 GiB swap file approached
saturation during the 128K concurrent workload, while large amounts of expert
data continued to be served from the GGUF file tier.

The result is therefore recorded as a successful compatibility and feasibility
test, but `UD-Q4_K_XL` is not considered practical for the intended dual-agent
128K workload on this P520.

IQ2_XS remains the preferred deployment for this machine.

Local result directory:

~~~text
results/c2-q4-v100-contract-20261002-164957
~~~

The result directory is excluded by the repository's `results/` gitignore rule.
The measured `summary.json` SHA256 is:

~~~text
f5f6427eb063af3ff61f7e2090219ca36f32c0d4f0bd758b3afdd7bb4f74d6dc
~~~

The Q4 GGUF files and generated pack were removed after testing, recovering
approximately 105 GB of model-NVMe capacity. The Q4 benchmark harness and
launcher are retained for reproducibility.

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
