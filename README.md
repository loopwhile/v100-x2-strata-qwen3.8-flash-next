# Qwen3.8-Flash-Next on Dual Tesla V100 GPUs with Strata

A reproducible deployment and benchmarking project for running **Qwen3.8-Flash-Next** on a Lenovo ThinkStation P520 equipped with two NVIDIA Tesla V100 16 GB GPUs.

The project explores how far legacy Volta hardware can be pushed using [Strata](https://github.com/Niko1221/Strata), GGUF quantization, memory-mapped experts, and independent GPU inference servers. The primary goal is to operate **two independent coding agents**, each supporting a **131,072-token context window**.

This repository documents the experimental progression from initial Volta compatibility through dual-agent deployment, quantization comparisons, upstream engine upgrades, optional V100 tuning, and mixed-quantization co-residency.

> **Stage 5 (completed — IQ3_S software-only optimization):** [Stage 5 plan and results](docs/STAGE5_PLAN.md) executed 3-batch fresh-process 128K C2 replications across upstream 0.1.47 (`T1`–`T4`), upstream 0.1.50 (`T6`, `T8`), and the updated V100 fork (`T7`, `T7-Fixed`). **T7-Fixed** (`jmnargi/Strata-V100@2c9b1dd` + `STRATA_SM70_PERF=0` + `STRATA_SELECT_SIMT=1` + `STRATA_PF_WMMA=1` + `STRATA_PF_WMMA2=1` + `STRATA_STAGER_SSD=0`) raised IQ3_S 128K prefill from Stage 4-B's 535.00 tok/s to **899.23 tok/s 3-run mean (905.40 tok/s median, 930.35 tok/s batch peak / 939.0 tok/s single-agent peak)** while preserving **21.45 tok/s mean decode (22.6 tok/s peak)** and cutting batch wall time to **212.18 s mean (205.85 s best)**. On pure upstream 0.1.47, **T4** achieved **887.37 tok/s mean prefill** and **21.20 tok/s decode** (`228.92 s` mean wall time).

> **Stage 6 (prepared, NOT run):** [Isolated IQ3_S decode-optimization containers and safety-first execution instructions](docs/STAGE6_PREP.md) reuse Stage 5 T7-Fixed on two independent V100s, with new test containers/loopback ports 18082/18083. The goal is **>=30 tok/s decode on each agent concurrently**; no Stage 6 result or production change is implied.

> **Current performance recommendations:** For **maximum throughput**, two independent **IQ2_XS** agents using **upstream Strata 0.1.47** remain fastest (**995.70 tok/s** prefill, **39.60 tok/s** decode in Stage 4-C; **981.55 / 38.50 tok/s** in vanilla Stage 4-B). For **higher-precision IQ3_S**, Stage 5 **T7-Fixed** (**899.23 tok/s** prefill, **21.45 tok/s** decode) or upstream **T4** (**887.37 tok/s** prefill, **21.20 tok/s** decode) is recommended. The preserved Stage 3-A deployment remains available for rollback. A benchmark result does not imply that its containers have been promoted to production.

---

## 1. Hardware Specifications

### 1.1 Lenovo ThinkStation P520

| Component | Specification |
| --- | --- |
| Workstation | Lenovo ThinkStation P520 |
| CPU | Intel Xeon W-2135, Skylake-W |
| CPU cores / threads | 6 / 12 |
| CPU frequency | 3.70 GHz base / 4.50 GHz turbo |
| System RAM | 64 GB DDR4-2400 ECC, approximately 61 GiB usable |
| GPU 0 | NVIDIA Tesla V100 16 GB |
| GPU 1 | NVIDIA Tesla V100 16 GB |
| Architecture | NVIDIA Volta, compute capability 7.0 (`sm_70`) |
| Combined GPU VRAM | 32 GB across **two separate GPUs**, not a unified memory pool |
| Operating system | Ubuntu Server 26.04.1 LTS |
| NVIDIA driver | 580.178.04 |
| Docker | Docker CE 29.1.3 |
| NVIDIA Container Toolkit | 1.20.0 |
| CUDA toolkit | 12.9.1 inside the Docker build images |
| Documented GPU power cap | 150 W per GPU, unchanged during Stage 4 |

The Xeon W-2135 supports AVX2 but does not meet the AVX-512 requirements of some newer Strata IQ expert CPU fast paths. Host-side expert processing, memory bandwidth, and storage activity can therefore limit performance even though the inference servers use separate GPUs.

### 1.2 Storage

| Storage | Role |
| --- | --- |
| Samsung 256 GB NVMe SSD | Primary model data under `/srv/models` |
| System NVMe | Ubuntu and some historical or additional model assets |
| Western Digital 1 TB SATA HDD | Cold archive under `/srv/backup` |

The validated IQ2_XS model physically resides under `/srv/models/strata-iq2xs`. Historical configurations also use the verified compatibility symlink:

```text
/home/loopwhile/models/strata-iq2xs -> /srv/models/strata-iq2xs
```

The historical relocation was verified using SHA-256 checksums across 19 files before removing the redundant copy under `/home`.

### 1.3 ThinkPad E14 client

The ThinkPad E14 is the development and orchestration machine, not the inference host. It handles Git work, Antigravity CLI and coding agents, SSH access to the P520, and local forwarding of the two OpenAI-compatible endpoints.

---

## 2. System Architecture

### 2.1 Two experimental topologies

**Topology A — One server spanning two V100s:** one Strata process uses both physical GPUs for one inference endpoint. This establishes a single-agent performance and feasibility baseline.

**Topology B — Two independent servers:** Agent A has GPU 0 and Agent B has GPU 1. Both have independent 128K context windows and can serve separate requests concurrently. **Topology B is the intended operational design.**

### 2.2 End-to-end request flow

```text
                        ThinkPad E14
                   Antigravity CLI / Git
                 OpenAI-compatible client
                              |
                       ssh p520 tunnel
                              |
                +-------------+-------------+
                |                           |
         127.0.0.1:18080            127.0.0.1:18081
                |                           |
                v                           v
       P520 127.0.0.1:8080          P520 127.0.0.1:8081
                |                           |
     +----------+-----------+   +-----------+----------+
     |       Agent A        |   |        Agent B       |
     |  Independent Docker  |   |   Independent Docker |
     |  Host GPU 0: V100    |   |   Host GPU 1: V100   |
     |  16 GB VRAM          |   |   16 GB VRAM         |
     |  CPUs 0-2,6-8        |   |   CPUs 3-5,9-11      |
     |  Context: 131072     |   |   Context: 131072    |
     |  INT8 KV cache       |   |   INT8 KV cache      |
     +----------+-----------+   +-----------+----------+
                |                           |
                +-------------+-------------+
                              |
                  Shared P520 host resources
                 +---------------------------+
                 | Xeon W-2135 / 64 GB RAM  |
                 | Linux filesystem cache  |
                 | DDR4 memory bandwidth   |
                 | NVMe / GGUF model files |
                 | Shared MTP model data   |
                 +---------------------------+
```

### 2.3 GPU assignment and API ports

| Resource | Agent A | Agent B |
| --- | --- | --- |
| Host GPU | GPU 0 | GPU 1 |
| Dedicated GPU VRAM | 16 GB | 16 GB |
| CPU affinity | `0-2,6-8` | `3-5,9-11` |
| Container port | 8080 | 8080 |
| P520 host port | 8080 | 8081 |
| ThinkPad tunnel port | 18080 | 18081 |
| Context | 131072 | 131072 |
| KV precision | INT8 | INT8 |

**Why does each JSON say `"gpu": 0`?** Each Docker container sees only its assigned physical GPU, renumbered to container-local GPU 0. This is not a conflict.

### 2.4 Shared resources and mmap expert weights

The GPU allocations and CPU affinities are separate, but the agents still compete for host RAM, memory bandwidth, Linux page cache, NVMe throughput, and parts of the host-side execution pipeline.

Strata's `--mmap-experts` option reads routed expert weights directly from original GGUF files. In a homogeneous deployment, two agents mapping the **same physical GGUF files** can share file-backed pages in the Linux page cache. Different quantizations use different GGUF files and do not share those expert pages. This distinction became decisive in the Stage 4-B mixed test.

---

## 3. Model Configuration

### 3.1 Qwen3.8-Flash-Next GSQ-RCO GGUF

- **Model source:** [ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF)
- **Pinned model revision:** `ed59f92082b1e93c0e96d60a8b11aab089b52f09`
- **Architecture:** Mixture-of-Experts; non-uniform GSQ/RCO GGUF quantizations
- **Inference mode:** text-only; no vision projector loaded in these experiments
- **Expert access:** original GGUF shards mapped in place, with a separate native Strata pack
- **Shared speculation assets:** read-only MTP data under `/srv/models/strata-data/mtp`

| Quantization | Role | Observed status |
| --- | --- | --- |
| **IQ2_XS** | Performance-oriented deployment | Preferred for maximum throughput |
| IQ3_XXS | Higher-precision candidate | Tested across Stages 2–4 |
| **IQ3_S** | Higher-precision candidate | Tested across Stages 2–5 (Stage 5 optimized: **899.23 tok/s** prefill, **21.45 tok/s** decode) |
| UD-Q4_K_XL | High-bit-width feasibility | Functional, impractically slow at 128K ×2 |

Official model-card scores are **not** measurements of real coding-agent task completion on this P520. The repository's C2 results measure inference performance, not code correctness.

### 3.2 Standard dual-agent runtime recipe

The Stage 3-A and Stage 4 primary comparisons use the following baseline arguments:

```bash
--max-context 131072
--kv int8
--kv-resident 32768
--expert-cache auto
--prefill auto
--spec 4
--spec-min-p 0.5
--mmap-experts
```

Each agent has its own native pack and log but shares model files with the other agent when both use the same quantization. The model and MTP mounts are read-only. The original IQ2_XS pack is approximately 1.5 GB; it does **not** contain a separate `experts.bin`.

---

## 4. Docker Runtime and Strata Versions

| Stage | Engine | Docker image | Purpose |
| --- | --- | --- | --- |
| Stage 2 | 0.1.31 | `strata-v100:0.1.31` | Original Volta baseline |
| Stage 3-A | 0.1.36 | `strata-v100-jmnargi:9d77749` | V100 fork |
| Stage 3-B | 0.1.36 | `strata-v100-jmnargi:9d77749` | Speculation/paired-expert tuning |
| Stage 4-A | 0.1.44.1 | `strata-v100-upstream:0.1.44.1` | First upstream migration |
| Stage 4-B | 0.1.47 | `strata-v100-upstream:0.1.47` | Vanilla newer upstream engine |
| Stage 4-C | 0.1.47 | `strata-v100-upstream:0.1.47` | Same image, `STRATA_SM70_TABLE=1` |
| Stage 5 (T1–T4) | 0.1.47 | `strata-v100-upstream:0.1.47` | IQ3_S 3-batch baseline & SIMT/WMMA ablations |
| Stage 5 (T6, T8) | 0.1.50 | `strata-v100-upstream:0.1.50` | Upstream v0.2.6 Qwen engine 0.1.50 |
| Stage 5 (T7, T7-Fixed) | 0.1.45.3 (`2c9b1dd`) | `strata-v100-jmnargi:2c9b1dd` | Updated V100 fork (PR #74 IQ3_S WMMA2 + PR #80 prefill scheduler) |

### 4.1 Why CUDA 12.9.1?

V100 is Volta (`sm_70`). CUDA 13 removed Volta device-code generation, so the images use CUDA 12.9.1 even with a newer host NVIDIA driver. No separate host CUDA toolkit is required for normal Docker inference.

For the upstream experimental older-GPU build, the critical CMake flags are:

```bash
-DSTRATA_ENABLE_CUDA=ON
-DSTRATA_EXPERIMENTAL_SM60=ON
-DCMAKE_CUDA_ARCHITECTURES=70
```

The older pinned `jmnargi/Strata-V100` fork has its own Volta support and does not require exactly the same patch/build procedure as upstream.

### 4.2 Effective defaults can differ

An unchanged JSON file does not guarantee identical runtime behavior across engine versions. New Strata releases may change expert-routing policies, cache behavior, prompt or decode kernels, and scheduling defaults. Record the engine revision, image ID, effective environment, model config, and logs with every benchmark result.

---

## 5. Day-to-Day Operations

### 5.1 Preserved operational baseline

The known Stage 3-A IQ2_XS pair is:

```text
strata-jmn-iq2xs-agent-a
strata-jmn-iq2xs-agent-b
```

These use the 0.1.36 V100 fork and were preserved throughout Stage 4. The repository cannot establish which pair is **currently running**; verify on P520 before changing anything.

**Do not create a new container to perform a routine start.** Existing containers are intentionally retained for reproducibility and rollback.

### 5.2 P520: start, inspect, and stop

Run locally on P520, or prefix the equivalent commands with `ssh p520` from ThinkPad.

Start the preserved Stage 3-A pair **only if GPUs and ports are free**:

```bash
docker start strata-jmn-iq2xs-agent-a strata-jmn-iq2xs-agent-b
```

Inspect active containers:

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
docker ps -a --filter name=strata-jmn-iq2xs
```

Check the API endpoints and loaded model IDs:

```bash
curl -fsS http://127.0.0.1:8080/health
echo
curl -fsS http://127.0.0.1:8081/health
echo

curl -fsS http://127.0.0.1:8080/v1/models
echo
curl -fsS http://127.0.0.1:8081/v1/models
echo
```

Inspect logs:

```bash
docker logs -f --tail 50 strata-jmn-iq2xs-agent-a
# In a separate terminal:
docker logs -f --tail 50 strata-jmn-iq2xs-agent-b
```

Stop **without deleting**:

```bash
docker stop strata-jmn-iq2xs-agent-a strata-jmn-iq2xs-agent-b
```

### 5.3 ThinkPad SSH tunnel

The existing ThinkPad service is `strata-tunnel.service`. It forwards the P520 host ports to:

```text
Agent A: http://127.0.0.1:18080/v1
Agent B: http://127.0.0.1:18081/v1
```

Inspect or restart the tunnel from ThinkPad:

```bash
systemctl --user status strata-tunnel
systemctl --user restart strata-tunnel
journalctl --user -u strata-tunnel -f
```

The tunnel does **not** select the quantization or engine. The active container connected to each P520 port determines the model.

### 5.4 Isolated Stage 4 candidates

| Test | Agent A | Agent B |
| --- | --- | --- |
| Stage 4-B IQ2_XS | `strata-s4b-iq2xs-agent-a` | `strata-s4b-iq2xs-agent-b` |
| Stage 4-C IQ2_XS | `strata-s4c-iq2xs-agent-a` | `strata-s4c-iq2xs-agent-b` |
| Stage 4-B mixed | `strata-s4b-mixed-iq3xxs-agent-a` | `strata-s4b-mixed-iq2xs-agent-b` |

All historical containers and launch scripts should remain available. Never run conflicting pairs simultaneously on the same GPUs or host ports, and do not silently promote a benchmark container into a serving role.

---

## 6. Benchmark Methodology

### 6.1 Frozen 128K C2 contract

The main benchmark is `V100-PERFORMANCE-C2-128K-v1`:

- **Workload file:** [`bench/workloads/v100-performance-v1.json`](bench/workloads/v100-performance-v1.json)
- **Manifest SHA-256:** `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`
- **Two independent synthetic projects:** storage-engine review (A) and async-scheduler review (B)
- **Context:** 131072 tokens per request
- **Actual prompt tokens:** A = 126967, B = 126968
- **Generation reserve:** 4096 tokens; **minimum output:** 1024 tokens per agent
- **Execution:** synchronized launch barrier, fresh Strata processes, no full-size warmup
- **Prefix reuse:** `cache_n=0` and `cached_tokens=0`
- **Concurrency:** both agents must actively overlap in decode
- **Validation:** prompt count, nonempty output, mechanical checks, and post-test health

The direct-Strata harness is [`bench/c2_v100_contract.py`](bench/c2_v100_contract.py). Some historical wrappers restart **only their selected benchmark containers**; inspect the targeted names first.

### 6.2 What the caches mean

| Mechanism | Meaning | Interpretation |
| --- | --- | --- |
| Prefix/KV cache | Reused request prefix | C2 requires zero prefix reuse |
| GPU expert cache | Hot routed expert weights held in VRAM | Reflected in expert hit rate |
| Linux page cache | Host RAM pages backing mmap GGUF files | Can be shared for the same physical model files |
| Storage file tier | Expert weights read beyond GPU/RAM residency | May introduce page faults and I/O stalls |

**Zero prefix reuse does not mean zero expert-cache or filesystem-cache benefit.** The Strata `file_mb` counters are cumulative logical file-tier metrics; do not treat them automatically as exact physical NVMe bytes read.

### 6.3 Measurement limits

Most Stage 2–4 arms have **one formal cold C2 batch**, with per-agent observations from that batch. The A/B observations are not separate independent experimental repetitions. In particular, small differences such as 38.50 vs 39.60 tok/s require repeated runs before being considered reliable tuning wins.

In **Stage 5**, every candidate arm (`T1`, `T2`, `T3`, `T4`, `T6-Fixed`, `T7`, `T7-Fixed`, `T8`) was evaluated using **three consecutive fresh-process C2 batches** (`docker restart` before each batch, `requests_kept == 0`), reporting 3-run means, medians, and ranges alongside host `vmstat`, `iostat`, `pidstat`, `fincore`, and GPU telemetry.

Longer generated outputs also change batch wall time. C2 performance numbers are not a direct comparison of coding quality.

---

## 7. Benchmark History — Chronological

### Stage 1 — Initial Volta compatibility and topology exploration

**Date:** October 1, 2026.

The project began with a Coder IQ1_M target and two architectures: one server spanning both V100s and two separate one-V100 servers. The initial work established that a CUDA 12.x Volta-compatible build and real long-context API tests were necessary.

Later IQ2_XS tests established the following **single-server, dual-GPU** reference:

| Approximate prompt | Prefill | Decode |
| --- | ---: | ---: |
| 32K | 1329.6 tok/s | 44.9 tok/s |
| 64K | 1398.9 tok/s | 43.9 tok/s |
| 125K | 1331.3 tok/s | 48.1 tok/s |

A separate **single-V100 IQ2_XS mmap** 32K test measured approximately 723.8 prefill tok/s, 17.6 decode tok/s, and an 82.2% expert-cache hit rate.

These diagnostic topologies and prompts are **not directly comparable** to the dual-independent 128K C2 contract.

### Stage 2 — Original IQ2_XS dual-independent 128K deployment

**Date:** October 1, 2026. **Engine:** Strata 0.1.31.

The initial formal IQ2_XS cold C2 test established a successful two-agent reference:

| Metric | Agent A | Agent B | Mean |
| --- | ---: | ---: | ---: |
| Prompt tokens | 126967 | 126968 | — |
| Prefill (tok/s) | 700.5 | 714.0 | **707.25** |
| Decode (tok/s) | 21.2 | 22.5 | **21.85** |
| TTFT (s) | 181.762 | 178.345 | **180.05** |
| Expert hit | 88.6% | 89.3% | **88.95%** |

```text
batch_wall_s      = 247.933
decode_overlap_s  = 60.771
pass_mechanical   = true
active_overlap    = true
post_health       = true
cache_n           = 0 / 0
cached_tokens     = 0 / 0
```

Historical result archive identifier:

```text
EXP-V100-Q38-STRATA-IQ2XS-2GPU2-C2-PERF-20261001-001
```

#### Stage 2 extension — UD-Q4_K_XL feasibility

**Date:** October 2, 2026. **Engine:** 0.1.31.

An Unsloth UD-Q4_K_XL model with four GGUF shards (approximately 104 GB) loaded successfully as two independent V100 agents, but its 128K C2 performance was not practical:

| Metric | Agent A | Agent B |
| --- | ---: | ---: |
| Prefill (tok/s) | 149.4 | 149.4 |
| Decode (tok/s) | 3.1 | 3.3 |
| TTFT (s) | 850.706 | 851.149 |
| Expert hit | 58.9% | 65.2% |

Batch wall: **1471.425 s**; decode overlap: **405.926 s**; C2 validation passed. The substantial host memory, swap, and file-tier pressure made the topology unsuitable for routine dual-agent service. The temporary Q4 GGUF and pack were later deleted to reclaim model NVMe space, while benchmark scripts and records were kept.

#### Stage 2 extension — IQ3_XXS and IQ3_S

**Date:** October 4, 2026. **Engine:** 0.1.31.

The same frozen C2 workload was run on the two IQ3 variants:

| Quantization | Mean prefill | Mean decode | Expert hit |
| --- | ---: | ---: | ---: |
| **IQ2_XS** | **707.25** | **21.85** | **88.95%** |
| IQ3_XXS | 623.05 | 11.45 | 76.15% |
| IQ3_S | 602.40 | 10.75 | 76.10% |

The large IQ3 decode gap was consistent with higher expert residency or miss-path costs, but the experiment did not isolate a unique cause.

### Stage 3-A — V100-optimized Strata 0.1.36 fork

**Date:** October 4, 2026.

- **Source:** [jmnargi/Strata-V100](https://github.com/jmnargi/Strata-V100)
- **Pinned commit:** `9d7774919e26d235359bc2c3001f61f607eb288d`
- **Image:** `strata-v100-jmnargi:9d77749`
- **Recipe:** same `--spec 4 --spec-min-p 0.5`, mmap experts, 128K/INT8 KV and frozen workload

| Model | Stage 2 prefill | Stage 3-A prefill | Stage 2 decode | Stage 3-A decode | Stage 3-A TTFT |
| --- | ---: | ---: | ---: | ---: | ---: |
| IQ2_XS | 707.25 | **909.90** | 21.85 | **22.20** | 140.09 s |
| IQ3_XXS | 623.05 | **790.95** | 11.45 | **12.70** | 161.08 s |
| IQ3_S | 602.40 | **721.30** | 10.75 | **10.65** | 176.62 s |

Long-context prefill improved by approximately **28.7%** for IQ2_XS, **26.9%** for IQ3_XXS, and **19.7%** for IQ3_S. The high-precision IQ3 decode slowdown largely remained.

### Stage 3-B — Speculative-window and paired-expert tuning

**Date:** October 4, 2026. **Engine:** 0.1.36.

Only the following speculative tuning bundle changed:

```text
Stage 3-A:
  --spec 4 --spec-min-p 0.5
  STRATA_EXPERT_PAIR unset

Stage 3-B:
  --spec 8 --spec-min-p 0.7
  STRATA_EXPERT_PAIR=1
```

| Model | Stage 3-A prefill | Stage 3-B prefill | Stage 3-A decode | Stage 3-B decode | Stage 3-B TTFT |
| --- | ---: | ---: | ---: | ---: | ---: |
| IQ2_XS | 909.90 | **925.45** | 22.20 | **23.90** | 137.73 s |
| IQ3_XXS | 790.95 | **815.05** | 12.70 | **12.75** | 156.35 s |
| IQ3_S | 721.30 | **731.15** | 10.65 | **10.70** | 174.25 s |

This bundle did not meaningfully resolve IQ3 decode. IQ2_XS improved in the observed mean, but the Agent A/B spread was wide. Stage 3-A remained the conservative shared recipe.

### Stage 4-A — Upstream Strata 0.1.44.1

**Date:** October 21, 2026.

The project built upstream Strata 0.1.44.1 for Volta in a separate image without overwriting the Stage 3-A baseline. The original IQ2_XS C2 inputs, quantization, context, and KV settings were maintained.

| Metric | Stage 3-A | Stage 4-A |
| --- | ---: | ---: |
| Prefill (tok/s) | 909.90 | **939.40** |
| Decode (tok/s) | 22.20 | **31.65** |
| TTFT (s) | 140.09 | **135.41** |
| Expert hit | 88.75% | **91.60%** |

Decode improved **42.6%** over Stage 3-A in the recorded batch.

[Build receipt](artifacts/stage4-results-20261021/stage4-a-build-receipt.md) · [C2 summary](artifacts/stage4-results-20261021/stage4-a-c2-benchmark-summary.md)

### Stage 4-B — Upstream Strata 0.1.47 (vanilla)

**Date:** October 21–22, 2026. **Engine:** 0.1.47 bundled with the Strata v0.2.2 release.

The updated upstream engine was built for `sm_70` with CUDA 12.9.1. The primary Stage 4-B tests did **not** enable `STRATA_SM70_TABLE=1`.

| Quantization | Mean prefill | Mean decode | Mean TTFT | Expert hit |
| --- | ---: | ---: | ---: | ---: |
| **IQ2_XS** | **981.55** | **38.50** | **129.60 s** | **93.55%** |
| IQ3_XXS | 725.50 | 26.15 | 175.27 s | 86.30% |
| IQ3_S | 535.00 | 21.35 | 237.60 s | 81.50% |

Relative to Stage 3-A, measured decode throughput increased **73.4%** for IQ2_XS, **105.9%** for IQ3_XXS, and **100.5%** for IQ3_S. The majority of the IQ3 decode improvement was already visible before optional SM70 table tuning.

However, Stage 4-B IQ3_XXS and IQ3_S prefill remained slower than Stage 3-A in the recorded runs.

[Build receipt](artifacts/stage4-results-20261021/stage4-b-build-receipt.md) · [IQ2_XS](artifacts/stage4-results-20261021/stage4-b-c2-benchmark-summary.md) · [IQ3_XXS](artifacts/stage4-results-20261021/stage4-b-iq3xxs-c2-benchmark-summary.md) · [IQ3_S](artifacts/stage4-results-20261021/stage4-b-iq3s-c2-benchmark-summary.md)

### Stage 4-C — Optional Volta SM70 table kernels

**Date:** October 21, 2026. **Engine:** 0.1.47.

Stage 4-C reused the Stage 4-B image, adding only `STRATA_SM70_TABLE=1` to the relevant serving runtime.

| Model | Stage | Mean prefill | Mean decode | Mean TTFT |
| --- | --- | ---: | ---: | ---: |
| IQ2_XS | 4-B vanilla | 981.55 | 38.50 | 129.60 s |
| **IQ2_XS** | **4-C SM70** | **995.70** | **39.60** | **127.77 s** |
| **IQ3_XXS** | **4-B vanilla** | **725.50** | **26.15** | **175.27 s** |
| IQ3_XXS | 4-C SM70 | 630.70 | 26.05 | 201.60 s |
| **IQ3_S** | **4-B vanilla** | **535.00** | **21.35** | **237.60 s** |
| IQ3_S | 4-C SM70 | 468.05 | 20.55 | 271.60 s |

**Observations:** Stage 4-C recorded the best single-run IQ2_XS prefill/decode/TTFT. Stage 4-B recorded better IQ3 prefill and TTFT, while IQ3 decode was similar under both runtime settings. Since these are single batches, repeat before treating small optimization differences as stable.

[IQ2_XS](artifacts/stage4-results-20261021/stage4-c-c2-benchmark-summary.md) · [IQ3_XXS](artifacts/stage4-results-20261021/stage4-c-iq3xxs-c2-benchmark-summary.md) · [IQ3_S](artifacts/stage4-results-20261021/stage4-c-iq3s-c2-benchmark-summary.md)

### Stage 4-B mixed — IQ3_XXS Agent A + IQ2_XS Agent B

**Date:** October 22, 2026. **Engine:** vanilla Strata 0.1.47.

The project deliberately placed **different quantizations** on the two independent GPUs:

| Resource | Agent A | Agent B |
| --- | --- | --- |
| Model | IQ3_XXS | IQ2_XS |
| Host GPU | 0 | 1 |
| CPU affinity | `0-2,6-8` | `3-5,9-11` |
| P520 port | 8080 | 8081 |
| ThinkPad port | 18080 | 18081 |

The baseline comparisons below use the **same physical-GPU position** from the prior homogeneous Stage 4-B runs.

| Metric | A homogeneous IQ3_XXS | **A mixed IQ3_XXS** | B homogeneous IQ2_XS | **B mixed IQ2_XS** |
| --- | ---: | ---: | ---: | ---: |
| Prefill (tok/s) | 720.4 | **138.8** | 988.5 | **593.9** |
| Decode (tok/s) | 27.1 | **7.9** | 36.6 | **22.6** |
| TTFT (s) | 176.50 | **914.90** | 128.69 | **214.04** |
| Expert hit | 88.4% | 89.2% | 92.6% | 91.9% |

Batch duration was **1077.63 s**, approximately 18 minutes. The individual prompts were valid (126967/126968 tokens), outputs exceeded 1024 tokens, and prefix reuse remained zero; nevertheless the central concurrency check **failed**:

```text
pass_mechanical = true
post_health     = true
active_overlap  = false
decode_overlap_s = 0.000
```

Agent B finished at approximately 304 s, but Agent A did not begin its decode until approximately 915 s.

The report records approximately **18,690 major page faults** for Agent A and **1.6 GiB** of host swap usage. Its reported file-tier traffic was extremely high. The leading explanation is that independent mmap expert working sets overwhelmed the **61 GiB usable host RAM**:

```text
IQ3_XXS expert working-set estimate: 47 GiB
IQ2_XS  expert working-set estimate: 39 GiB
Combined estimate:                 86 GiB
Available RAM:                    ~61 GiB
```

Unlike homogeneous agents, the two quantizations cannot share the same file-backed GGUF expert pages. Page reclaim and repeated expert-file reads are consistent with the severe slowdown. The 86 GiB value is a working-set estimate, not a direct peak resident-memory measurement; cumulative Strata file-tier counters are not automatically physical NVMe-read bytes.

**Conclusion:** This particular 64 GB RAM machine should **not use the tested mixed quantizations for simultaneous dual-128K serving**. This is a host-specific result, not proof that mixed inference is impossible with more RAM or different residency policies. The mixed containers were documented as stopped and preserved, without changing the ThinkPad tunnel or GPU power settings.

[Detailed report and root cause analysis](artifacts/stage4-results-20261021/stage4-b-mixed-c2-benchmark-summary.md) · [Raw summary](artifacts/stage4-results-20261021/c2-stage4b-mixed-run1-summary.json) · [Antigravity handoff](docs/STAGE4B_MIXED_AGY_HANDOFF.md)

### Stage 5 — IQ3_S software-only optimization (3-batch C2 replications)

**Date:** October 27, 2026. **Model:** Qwen3.8-Flash-Next GSQ-RCO **IQ3_S** (`/srv/models/strata-iq3s`).

Stage 5 investigated whether IQ3_S could recover and surpass its Stage 3-A 128K prefill speed (`721.30 tok/s`) from the Stage 4-B reference (`535.00 tok/s`) while preserving Stage 4-B's ~2× decode gain (`21.35 tok/s`), without changing hardware, GPU power caps (150 W), or the ThinkPad SSH tunnel. Every measured arm executed **three consecutive fresh-process C2 batches** (`--batches 3`).

| ID | Engine / Image | Runtime flags | 3-Run Mean Prefill | 3-Run Median Prefill | Peak Prefill | 3-Run Mean Decode | 3-Run Mean TTFT | 3-Run Mean Wall |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **T1** | Upstream `0.1.47` | Vanilla baseline | 744.55 | 759.35 | 771.25 | **21.45** | 171.10 s | 254.48 s |
| **T2** | Upstream `0.1.47` | `STRATA_SELECT_SIMT=1` | 879.00 | 879.10 | 880.10 | 21.30 | 144.81 s | 229.62 s |
| **T3** | Upstream `0.1.47` | `STRATA_PF_WMMA=1` | 798.67 | 798.75 | 799.20 | 21.20 | 159.30 s | 254.37 s |
| **T4** | Upstream `0.1.47` | `SELECT_SIMT=1` + `PF_WMMA=1` | **887.37** | **888.55** | **891.15** | **21.20** | **143.36 s** | **228.92 s** |
| **T6-Unfixed** | Upstream `0.1.50` | Vanilla (post-build 86.7% cache) | 247.10* | 247.10* | 247.10* | 21.30* | 514.12 s* | 599.26 s* |
| **T6-Fixed** | Upstream `0.1.50` | `STRATA_STAGER_SSD=0` | 751.77 | 741.35 | 791.30 | 21.20 | 169.44 s | 253.91 s |
| **T8** | Upstream `0.1.50` | `SELECT_SIMT=1` + `PF_WMMA=1` + `STAGER_SSD=0` | 876.00 | 875.85 | 876.95 | 20.77 | 145.22 s | 234.40 s |
| **T7** | `jmnargi@2c9b1dd` | Default `SM70_PERF=1` + `SIMT=1` + `WMMA=1` + `STAGER_SSD=0` | 868.93 | 905.05 | **939.85** | 18.60 | 147.66 s | 247.78 s |
| **T7-Fixed** | `jmnargi@2c9b1dd` | `SM70_PERF=0` + `SIMT=1` + `WMMA=1` + `WMMA2=1` + `STAGER_SSD=0` | **899.23** | **905.40** | **930.35** | **21.45** | **141.64 s** | **212.18 s** |

*\*T6-Unfixed was stopped after 1 batch per the Stage 5 thrashing gate and resolved in T6-Fixed. T5 (single-agent contention control) was placed on hold after root-causing the page-cache/stager threshold directly.*

**Key technical findings from Stage 5:**

1. **Linux page-cache 90% threshold & SSD stager thrashing (`STRATA_STAGER_SSD=0`):** Unlike the failed mixed-quant run (86 GiB combined working set), two homogeneous IQ3_S agents share the same 51.1 GiB `00001-of-00002.gguf` shard in the Linux page cache (~41.9 GiB active expert working set). However, when `docker build` or other host I/O pushes GGUF page-cache residency below **90%** (`src->cached_share(256) < 0.90` in `prefill.cpp`), Strata switches from the RAM stager profile (3 threads, 16-slot ring) to the SSD stager profile (32 threads, 128-slot pinned ring = 680 MB extra pinned RAM), causing cyclic LRU page-cache thrashing (`247.1 tok/s` in T6-Unfixed; `535.0 tok/s` in Stage 4-B). Restoring `Active(file)` page cache and setting `STRATA_STAGER_SSD=0` eliminated swap thrashing and stabilized vanilla prefill at **744.55–751.77 tok/s**.
2. **Upstream 0.1.47 SIMT scorer + Volta FP16 WMMA (`T2`, `T3`, `T4`):** `STRATA_SELECT_SIMT=1` alone (`T2`) improved 3-run mean prefill by **+18.1%** (`879.00 tok/s`) with 100% bit-exact output parity against `T1`. Combining `STRATA_SELECT_SIMT=1` + `STRATA_PF_WMMA=1` (`T4`) reached **887.37 tok/s** mean prefill (`143.36 s` TTFT, `21.20 tok/s` decode, `228.92 s` batch wall time).
3. **Updated V100 fork (`jmnargi/Strata-V100@2c9b1dd`, `T7` vs `T7-Fixed`):** PR #74 (`STRATA_PF_WMMA2=1` 128-token grouped tiles for `IQ3_S`) and PR #80 (V100 prefill scheduler) pushed warm prefill above **930–947 tok/s**. In unfixed `T7`, the fork's default `STRATA_SM70_PERF=1` bundle (tuned for 2-GPU `--layer-split 16`) enabled `STRATA_ADAPT_OVERLAP=1`, `STRATA_SM70_TABLE=1`, and `STRATA_EXPDEC=1`, which contended with `--mmap-experts` CPU pool fetches on single 16 GB GPUs and lowered decode to `18.60 tok/s`. Setting `STRATA_SM70_PERF=0` while explicitly keeping `STRATA_SELECT_SIMT=1`, `STRATA_PF_WMMA=1`, `STRATA_PF_WMMA2=1`, and `STRATA_STAGER_SSD=0` (**T7-Fixed**) restored decode to **21.45 tok/s mean (22.6 tok/s peak)** alongside **899.23 tok/s mean (905.40 tok/s median, 930.35 tok/s batch peak / 939.0 tok/s Agent B peak) prefill** and **212.18 s mean (205.85 s best) batch wall time**.

[Stage 5 plan](docs/STAGE5_PLAN.md) · [T1 baseline](artifacts/stage5-results-20261027/stage5-t1-baseline-summary.md) · [T2 SIMT](artifacts/stage5-results-20261027/stage5-t2-simt-summary.md) · [T3 WMMA](artifacts/stage5-results-20261027/stage5-t3-wmma-summary.md) · [T4 combined](artifacts/stage5-results-20261027/stage5-t4-combined-summary.md) · [T6 0.1.50](artifacts/stage5-results-20261027/stage5-t6-engine0150-summary.md) · [T8 0.1.50 combined](artifacts/stage5-results-20261027/stage5-t8-engine0150-combined-summary.md) · [T7 & T7-Fixed V100 fork](artifacts/stage5-results-20261027/stage5-t7-jmnargi-summary.md)

---

## 8. Consolidated 128K Results

Values for Stages 2–4 are **arithmetic means of the two agents' per-request rates within one homogeneous C2 batch**; values for Stage 5 are **3-batch means (6 agent requests per arm)** across three consecutive fresh-process C2 batches.

| Stage | Engine | Model | Prefill (tok/s) | Decode (tok/s) | TTFT (s) |
| --- | --- | --- | ---: | ---: | ---: |
| Stage 2 | 0.1.31 | IQ2_XS | 707.25 | 21.85 | 180.05 |
| Stage 2 | 0.1.31 | IQ3_XXS | 623.05 | 11.45 | 204.39 |
| Stage 2 | 0.1.31 | IQ3_S | 602.40 | 10.75 | 211.36 |
| Stage 3-A | 0.1.36 | IQ2_XS | 909.90 | 22.20 | 140.09 |
| Stage 3-A | 0.1.36 | IQ3_XXS | 790.95 | 12.70 | 161.08 |
| Stage 3-A | 0.1.36 | IQ3_S | 721.30 | 10.65 | 176.62 |
| Stage 3-B | 0.1.36 tuned | IQ2_XS | 925.45 | 23.90 | 137.73 |
| Stage 3-B | 0.1.36 tuned | IQ3_XXS | 815.05 | 12.75 | 156.35 |
| Stage 3-B | 0.1.36 tuned | IQ3_S | 731.15 | 10.70 | 174.25 |
| Stage 4-A | 0.1.44.1 | IQ2_XS | 939.40 | 31.65 | 135.41 |
| Stage 4-B | 0.1.47 | IQ2_XS | 981.55 | 38.50 | 129.60 |
| Stage 4-B | 0.1.47 | IQ3_XXS | 725.50 | 26.15 | 175.27 |
| Stage 4-B | 0.1.47 | IQ3_S | 535.00 | 21.35 | 237.60 |
| **Stage 4-C** | **0.1.47 + SM70 table** | **IQ2_XS** | **995.70** | **39.60** | **127.77** |
| Stage 4-C | 0.1.47 + SM70 table | IQ3_XXS | 630.70 | 26.05 | 201.60 |
| Stage 4-C | 0.1.47 + SM70 table | IQ3_S | 468.05 | 20.55 | 271.60 |
| Stage 5 T1 (3-run mean) | 0.1.47 | IQ3_S | 744.55 | 21.45 | 171.10 |
| Stage 5 T2 (3-run mean) | 0.1.47 + SIMT | IQ3_S | 879.00 | 21.30 | 144.81 |
| Stage 5 T3 (3-run mean) | 0.1.47 + WMMA | IQ3_S | 798.67 | 21.20 | 159.30 |
| **Stage 5 T4 (3-run mean)** | **0.1.47 + SIMT + WMMA** | **IQ3_S** | **887.37** | **21.20** | **143.36** |
| Stage 5 T6-Fixed (3-run mean) | 0.1.50 + `STAGER_SSD=0` | IQ3_S | 751.77 | 21.20 | 169.44 |
| Stage 5 T8 (3-run mean) | 0.1.50 + SIMT + WMMA | IQ3_S | 876.00 | 20.77 | 145.22 |
| **Stage 5 T7-Fixed (3-run mean)** | **`jmnargi@2c9b1dd` + SIMT + WMMA2 (`SM70_PERF=0`)** | **IQ3_S** | **899.23** | **21.45** | **141.64** |

The mixed trial is intentionally not pooled into a homogeneous mean: its quantizations differ and its active-decode-overlap criterion failed.

**Summary of engineering findings:** Newer upstream Strata improved decode substantially; IQ3 decode roughly doubled by Stage 4-B; optional SM70 table tuning helped IQ2_XS but hurt single-GPU IQ3_S; the mixed trial demonstrated how unshared host RAM/page-cache working sets can saturate 61 GiB usable RAM; and Stage 5 proved that homogeneous IQ3_S with `STRATA_STAGER_SSD=0`, `STRATA_SELECT_SIMT=1`, and `STRATA_PF_WMMA=1`/`STRATA_PF_WMMA2=1` (`SM70_PERF=0`) achieves **899.23 tok/s mean (930.35 tok/s batch peak) 128K prefill** while retaining **21.45 tok/s decode**. Real coding-task quality remains unmeasured.

---

## 9. Reproducibility and Repository Layout

```text
v100-x2-strata-qwen3.8-flash-next/
├── README.md
├── AGENTS.md
├── Dockerfile.v100
├── Dockerfile.jmnargi-v100
├── Dockerfile.jmnargi-v100-stage5
├── Dockerfile.upstream-v100
├── Dockerfile.upstream-0.1.47
├── Dockerfile.upstream-0.1.50
├── docker/                     Engine build and packaging helpers
├── scripts/
│   ├── 00-12                   Initial validation and original dual agents
│   ├── 20-33                   Dockerized base runtimes
│   ├── 40-53                   IQ2_XS preparation / original C2 / Q4
│   ├── 54                      Strata-V100 0.1.36 fork
│   ├── 55-58                   Stage 4-A
│   ├── 59-62                   Stage 4-B IQ2_XS
│   ├── 63-65                   Stage 4-C IQ2_XS
│   ├── 66-71                   Stage 4-C IQ3 variants
│   ├── 72-77                   Stage 4-B IQ3 variants
│   ├── 78-80                   Stage 4-B mixed A/B
│   └── 81-87                   Stage 5 IQ3_S optimization & telemetry
├── bench/
│   ├── api_bench.py
│   ├── c2_v100_contract.py
│   ├── c2_q4_v100_contract.py
│   └── workloads/v100-performance-v1.json
├── artifacts/
│   ├── stage3-configs-20261004/
│   ├── stage3-results-20261004/
│   ├── stage4-configs-20261021/
│   ├── stage4-results-20261021/
│   ├── stage5-configs-20261027/
│   └── stage5-results-20261027/
├── docs/
│   ├── STAGE4_PLAN.md
│   ├── STAGE4_ANTIGRAVITY_HANDOFF.md
│   ├── STAGE4B_MIXED_AGY_HANDOFF.md
│   └── STAGE5_PLAN.md
└── results/                    Local, gitignored benchmark outputs
```

### 9.1 Build scripts

| Script | Purpose |
| --- | --- |
| `scripts/20-docker-build-v100.sh` | Original 0.1.31 Volta image |
| `scripts/54-docker-build-jmnargi-v100.sh` | Stage 3-A 0.1.36 V100 fork |
| `scripts/55-docker-build-upstream-v100.sh` | Stage 4-A 0.1.44.1 |
| `scripts/59-docker-build-upstream-0.1.47.sh` | Stage 4-B/C/5 0.1.47 |
| `scripts/86-docker-build-upstream-0.1.50.sh` | Stage 5 T6/T8 upstream 0.1.50 (v0.2.6) |
| `scripts/87-docker-build-jmnargi-stage5.sh` | Stage 5 T7 V100 fork (`2c9b1dd`) |

Do not overwrite preserved tags without an explicit migration and rollback plan.

### 9.2 Benchmark scripts

| Script | C2 target |
| --- | --- |
| `scripts/52-bench-v100-contract-c2-performance.sh` | Original IQ2_XS |
| `scripts/53-bench-q4-v100-contract-c2-performance.sh` | UD-Q4_K_XL |
| `scripts/58-bench-stage4a-c2.sh` | Stage 4-A IQ2_XS |
| `scripts/62-bench-stage4b-c2.sh` | Stage 4-B IQ2_XS |
| `scripts/65-bench-stage4c-c2.sh` | Stage 4-C IQ2_XS |
| `scripts/68-bench-stage4c-iq3xxs-c2.sh` | Stage 4-C IQ3_XXS |
| `scripts/71-bench-stage4c-iq3s-c2.sh` | Stage 4-C IQ3_S |
| `scripts/74-bench-stage4b-iq3xxs-c2.sh` | Stage 4-B IQ3_XXS |
| `scripts/77-bench-stage4b-iq3s-c2.sh` | Stage 4-B IQ3_S |
| `scripts/80-bench-stage4b-mixed-c2.sh` | Stage 4-B mixed |
| `scripts/84-bench-stage5-c2.sh` | Stage 5 IQ3_S C2 runner with host telemetry (`T1`–`T8`) |

These scripts are **not routine start commands**. They may restart selected test containers to enforce fresh-process measurements.

### 9.3 Evidence and checksums

- [Stage 3 configs](artifacts/stage3-configs-20261004/)
- [Stage 3 results](artifacts/stage3-results-20261004/)
- [Stage 4 configs](artifacts/stage4-configs-20261021/)
- [Stage 4 results and SHA-256 receipts](artifacts/stage4-results-20261021/)
- [Stage 5 configs](artifacts/stage5-configs-20261027/)
- [Stage 5 results and 3-batch summaries](artifacts/stage5-results-20261027/)
- [Stage 5 IQ3_S optimization test plan](docs/STAGE5_PLAN.md)
- [Stage 4 plan](docs/STAGE4_PLAN.md)
- [Stage 4 Antigravity CLI handoff](docs/STAGE4_ANTIGRAVITY_HANDOFF.md)
- [Mixed trial handoff](docs/STAGE4B_MIXED_AGY_HANDOFF.md)

Raw runs are kept under the gitignored `results/` directory. Only sanitized summaries, receipts, and appropriate checksums should be committed.

---

## 10. Stability and Operational Safety

### 10.1 Preserved container registry

These names are historical experiment assets and are **not** an inventory of what is currently running:

```text
Stage 2:
  strata-iq2xs-agent-a
  strata-iq2xs-agent-b
  strata-iq2xs-single-mmap
  strata-iq2xs-mgpu

Stage 3-A:
  strata-jmn-iq2xs-agent-a
  strata-jmn-iq2xs-agent-b

Stage 4-A:
  strata-s4a-iq2xs-agent-a
  strata-s4a-iq2xs-agent-b

Stage 4-B:
  strata-s4b-iq2xs-agent-a
  strata-s4b-iq2xs-agent-b
  strata-s4b-iq3xxs-agent-a
  strata-s4b-iq3xxs-agent-b
  strata-s4b-iq3s-agent-a
  strata-s4b-iq3s-agent-b

Stage 4-C:
  strata-s4c-iq2xs-agent-a
  strata-s4c-iq2xs-agent-b
  strata-s4c-iq3xxs-agent-a
  strata-s4c-iq3xxs-agent-b
  strata-s4c-iq3s-agent-a
  strata-s4c-iq3s-agent-b

Stage 4-B mixed:
  strata-s4b-mixed-iq3xxs-agent-a
  strata-s4b-mixed-iq2xs-agent-b
```

Use `docker start`, `docker stop`, `docker restart`, `docker logs`, and `docker inspect` for ordinary management. Do not delete preserved containers, native packs, or historical model records without a deliberate, separately approved cleanup.

### 10.2 Earlier unexpected host reset

An earlier dual-agent cold prefill attempt ended with an unexpected P520 reset while both requests were above 100K tokens. The post-reboot logs did not establish an OOM event, contemporaneous NVIDIA Xid, kernel panic, MCE, or thermal trip. Later formal dual-agent 128K C2 runs completed successfully. The original reset's cause remains **unresolved**; universal stability is not claimed.

### 10.3 Power and service preservation

Stage 4 experiments intentionally **did not change** host GPU power limits, clocks, or the ThinkPad SSH forwarding service. Do not change those settings as an incidental part of a benchmark or README-related task.

Before launching a different topology:

1. Inspect the currently running containers and GPU allocations.
2. Check that the required ports (8080/8081) are free.
3. Obtain explicit approval before stopping a serving agent.
4. Preserve existing images, containers, model files, logs, and recorded measurements.
5. Use dedicated test container names.
6. Archive and inspect results before any promotion.

A benchmark candidate is **not** an automatically deployed production service.

---

## 11. Conclusions and Recommended Configuration

This project demonstrates that two legacy Tesla V100 GPUs can serve large modern MoE models with 128K contexts using an appropriately built Strata engine, efficient quantization, and memory-mapped experts.

The strongest findings are:

- **True independent inference:** two one-GPU Strata servers passed homogeneous concurrent 128K C2 tests.
- **Large engine improvements:** mean IQ2_XS decode increased from **22.20 tok/s (Stage 3-A)** to **38.50 tok/s (Stage 4-B)**; Stage 4-C recorded **39.60 tok/s**.
- **Higher-precision IQ3_S optimization (Stage 5):** combining homogeneous page-cache residency (`STRATA_STAGER_SSD=0`), SIMT QSA scoring (`STRATA_SELECT_SIMT=1`), and Volta FP16 grouped WMMA/WMMA2 tiles (`STRATA_PF_WMMA=1`, `STRATA_PF_WMMA2=1`, `STRATA_SM70_PERF=0`) raised IQ3_S 128K prefill from **535.00 tok/s (Stage 4-B)** to **899.23 tok/s 3-run mean (905.40 tok/s median, 930.35 tok/s batch peak)** in **T7-Fixed** and **887.37 tok/s 3-run mean** in upstream **T4**, while preserving **21.20–21.45 tok/s** decode.
- **Shared host memory matters:** the mixed-quant experiment suffered severe page-cache and storage contention on the 64 GB host and failed the concurrent-decode C2 requirement, whereas homogeneous agents share the 51.1 GiB GGUF shard in Linux page cache.
- **Quality remains untested locally:** a future matched coding-agent benchmark is required to establish whether IQ3's model-card accuracy gain outweighs IQ2_XS's higher decode throughput.

### Recommended configurations (speed vs. precision)

| Component | Maximum-Throughput Selection (**IQ2_XS**) | High-Precision Selection (**IQ3_S — Stage 5**) |
| --- | --- | --- |
| Model | Qwen3.8-Flash-Next **IQ2_XS** | Qwen3.8-Flash-Next **IQ3_S** |
| Engine / Image | Upstream Strata **0.1.47** (`strata-v100-upstream:0.1.47`) | **T7-Fixed:** `strata-v100-jmnargi:2c9b1dd` *(or **T4:** `strata-v100-upstream:0.1.47`)* |
| Agents | Two independent Docker servers | Two independent Docker servers |
| GPU allocation | One Tesla V100 16 GB per agent | One Tesla V100 16 GB per agent |
| CPU affinity | A: `0-2,6-8`; B: `3-5,9-11` | A: `0-2,6-8`; B: `3-5,9-11` |
| Context | 131072 tokens per agent | 131072 tokens per agent |
| KV cache | INT8; resident 32768 | INT8; resident 32768 |
| Expert access | Native pack and `--mmap-experts` | Native pack and `--mmap-experts` |
| Storage | Shared read-only GGUF and MTP | Shared read-only GGUF and MTP (`/srv/models/strata-iq3s`) |
| Runtime flags | Stage 4-C: `STRATA_SM70_TABLE=1` *(or vanilla 4-B)* | **T7-Fixed:** `STRATA_SM70_PERF=0 STRATA_SELECT_SIMT=1 STRATA_PF_WMMA=1 STRATA_PF_WMMA2=1 STRATA_STAGER_SSD=0`<br>**T4 (Upstream):** `STRATA_SELECT_SIMT=1 STRATA_PF_WMMA=1 STRATA_STAGER_SSD=0` |
| Rollback | Preserved Stage 3-A 0.1.36 agent pair | Preserved Stage 3-A 0.1.36 agent pair |

The best recorded **per-agent means** across the two recommended tiers are:

```text
IQ2_XS (Stage 4-C, 1-batch mean):          IQ3_S (Stage 5 T7-Fixed, 3-batch mean / peak):
  Prefill:  995.70 tok/s                     Prefill:  899.23 tok/s (median 905.40, peak 930.35)
  Decode:    39.60 tok/s                     Decode:    21.45 tok/s (peak 22.00)
  TTFT:     127.77 s                         TTFT:     141.64 s     (best 136.77 s)
```

These values are arithmetic means within dual-agent C2 batches, **not the sum of both agents' throughput**. Repeatable stability and coding quality should be established before final production promotion.

---

## 12. References

### Software and models

- [Strata upstream](https://github.com/Niko1221/Strata)
- [Strata-V100 fork (Stage 3-A & Stage 5 T7)](https://github.com/jmnargi/Strata-V100)
- [Qwen3.8-Flash-Next GSQ-RCO GGUF model card](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF)

### Volta support

- [Upstream older-GPU support](https://github.com/Niko1221/Strata/blob/main/docs/OLDER_GPUS.md)
- [Upstream NVIDIA V100 notes](https://github.com/Niko1221/Strata/blob/main/docs/NVIDIA_V100.md)
- [Volta support issue #236](https://github.com/Niko1221/Strata/issues/236)
- [Multi-GPU documentation](https://github.com/Niko1221/Strata/blob/main/docs/MULTI_GPU.md)

### Repository documentation

- [Stage 6 container preparation and decode test plan](docs/STAGE6_PREP.md)
- [Stage 5 plan and checklist](docs/STAGE5_PLAN.md)
- [Stage 5 measured results (3-batch summaries)](artifacts/stage5-results-20261027/)
- [Stage 4 plan](docs/STAGE4_PLAN.md)
- [Antigravity CLI handoff](docs/STAGE4_ANTIGRAVITY_HANDOFF.md)
- [Stage 4-B mixed experiment](docs/STAGE4B_MIXED_AGY_HANDOFF.md)
- [Stage 4 measured results](artifacts/stage4-results-20261021/)

---

**Project:** V100 ×2 + Strata + Qwen3.8-Flash-Next  
**Hardware:** Lenovo ThinkStation P520 / Tesla V100 16 GB ×2  
**Focus:** Reproducible 128K dual-agent inference on NVIDIA Volta GPUs.
