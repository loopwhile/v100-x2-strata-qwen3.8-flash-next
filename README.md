# V100 x2 + Strata + Qwen3.8-Flash-Next

Experimental Docker-first deployment and benchmark harness for running and comparing Qwen3.8-Flash-Next quantizations on a Lenovo ThinkStation P520 with two Tesla V100 16 GB GPUs.

---

## 1. Executive Summary & Recommended Deployment

### Production Serving Recommendation
- **Primary Recommendation**: **IQ2_XS + Stage 4-C (Upstream Strata 0.1.47 + `STRATA_SM70_TABLE=1`)**
  - **Prefill Speed**: **995.70 tok/s** (near 1,000 tok/s)
  - **Decode Speed**: **39.60 tok/s** (**+78.38% 🚀** vs Stage 3-A baseline)
  - **TTFT (Latency to First Token)**: **127.77 s**
  - **Expert Cache Hit Rate**: **93.10%**
- **Preserved Serving Baseline**: Stage 3-A (`strata-v100-jmnargi:9d77749`, Strata 0.1.36 fork) on `strata-jmn-iq2xs-agent-a/b` remains preserved and validated as the historical baseline.

### Key Engineering Discoveries
1. **Upstream Strata 0.1.47 Engine Breakthrough**:
   Upstream v0.1.47 (Release v0.2.2) delivers massive performance leaps across all models (+73% decode on IQ2_XS, +106% on IQ3_XXS, +100% on IQ3_S).
2. **IQ3 Decode Cliff Resolution**:
   The historical "IQ3 decode cliff" on Tesla V100 (where IQ3 decode stalled at 10~12 tok/s) is **completely resolved by Upstream Strata 0.1.47 core engine improvements**, doubling IQ3 decode speeds natively to ~26 tok/s (IQ3_XXS) and ~21 tok/s (IQ3_S).
3. **Quantization-Specific Tuning Rules**:
   - **IQ2_XS**: `STRATA_SM70_TABLE=1` provides positive speedups for both prefill (+14 tok/s) and decode (+1.1 tok/s) -> **Stage 4-C is optimal**.
   - **IQ3_XXS / IQ3_S**: `STRATA_SM70_TABLE=1` yields no decode benefit but degrades prefill by 13~15% and adds 26~34s to TTFT -> **Vanilla Stage 4-B is optimal**.
4. **Architectural Limit: Heterogeneous Mixed Quantization is Prohibited**:
   Co-locating different quantizations (e.g., Host GPU0 = IQ3_XXS, Host GPU1 = IQ2_XS) on a single 61 GB host breaks Linux OS Page Cache sharing across mmapped models (47 GB + 39 GB = **86 GB working set > 61 GB RAM**). This induces severe memory thrashing (1.6 GiB swap spillage, 18,690 major page faults, 606 GB NVMe read), causing TTFT to explode by 5.2x (914.9s) and collapsing active decode concurrency to 0.000s. **Co-located independent agents must remain homogeneous**.

---

## 2. Day-to-Day Operations & Serving Guide

### Dual-Agent Independent Topology
The primary serving topology runs two independent symmetric 1-GPU agents, sharing physical model shards read-only via `--mmap-experts`:

```text
Agent A (Port 8080)                  Agent B (Port 8081)
Host GPU 0 (Tesla V100 16GB)          Host GPU 1 (Tesla V100 16GB)
CPUs 0-2, 6-8                        CPUs 3-5, 9-11
128K context, INT8 KV                128K context, INT8 KV
mmap experts (NVMe)                  mmap experts (NVMe)
        \                                   /
         \--- Shared IQ2_XS + MTP (NVMe) ---/
```

### Server Management Commands (P520)

#### Starting Preserved Serving Agents
To start the validated Stage 3-A production agents after a reboot:
```bash
cd ~/v100-x2-strata-qwen3.8-flash-next
docker start strata-jmn-iq2xs-agent-a strata-jmn-iq2xs-agent-b
```
*(Or to run the Stage 4-C high-performance candidate agents: `docker start strata-s4c-iq2xs-agent-a strata-s4c-iq2xs-agent-b`)*

#### Checking Status & Health
```bash
# Check Docker container status
docker ps --filter name=strata-   --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

# Health endpoints
curl -fsS http://127.0.0.1:8080/health && echo
curl -fsS http://127.0.0.1:8081/health && echo

# OpenAI-compatible model endpoints
curl -fsS http://127.0.0.1:8080/v1/models && echo
curl -fsS http://127.0.0.1:8081/v1/models && echo
```

#### Monitoring Logs
```bash
# Agent A (GPU 0)
docker logs -f --tail 50 strata-jmn-iq2xs-agent-a

# Agent B (GPU 1)
docker logs -f --tail 50 strata-jmn-iq2xs-agent-b
```

#### Stopping Serving Agents
```bash
docker stop strata-jmn-iq2xs-agent-a strata-jmn-iq2xs-agent-b
```
> [!IMPORTANT]
> Always use `docker stop` and `docker start`. Never run destructive Docker cleanups (`docker system prune` or `docker rm -f`) on validated containers.

### ThinkPad SSH Tunnel Integration
The ThinkPad E14 runs `strata-tunnel.service` to forward P520 agent endpoints locally:
- **ThinkPad `127.0.0.1:18080/v1`** -> P520 Agent A `127.0.0.1:8080/v1`
- **ThinkPad `127.0.0.1:18081/v1`** -> P520 Agent B `127.0.0.1:8081/v1`

---

## 3. Stage 4 Comprehensive Benchmarks (2026-10-21 ~ 2026-10-22)

Stage 4 evaluated the latest upstream Strata releases (v0.1.44.1 and v0.1.47), kernel optimizations (`STRATA_SM70_TABLE=1`), cross-quantization behavior, and isolated mixed-quantization serving under the frozen `V100-PERFORMANCE-C2-128K-v1` workload (SHA-256: `e413acced27c...`).

### 3.1 Engine Evolution (IQ2_XS Primary Arm)
All runs: Dual independent V100s, 131,072 context, INT8 KV (`--kv-resident 32768`), cold process, 128K concurrent C2 contract:

| Engine / Release | Prefill (tok/s) | TTFT (s) | Decode (tok/s) | Expert Hit | vs Stage 3-A Decode |
|---|---|---|---|---|---|
| **Stage 3-A** (Strata 0.1.36 / jmnargi fork) | 909.90 | 140.09 | 22.20 | ~90.0% | Baseline |
| **Stage 4-A** (Upstream Strata v0.1.44.1) | 939.40 | 135.41 | 31.65 | 91.60% | **+42.57%** |
| **Stage 4-B** (Upstream Strata v0.1.47 / v0.2.2) | 981.55 | 129.60 | 38.50 | 93.55% | **+73.42%** |
| **Stage 4-C** (0.1.47 + `STRATA_SM70_TABLE=1`) | **995.70** | **127.77** | **39.60** | **93.10%** | **+78.38% 🚀🚀** |

---

### 3.2 Cross-Quantization Matrix: Stage 4-B (Vanilla) vs Stage 4-C (SM70_TABLE)

| Quantization | Configuration | Prefill (tok/s) | TTFT (s) | Decode (tok/s) | Expert Hit | vs Stage 3-A Decode | Optimal Profile |
|---|---|---|---|---|---|---|---|
| **IQ2_XS** | **Stage 4-B (vanilla 0.1.47)** | 981.55 | 129.60 | 38.50 | 93.55% | +73.42% | |
| **IQ2_XS** | **Stage 4-C (+ SM70_TABLE)** | **995.70** | **127.77** | **39.60** | **93.10%** | **+78.38% 🚀** | **Stage 4-C (Optimal)** |
| **IQ3_XXS** | **Stage 4-B (vanilla 0.1.47)** | **725.50** | **175.27** | **26.15** | 86.30% | **+105.91% 🚀🚀** | **Stage 4-B (Optimal)** |
| **IQ3_XXS** | **Stage 4-C (+ SM70_TABLE)** | 630.70 | 201.60 | 26.05 | 86.90% | +105.12% 🚀🚀 | |
| **IQ3_S** | **Stage 4-B (vanilla 0.1.47)** | **535.00** | **237.60** | **21.35** | 81.50% | **+100.47% 🚀🚀** | **Stage 4-B (Optimal)** |
| **IQ3_S** | **Stage 4-C (+ SM70_TABLE)** | 468.05 | 271.60 | 20.55 | 81.50% | +92.96% 🚀 | |

---

### 3.3 Stage 4-B MIXED Quantization Trial (Agent A: IQ3_XXS + Agent B: IQ2_XS)

A dedicated trial was conducted to evaluate mixed-quantization co-residency on vanilla Strata 0.1.47: Host GPU0 = IQ3_XXS, Host GPU1 = IQ2_XS.

#### Measured Results (Single Cold Run #1)
| Metric | Agent A (Host GPU0 - IQ3_XXS) | Agent B (Host GPU1 - IQ2_XS) | Stage 4-B Homogeneous A (IQ3_XXS) | Stage 4-B Homogeneous B (IQ2_XS) |
|---|---|---|---|---|
| **Prompt Tokens** | 126,967 | 126,968 | 126,967 | 126,968 |
| **Output Tokens** | 1,289 (PASS) | 2,036 (PASS) | 1,396 | 1,717 |
| **Wall Time** | **1,077.62 s (~18.0 min)** | **303.87 s (~5.1 min)** | 228.02 s | 175.54 s |
| **TTFT** | **914.90 s (5.2x slower ⚠️)** | **214.04 s (+66% slower)** | 176.50 s | 128.69 s |
| **Prefill Speed** | **138.8 tok/s (-80.7% ⚠️)** | **593.9 tok/s (-39.9%)** | 720.4 tok/s | 988.5 tok/s |
| **Decode Speed** | **7.9 tok/s (-70.8% ⚠️)** | **22.6 tok/s (-38.3%)** | 27.1 tok/s | 36.6 tok/s |
| **Major Page Faults** | **18,690 faults** | 274 faults | 0 | 0 |
| **Storage Read (NVMe)** | **606.1 GB** | 25.3 GB | Normal GGUF read | Normal GGUF read |
| **Host Swap Spilled** | **1.6 GiB** | **1.6 GiB** | 0 B | 0 B |
| **Decode Overlap** | **0.000 s (FAIL ❌)** | **0.000 s (FAIL ❌)** | 51.52 s (PASS) | 36.81 s (PASS) |

#### Root Cause Analysis
1. **OS Page Cache Sharing Breakdown**: When running homogeneous agents (IQ2_XS + IQ2_XS), both containers mmap the *identical* GGUF file. Linux kernel shares the exact same page-cache pages across processes, requiring only **~39 GiB RAM** (fitting completely in 61 GiB RAM). In the mixed setup, two distinct GGUF models required **47 GiB + 39 GiB = 86 GiB**, overflowing host RAM by 25 GiB.
2. **Catastrophic Memory Thrashing & Swap Spillage**: The host exhausted available RAM, spilling **1.6 GiB into swap** and generating **18,690 major page faults** on Agent A. Physical NVMe reads hit 606 GB for a single request, stalling Agent A's prefill for 15 minutes.
3. **Loss of Concurrency**: Agent B finished in 304s, while Agent A did not start decoding until 915s. Decode overlap was 0.000s (`active_overlap = False`), failing the C2 concurrency contract.

---

### 3.4 Stage 4 Artifact Receipts & Verification Links
All Stage 4 experimental receipts, raw summaries, and runner scripts are versioned and verified:
- [Stage 4 Plan](docs/STAGE4_PLAN.md)
- [Stage 4 Antigravity CLI Handoff](docs/STAGE4_ANTIGRAVITY_HANDOFF.md)
- [Stage 4-B Mixed AGY Handoff](docs/STAGE4B_MIXED_AGY_HANDOFF.md)
- [Stage 4-0 Inventory Receipt](artifacts/stage4-results-20261021/stage4-0-inventory-receipt.md)
- [Stage 4-A Build Receipt](artifacts/stage4-results-20261021/stage4-a-build-receipt.md) & [Stage 4-A C2 Benchmark Summary](artifacts/stage4-results-20261021/stage4-a-c2-benchmark-summary.md)
- [Stage 4-B Build Receipt](artifacts/stage4-results-20261021/stage4-b-build-receipt.md) & [Stage 4-B IQ2_XS C2 Summary](artifacts/stage4-results-20261021/stage4-b-c2-benchmark-summary.md)
- [Stage 4-B IQ3_XXS C2 Summary](artifacts/stage4-results-20261021/stage4-b-iq3xxs-c2-benchmark-summary.md)
- [Stage 4-B IQ3_S C2 Summary](artifacts/stage4-results-20261021/stage4-b-iq3s-c2-benchmark-summary.md)
- [Stage 4-B MIXED C2 Summary & Deep Root Cause Analysis](artifacts/stage4-results-20261021/stage4-b-mixed-c2-benchmark-summary.md)
- [Stage 4-C IQ2_XS C2 Summary](artifacts/stage4-results-20261021/stage4-c-c2-benchmark-summary.md)
- [Stage 4-C IQ3_XXS C2 Summary](artifacts/stage4-results-20261021/stage4-c-iq3xxs-c2-benchmark-summary.md)
- [Stage 4-C IQ3_S C2 Summary](artifacts/stage4-results-20261021/stage4-c-iq3s-c2-benchmark-summary.md)
- [Stage 4-A Preserved Containers](artifacts/stage4-results-20261021/stage4-a-preserved-containers.md)
- [Stage 4-B Preserved Containers](artifacts/stage4-results-20261021/stage4-b-preserved-containers.md)
- [Stage 4-C Preserved Containers](artifacts/stage4-results-20261021/stage4-c-preserved-containers.md)

---

## 4. Historical Benchmark Progression (Stage 2 ~ Stage 3-B)

### 4.1 Stage 3-B: Speculative Window & Paired-Expert Tuning (2026-10-04)
Stage 3-B evaluated higher speculative windows (`--spec 8 --spec-min-p 0.7`) and paired-expert kernels (`STRATA_EXPERT_PAIR=1`) on the Strata 0.1.36 fork:

| Quantization | Stage 3-A Decode | Stage 3-B Decode | Delta (%) | Stage 3-A Prefill | Stage 3-B Prefill |
|---|---|---|---|---|---|
| **IQ2_XS** | 22.20 tok/s | **23.90 tok/s** | **+7.66%** | 909.90 tok/s | 913.40 tok/s |
| **IQ3_XXS** | 12.70 tok/s | 12.75 tok/s | +0.39% | 790.95 tok/s | 815.05 tok/s |
| **IQ3_S** | 10.65 tok/s | 10.70 tok/s | +0.47% | 721.30 tok/s | 731.15 tok/s |

> **Conclusion**: Stage 3-B tuning offered slight decode gains for IQ2_XS (+1.7 tok/s) but yielded negligible improvements for IQ3 while reducing expert cache hit rates.

---

### 4.2 Stage 3-A: Strata-V100 0.1.36 Fork Introduction (2026-10-04)
Stage 3-A evaluated the V100-optimized `jmnargi/Strata-V100:9d77749` fork (`strata-v100-jmnargi:9d77749`), enabling native Volta prompt-attention paths without `STRATA_PROMPT_ATTN_OLD=1`:

| Quantization | 0.1.31 Baseline Prefill | 0.1.36 Fork Prefill | Prefill Gain | 0.1.31 Decode | 0.1.36 Decode | Decode Gain |
|---|---|---|---|---|---|---|
| **IQ2_XS** | 707.25 tok/s | **909.90 tok/s** | **+28.65%** | 21.85 tok/s | **22.20 tok/s** | +1.60% |
| **IQ3_XXS** | 623.05 tok/s | **790.95 tok/s** | **+26.95%** | 11.45 tok/s | **12.70 tok/s** | +10.92% |
| **IQ3_S** | 602.40 tok/s | **721.30 tok/s** | **+19.74%** | 10.75 tok/s | 10.65 tok/s | -0.93% |

> **Conclusion**: The fork dramatically improved 128K long-context prefill across all models (+20~29%), slashing TTFT by 16~22%, but left the IQ3 decode cliff largely unaddressed.

---

### 4.3 Stage 2: Initial Baseline & Frozen C2 Contract (2026-10-01)
The foundational stage established the dual-agent 128K mmap architecture on upstream Strata 0.1.31 (`strata-v100:0.1.31`):
- **IQ2_XS C2 Baseline**: Prefill 707.25 tok/s, Decode 21.85 tok/s, TTFT 180.05 s, Expert hit 88.95%.
- **IQ3_XXS C2 Baseline**: Prefill 623.05 tok/s, Decode 11.45 tok/s, TTFT 204.39 s, Expert hit 76.15%.
- **IQ3_S C2 Baseline**: Prefill 602.40 tok/s, Decode 10.75 tok/s, TTFT 211.36 s, Expert hit 76.10%.
- **Prefix Cache Isolation**: Confirmed `cache_n = 0` and `cached_tokens = 0` across all runs, verifying raw model speed without prefix reuse.

---

### 4.4 Experimental UD-Q4_K_XL Single-Server Test (2026-10-02)
Unsloth's `Qwen3.8-Flash-Next-UD-Q4_K_XL` (104 GB, 4 GGUF shards) was tested on Strata 0.1.31:
- **Measured Result**: Prefill **149.4 tok/s**, Decode **3.2 tok/s**, TTFT **850.9 s (14.2 min)**, Batch Wall **1,471 s**.
- **Assessment**: While mechanically functional under 128K context, Q4 was 4.7x slower in prefill and 6.6x slower in decode than IQ2_XS, while saturating swap. It is not practical for 16 GB V100 dual serving.

---

## 5. System Specifications & Storage Architecture

### Host Hardware & Driver Environment
- **Platform**: Lenovo ThinkStation P520
- **CPU**: Intel Xeon W-2135 (6C / 12T, 3.70 GHz base / 4.50 GHz turbo, AVX2)
- **Host RAM**: 64 GB DDR4-2400 ECC (61 GiB usable)
- **GPUs**: 2x NVIDIA Tesla V100-SXM2-16GB (`sm_70`, Volta architecture)
- **Power Cap**: Fixed 150W per GPU (strictly preserved)
- **OS**: Ubuntu Server 26.04 LTS (Kernel 7.0.0-38-generic)
- **NVIDIA Driver**: 580.178.04 (CUDA 13.0 driver level)
- **Docker**: Docker CE 29.1.3 with NVIDIA Container Toolkit 1.20.0

### Storage Layout (NVMe vs Backup HDD)
Physical storage layout on P520:

```text
/srv/models/ (SAMSUNG NVMe SSD - 256GB, High-Throughput Inference)
├── strata-iq2xs/
│   ├── model/ (2 GGUF shards, ~64 GB, mmapped read-only)
│   └── pack/  (Native Strata pack, ~1.5 GB, tokenizer & config)
├── strata-iq3xxs/
│   ├── IQ3_XXS/ (2 GGUF shards, ~71 GB, mmapped read-only)
│   └── pack/    (Native Strata pack, ~1.5 GB)
└── strata-data/
    └── mtp/     (Shared MTP speculative verification data)

/srv/backup/ (Western Digital 1TB SATA HDD - Long-Term Archive)
└── models-archive/ (Cold archives of IQ3_XXS, IQ3_S, and environments)
```

### Preserved Docker Containers Registry
The following containers are strictly preserved on P520 for reproducible benchmarking and rollback:
- **Stage 4-C**: `strata-s4c-iq2xs-agent-a/b`, `strata-s4c-iq3xxs-agent-a/b`, `strata-s4c-iq3s-agent-a/b`
- **Stage 4-B**: `strata-s4b-iq2xs-agent-a/b`, `strata-s4b-iq3xxs-agent-a/b`, `strata-s4b-iq3s-agent-a/b`, `strata-s4b-mixed-iq3xxs-agent-a`, `strata-s4b-mixed-iq2xs-agent-b`
- **Stage 4-A**: `strata-s4a-iq2xs-agent-a/b`
- **Stage 3-A**: `strata-jmn-iq2xs-agent-a/b` (Current serving baseline)
- **Stage 2**: `strata-iq2xs-agent-a/b`, `strata-iq2xs-single-mmap`, `strata-iq2xs-mgpu`

---

## 6. Safety, Power Caps & Repository Guardrails

Before changing code or executing commands on P520, adhere to the strict guardrails in [AGENTS.md](AGENTS.md):
1. **Host Power & Clocks**: Never modify GPU power caps (150W), GPU clocks, or host power settings.
2. **Serving Continuity**: Never stop or overwrite active serving containers (`strata-jmn-iq2xs-agent-a/b`) without explicit user approval.
3. **Container Immutability**: Do not update existing container images in place or execute destructive Docker cleanup. Always spawn isolated containers for benchmark arms.
4. **SSH Tunnel Integrity**: Preserve ThinkPad `strata-tunnel.service` and forwarded ports `18080/18081`.
5. **Worktree Hygiene**: Always verify clean worktrees before synchronization (`git pull --ff-only`).

---

## References

- **Strata Core Engine**: https://github.com/Niko1221/Strata
- **Strata-V100 Fork (Stage 3-A)**: https://github.com/jmnargi/Strata-V100
- **Model Card (GSQ-RCO GGUF)**: `ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF`
- **Volta SM70 Context Issue**: https://github.com/Niko1221/Strata/issues/236
- **Multi-GPU Strata Architecture**: https://github.com/Niko1221/Strata/blob/main/docs/MULTI_GPU.md
