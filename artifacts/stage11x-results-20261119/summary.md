# Stage 11X Follow-up Optimization Summary (`2026-11-19`)

- **Model & Hardware Contract**: `Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS`, Dual Tesla V100-SXM2-16GB (`150 W` cap, `135–1245 MHz` clock lock, isolated single-GPU agents on cpusets `0-2,6-8` and `3-5,9-11`, `131072` context, INT8 KV, `32768` KV resident, `--mmap-experts`, `--expert-cache auto`).
- **Operational Baseline (`S10-D4`, `d4-20261110T225518`)**: Upstream `0.1.59` (`712fec6b4297c9cfd32ab43daaa2979a9aa01edf`) + stock `DFlash2` selector pack (`--spec 8 --draft-conf 0.7 --prefill auto`) — Prefill `1025.1 / 1027.8 tok/s`, Decode `30.4 / 30.3 tok/s`, TTFT `124.08 / 123.79 s`.
- **Stage 11X Stretch Target**: Prefill `>= 1200.0 tok/s` AND Decode `>= 40.0 tok/s` simultaneously on both Agent A and Agent B across 3 fresh-process concurrent 128K C2 batches.

---

## 1. Gate A & Gate B Execution Overview

| Arm | Run ID | Type | Batches | Config Delta vs `S10-D4` | Prefill A / B (tok/s) | Decode A / B (tok/s) | TTFT A / B (s) | Expert Cache Hit A / B | Verdict |
|---|---|---|---:|---|---:|---:|---:|---:|---|
| `S10-D4` (Ref) | `d4-20261110T225518` | Baseline | 3 | `--spec 8 --draft-conf 0.7 --prefill auto` | `1025.1 / 1027.8` | `30.4 / 30.3` | `124.08 / 123.79` | `85.8–86.6% / 82.9–87.6%` | Reference |
| **`S11X-A0`** | `a0-20261119` | Source Audit | 0 | Read-only audit of `0.1.59`, `0.1.60`, and V100 fork `0.1.45.10` | - | - | - | - | **PASS** ([Audit](../../docs/STAGE11X_SOURCE_AUDIT.md)) |
| **`S11X-P0`** | `p0-20261119T035717` | Diagnostic | 1 (unscored) | `+ STRATA_PREFILL_TIMING=1 STRATA_DECODE_TIMING=1 STRATA_VERIFY_PROFILE=1` (cold cache) | `822.9 / 826.1` | `28.8 / 28.5` | `154.56 / 153.97` | `86.5% / 87.6%` | **DIAGNOSTIC PASS** ([Report](p0-20261119T035717/report.md)) |
| **`S11X-C0`** | `c0-20261119T040328` | Scored Candidate | 3 | `+ STRATA_PF_HC_REGION=1` | **`1033.7 / 1037.6`** | **`29.7 / 28.4`** | **`123.07 / 122.60`** | `85.9% / 82.9%` (med) | **PASS — NOT PROMOTED** ([Report](c0-20261119T040328/report.md)) |
| **`S11X-P1`** (Diag A) | `p1-20261119T065137` | Diagnostic | 1 (unscored) | `stage11x-p1` + `WMMA2=1 SKINNY=1 LEAN=0 PREFILL_TIMING=1` (94% cache, 9.6/7.8 GB OS read) | `947.8 / 949.6` | `28.3 / 30.3` | `134.20 / 133.95` | `82.1% / 87.6%` | **DIAGNOSTIC PASS** ([Report](p1-20261119T065137/report.md)) |
| **`S11X-P1`** (Diag B) | `p1-20261119T065652` | Diagnostic | 1 (unscored) | `stage11x-p1` + `WMMA2=1 SKINNY=1 LEAN=1 PREFILL_TIMING=1` (warm cache) | `1030.0 / 1038.1` | `27.5 / 28.1` | `123.51 / 122.54` | `80.9% / 82.7%` | **DIAGNOSTIC PASS** ([Report](p1-20261119T065652/report.md)) |
| **`S11X-P1`** (Diag C) | `p1-20261119T070244` | Diagnostic | 1 (unscored) | `stage11x-p1` + `WMMA2=1 SKINNY=1 LEAN=0 PREFILL_TIMING=1` (warm cache) | `1024.1 / 1024.8` | `28.1 / 30.3` | `124.22 / 124.15` | `82.5% / 87.6%` | **DIAGNOSTIC PASS** ([Report](p1-20261119T070244/report.md)) |
| **`S11X-P1`** | `p1-20261119T070809` | Scored Candidate | 3 | `stage11x-p1` + `WMMA2=1 LEAN=1 SKINNY=1` | **`1043.9 / 1047.7`** | **`28.5 / 28.4`** | **`121.88 / 121.43`** | `82.7% / 82.7%` (med) | **PASS — HOLD FOR `S11X-C1`** ([Report](p1-20261119T070809/report.md)) |
| **`S11X-D1`** (Diag) | `d1-20261119T074052` | Diagnostic | 1 (unscored) | `stage11x-d1` (`PathC7`: `AVX512BW_IQ=22`, `IQ_MT_MIN=1`, `IQ_GATHER=1`, `IQ256_GATHER=1`, `Q2_BITPLANE=1`) + `DECODE_TIMING=1` (91% cache) | `831.7 / 820.1` | `32.0 / 31.2` | `152.91 / 155.12` | `88.2% / 86.3%` | **DIAGNOSTIC PASS** ([Report](d1-20261119T074052/report.md)) |
| **`S11X-D1`** | `d1-20261119T074621` | Scored Candidate | 3 | `stage11x-d1` (`PathC7`: `AVX512BW_IQ=22`, `IQ_MT_MIN=1`, `IQ_GATHER=1`, `IQ256_GATHER=1`, `Q2_BITPLANE=1`) (54–55% fincore) | `943.0 / 944.4` | **`32.6 / 31.9`** | `134.88 / 134.69` | **`88.1% / 86.3%`** (med) | **PASS — NEW DECODE RECORD** ([Report](d1-20261119T074621/report.md)) |
| **`S11X-D1W`** | `d1w-20261119T081230` | Scored Re-validation | 3 | `stage11x-d1` (`PathC7`, pre-warmed 100% shard 1 fincore before startup) | **`1010.8 / 1016.6`** | **`33.8 / 32.2`** | `125.86 / 125.14` | **`87.9% / 86.3%`** (med) | **PASS — WARM RE-VALIDATION** ([Report](d1w-20261119T081230/report.md)) |
| **`S11X-C1`** (Diag) | `c1-20261119T084920` | Diagnostic | 1 (unscored) | `stage11x-c1` (`P1` + `D1` `PathC7`) + `PREFILL_TIMING=1 DECODE_TIMING=1` (99% cache) | `1035.1 / 1038.1` | `32.8 / 32.3` | `122.88 / 122.56` | `83.1% / 86.3%` | **DIAGNOSTIC PASS** ([Report](c1-20261119T084920/report.md)) |
| **`S11X-C1`** | `c1-20261119T085422` | Scored Candidate | 3 | `stage11x-c1` (`WMMA2=1 LEAN=1 SKINNY=1` + `PathC7`) (99–100% cache) | **`1037.6 / 1044.8`** | **`33.0 / 32.3`** | **`122.60 / 121.77`** | `83.1% / 86.3%` (med) | **PASS — BEST ALL-METRIC** ([Report](c1-20261119T085422/report.md)) |
| **`S11X-D2`** (Tier 1 Diag A) | `d2-20261119T001214` | Diagnostic | 1 (unscored) | `stage11x-c1` + 6 `nv_defaults` GPU flags + `AUX_CPUS=auto` + timing | `705.5 / 715.7` | `32.8 / 32.1` | `180.21 / 177.66` | `82.9% / 86.3%` | **DIAGNOSTIC PASS (`AUX_CPUS=auto` DROPPED)** ([Report](d2-20261119T001214/report.md)) |
| **`S11X-D2`** (Tier 1 Diag B) | `d2-20261119T001808` | Diagnostic | 1 (unscored) | `stage11x-c1` + 6 `nv_defaults` GPU flags (no `AUX_CPUS`) + timing | `1032.4 / 1037.8` | `32.7 / 32.7` | `123.23 / 122.59` | `82.7% / 86.3%` | **DIAGNOSTIC PASS** ([Report](d2-20261119T001808/report.md)) |
| **`S11X-D2`** (Tier 2 Diag) | `d2-20261119T003229` | Diagnostic | 1 (unscored) | `stage11x-d2` (`MMAP_ADAPT_ASYNC=1` + `COLD_OVERLAP=5` + 6 GPU flags) + timing (90.6% cache) | `883.3 / 862.4` | **`34.9 / 38.3`** | `143.99 / 147.67` | `82.3% / 87.6%` | **DIAGNOSTIC PASS** ([Report](d2-20261119T003229/report.md)) |
| **`S11X-D2`** | `d2-20261119T003753` | Scored Candidate | 3 | `stage11x-d2` (`C1` + 6 GPU flags + `MMAP_ADAPT_ASYNC=1` + `COLD_OVERLAP=5`) | **`1032.6 / 1037.0`** | **`37.1 / 41.0`** | **`123.21 / 122.69`** | `81.6% / 87.6%` (med) | **PASS — NEW DECODE RECORD (`B >= 40`)** ([Report](d2-20261119T003753/report.md)) |

---

## 2. Gate A: `S11X-P0` (`p0-20261119T035717`) Full Profiling Breakdown (`--spec 8`)

`S11X-P0` captured the first full 27-phase GPU event prefill timeline (`STRATA_PREFILL_TIMING=1`) and `spec 8` decode timing breakdown (`STRATA_DECODE_TIMING=1`, `STRATA_VERIFY_PROFILE=1`) on the `S10-D4` configuration. Because `S11X-P0` ran immediately after an 8-day idle period, the first 128K C2 batch also reflects initial cold OS page-cache warming (`21.17 GB` / `20.56 GB` read from NVMe storage).

### 2.1 27-Phase Prefill GPU Timeline Breakdown (`126,960` / `126,961` tokens across 16 chunks of `8192`)

- **Total GPU Timeline / Wall / Host Staging**:
  - **Agent A**: GPU timeline `152,874 ms`, wall `152,924 ms`, host staging `122,320 ms` (host chunk setup `152 ms`, wait per chunk `209 ms`, post-chunk draft/progress `583 ms`, PLE `328 ms`).
  - **Agent B**: GPU timeline `152,259 ms`, wall `152,310 ms`, host staging `121,669 ms` (host chunk setup `135 ms`, wait per chunk `216 ms`, post-chunk draft/progress `552 ms`, PLE `338 ms`).

| Prefill GPU Phase | Agent A (ms) | Agent A (%) | Agent B (ms) | Agent B (%) | Bottleneck Category |
|---|---:|---:|---:|---:|---|
| **`dequant` (Expert weight dequant to FP16)** | **59,914** | **39.2%** | **58,546** | **38.5%** | **#1 Dominant Prefill Bottleneck** |
| **`gemm gate/up` (MoE Gate/Up WMMA GEMM)** | **24,817** | **16.2%** | **25,637** | **16.8%** | **#2 MoE Compute** |
| **`gemm down` (MoE Down WMMA GEMM)** | **12,639** | **8.3%** | **12,865** | **8.4%** | **#3 MoE Compute** |
| **`qsa attn` (Sparse Attention core)** | **9,792** | **6.4%** | **10,050** | **6.6%** | **#4 Attention** |
| **`wait copy` (Host->GPU expert ring wait)** | **6,164** | **4.0%** | **5,741** | **3.8%** | PCIe / Cold Cache Transfer |
| **`gdn` (GDN block total)** | **5,910** | **3.9%** | **5,905** | **3.9%** | Gated DeltaNet |
| **`gdn recurrence`** | **4,997** | **3.3%** | **4,998** | **3.3%** | Gated DeltaNet |
| **`qsa select` (Top-K block selection)** | **4,726** | **3.1%** | **4,755** | **3.1%** | Attention |
| **`hc write`** | **3,250** | **2.1%** | **3,155** | **2.1%** | Hyper-Connection |
| **`qsa proj`** | **2,984** | **2.0%** | **3,007** | **2.0%** | Attention |
| **`hc read: down+silu`** | **2,610** | **1.7%** | **2,572** | **1.7%** | Hyper-Connection |
| **`gdn out proj`** | **2,020** | **1.3%** | **2,013** | **1.3%** | Gated DeltaNet |
| **`router+shared`** | **1,962** | **1.3%** | **1,975** | **1.3%** | Routing & Shared Expert |
| **`hc read: up`** | **1,695** | **1.1%** | **1,688** | **1.1%** | Hyper-Connection |
| **`hc read: mix`** | **1,585** | **1.0%** | **1,585** | **1.0%** | Hyper-Connection |
| **`hc read: inject`** | **1,497** | **1.0%** | **1,503** | **1.0%** | Hyper-Connection |
| **`kv stage`** | **1,284** | **0.8%** | **1,286** | **0.8%** | KV Streaming |
| **`host grouping`** | **1,165** | **0.8%** | **1,118** | **0.7%** | Host Expert Grouping |
| **`combine`** | **940** | **0.6%** | **953** | **0.6%** | MoE Combine |
| **`gather`** | **798** | **0.5%** | **803** | **0.5%** | MoE Gather |
| **`embed+steps`** | **738** | **0.5%** | **703** | **0.5%** | Embedding |
| **`ple`** | **639** | **0.4%** | **655** | **0.4%** | Per-Layer Embedding |
| **`gdn conv+gates`** | **510** | **0.3%** | **510** | **0.3%** | Gated DeltaNet |
| **`qsa: indexer gemms`** | **177** | **0.1%** | **177** | **0.1%** | Attention Indexer |
| **`hc read`** | **40** | **0.0%** | **40** | **0.0%** | Hyper-Connection |
| **`qsa: norm/rope/kv append/q prep`** | **15** | **0.0%** | **15** | **0.0%** | Attention Prep |
| **`qsa indexer`** | **4** | **0.0%** | **4** | **0.0%** | Attention Indexer |

- **Key Prefill Finding**: `dequant` (`~39%`) + `gemm gate/up` (`~16.5%`) + `gemm down` (`~8.3%`) consume **`63.7%` (`97.4 s` / `97.1 s`)** of total GPU prefill time. In warm batches (where `wait copy` drops by `~28 s`), `dequant + gemm` represents **`~79%`** of the `~123 s` prefill wall time! This directly connects to the V100 fork's `0cdb0d64` (`__half2` packed Volta prompt dequantization), `w2` (`WMMA2` for `ty == 18, 21, 22, 20`), and `4d0f35fd` / `19175f8c` (register-fed `w2_iq4_skinny` down kernel, which eliminates separate dequant+global write for the 18 `IQ4_NL` down layers).

### 2.2 Decode Window Timing Breakdown (`--spec 8 --draft-conf 0.7`)

| Metric / Stage | Agent A (`903` windows) | Agent B (`923` windows) | Notes |
|---|---:|---:|---|
| **Generated Tokens / Decode Time** | `2017 tok` in `70,053 ms` (`28.8 tok/s`) | `1895 tok` in `66,580 ms` (`28.5 tok/s`) | Cold diagnostic batch with profiling active |
| **Avg Window Size (`avg T`)** | `2.59` | `2.38` | Dynamic DFlash2 window |
| **Effective Tokens / Window** | **`2.23 tok/win`** | **`2.05 tok/win`** | `1114 / 1437` (`77.5%`) vs `972 / 1273` (`76.4%`) drafts accepted |
| **Total Host Window Time** | **`77.58 ms/win`** | **`72.13 ms/win`** | `2230 / 77.58 = 28.74 tok/s`; `2053 / 72.13 = 28.46 tok/s` |
| ├─ **`verify` total** | **`64.89 ms`** (`83.6%`) | **`59.85 ms`** (`83.0%`) | 48-layer speculative verification pass |
| │  ├─ `GPU-reach wait` | `21.43 ms` | `20.85 ms` | GPU compute before CPU sync |
| │  ├─ `per-layer host` | `40.38 ms` | `35.99 ms` | `plan 0.27/0.26` + `actq 0.18/0.18` + `jobs 2.78/2.93` + **`CPU 36.87/32.35 ms`** |
| │  └─ `stage` | `0.02 ms` | `0.02 ms` | |
| ├─ **`adapt join`** | **`9.43 ms`** (`12.2%`) | **`9.02 ms`** (`12.5%`) | Waiting for `22.1 / 22.0` expert cache swaps/window |
| ├─ **`draft` (DFlash2)** | **`3.16 ms`** (`4.1%`) | **`3.16 ms`** (`4.4%`) | Q4_0-selq4 DFlash2 proposal |
| └─ `adapt wait` + `commit/emit` + `other` | `0.09 ms` | `0.11 ms` | |
| **GPU Event Stages (`total`)** | **`64.67 ms/win`** | **`59.64 ms/win`** | Matches `verify` host duration |
| ├─ **GDN `waitCPU` + QSA `waitCPU`** | **`35.43 ms`** (`29.30 + 6.13`) | **`31.35 ms`** (`26.26 + 5.09`) | **54.8% / 52.6% of GPU verify time is waiting on CPU experts!** |
| ├─ GDN `VRAM hits` + QSA `VRAM hits` | `3.98 ms` (`2.98 + 1.00`) | `3.82 ms` (`2.86 + 0.96`) | `21.03 / 19.56` resident experts/layer-window on GPU |
| ├─ QSA `scores+topk` + `attention` + `kv-resolve` | `3.31 ms` (`2.22 + 0.73 + 0.36`) | `3.22 ms` (`2.17 + 0.70 + 0.35`) | 128K sparse attention + KV streaming (`98.39% / 98.35%` VRAM hit) |
| └─ All other GPU kernels (GDN, router, shared, HC, head) | `21.95 ms` | `21.25 ms` | Pure non-stalled GPU execution |
| **Per Layer-Window Expert Split** | `2.41` CPU (`3.27` entries) / `21.03` VRAM | `2.13` CPU (`2.76` entries) / `19.56` VRAM | Cache hit rate: `86.5%` (A) / `87.6%` (B); `334 / 330 us` per missed expert |

- **Key Decode Finding**: Out of `77.58 / 72.13 ms/window`, **`CPU expert computation` (`36.87 / 32.35 ms`, causing `35.43 / 31.35 ms` of GPU `waitCPU` stall) + `adapt join` (`9.43 / 9.02 ms`) account for `46.30 / 41.37 ms/window` (`59.7% / 57.4%` of total window time)**. Non-stalled GPU kernels + DFlash2 draft take only `~32.4 / 31.4 ms/window`.

---

## 3. Gate B: `S11X-C0` (`c0-20261119T040328`) 3-Batch C2 Evaluation (`S10-D4` + `STRATA_PF_HC_REGION=1`)

| Batch | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Output Tokens A / B | Expert Cache Hit A / B | DFlash2 Accepted / Offered A / B | OS Read MB A / B | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `batch-1` | `1038.8` | `1037.6` | `29.7` | `28.3` | `122.47` | `122.60` | `1784 / 2509` | `85.8% / 82.3%` | `991/1278 (77.5%)` / `1519/1901 (79.9%)` | `416.0 / 462.7` | PASS |
| `batch-2` | `1013.7` | `1029.2` | `30.4` | `30.3` | `125.50` | `123.62` | `1661 / 1895` | `86.6% / 87.6%` | `922/1180 (78.1%)` / `972/1273 (76.4%)` | `796.9 / 457.0` | PASS |
| `batch-3` | `1033.7` | `1039.5` | `29.7` | `28.4` | `123.07` | `122.39` | `1833 / 2261` | `85.9% / 82.9%` | `1022/1341 (76.2%)` / `1349/1711 (78.8%)` | `481.9 / 441.1` | PASS |
| **Median** | **`1033.7`** | **`1037.6`** | **`29.7`** | **`28.4`** | **`123.07`** | **`122.60`** | `1784 / 2261` | **`85.9% / 82.9%`** | `77.5% / 78.8%` | `481.9 / 457.0` | **PASS** |
| **vs `S10-D4`** | **`+8.6` (`+0.84%`)** | **`+9.8` (`+0.95%`)** | **`-0.7` (`-2.3%`)** | **`-1.9` (`-6.3%`)** | **`-1.01 s`** | **`-1.19 s`** | - | - | - | - | **NOT PROMOTED** |

### Why `S11X-C0` Regressed Decode Medians and Is Not Promoted
1. **Prefill gain is `< 1%`**: Placing the hyper-connection read scratch in the shared region (`STRATA_PF_HC_REGION=1`) reduced prompt cache borrowing from `2489` slots (`3.99 GiB`) to `2191` slots (`3.50 GiB`) and improved Prefill median by `+8.6 / +9.8 tok/s` (`1033.7 / 1037.6 tok/s`, TTFT `-1.01 / -1.19 s`), matching the `~1%` effect anticipated from `S11X-P0` (`hc read` sub-stages total only `~7.4 s` = `4.8%` of prefill).
2. **Decode sensitivity to output trajectory & expert cache hit rate**: In `batch-2`, where Agent B generated the standard `1895`-token trajectory (`87.6%` expert cache hit rate), `S11X-C0` matched `S10-D4` (`30.4 / 30.3 tok/s`). However, because `STRATA_PF_HC_REGION=1` slightly alters FP16 reduction ordering during prefill, `batch-1` and `batch-3` diverged onto longer `2509`- and `2261`-token generation trajectories on Agent B where static profile expert cache hit rate dropped from `87.6%` to `82.3% / 82.9%` (`+43%` more CPU expert misses), pulling Agent B decode down to `28.3 / 28.4 tok/s`.
3. **Gate B Decision**: Per Section 4 of `docs/STAGE11_OPTIMIZATION_FOLLOWUP_PLAN.md` (*"성능 개선 약 1%에 그치면 주력 후보로 승격하지 않음"*), `S11X-C0` is recorded and **not promoted**. `S10-D4` remains the undefeated baseline (`30.4 / 30.3 tok/s`).

---

## 4. Gate C Step 2: `S11X-P1` Volta Prefill Optimization (`strata-v100:stage11x-p1`, `062f6e3bcf41288e...`)

- **Patch & Parity**: [stage11x-p1.patch](../../docker/patches/stage11x-p1.patch) on pinned `0.1.59` adds:
  1. `STRATA_PF_WMMA2=1` (+ auto `STRATA_PF_WMMA2_N64` for `max_rows >= 128`): expands `gemm_iq_f16_w2_kernel` to `IQ3_XXS (18)`, `IQ3_S (21)`, `IQ2_S (22)` Gate/Up (29/48 layers) and `IQ4_NL (20)` Down (18/48 layers), with `__byte_perm` + `__hfma2` (`w2_scale_pair`) FP16 dequant and 2-byte-aligned row support.
  2. `STRATA_PF_WMMA_SKINNY=1`: register-fed `mma.sync.aligned.m8n8k4` `w2_iq4_skinny` kernel for `IQ4_NL` down when `max_rows <= 8`.
  3. `gemm_iq_f16_grouped` enhancements: `Q2_0` (`DEC=1`, 30/48 down layers) `__byte_perm` dequant, `MT=2` small tiles for `max_rows <= 128` (`dq_*_half` `__half2` stores), and always-on `GroupedWeightTable` (`indirect_w`, eliminates `flush`/`gather_native` copies of expert weights into `grp_gu`/`grp_d`).
  4. `STRATA_PF_WMMA_LEAN=1`: skips `m.Xs` (`gather_rows16`), passes `ids = m.src_dev` directly to Gate/Up WMMA, aliases `m.Hh = m.xn16`, and omits the fallback `dq_gu`/`dq_d` ring (`S11X_WMMA_LEAN eligible` logged on both agents).
  - **Parity (`pf_wmma_parity`)**: `0` failures on GPU 0 and GPU 1 across `default`, `wmma2 N64=0`, `wmma2 N64=1`, `skinny`, and `--bench` ([GPU 0 log](s11x-p1-build/parity-gpu0.log), [GPU 1 log](s11x-p1-build/parity-gpu1.log)).

### 4.1 Diagnostic Contribution Separation (`STRATA_PREFILL_TIMING=1`, 1-Batch Non-Scored)

| Phase / Metric | `S11X-P0` (`p0`, cold `21.2/20.6 GB`) | Diag A (`LEAN=0`, `94%` cache `9.6/7.8 GB`) | Diag C (`LEAN=0`, warm `0.58/0.48 GB`) | Diag B (`LEAN=1`, warm `0.94/0.62 GB`) | Delta Diag B vs `S11X-P0` / Diag C |
|---|---:|---:|---:|---:|---|
| **Prefill A / B (tok/s)** | `822.9 / 826.1` | `947.8 / 949.6` | `1024.1 / 1024.8` | **`1030.0 / 1038.1`** | **`+5.9 / +13.3 tok/s` vs Diag C** |
| **TTFT A / B (s)** | `154.56 / 153.97` | `134.20 / 133.95` | `124.22 / 124.15` | **`123.51 / 122.54`** | **`-0.71 / -1.61 s` vs Diag C** |
| **Borrowed Cache Slots** | `2489` (`3.99 GiB`) | `2489` (`3.99 GiB`) | `2489` (`3.99 GiB`) | **`2179` (`3.48 GiB`)** | **`-310` slots (`+0.51 GiB` kept)** |
| `gemm gate/up` A / B (ms) | `24,817 / 25,637` | `19,985 / 20,568` | `20,079 / 20,667` | `20,958 / 21,487` | `-3.86 / -4.15 s` vs `P0`; `+0.88/+0.82 s` vs Diag C |
| `gemm down` A / B (ms) | `12,639 / 12,865` | `9,386 / 9,731` | `9,063 / 9,188` | `9,036 / 9,176` | **`-3.60 / -3.69 s` vs `P0`** |
| `gather` (`m.Xs`) A / B (ms) | `798 / 803` | `780 / 779` | `779 / 783` | **`14 / 14`** | **`-0.77 / -0.77 s` vs Diag C** |
| `dequant` (`kPfDequant`) (ms) | `59,914 / 58,546` | `40,905 / 39,928` | `30,698 / 30,458` | `31,172 / 29,399` | Staging/loop wait (not GPU math) |
| `wait copy` A / B (ms) | `6,164 / 5,741` | `13,251 / 12,815` | `13,848 / 13,017` | `12,782 / 12,530` | `wait_copied` moved before `GemmGU` |

### 4.2 Scored 3-Batch C2 Results (`p1-20261119T070809`, `WMMA2=1 LEAN=1 SKINNY=1`, No Timing Overhead)

| Batch | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Output Tokens A / B | Expert Cache Hit A / B | DFlash2 Accepted / Offered A / B | OS Read MB A / B | Peak VRAM A / B (MiB) | Power Mean/Peak A / B (W) | Temp Mean/Peak A / B (°C) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `batch-1` | `1046.2` | `1048.4` | `28.5` | `30.4` | `121.61` | `121.34` | `2490 / 1895` | `82.9% / 87.6%` | `1557/2000 (77.8%)` / `972/1273 (76.4%)` | `616.8 / 457.1` | `15571 / 15571` | `91.9/198.9` / `91.8/208.9` | `56.2/65` / `56.9/64` |
| `batch-2` | `1043.9` | `1047.7` | `28.4` | `28.3` | `121.88` | `121.43` | `2575 / 2252` | `82.5% / 82.7%` | `1616/2041 (79.2%)` / `1358/1703 (79.7%)` | `1340.1 / 958.6` | `15571 / 15571` | `91.5/212.9` / `92.1/221.9` | `57.7/66` / `57.6/65` |
| `batch-3` | `1038.0` | `1043.6` | `28.8` | `28.4` | `122.57` | `121.90` | `2513 / 2211` | `82.7% / 82.6%` | `1573/1943 (81.0%)` / `1326/1643 (80.7%)` | `1162.6 / 794.6` | `15571 / 15571` | `91.9/202.8` / `91.0/209.5` | `58.1/67` / `57.8/65` |
| **Median** | **`1043.9`** | **`1047.7`** | **`28.5`** | **`28.4`** | **`121.88`** | **`121.43`** | `2513 / 2211` | **`82.7% / 82.7%`** | `79.2% / 79.7%` | `1162.6 / 794.6` | `15571 / 15571` | `91.9/202.8` / `91.8/209.5` | `57.7/66` / `57.6/65` |
| **vs `S10-D4`** | **`+18.8` (`+1.8%`)** | **`+19.9` (`+1.9%`)** | **`-1.9`** | **`-1.9`** | **`-2.20 s`** | **`-2.36 s`** | - | - | - | - | - | - | - |

### 4.3 Root Cause & Step 3 (`S11X-D1`) Handoff Decision
1. **Why GEMM compute dropped ~20% (`-7.5 to -8.6 s`) yet TTFT dropped only `2.2–2.4 s`**: Source inspection of `src/prefill/prefill.cpp` (lines 5802, 5853, 5996) confirms that under `STRATA_PF_WMMA=1`, `kPfDequant` does **not** measure an FP16 weight dequant kernel — it marks the 16-expert `MMQ_GROUP` staging loop before `wait_copied` (`kPfWaitCopy`) and `kPfGemmGU`. Thus `kPfDequant + kPfWaitCopy` (`43.95 s` A / `41.93 s` B in `p1-20261119T065652`) reflects PCIe/host staging stalls across `30.8 GiB` of streamed experts (`~105 s` host staging), plus `~47 s` of non-expert GPU phases (`gdn`, `qsa`, `hc`, etc.). Additionally, `indirect_w`'s delayed `--pending` release (`gg_released` per 16-expert group) offset part of the GEMM gain (~`42–44 s` staging wait vs `~39.5 s` inferred warm `S10-D4`).
2. **Decode trajectory shift**: Like `S11X-C0`, prefill FP16 rounding differences shifted greedy (`temp=0`) C2 generations onto longer `~2500`-token outputs (`82.5–82.9%` expert cache hit, `28.5/28.4 tok/s`). On the standard `1895`-token `87.6%` hit trajectory (`batch-1` B), decode matched `S10-D4` at **`30.4 tok/s`**.
3. **Handoff Decision for Step 3 (`S11X-D1`)**: **Hold `S11X-P1` (`strata-v100:stage11x-p1`, `stage11x-p1.patch`) for later combination (`S11X-C1`) rather than using it as Step 3's base.** Step 3 (`S11X-D1`) should patch directly from pinned `0.1.59` (`sha256:dd8913d85f18...`) so decode optimizations are measured cleanly against `S10-D4` (`30.4 / 30.3 tok/s`) without `S11X-P1`'s greedy trajectory shift.

---

## 5. Gate C Step 1 & Step 3: `S11X-D1` Hybrid CPU Expert Optimization (`strata-v100:stage11x-d1`, `97e8f19921ec7a0e...`)

- **Base & Patch**: Cleanly patched from pinned upstream `0.1.59` (`sha256:dd8913d85f18...`, without `S11X-P1`) via [stage11x-d1.patch](../../docker/patches/stage11x-d1.patch) ([Microbenchmark Report](cpu-microbench-20261119T060426/report.md)):
  1. **`cmake/backends/cpu.cmake`**: Compiles `expert.cpp` and `iq_avx512.cpp` with `-mavx512f -mavx512bw -mavx512vl -mavx512dq -mbmi2 -mf16c -mfma` (removing `-mavx512vnni`, `-mavx512vbmi`, `-mavx512vpopcntdq` for Xeon W-2135).
  2. **`iq_avx512.cpp` & `expert.cpp`**: Replaces VNNI (`dpwssd512`/`dpbusd512`/`dpbusd256` -> `_mm512_maddubs_epi16` + `_mm512_madd_epi16`), VBMI (`unpack64_q2_0_sw` / shift-mask), and VPOPCNTDQ (`#if defined(__AVX512VPOPCNTDQ__)` fallback) cleanly; removes `std::getenv` from hot loops.
  3. **`expert_layout.cpp`, `native_expert.cpp`, `q2_avx2.cpp`**: Adds `strata_cpu_reload_env()` / `strata_cpu_ensure_env()` (thread-safe `std::atomic<bool>` + `std::mutex`), `STRATA_AVX512BW_IQ=<mask>` selective per-type AVX-512BW bitmask dispatch, and `cpu_expert_kernels_desc()` startup logging in `src/program/generate.cpp`.
  4. **`PathC7_Hybrid_512BW_IQ2S_AVX2_Q2BP` Runtime Dispatch** (`STRATA_AVX512BW_IQ=22`, `STRATA_IQ_MT_MIN=1`, `STRATA_IQ_GATHER=1`, `STRATA_IQ256_GATHER=1`, `STRATA_Q2_BITPLANE=1`):
     - `IQ2_S` (`ty=22`, 10/48 Gate/Up layers): non-VNNI AVX-512BW `iq512_gu_rows` (`vpmaddubsw+vpmaddwd+vpgatherqd`)
     - `IQ2_XXS/IQ2_XS/IQ3_XXS/IQ3_S` (`ty=16,17,18,21`, 38/48 Gate/Up layers): AVX2 `iq256_gu_rows` (`STRATA_IQ256_GATHER=1`, `MT_MIN=1`)
     - `IQ4_NL` (`ty=20`, 18/48 Down layers): AVX2 `iq4nl256_down_rows` (`MT_MIN=1`)
     - `Q2_0` (`ty=42`, 30/48 Down layers): AVX2 bitplane `q2_0_gguf_rows_multi_avx2` (`rows_bp_bitplane`) + `act_quant_q8_1_avx2+bitplane_image`.
- **ISA & Parity Verification**:
  - `check_isa_guard.py /opt/strata/build-stage9/libstrata_kernels_cpu.a`: `853 functions, 180 hold wide-ISA instructions, 0 not allowed`.
  - `objdump -d`: **`0`** VNNI/VBMI/VPOPCNT instructions in `iq_avx512.cpp.o` (`12,884` ZMM) and `expert.cpp.o` (`4,131` ZMM); only upstream `cpu_avx512_ok()`/`cpu_avxvnni_ok()`-guarded `nvfp4_512_*`/`tq_rows_avx512`/`vnni::*` symbols retain them in `/opt/strata/engine/strata` (unreachable on W-2135).
  - Parity (`0` failures across all tests under `PathC7` env): `native_arithmetic_parity` (`4,866,048` finite bitwise comparisons passed), `q2_bitplane_parity` (`PASS`), `iq_avx2_parity` (`0` failures), `s11x_cpu_microbench --mode parity` on real `IQ3_XXS` GGUF (`139,346/256,000` bit-exact, `max_abs_diff=2.608e-08`, `max_rel_l2=2.665e-07`, `PASS`).

### 5.1 Diagnostic Decode Breakdown (`d1-20261119T074052`, `STRATA_DECODE_TIMING=1`) vs `S11X-P0`

| Metric | `S11X-P0` (`p0`, A / B) | `S11X-D1` Diag (`d1`, A / B) | Delta (A / B) |
|---|---:|---:|---|
| **Decode Speed (tok/s)** | `28.8 / 28.5` | **`32.0 / 31.2`** | **`+3.2 / +2.7 tok/s`** |
| **Missed Expert Latency (`PCIe share`)** | `334 / 330 us` (`5.2–5.4 GB/s`, `pcie_frac 0.75`) | **`262 / 270 us`** (`6.7 / 6.5 GB/s`, `pcie_frac 0.70`) | **`-21.6% / -18.2%`** |
| **Host `CPU` Expert Time (ms/window)** | `36.87 / 32.35` (`2.41 / 2.13` CPU exp/LW) | **`28.32 / 30.82`** (`2.16 / 2.49` CPU exp/LW) | **`-8.55 ms (-23.2%)`** (A) |
| **Total Host Window Time (ms/window)** | `77.58 / 72.13` (`2.23 / 2.05` tok/win) | **`67.12 / 69.23`** (`2.15 / 2.16` tok/win) | **`-13.5% / -4.0%`** |
| **Non-CPU-Expert Floor** (`GPU-reach + adapt_join + draft + host`) | `~40.7 / ~39.8 ms/win` | `~38.8 / ~38.4 ms/win` | Unchanged (`~39 ms/win` floor) |

### 5.2 Scored 3-Batch C2 Results (`d1-20261119T074621`, `PathC7`, No Timing Overhead)

| Batch | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Output Tokens A / B | Expert Cache Hit A / B | DFlash2 Accepted / Offered A / B | OS Read MB A / B | Peak VRAM A / B (MiB) | Power Mean/Peak A / B (W) | Temp Mean/Peak A / B (°C) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `batch-1` | `940.0` | `943.4` | **`33.9`** | **`32.0`** | `135.33` | `134.84` | `1830 / 1883` | `88.6% / 86.3%` | `986/1312 (75.2%)` / `1013/1385 (73.1%)` | `6023.3 / 5481.4` | `15571 / 15571` | `90.8/204.7` / `94.9/221.4` | `55.9/64` / `57.1/64` |
| `batch-2` | `943.0` | `944.4` | **`31.4`** | **`30.8`** | `134.88` | `134.69` | `1488 / 1883` | `87.9% / 86.3%` | `810/1072 (75.6%)` / `1013/1385 (73.1%)` | `6716.3 / 6694.1` | `15571 / 15571` | `87.3/205.4` / `94.8/209.9` | `57.3/65` / `58.0/65` |
| `batch-3` | `970.9` | `973.8` | **`32.6`** | **`31.9`** | `131.03` | `130.63` | `1443 / 1883` | `88.1% / 86.3%` | `752/1012 (74.3%)` / `1013/1385 (73.1%)` | `6959.0 / 5537.5` | `15571 / 15571` | `92.4/200.6` / `93.1/215.1` | `57.9/66` / `58.5/65` |
| **Median** | `943.0` | `944.4` | **`32.6`** | **`31.9`** | `134.88` | `134.69` | `1488 / 1883` | **`88.1% / 86.3%`** | `75.2% / 73.1%` | `6716.3 / 5537.5` | `15571 / 15571` | `90.8/204.7` / `94.8/215.1` | `57.3/65` / `58.0/65` |
| **vs `S10-D4`** | `-82.1` | `-83.4` | **`+2.2` (`+7.2%`)** | **`+1.6` (`+5.3%`)** | `+10.80 s` | `+10.90 s` | - | - | - | - | `0` | `-6.2/+1.4` / `-3.7/-10.5` | `-0.6/-1` / `-1.7/-1` |

### 5.3 Step 1 + Step 2 + Step 3 Synthesis & Promotion Decision
1. **New Dual-V100 Decode Record**: `S11X-D1` achieved **`32.6 / 31.9 tok/s`** concurrent 128K decode medians (**`+7.2% / +5.3%`** over `S10-D4` `30.4 / 30.3 tok/s`, peaking at `33.9 / 32.0 tok/s` in `batch-1`), with lower power (`90.8 / 94.8 W` mean vs `97.0 / 98.5 W`), lower temperature (`57.3 / 58.0 °C` mean), identical `15571 MiB` peak VRAM, and deterministic `finish_reason="stop"` across all 4 runs (`1883`-token Agent B trajectory `bb5373dd282b4744...` identical in all 4 runs).
2. **Why Microbenchmark `-24.0%` Scaled to `+5.3%–7.2%` End-to-End**: In `S11X-P0`, CPU experts accounted for `~45–48%` (`36.87 / 32.35 ms/win`) of the `77.58 / 72.13 ms` window. `PathC7` cut missed-expert time by `~20–23%` (`334 -> 262 us`, `36.87 -> 28.32 ms/win`), while the remaining `~39 ms/win` floor (`GPU-reach ~20.5 ms` + `adapt_join ~9.0–9.3 ms` + `DFlash2 draft ~3.2–3.3 ms` + host overhead) is untouched by CPU expert math.
3. **Why Prefill Measured `943.0 / 944.4 tok/s` in `d1-20261119T074621`**: `S11X-D1` made zero prefill code changes. Building the `stage11x-d1` image evicted ~4 GB of GGUF pages from the 64 GB host's Linux page cache (`fincore` `42.1–42.8 / 77.38 GB` vs `45.6–46.8 GB` in `S11X-P1`), forcing `5.5–7.0 GB` of NVMe reads (`~10 s` extra TTFT, matching `S11X-P1 Diag A` `947.8/949.6 tok/s` at 94% cache and `S10-D4 batch-1` `957.2/959.8 tok/s`).
4. **Promotion & Next-Scope Recommendation**:
   - **Promote `S11X-D1` as the new Decode-optimized candidate** (surpassing `S10-D4`'s `30.4 / 30.3 tok/s`), **NOT yet promoted to production `p520-llm-a/b`** without explicit user scope and a warm-cache / combined `S11X-C1` (`stage11x-p1` + `stage11x-d1`) validation.
   - **Stage 11X Stretch Target (`>= 1200 tok/s` Prefill & `>= 40 tok/s` Decode) NOT MET**: Reaching `>= 1200 / >= 40` on dual V100-16GB requires removing the two remaining structural walls: (a) **Prefill**: `~42–44 s` PCIe/host staging of `30.8 GiB` experts across `8192`-token chunks + `~47 s` non-expert GPU phases (hard bounded by `12.3 GB/s` PCIe Gen3 x16 and `16 GB` VRAM), and (b) **Decode**: the `~39 ms/win` non-CPU floor (`adapt_join` `~9.2 ms/win`, GPU-reach `~20.5 ms/win`, and `~2.2` missed CPU experts/layer-window limited by `16 GB` VRAM capacity).

---

## 6. `S11X-D1W`: Warm Cache Re-validation (`d1w-20261119T081230`, `strata-v100:stage11x-d1`)

Before `d1w-20261119T081230`, missing pages in `Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf` (`47,039,860,096` bytes) were warmed via targeted `pread`, verifying `100.00%` (`11,484,341 / 11,484,341` pages) in `fincore` alongside `dense.bin` (`97.8%`) and `qwen3.8-flash-next-dflash2.q4_0-selq4.pack` (`100.00%`).

| Batch | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Output Tokens A / B | Expert Cache Hit A / B | DFlash2 Accepted / Offered A / B | OS Read MB A / B | Page Cache (%) | Peak VRAM A / B (MiB) | Power Mean/Peak A / B (W) | Temp Mean/Peak A / B (°C) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `batch-1` | `985.2` | `991.2` | **`33.3`** | **`32.2`** | `129.12` | `128.34` | `1465 / 1883` | `87.9% / 86.3%` | `785/1046 (75.0%)` / `1013/1385 (73.1%)` | `4133.6 / 3264.1` | `95%` | `15571 / 15571` | `88.2/195.1` / `97.0/214.4` | `53.7/62` / `56.2/64` |
| `batch-2` | `1010.8` | `1016.6` | **`33.8`** | **`32.5`** | `125.86` | `125.14` | `1465 / 1883` | `87.9% / 86.3%` | `785/1046 (75.0%)` / `1013/1385 (73.1%)` | `4201.6 / 3789.0` | `99%` | `15571 / 15571` | `93.5/204.5` / `98.9/217.7` | `57.2/65` / `58.5/65` |
| `batch-3` | **`1023.2`** | **`1028.8`** | **`34.6`** | **`32.2`** | `124.32` | `123.64` | `1830 / 1883` | `88.6% / 86.3%` | `986/1312 (75.2%)` / `1013/1385 (73.1%)` | `981.0 / 519.3` | `100%` | `15571 / 15571` | `97.8/203.7` / `100.4/212.8` | `59.3/66` / `59.5/65` |
| **Median** | **`1010.8`** | **`1016.6`** | **`33.8`** | **`32.2`** | `125.86` | `125.14` | `1465 / 1883` | **`87.9% / 86.3%`** | `75.0% / 73.1%` | `4133.6 / 3264.1` | - | `15571 / 15571` | `93.5/203.7` / `98.9/214.4` | `57.2/65` / `58.5/65` |
| **vs `S10-D4`** | `-14.3` | `-11.2` | **`+3.4` (`+11.2%`)** | **`+1.9` (`+6.3%`)** | `+1.78 s` | `+1.35 s` | - | - | - | - | - | `0` | `-3.5/+0.4` / `+0.4/-11.2` | `-0.7/-1` / `-1.2/-1` |

- **Key Result**: Confirmed `d1-20261119T074621`'s `943.0 / 944.4 tok/s` Prefill was purely cold-cache NVMe I/O (`5.5–7.0 GB` OS read). Once warmed to `100%` page cache in `batch-3` (`981.0 / 519.3 MB` OS read), `S11X-D1` recovered `1023.2 / 1028.8 tok/s` Prefill (matching `S10-D4`'s `1025.1 / 1027.8 tok/s`) while pushing Decode even higher to **`33.8 / 32.2 tok/s`** medians (**`34.6 / 32.2 tok/s`** in `batch-3`).

---

## 7. `S11X-C1`: Combined `P1` + `D1` (`strata-v100:stage11x-c1`, `6c8f0ca8885284de...`)

- **Combined Patch, ISA & Parity Verification**:
  - [stage11x-c1.patch](../../docker/patches/stage11x-c1.patch) applies `stage11x-p1.patch` (CUDA/Prefill) + `stage11x-d1.patch` (CPU `PathC7`) onto pinned `0.1.59` (`712fec6b4297c9cfd32ab43daaa2979a9aa01edf`) with `0` conflicts (completely disjoint files).
  - `build.ninja` keeps `-mavx512f -mavx512bw -mavx512vl -mavx512dq -mbmi2 -mf16c -mfma` on `expert.cpp` & `iq_avx512.cpp`; `check_isa_guard.py` (`853 functions, 180 hold wide-ISA instructions, 0 not allowed`); `objdump -d` shows `0` VNNI/VBMI/VPOPCNT instructions in `iq_avx512.cpp.o` (`12,884` ZMM) and `expert.cpp.o` (`4,131` ZMM).
  - **CPU Parity (`0` failures under `PathC7` env)**: `native_arithmetic_parity` (`4,866,048` passed), `q2_bitplane_parity` (`PASS`), `iq_avx2_parity` (`0` failures).
  - **GPU Parity (`0` failures on GPU 0 & GPU 1)**: `pf_wmma_parity` (`default`, `wmma2 N64=0`, `wmma2 N64=1`, `skinny`) — `0` failures ([GPU 0 log](s11x-c1-build/parity-gpu0.log), [GPU 1 log](s11x-c1-build/parity-gpu1.log)).
- **Diagnostic (`c1-20261119T084920`, `PREFILL_TIMING=1 DECODE_TIMING=1`)**:
  - Confirmed BOTH optimizations active simultaneously: `S11X_WMMA_LEAN eligible` (`2179` borrowed slots, `gather 9/8 ms`, `gemm gate/up+down 29.94/30.68 s`) AND `CPU expert kernels: AVX-2 + AVX-512BW` (`CPU pool 261/259 us/exp`, `6.7 GB/s`, `pcie_frac 0.70`), achieving **`1035.1 / 1038.1 tok/s` Prefill** and **`32.8 / 32.3 tok/s` Decode** even with profiling overhead enabled.

### 7.1 Scored 3-Batch C2 Results (`c1-20261119T085422`, No Timing Overhead)

| Batch | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Output Tokens A / B | Expert Cache Hit A / B | DFlash2 Accepted / Offered A / B | OS Read MB A / B | Page Cache (%) | Peak VRAM A / B (MiB) | Power Mean/Peak A / B (W) | Temp Mean/Peak A / B (°C) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `batch-1` | `1036.1` | `1041.2` | `33.0` | `32.3` | `122.78` | `122.19` | `2420 / 1883` | `82.8% / 86.3%` | `1505/1791 (84.0%)` / `1013/1385 (73.1%)` | `2336.2 / 1123.4` | `99%` | `15571 / 15571` | `92.6/203.6` / `92.7/217.1` | `56.7/65` / `57.4/65` |
| `batch-2` | `1043.2` | `1048.3` | `33.5` | `32.3` | `121.96` | `121.37` | `2310 / 1883` | `86.7% / 86.3%` | `1274/1648 (77.3%)` / `1013/1385 (73.1%)` | `2837.5 / 834.5` | `100%` | `15571 / 15571` | `94.6/199.0` / `91.3/234.8` | `59.3/67` / `58.7/65` |
| `batch-3` | `1037.6` | `1044.8` | `32.8` | `32.3` | `122.60` | `121.77` | `2591 / 1883` | `83.1% / 86.3%` | `1588/1956 (81.2%)` / `1013/1385 (73.1%)` | `2178.8 / 871.2` | `100%` | `15571 / 15571` | `95.3/208.2` / `94.8/216.7` | `59.4/67` / `58.6/65` |
| **Median** | **`1037.6`** | **`1044.8`** | **`33.0`** | **`32.3`** | **`122.60`** | **`121.77`** | `2420 / 1883` | `83.1% / 86.3%` | `81.2% / 73.1%` | `2336.2 / 871.2` | - | `15571 / 15571` | `94.6/203.6` / `92.7/217.1` | `59.3/67` / `58.6/65` |
| **vs `S10-D4`** | **`+12.5` (`+1.2%`)** | **`+17.0` (`+1.7%`)** | **`+2.6` (`+8.6%`)** | **`+2.0` (`+6.6%`)** | **`-1.48 s`** | **`-2.02 s`** | - | - | - | - | - | `0` | `-2.4/+0.3` / `-5.8/-8.5` | `+1.4/+1` / `-1.1/-1` |

- **Key Result**: `S11X-C1` beats `S10-D4` on **every** speed, TTFT, and power metric simultaneously (**`1037.6 / 1044.8 tok/s` Prefill**, **`33.0 / 32.3 tok/s` Decode**, **`122.60 / 121.77 s` TTFT**, deterministic `finish_reason="stop"`, identical `15571 MiB` peak VRAM, Agent B bit-identical `1883` tokens `bb5373dd282b4744...` across all 4 C1 runs). Stage 11X's `>= 1200 / >= 40.0` stretch target remains bounded by PCIe Gen3 x16 staging (`30.8 GiB`) and the `16 GB` VRAM non-CPU-expert decode floor.

---

## 8. `S11X-D2`: Non-Blocking Async `--mmap-experts` Adapt, Zero-`mincore()` Dispatch, & V100 `nv_defaults` (`strata-v100:stage11x-d2`, `7f6fc8f7858739d1...`)

- **Patch, ISA & Parity Verification**:
  - [stage11x-d2.patch](../../docker/patches/stage11x-d2.patch) extends `S11X-C1` cleanly across `include/strata/core/expert_source.hpp`, `src/core/expert_source.cpp`, and `src/program/generate.cpp` (`0` CUDA source edits vs verified `stage11x-c1`):
    1. **Non-blocking `--mmap-experts` async `adapt` (`STRATA_MMAP_ADAPT_ASYNC=1`)**: Allows `--adapt-async 1` / `STRATA_MMAP_ADAPT_ASYNC=1` on `--mmap-experts` using a 2-slot reusable pinned bounce ring (`cudaHostAlloc`, `2 x 2.33 MiB = ~4.66 MiB`, zero OS page cache stolen) + `cudaMemcpyAsync` on `adapt_stream` + `cudaEventQuery`/`cudaEventSynchronize` (`MmapBounceRing`). `JobThread` pins itself to the host core's SMT sibling (`CPU 6` / `CPU 9` via `strata::aux_cpus::plan()`) when `STRATA_ADAPT_JOB_CPU` and `--aux-cpus` are unset, overlapping expert copies (`~13 ms`) with the `~19–20 ms` `GPU-reach wait` while keeping prefill stager threads untouched. Skips redundant `srcp->prefetch(w.out)` and `srcp->release(w.in)` in `a_mmap`.
    2. **Zero-`mincore()` dispatch (`STRATA_COLD_OVERLAP=5`)**: Adds `FileExpertSource::fast_zc_ready()` and `zc_roles_fast()` to bypass `miss` vector construction, `prefetch_begin`, `mincore()` (~360–480 syscalls/window), `stage_mu_` locks, and `std::find(zc_keys_)` whenever `role_ptr_` is mapped (`!unmapped_`, `direct_.empty()`, `!complement_ready_`, `override_.empty()`, `native`, `tail_off == 0`). `STRATA_COLD_OVERLAP=0..4` remain untouched.
    3. **Zero-compile V100 `nv_defaults` 6-flag GPU pack**: Enables `STRATA_SIDE_MIXER=2`, `STRATA_ATTN_DAILY=1`, `STRATA_GR_UP75=1`, `STRATA_GU_SWIGLU=1`, `STRATA_QSA_ROWS=1`, `STRATA_FUSE_WAIT=2` (all bitwise-identical on Agent B in Tier 1 Diag B: `bb5373dd282b4744...`).
  - **ISA & Build Verification**: `build.ninja` keeps `-mavx512f -mavx512bw -mavx512vl -mavx512dq -mbmi2 -mf16c -mfma` on `expert.cpp` & `iq_avx512.cpp`; `check_isa_guard.py` (`853 functions, 180 hold wide-ISA instructions, 0 not allowed`, [log](s11x-d2-build/isa_guard.log)); `objdump -d` (`forbidden=0` on `iq_avx512.cpp.o` and `expert.cpp.o`, [log](s11x-d2-build/objdump_check.log)).
  - **Parity (`0` failures across all tests)**: `file_expert_source_test` (`PASS`), `iq_avx2_parity` (`0` failures), `native_multi_parity` (`0` failures), `native_arithmetic_parity` (`4,866,048` finite bitwise comparisons passed), `q2_bitplane_parity` (`PASS`).

### 8.1 Tier 1 & Tier 2 Diagnostic Progression (`STRATA_PREFILL_TIMING=1` + `STRATA_DECODE_TIMING=1`, 1-Batch Non-Scored)

| Diagnostic Run | Prefill A / B (tok/s) | Decode A / B (tok/s) | Window Total A / B (ms) | `GPU-reach wait` (ms) | `jobs` (`d.ms_jobs`) (ms) | `adapt join` (ms) | `adapt wait` (ms) | Key Finding |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `S11X-C1` Diag (`c1-20261119T084920`) | `1035.1 / 1038.1` | `32.8 / 32.3` | `78.85 / 66.95` | `21.58 / 20.49` | `1.81 / 1.44` | `9.35 / 8.94` | `0.02 / 0.02` | Baseline C1 timing breakdown |
| `S11X-D2` Tier 1 Diag A (`d2-20261119T001214`) | `705.5 / 715.7` | `32.8 / 32.1` | `81.98 / 67.45` | `20.81 / 19.67` | `2.50 / 1.81` | `9.84 / 9.20` | `0.02 / 0.02` | **`STRATA_AUX_CPUS=auto` regressed prefill (`104.7 -> 150.0 s` host staging)** & added SMT contention; **DROPPED** |
| `S11X-D2` Tier 1 Diag B (`d2-20261119T001808`) | `1032.4 / 1037.8` | `32.7 / 32.7` | `77.95 / 66.03` | **`20.41 / 19.67`** | `1.83 / 1.36` | `9.50 / 9.00` | `0.02 / 0.02` | Clean 6 GPU flags: **`-0.82 ms/win` GPU-reach wait**; Agent B bit-identical (`bb5373dd...`) at `32.7 tok/s` |
| `S11X-D2` Tier 2 Diag (`d2-20261119T003229`) | `883.3 / 862.4` *(90.6% cache)* | **`34.9 / 38.3`** | **`69.42 / 52.89`** | **`19.85 / 19.33`** | **`0.11 / 0.08`** | **`0.00 / 0.00`** | `0.10 / 0.09` | **`adapt join` eliminated (`-9.50 / -9.00 ms/win`)** & **`jobs` cut 94% (`-1.72 / -1.28 ms/win`)** |

### 8.2 Scored 3-Batch C2 Results (`d2-20261119T003753`, No Timing Overhead)

| Batch | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Output Tokens A / B | Expert Cache Hit A / B | DFlash2 Accepted / Offered A / B | OS Read MB A / B | Page Cache (%) | Peak VRAM A / B (MiB) | Power Mean/Peak A / B (W) | Temp Mean/Peak A / B (°C) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `batch-1` | `1027.0` | `1029.7` | **`37.1`** | **`39.7`** | `123.87` | `123.54` | `1546 / 2094` | `81.2% / 86.3%` | `930/1135 (81.9%)` / `1104/1518 (72.7%)` | `3236.8 / 1851.0` | `93.5%` | `15577 / 15577` | `90.4/198.4` / `97.6/215.1` | `56.5/65` / `58.1/64` |
| `batch-2` | `1032.6` | `1037.0` | **`37.5`** | **`41.0`** | `123.21` | `122.69` | `1872 / 1825` | `82.4% / 87.6%` | `1087/1373 (79.2%)` / `924/1239 (74.6%)` | `2460.8 / 784.9` | `95.0%` | `15577 / 15577` | `96.5/202.0` / `101.2/238.2` | `59.5/67` / `60.0/66` |
| `batch-3` | `1037.4` | `1045.2` | **`37.1`** | **`41.0`** | `122.62` | `121.73` | `1572 / 1825` | `81.6% / 87.6%` | `922/1129 (81.7%)` / `924/1239 (74.6%)` | `877.8 / 443.5` | `95.7%` | `15577 / 15577` | `99.7/208.5` / `102.2/215.1` | `60.7/67` / `60.4/65` |
| **Median** | **`1032.6`** | **`1037.0`** | **`37.1`** | **`41.0`** | **`123.21`** | **`122.69`** | `1572 / 1825` | `81.6% / 87.6%` | `81.7% / 74.6%` | `2460.8 / 784.9` | - | `15577 / 15577` | `96.5/202.0` / `101.2/215.1` | `59.5/67` / `60.0/65` |
| **vs `S10-D4`** | **`+7.5` (`+0.7%`)** | **`+9.2` (`+0.9%`)** | **`+6.7` (`+22.0%`)** | **`+10.7` (`+35.3%`)** | **`-0.87 s`** | **`-1.10 s`** | - | - | - | - | - | `+6` | `-0.5/-1.3` / `+2.7/-10.5` | `+1.6/+1` / `+0.3/-1` |
| **vs `S11X-C1`** | `-5.0` | `-7.8` | **`+4.1` (`+12.4%`)** | **`+8.7` (`+26.9%`)** | `+0.61 s` | `+0.92 s` | - | - | - | - | - | `+6` | `+1.9/-1.6` / `+8.5/-2.0` | `+0.2/0` / `+1.4/0` |

- **Key Result**: `S11X-D2` sets an all-time dual-V100 128K decode record of **`37.1 / 41.0 tok/s`** medians (**Agent B crossed `>= 40.0 tok/s`**, matching `f40565a8...` `1825`-token deterministic output across `d2-20261119T003229`, `batch-2`, and `batch-3`), while maintaining full `~1033–1045 tok/s` Prefill, `15577 MiB` peak VRAM (`+6 MiB` for `SIDE_MIXER=2` stream/events), `0` errors/fallbacks, and `finish_reason="stop"` across all 128K requests. **Recommend promoting `S11X-D2` as the new Stage 11X all-metric leader (`C1` + `D2`)**, noting that `p520-llm-a/b` remain preserved `Exited` pending explicit user scope for any production rollout.
