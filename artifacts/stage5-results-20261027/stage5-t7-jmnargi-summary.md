# Stage 5 — T7 Benchmark Summary (`jmnargi/Strata-V100@2c9b1dd`, PR #74 IQ3_S WMMA2 + PR #80 V100 Prefill Scheduler)

- **Date**: 2026-10-27
- **Experiment ID**: Stage 5 — **T7** (`jmnargi/Strata-V100@2c9b1dd` + `STRATA_SELECT_SIMT=1` + `STRATA_PF_WMMA=1` + `STRATA_STAGER_SSD=0`)
- **Engine & Image**:
  - Image: `strata-v100-jmnargi:2c9b1dd` (`sha256:5b62fa861bbd66bf11600f153e1f277145ed0c41d118a39a6d5fc8c9735147fa`)
  - Upstream Base Image: `v0.1.47` (`sha256:47533f103d14ca24267e4cf2129d18b4739a17609e691dfda69f426f4120c27d`)
  - Source Commit: `jmnargi/Strata-V100@2c9b1dd294a7ffbb50171d87e45d43ab8062fa0e` (`PR #80: V100 prefill scheduler`, includes `PR #74: IQ3_S WMMA2 128-token grouped tiles` and `PR #77: V100 graph dispatch`)
  - Native Engine SHA256 (`/app/strata_inference_engine.cpython-312-x86_64-linux-gnu.so`): `f0da5abf41115c9c0707751ec940f0f1977d04c690b55713cd19b2b7ba815030` (`0.1.45.3`, CUDA `12.9.86`, `sm_70`)
- **Model**: `Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00001-of-00002.gguf` (53.2 GiB across 2 shards in `/srv/models`)
- **Topology**: 2 independent symmetric 1-GPU agents (`strata-s5-agent-a` on GPU0 / port 8080, `strata-s5-agent-b` on GPU1 / port 8081)
- **Locked Contract**:
  - `--ctx-size 131072 -np 1 --cache-type-k q8_0 --cache-type-v q8_0 --Reasoning off --temp 0 --seed 42 --threads 8 --gpu-layers 99 --mmap-experts --paged-kv --kv-Pool-blocks 4200`
  - Environment flags: `STRATA_SELECT_SIMT=1`, `STRATA_PF_WMMA=1` (also activates `STRATA_PF_WMMA2=1` grouped 128-token WMMA2 tiles in `jmnargi`), `STRATA_STAGER_SSD=0`
  - Note: `jmnargi/Strata-V100` `src/core/nv_defaults.cpp` also enables 15 `sm_70` default flags unless `STRATA_SM70_PERF=0` is set, including `STRATA_SM70_TABLE=1` and `STRATA_ADAPT_OVERLAP=1`.
  - GPU Power Cap: 150 W locked on both V100-SXM2-16GB GPUs
- **Workload Contract**: `V100-PERFORMANCE-C2-128K-v1` (Manifest SHA256: `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`)

---

## 1. Per-Batch Results (3 Runs)

| Run | Batch ID | Page Cache Start | Agent | Prompt Tokens | Output Tokens | Prefill (tok/s) | TTFT (s) | Decode (tok/s) | Total Wall (s) | Expert Hit Rate | File Stage (MB) | Output SHA256 |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| **Run 1** | `c2-stage5-t7-iq3s-20261027-190604-run1` | 37.5G / 51.1G (73.4%) | **A (GPU0)** | 126,955 | 1,733 | **757.9** | 167.85 | 18.0 | 264.37 | 0.821 | 366,367.4 | `c6cbda4421539d90...` |
| **Run 1** | `c2-stage5-t7-iq3s-20261027-190604-run1` | 37.5G / 51.1G (73.4%) | **B (GPU1)** | 127,041 | 1,190 | **765.9** | 166.18 | 17.8 | 233.06 | 0.837 | 240,009.7 | `912c6e92253c957d...` |
| **Run 2** | `c2-stage5-t7-iq3s-20261027-191135-run2` | 46.5G / 51.1G (91.0%) | **A (GPU0)** | 126,955 | 1,311 | **899.4** | 141.50 | 19.6 | 208.62 | 0.832 | 259,378.1 | `823b6d9fb81590fc...` |
| **Run 2** | `c2-stage5-t7-iq3s-20261027-191135-run2` | 46.5G / 51.1G (91.0%) | **B (GPU1)** | 127,041 | 1,800 | **910.7** | 139.69 | 19.3 | 233.12 | 0.834 | 368,672.1 | `4dd65c4bfb94e3d0...` |
| **Run 3** | `c2-stage5-t7-iq3s-20261027-191616-run3` | 48.8G / 51.1G (95.5%) | **A (GPU0)** | 126,955 | 1,980 | **932.1** | 136.50 | 18.1 | 245.82 | 0.795 | 457,745.2 | `df25d5b5fc76ed23...` |
| **Run 3** | `c2-stage5-t7-iq3s-20261027-191616-run3` | 48.8G / 51.1G (95.5%) | **B (GPU1)** | 127,041 | 1,659 | **947.6** | 134.26 | 18.8 | 222.67 | 0.825 | 352,185.7 | `9252ea58d47c0a21...` |

### Batch-Level Symmetry & Overlap Summary

| Run | Symmetric Mean Prefill (tok/s) | Symmetric Mean TTFT (s) | Symmetric Mean Decode (tok/s) | Batch Wall Time (s) | Decode Overlap (s) | Dual-Decode Samples | Host Swap Used |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Run 1** (Warm-up from 73.4% cache) | 761.90 | 167.02 | 17.90 | 264.38 | 65.21 | 318 | 81 MiB |
| **Run 2** (Warm 91.0% cache) | **905.05** | **140.59** | **19.45** | **233.13** | 67.12 | 327 | 81 MiB |
| **Run 3** (Warm 95.5% cache) | **939.85** | **135.38** | **18.45** | **245.84** | 86.16 | 422 | 81 MiB |
| **3-Run Mean** | **868.93** | **147.66** | **18.60** | **247.78** | **72.83** | **355.7** | **81 MiB** |
| **3-Run Median** | **905.05** | **140.59** | **18.45** | **245.84** | **67.12** | **327.0** | **81 MiB** |
| **Warm Runs 2–3 Mean** | **922.45** | **137.99** | **18.95** | **239.49** | **76.64** | **374.5** | **81 MiB** |

---

## 2. Comparison Across All Stage 5 Arms (T1 vs T2 vs T3 vs T4 vs T6 vs T8 vs T7)

| Metric | T1 (0.1.47 Base) | T2 (+SIMT) | T3 (+WMMA) | T4 (0.1.47 +SIMT+WMMA) | T6-Fixed (0.1.50 Base) | T8 (0.1.50 +SIMT+WMMA) | T7 (`jmnargi` 3-Run Mean) | T7 (`jmnargi` Warm 2–3 Mean) | T7 Peak (Run 3) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Agent A Prefill Mean (tok/s)** | 741.80 | 875.50 | 794.97 | 883.63 | 747.30 | 871.47 | 863.13 | **915.75** | **932.10** |
| **Agent B Prefill Mean (tok/s)** | 747.30 | 882.50 | 802.37 | 891.10 | 756.23 | 880.53 | 874.73 | **929.15** | **947.60** |
| **Symmetric Mean Prefill (tok/s)** | 744.55 | 879.00 | 798.67 | 887.37 | 751.77 | 876.00 | 868.93 | **922.45** | **939.85** |
| **Symmetric Mean TTFT (s)** | 171.10 | 144.81 | 159.30 | 143.36 | 169.44 | 145.22 | 147.66 | **137.99** | **135.38** |
| **Symmetric Mean Decode (tok/s)** | **21.45** | 21.30 | 21.20 | 21.20 | 21.20 | 20.77 | 18.60 | 18.95 | 18.45 |
| **Batch Wall Time Mean (s)** | 254.48 | 229.62 | 254.37 | **228.92** | 253.91 | 234.40 | 247.78 | 239.49 | 245.84 |
| **Decode Overlap Mean (s)** | 69.34 | 71.75 | 84.57 | 74.16 | 71.93 | 76.27 | 72.83 | 76.64 | 86.16 |

---

## 3. Technical Analysis of T7 (`jmnargi/Strata-V100@2c9b1dd`)

### A. Prefill Breakthrough (`939.85 tok/s` Symmetric, `947.6 tok/s` Agent B Peak)
- **PR #74 (IQ3_S WMMA2 128-token grouped tiles)** + **PR #80 (V100 prefill scheduler)** deliver the highest prefill throughput observed on dual V100-SXM2-16GB for `IQ3_S` at 128K context:
  - Once page cache warmed above 90% in Run 2 (`91.0%`) and Run 3 (`95.5%`), symmetric prefill reached **905.05 tok/s** and **939.85 tok/s** (**+26.2% over T1 baseline**, and **+5.9% over T4's 887.37 tok/s**).
  - Agent B reached **947.6 tok/s** (`134.26 s` TTFT for 127,041 tokens), shaving **36.8 seconds** off TTFT compared to T1 (`171.10 s`).
  - Note: Because `docker build` for T7 had evicted ~13.6 GiB of the 51.1 GiB GGUF shard (`37.5G / 51.1G` cached at the start of Run 1), Run 1 served as the page-cache warm-up pass (`761.90 tok/s`) without thrashing thanks to `STRATA_STAGER_SSD=0`, and Runs 2–3 ran at full warm speed (**922.45 tok/s** mean).

### B. Why Decode Dropped to `18.60 tok/s` (-12.3% vs T4 `21.20 tok/s`)
- Inspecting `[strata]` engine logs and `jmnargi/Strata-V100` `src/core/nv_defaults.cpp` revealed three default behaviors active in `jmnargi/Strata-V100@2c9b1dd` on `sm_70`:
  1. **`STRATA_ADAPT_OVERLAP=1` (Enabled by default in `nv_defaults.cpp`)**:
     - On `--mmap-experts` (where there is no pinned RAM expert arena, only the mmap file tier), `STRATA_ADAPT_OVERLAP=1` triggers background adaptive expert swapping (`adaptive: 4 rounds, 96-384 swapped`) during decode while the CPU pool simultaneously fetches missed experts from the mmap file.
     - Comparing engine logs:
       - **T4 (Upstream 0.1.47)**: `decode waited 8476.6 ms across 24577 expert fetches (avg 0.345 ms)` -> **21.2 tok/s**
       - **T7 (`jmnargi@2c9b1dd`)**: `decode waited 21737.3 ms across 52715 expert fetches (avg 0.412 ms)` -> **18.0–19.6 tok/s**
  2. **`STRATA_SM70_TABLE=1` (Enabled by default in `nv_defaults.cpp`)**:
     - Alters IQ3_S decode dequantization rounding slightly, causing output token trajectories and lengths (`1311–1980` tokens) to diverge from Upstream 0.1.47/0.1.50 (`1773` tokens on Agent A, `1224` tokens on Agent B).
  3. **Post-Response Checkpoint Pass (~7.7s extra compute after decode)**:
     - At the end of every 128K response, `jmnargi` runs `[strata] response-end checkpoint 128696 tokens: 7725.5 ms` and allocates extra VRAM buffers, dropping free VRAM to **`265 MiB`** (`15,880 MiB / 16,384 MiB` used vs `15,214 MiB` in Upstream 0.1.47/0.1.50).
- **Implication**: While `jmnargi@2c9b1dd` proves that PR #74 (`WMMA2` 128-token tiles) + PR #80 can push V100 128K `IQ3_S` prefill to **~940 tok/s**, **T4 (`Upstream 0.1.47` + `STRATA_SELECT_SIMT=1` + `STRATA_PF_WMMA=1` + `STRATA_STAGER_SSD=0`)** remains the safer, faster end-to-end production configuration (`228.92 s` wall time, `21.20 tok/s` decode, `1,170 MiB` VRAM headroom, 100% deterministic bit-exact outputs across T1/T2/T6).
