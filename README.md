# V100 x2 + Strata + Qwen3.8-Flash-Next

Experimental harness for:

- ThinkStation P520
- Xeon W-2135
- 64 GB DDR4-2400
- Tesla V100 16 GB x2 (sm_70)
- Ubuntu Server 26.04
- target context: 128K

## Current execution policy: Docker-first

The host already has a working NVIDIA 580 driver, Docker 29.1.3, NVIDIA Container Toolkit 1.20.0, and verified GPU passthrough for both V100s. Do **not** install a host CUDA toolkit for this experiment.

The V100 Strata environment is isolated in `Dockerfile.v100`:

- Ubuntu 24.04
- CUDA Toolkit 12.9.1
- Strata engine 0.1.31, pinned to commit `9259cad4cfa3543cd3b8decab5962672b968c649`
- `CMAKE_CUDA_ARCHITECTURES=70`
- `STRATA_EXPERIMENTAL_SM60=ON`
- vision omitted
- the remaining setup.py GPU admission check is patched from sm_75 to sm_70

The model data stays on the host under `/srv/models/strata-data` and is bind-mounted into the containers.

The old native-host scripts are kept only as reference. The Docker workflow below is authoritative.

## 1. Build the V100 image

```bash
git pull
bash scripts/20-docker-build-v100.sh
```

This pulls `nvidia/cuda:12.9.1-devel-ubuntu24.04` and builds a text-only Strata sm_70 engine. It prints an image receipt with nvcc, compiler, Strata commit, and `engine/BUILD.json`.

## 2. Baseline: one Strata server using both V100s

```bash
bash scripts/21-docker-run-multigpu-128k.sh
docker logs -f strata-v100-mgpu
```

Target:

```text
V100 #0 16 GB + V100 #1 16 GB
        |
        +-- Strata layer split
        |
Qwen3.8-Flash-Next Coder IQ1_M
128K / INT8 KV / vision off
```

The first run downloads/prepares the model in `/srv/models/strata-data`.

When the log prints `ready`:

```bash
bash scripts/04-smoke-api.sh http://127.0.0.1:8080
bash scripts/23-docker-bench-multigpu.sh
```

The benchmark sends real long prompts targeting approximately 32K, 64K, and 125K user-content tokens. Merely starting with `--max-context 131072` is not counted as a 128K pass.

Stop the baseline with:

```bash
bash scripts/22-docker-stop-multigpu.sh
```

## 3. True two-agent test

After the multi-GPU baseline is stable:

```bash
bash scripts/30-docker-prepare-dual-agents.sh
bash scripts/31-docker-run-dual-agents.sh
```

Topology:

```text
Agent A container                    Agent B container
host GPU 0                           host GPU 1
V100 16 GB                           V100 16 GB
128K                                 128K
low-RAM mmap experts                 low-RAM mmap experts
127.0.0.1:8080                       127.0.0.1:8081
CPUs 0-2,6-8                         CPUs 3-5,9-11
        \                           /
         \-- shared read-only model data --/
```

Both containers reuse the same model files. Each container sees one physical V100 and uses logical CUDA GPU 0 internally.

Follow logs:

```bash
docker logs -f strata-agent-a
docker logs -f strata-agent-b
```

When both are ready:

```bash
bash scripts/33-docker-bench-dual-agents.sh
```

That benchmark launches both long-context API requests at the same time.

Stop them with:

```bash
bash scripts/32-docker-stop-dual-agents.sh
```

## Goals

Two configurations are deliberately measured separately:

1. **2 x V100 -> one Strata instance**
   - best single-agent residency/performance baseline
   - layer split
   - one request at a time

2. **1 x V100 -> one Strata instance, twice**
   - actual concurrent Agent A + Agent B
   - two independent 128K servers
   - shared model files, shared system RAM/NVMe

The second test determines whether the host bottleneck becomes Xeon W-2135 CPU work, DDR4 bandwidth, Linux page cache, or NVMe reads.

## Why Coder IQ1_M first

Coder IQ1_M has a substantially smaller expert arena than the original Q2/IQ2/IQ3 variants, so it is the least ambiguous first test of the two-independent-server architecture. It is not assumed to be the final preferred model.

After this path works, the same harness can be extended to original Qwen3.8-Flash-Next sizes such as IQ2_XS.

## Host changes

The earlier native-host prerequisite path is retired. The user interrupted it before CUDA installation; only GCC/G++ 14 was added to the host. That does not replace GCC 15 and may be left installed.

No host CUDA toolkit or permanent host memlock change is required for the Docker path. Runtime containers use:

```bash
--ulimit memlock=-1:-1
```

## References

- Strata: https://github.com/Niko1221/Strata
- Volta issue: https://github.com/Niko1221/Strata/issues/236
- V100 experimental PR: https://github.com/Niko1221/Strata/pull/130
- V100 multi-GPU measurements: https://github.com/Niko1221/Strata/pull/139
- Multi-GPU docs: https://github.com/Niko1221/Strata/blob/main/docs/MULTI_GPU.md
