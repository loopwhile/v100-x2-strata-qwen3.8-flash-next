# Stage 5 T1 — Upstream Strata 0.1.47 Vanilla Baseline Benchmark Summary

- **Date**: 2026-10-27
- **Target**: Lenovo ThinkStation P520, Xeon W-2135, 64 GB DDR4 ECC, 2 × Tesla V100 16 GB (150 W caps)
- **Model**: Qwen3.8-Flash-Next GSQ-RCO IQ3_S (Mounted from NVMe1 `/srv/models/strata-iq3s`)
- **Engine**: Upstream Strata `0.1.47` (Vanilla defaults, no `STRATA_SM70_TABLE=1`)
- **Workload**: `V100-PERFORMANCE-C2-128K-v1` (SHA256: `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`)
- **Execution Protocol**: 3 Independent Fresh-Process C2 Batches (`cache_n=0`, `cached_tokens=0`, `requests_kept=0`), with full telemetry (`vmstat`, `iostat`, `pidstat`, `nvidia-smi`).

---

## 1. 3-Batch Empirical Results

| Metric | Run 1 (Cold Page Cache) | Run 2 (Warm Page Cache) | Run 3 (Warm Page Cache) | **3-Run Mean** | **3-Run Median** | Stage 4-B Reference (2026-10-21) |
|---|---|---|---|---|---|---|
| **Agent A Prefill (tok/s)** | 700.2 | 754.3 | 759.7 | **738.07** | 754.30 | 533.80 |
| **Agent B Prefill (tok/s)** | 706.4 | 764.1 | 782.6 | **751.03** | 764.10 | 536.20 |
| **Symmetric Mean Prefill** | **703.30** | **759.20** | **771.15** | **744.55** | **759.20** | **535.00 (+39.2% 🚀)** |
| **Agent A TTFT (s)** | 181.58 | 168.60 | 167.43 | **172.54** | 168.60 | 238.12 |
| **Agent B TTFT (s)** | 180.01 | 166.44 | 162.52 | **169.66** | 166.44 | 237.08 |
| **Symmetric Mean TTFT (s)** | **180.80** | **167.52** | **164.98** | **171.10** | **167.52** | **237.60 (-66.5s ⚡)** |
| **Agent A Decode (tok/s)** | 21.2 | 21.2 | 20.8 | **21.07** | 21.20 | 21.20 |
| **Agent B Decode (tok/s)** | 21.5 | 22.4 | 21.6 | **21.83** | 21.60 | 21.50 |
| **Symmetric Mean Decode** | **21.35** | **21.80** | **21.20** | **21.45** | **21.35** | **21.35 (Identical)** |
| **Batch Wall Time (s)** | 259.39 | 247.36 | 256.69 | **254.48** | 256.69 | 315.90 (-61.4s ⚡) |
| **Decode Overlap (s)** | 75.24 | 77.47 | 71.76 | **74.82** | 75.24 | 76.09 |
| **Expert Hit Rate (Mean)** | 81.45% | 81.80% | 81.55% | **81.60%** | 81.55% | 81.50% |
| **Mechanical Contract** | PASS | PASS | PASS | **PASS** | PASS | PASS |

---

## 2. Telemetry and Bottleneck Diagnosis

1. **Physical NVMe I/O vs Linux OS Page Cache**:
   - **Run 1 (Cold Page Cache)**: `iostat` recorded sustained reads on `nvme1n1` up to **1,140 MB/s**, reading **31.9 GB** from NVMe during prompt ingestion. Prefill speed: **703.30 tok/s**.
   - **Run 2 (Warm Page Cache)**: `iostat` reads dropped to **13.9 GB** as frequently accessed weight pages remained cached in Linux host memory (`buff/cache`). Prefill speed jumped to **759.20 tok/s**.
   - **Run 3 (Max Warmth / Memory Saturation)**: Prefill reached **771.15 tok/s**. Host memory saturation caused `kswapd` to push ~958 MB of inactive host daemons/buffers to swap, with 25,313 major faults during the batch. However, inference decode remained completely unaffected at **21.20 tok/s**.

2. **Root Cause of Past Stage 4-B 535 tok/s Baseline**:
   - In Stage 4-B, IQ3_S was measured under fragmented storage/memory conditions before the dedicated NVMe1 cleanup.
   - On clean NVMe1 storage, **Upstream Strata 0.1.47 vanilla natively achieves ~703 tok/s cold and ~760 tok/s warm**, completely exceeding the Stage 5 target milestone of 600 tok/s before even applying candidate kernel flags!

---

## 3. Next Step: T2 Gate Preparation

With T1 baseline variability and resource profile firmly established:
- **Baseline to beat**:
  - Cold prefill: **703.3 tok/s**
  - Warm prefill: **759.2 tok/s**
  - Decode: **21.4 tok/s**
  - TTFT: **167~180 s**
- **Candidate T2**: Upstream 0.1.47 with `-e STRATA_SELECT_SIMT=1`.
- **Primary question for T2**: Does SIMT scoring kernel provide additional prefill speedup beyond 760 tok/s on independent 1-GPU V100 agents, and does it introduce any quality/output drift?
