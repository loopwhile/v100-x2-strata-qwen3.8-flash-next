# Stage 5 — T7 & T7-Fixed Benchmark Summary (`jmnargi/Strata-V100@2c9b1dd`, PR #74 IQ3_S WMMA2 + PR #80 V100 Prefill Scheduler)

- **Date**: 2026-10-27
- **Experiment IDs**:
  - **T7 (Default `STRATA_SM70_PERF=1`)**: `jmnargi/Strata-V100@2c9b1dd` + `STRATA_SELECT_SIMT=1` + `STRATA_PF_WMMA=1` + `STRATA_STAGER_SSD=0`
  - **T7-Fixed (`STRATA_SM70_PERF=0` + `STRATA_PF_WMMA2=1`)**: `jmnargi/Strata-V100@2c9b1dd` + `STRATA_SM70_PERF=0` + `STRATA_SELECT_SIMT=1` + `STRATA_PF_WMMA=1` + `STRATA_PF_WMMA2=1` + `STRATA_STAGER_SSD=0`
- **Engine & Image**:
  - Image: `strata-v100-jmnargi:2c9b1dd` (`sha256:5b62fa861bbd66bf11600f153e1f277145ed0c41d118a39a6d5fc8c9735147fa`)
  - Source Commit: `jmnargi/Strata-V100@2c9b1dd7bda3102c4a8e65fbe56c45f5c6882926` (`PR #80: V100 prefill scheduler`, includes `PR #74: IQ3_S WMMA2 128-token grouped tiles` and `PR #77: V100 graph dispatch`)
  - Native Engine SHA256 (`/opt/strata/engine/strata`): `f0da5abf41115c9c0707751ec940f0f1977d04c690b55713cd19b2b7ba815030` (`0.1.45.3`, CUDA `12.9.86`, `sm_70`)
- **Model**: `Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00001-of-00002.gguf` (53.2 GiB across 2 shards in `/srv/models`)
- **Topology**: 2 independent symmetric 1-GPU agents (`strata-s5-agent-a` on GPU0 / port 8080, `strata-s5-agent-b` on GPU1 / port 8081)
- **Workload Contract**: `V100-PERFORMANCE-C2-128K-v1` (Manifest SHA256: `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`)

---

## 1. T7-Fixed Per-Batch Results (`STRATA_SM70_PERF=0` + `STRATA_SELECT_SIMT=1` + `STRATA_PF_WMMA=1` + `STRATA_PF_WMMA2=1` + `STRATA_STAGER_SSD=0`)

By setting `STRATA_SM70_PERF=0` (disabling the 15 decode/table switches in `src/core/nv_defaults.cpp` that were tuned for `--layer-split 16` rather than single-GPU 16GB `--mmap-experts`: `STRATA_SM70_TABLE=1`, `STRATA_ADAPT_OVERLAP=1`, `STRATA_EXPDEC=1`, etc.) and explicitly enabling `STRATA_SELECT_SIMT=1`, `STRATA_PF_WMMA=1`, `STRATA_PF_WMMA2=1`, and `STRATA_STAGER_SSD=0`, **T7-Fixed preserved 100% of the Stage 4-B/T1 decode speed (`21.45 tok/s` 3-run mean, up to `22.6 tok/s`) while achieving `899.23 tok/s` 3-run mean prefill (`905.40 tok/s` median, `939.0 tok/s` peak) and the shortest batch wall time of all Stage 5 experiments (`212.18 s` mean, `205.85 s` best)**.

| Run | Batch ID | Agent | Prompt Tokens | Output Tokens | Prefill (tok/s) | TTFT (s) | Decode (tok/s) | Total Wall (s) | Expert Hit Rate | File Stage (MB) | Output SHA256 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| **Run 1** | `c2-stage5-t7-fixed-iq3s-20261027-195330-run1` | **A (GPU0)** | 126,967 | 1,332 | **921.7** | 138.03 | **22.6** | **197.04** | 0.828 | 223,112.0 | `72e11c1e388b425c...` |
| **Run 1** | `c2-stage5-t7-fixed-iq3s-20261027-195330-run1` | **B (GPU1)** | 126,968 | 1,503 | **939.0** | 135.50 | **21.4** | **205.84** | 0.831 | 270,970.4 | `869d2bdd4f456cc9...` |
| **Run 2** | `c2-stage5-t7-fixed-iq3s-20261027-195737-run2` | **A (GPU0)** | 126,967 | 1,371 | **856.7** | 148.48 | **21.4** | 212.83 | 0.827 | 231,957.7 | `e6d8bbb4ab2ef70a...` |
| **Run 2** | `c2-stage5-t7-fixed-iq3s-20261027-195737-run2` | **B (GPU1)** | 126,968 | 1,489 | **867.2** | 146.69 | **20.6** | 218.99 | 0.830 | 268,537.2 | `51d312dc042b9fce...` |
| **Run 3** | `c2-stage5-t7-fixed-iq3s-20261027-200143-run3` | **A (GPU0)** | 126,967 | 1,469 | **891.4** | 142.71 | **21.3** | 211.68 | 0.828 | 257,046.8 | `82bc30ff43d4c511...` |
| **Run 3** | `c2-stage5-t7-fixed-iq3s-20261027-200143-run3` | **B (GPU1)** | 126,968 | 1,418 | **919.4** | 138.40 | **21.4** | **204.62** | 0.832 | 250,657.1 | `0ff40635a805c379...` |

### T7-Fixed Batch-Level Symmetry & Overlap Summary

| Run | Symmetric Mean Prefill (tok/s) | Symmetric Mean TTFT (s) | Symmetric Mean Decode (tok/s) | Batch Wall Time (s) | Decode Overlap (s) | Dual-Decode Samples |
|---|---:|---:|---:|---:|---:|---:|
| **Run 1** | **930.35** | **136.77** | **22.00** | **205.85** | 59.01 | 290 |
| **Run 2** | 861.95 | 147.59 | 21.00 | 219.00 | 64.35 | 315 |
| **Run 3** | **905.40** | **140.55** | **21.35** | **211.70** | 61.90 | 304 |
| **3-Run Mean** | **899.23** | **141.64** | **21.45** | **212.18** | **61.75** | **303.0** |
| **3-Run Median** | **905.40** | **140.55** | **21.35** | **211.70** | **61.90** | **304.0** |

---

## 2. T7 Unfixed Per-Batch Results (Default `STRATA_SM70_PERF=1` Stack Active)

| Run | Batch ID | Page Cache Start | Agent | Prompt Tokens | Output Tokens | Prefill (tok/s) | TTFT (s) | Decode (tok/s) | Total Wall (s) | Expert Hit Rate | File Stage (MB) | Output SHA256 |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| **Run 1** | `c2-stage5-t7-iq3s-20261027-190604-run1` | 37.5G / 51.1G (73.4%) | **A (GPU0)** | 126,955 | 1,733 | **757.9** | 167.85 | 18.0 | 264.37 | 0.821 | 366,367.4 | `c6cbda4421539d90...` |
| **Run 1** | `c2-stage5-t7-iq3s-20261027-190604-run1` | 37.5G / 51.1G (73.4%) | **B (GPU1)** | 127,041 | 1,190 | **765.9** | 166.18 | 17.8 | 233.06 | 0.837 | 240,009.7 | `912c6e92253c957d...` |
| **Run 2** | `c2-stage5-t7-iq3s-20261027-191135-run2` | 46.5G / 51.1G (91.0%) | **A (GPU0)** | 126,955 | 1,311 | **899.4** | 141.50 | 19.6 | 208.62 | 0.832 | 259,378.1 | `823b6d9fb81590fc...` |
| **Run 2** | `c2-stage5-t7-iq3s-20261027-191135-run2` | 46.5G / 51.1G (91.0%) | **B (GPU1)** | 127,041 | 1,800 | **910.7** | 139.69 | 19.3 | 233.12 | 0.834 | 368,672.1 | `4dd65c4bfb94e3d0...` |
| **Run 3** | `c2-stage5-t7-iq3s-20261027-191616-run3` | 48.8G / 51.1G (95.5%) | **A (GPU0)** | 126,955 | 1,980 | **932.1** | 136.50 | 18.1 | 245.82 | 0.795 | 457,745.2 | `df25d5b5fc76ed23...` |
| **Run 3** | `c2-stage5-t7-iq3s-20261027-191616-run3` | 48.8G / 51.1G (95.5%) | **B (GPU1)** | 127,041 | 1,659 | **947.6** | 134.26 | 18.8 | 222.67 | 0.825 | 352,185.7 | `9252ea58d47c0a21...` |

---

## 3. Comparison Across All Stage 5 Arms (T1 vs T2 vs T3 vs T4 vs T6 vs T8 vs T7 vs T7-Fixed)

| Metric | T1 (0.1.47 Base) | T2 (+SIMT) | T3 (+WMMA) | T4 (0.1.47 +SIMT+WMMA) | T6-Fixed (0.1.50 Base) | T8 (0.1.50 +SIMT+WMMA) | T7 Unfixed (`jmnargi` Default) | **T7-Fixed ⭐ (`jmnargi` + `SM70_PERF=0` + `WMMA2=1`)** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Agent A Prefill Mean (tok/s)** | 741.80 | 875.50 | 794.97 | 883.63 | 747.30 | 871.47 | 863.13 | **889.93** (Med **891.40**, Peak **921.70**) |
| **Agent B Prefill Mean (tok/s)** | 747.30 | 882.50 | 802.37 | 891.10 | 756.23 | 880.53 | 874.73 | **908.53** (Med **919.40**, Peak **939.00**) |
| **Symmetric Mean Prefill (tok/s)** | 744.55 | 879.00 | 798.67 | 887.37 | 751.77 | 876.00 | 868.93 | **899.23** (Med **905.40**, Peak **930.35**) |
| **Symmetric Mean TTFT (s)** | 171.10 | 144.81 | 159.30 | 143.36 | 169.44 | 145.22 | 147.66 | **141.64** (Med **140.55**, Best **136.77**) |
| **Symmetric Mean Decode (tok/s)** | **21.45** | 21.30 | 21.20 | 21.20 | 21.20 | 20.77 | 18.60 | **21.45** (Med **21.35**, Peak **22.00**) |
| **Batch Wall Time Mean (s)** | 254.48 | 229.62 | 254.37 | 228.92 | 253.91 | 234.40 | 247.78 | **212.18** (Med **211.70**, Best **205.85**) |
| **Decode Overlap Mean (s)** | 69.34 | 71.75 | 84.57 | 74.16 | 71.93 | 76.27 | 72.83 | **61.75** |

---

## 4. Technical Root Cause & Resolution Summary

1. **Why Unfixed T7 Decode Dropped to `18.60 tok/s`**:
   - In `jmnargi/Strata-V100@2c9b1dd`, `src/core/nv_defaults.cpp` enables 16 `sm_70` switches by default (`STRATA_SM70_PERF=1`), which were tuned on a 2-GPU `--layer-split 16` rig where 32 GB of combined VRAM holds nearly all experts in VRAM.
   - On our independent 1-GPU-per-agent 16 GB `--mmap-experts` topology (where 4,625 expert slots fit in VRAM and ~17% miss to the CPU pool), `STRATA_ADAPT_OVERLAP=1`, `STRATA_SM70_TABLE=1`, and `STRATA_EXPDEC=1` caused adaptive tier swap contention (`decode waited 18.3–21.7s` vs `8.5s`) and extra CUDA graph VRAM consumption.
2. **How T7-Fixed Achieved Both `900–930 tok/s` Prefill AND `21.45 tok/s` (`22.6 tok/s` Peak) Decode**:
   - Setting `STRATA_SM70_PERF=0` turned off all 15 decode/table switches in `nv_defaults.cpp`, restoring the clean upstream decode path (`21.45 tok/s` 3-run mean, matching T1's `21.45 tok/s` 100%).
   - Explicitly passing `STRATA_SELECT_SIMT=1`, `STRATA_PF_WMMA=1`, `STRATA_PF_WMMA2=1`, and `STRATA_STAGER_SSD=0` kept PR #74's grouped 128-token `IQ3_S` WMMA2 kernel and PR #80's V100 prefill scheduler active, yielding **899.23 tok/s mean (`905.40 tok/s` median, `930.35 tok/s` peak) prefill** and cutting 3-run mean batch wall time to **212.18 s** (**-42.30 s faster than T1** and **-16.74 s faster than T4**).
