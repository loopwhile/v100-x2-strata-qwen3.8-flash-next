# Stage 11X — Source Audit Report (`S11X-A0`)

> **Date:** 2026-11-19
> **Campaign:** Stage 11 Follow-up Optimization (`S11X-*` namespace)
> **Scope:** Read-only code and asset audit comparing pinned upstream `0.1.59` (`712fec6b4297c9cfd32ab43daaa2979a9aa01edf`), latest upstream `v0.2.15` (`c77572806996`, engine `0.1.60` `09b603886925`), and latest V100 fork (`8b4c09bd` `0.1.45.7` → `776e1755` `0.1.45.10`) against the live `IQ3_XXS` dual-V100 (`sm_70`) hardware and expert layout on P520.
> **Target Reference:** `S10-D4` (`IQ3_XXS` + stock `DFlash2` selector pack, `--spec 8 --draft-conf 0.7 --prefill auto`, Prefill `1025.1 / 1027.8 tok/s`, Decode `30.4 / 30.3 tok/s`, TTFT `124.08 / 123.79 s`).

---

## 1. 48-Layer `IQ3_XXS` Native Expert Quantization Map

Inspection of `/srv/models/strata-iq3xxs/pack/iq3_xxs-native/native_experts.txt` (`n_expert 512`, `42,912,972,800` bytes across 48 MoE layers) establishes the exact per-layer tensor types (`gu_type` for Gate/Up projections, `d_type` for Down projection) that any CPU or CUDA kernel optimization must target on `IQ3_XXS`:

### 1.1 Gate/Up Projection (`gu_type`) Distribution (48 Layers)

| `ggml_type` ID | Quantization Name | Layer Count | Share | Layers |
|---:|---|---:|---:|---|
| `16` | `IQ2_XXS` | **9** | 18.75% | `1, 3, 6, 7, 11, 13, 16, 27, 31` |
| `17` | `IQ2_XS` | **10** | 20.83% | `0, 2, 4, 5, 9, 10, 14, 19, 25, 39` |
| `18` | `IQ3_XXS` | **6** | 12.50% | `35, 36, 41, 44, 45, 47` |
| `21` | `IQ3_S` | **13** | 27.08% | `8, 18, 20, 22, 23, 24, 28, 30, 32, 33, 34, 37, 43` |
| `22` | `IQ2_S` | **10** | 20.83% | `12, 15, 17, 21, 26, 29, 38, 40, 42, 46` |

### 1.2 Down Projection (`d_type`) Distribution (48 Layers)

| `ggml_type` ID | Quantization Name | Layer Count | Share | Layers |
|---:|---|---:|---:|---|
| `20` | `IQ4_NL` | **18** | 37.50% | `0, 2, 4, 28, 29, 30, 31, 32, 34, 35, 37, 38, 39, 42, 43, 44, 46, 47` |
| `42` | `Q2_0` | **30** | 62.50% | `1, 3, 5..27, 33, 36, 40, 41, 45` |

### 1.3 Audit Implications of the Layer Map
- **`IQ3_XXS` is a heterogeneous GSQ-RCO mix**, not pure `ty == 18`. In fact, `ty == 18` (`IQ3_XXS`) is only 6 of 48 Gate/Up layers (12.5%), while `ty == 21` (`IQ3_S`, 13 layers), `ty == 17` (`IQ2_XS`, 10 layers), `ty == 22` (`IQ2_S`, 10 layers), and `ty == 16` (`IQ2_XXS`, 9 layers) account for the other 87.5%.
- Any Volta WMMA2 or CPU GEMV optimization that only covers a single type (or only `ty == 22` and `ty == 20` as in upstream `0.1.59`) misses the majority of `IQ3_XXS` Gate/Up layers.

---

## 2. Built-in Instrumentation in Pinned Upstream `0.1.59` (`712fec6b4297c9cfd32ab43daaa2979a9aa01edf`)

Review of the `0.1.59` engine source confirms three built-in profiling hooks that require zero binary modification:

1. **`STRATA_PREFILL_TIMING=1`** (`src/prefill/prefill.cpp:3113`):
   - Instruments all **27 GPU event phases** across the 128K prefill chunks (`norm1`, `qsa_proj`, `qsa_attn`, `qsa_out`, `gdn_proj`, `gdn_ recurrence`, `gdn_out`, `norm2`, `route`, `expert_gather`, `expert_gu`, `expert_swiglu`, `expert_down`, `expert_scatter`, `shared_expert`, `hc_region`, etc.) plus total chunk kernel time vs wall time.
   - **Note:** `STRATA_PREFILL_TIMING=1` was **omitted** in `S10-P0` (which only enabled `STRATA_DECODE_TIMING=1` and `STRATA_VERIFY_PROFILE=1` at `--spec 6`). Running `S11X-P0` at `--spec 8` with all three variables provides the first complete 27-phase Prefill and `spec 8` Decode breakdown on `S10-D4`.
2. **`STRATA_DECODE_TIMING=1`** (`src/generate.cpp`):
   - Emits `[strata decode timing]` per-window host wall breakdown (`total`, `cpuExp`, `adapt` join wait, `draft` DFlash2 proposal, `gpuSub`, `samp`, `tok/win`, `offered`, `accepted`) and `[strata decode GPU stages]` CUDA event breakdown (`attn`, `route`, `waitCPU`, `shared`, `merge`, `total`).
3. **`STRATA_VERIFY_PROFILE=1`** (`src/prefill/prefill.cpp`):
   - Profiles tree/speculative verification step latency during decode windows.

---

## 3. Upstream Differential: `0.1.59` (`712fec6b4`) → `0.1.60` / `v0.2.15` (`09b603886925` / `c77572806996`)

In `v0.2.15` (`c77572806996`, control `0.1.61`), the engine package remains `0.1.60` (`09b603886925`). Comparing `712fec6b4..09b603886925` for `IQ3_XXS` + single-card Volta (`sm_70`):

| Commit | Area | Finding & Impact on P520 Dual-V100 (`IQ3_XXS`) | Verdict |
|---|---|---|---|
| `c7c78ed4` | Prefill Auto Chunking | **CRITICAL SAFETY CATCH:** Upstream `0.1.60` raised bare `--prefill auto` on single Volta (`sm_70`) cards from `8192` to `32768` tokens. On our dual-V100 host, `S10-P3` (`--prefill auto:16384`) triggered an immediate hardware PSU power trip during concurrent 16K tensor bursts. **Any future test of engine `0.1.60` MUST explicitly pin `--prefill auto:8192` and NEVER use bare `--prefill auto`.** (Pinned `0.1.59` resolves `--prefill auto` to `8192`). | **Safety Guard Required for 0.1.60** |
| `2fe91fdd` & `6213c083` | CPU Expert ISA (`Isa::Avx512`) | Upstream added AVX-512 dot-product kernels gated by runtime `Isa::Avx512`, which requires **`avx512vnni`** (`cpuid` leaf 7, ECX bit 11). Live P520 `lscpu` verification confirms Xeon W-2135 (Skylake-W) supports `avx512f`, `avx512dq`, `avx512cd`, `avx512bw`, `avx512vl` **only** — it **lacks `avx512vnni`**. Therefore, `0.1.60` falls back to `Isa::Avx2` on W-2135, yielding zero CPU expert speedup as-is. A custom AVX-512F/BW (`_mm512_maddubs_epi16` + `_mm512_madd_epi16`) kernel without VNNI would be required to exploit W-2135's 512-bit SIMD units. | **No effect on W-2135 without custom non-VNNI AVX-512F/BW port** |
| `29147556` & `9e52144f` | Thread / Cgroup Affinity | Confines background expert copy/adaptation threads to the container's active `cpuset` (`0-2,6-8` for A, `3-5,9-11` for B) and traverses cgroup v1/v2 CPU quotas accurately. Prevents stray cross-agent thread migration or over-spawning under Docker `--cpuset-cpus`. | **Valid low-risk hygiene candidate** |
| `f0356cb2` | KV Host DMA (`STRATA_KV_HOST_DMA=1`) | Enables asynchronous CUDA host-to-device DMA for streamed KV (`--kv-resident 32768` at 128K context). Since our KV VRAM hit rate in C2 is already `97.7–98.9%` (`kv-resolve` `~0.43 ms/window`), expected decode impact is minor (`<0.5%`), though prefill KV streaming eviction may see slight smoothing. | **Low expected impact** |

---

## 4. V100 Fork Differential: `8b4c09bd` (`0.1.45.7`) → `776e1755` (`0.1.45.10`) vs Upstream `0.1.59`

Comparing the latest V100 fork (`v0.1.45.10`, `776e1755`) against upstream `0.1.59` (`712fec6b4`) reveals significant differences in Volta Prefill (`w2` / `WMMA2`) and resident routing:

### 4.1 Volta Prefill `WMMA2` (`w2`) Type Coverage & Kernel Optimizations
- **Upstream `0.1.59` limitation:**
  - In `0.1.59`, the second-tile Volta WMMA prefill path (`STRATA_PF_WMMA2=1`, `w2`) is **unset by default** (so `S10-D4` ran with `STRATA_PF_WMMA=1` only).
  - Furthermore, upstream `0.1.59`'s `w2` dispatcher only supports **`ty == 22` (`IQ2_S`)** for Gate/Up (10/48 layers) and **`ty == 20` (`IQ4_NL`)** for Down (18/48 layers), leaving 38/48 Gate/Up layers and 30/48 Down layers on the baseline path.
- **V100 Fork `0.1.45.10` advances:**
  - Expands `w2` (`STRATA_PF_WMMA2=1`) dispatch to cover **`ty == 18` (`IQ3_XXS`), `ty == 21` (`IQ3_S`), `ty == 22` (`IQ2_S`)** for Gate/Up (**29/48 layers = 60.4%** of Gate/Up layers on `IQ3_XXS`) plus **`ty == 20` (`IQ4_NL`)** for Down (**18/48 layers = 37.5%**).
  - **`0cdb0d64`**: Packs Volta prompt expert dequantization into `__half2` SIMD operations, cutting scalar half conversion overhead during prefill expert GEMM.
  - **`4d0f35fd`, `fa984808`, `25d7c1f6`, `19175f8c`**: Adds opt-in register-fed Volta `IQ4_NL` prompt down kernel (`w2_iq4_skinny`), aligned 8-warp block loads, and compact nibble lookup for paired Volta `IQ4_NL` loads (applicable to the 18 `d_type == 20` layers in `IQ3_XXS`).
  - **`WMMA_LEAN` buffer aliasing** (proven safe in `S7-XXS-16`): Aliases intermediate WMMA scratch buffers to save VRAM and reduce memory traffic during 8192-token prefill chunks.
  - *(Note: Fork commits `505a6647`, `f6bc3f41`, `c082f106` in `0.1.45.10` target NVFP4 QAD, which does not apply to `IQ3_XXS`.)*

### 4.2 Decode & Routing Path (`route_resident_k`, `STRATA_TOPK_COMPACT`)
- **`2bdb0049` / `213f3654`** (`0.1.45.9`): Optimizes `route_resident_k` on CUDA to skip unused routing diagnostics and redundant global memory writes when selecting top-K resident/CPU experts per token in the 9-token (`spec 8`) verification window.
- **`53a36c9b`**: `STRATA_TOPK_COMPACT=1` compacts top-K expert indices before CPU/GPU split dispatch.

---

## 5. Gate A → Gate B/C Actionable Conclusions

1. **Execute `S11X-P0` (Gate A diagnostic):** Run pinned `0.1.59` with `S10-D4` config (`--spec 8 --draft-conf 0.7 --prefill auto`) and `STRATA_PREFILL_TIMING=1 STRATA_DECODE_TIMING=1 STRATA_VERIFY_PROFILE=1` (1 non-scored diagnostic C2 batch) to capture exact 27-phase Prefill and `spec 8` Decode timings.
2. **Execute `S11X-C0` (Gate B low-cost candidate):** Test `S10-D4` (`--spec 8`) + `STRATA_PF_HC_REGION=1` across 3 scored concurrent 128K C2 batches to determine whether `S10-P1`'s prefill gain (`+11~16 tok/s` at `spec 6`) holds at `spec 8` without degrading the `30.4 / 30.3 tok/s` decode baseline.
3. **Subsequent Gate C Engineering Targets (informed by `S11X-A0` + `S11X-P0`):**
   - **Prefill (`S11X-P1`):** Port/enable the fork's expanded `w2` (`ty == 18, 21, 22, 20`) + `__half2` packed dequant (`0cdb0d64`) + `IQ4_NL` skinny down kernel (`19175f8c`) onto the `0.1.59` DFlash2 engine while keeping `--prefill auto` at `8192`.
   - **Decode (`S11X-D1` / `S11X-D2`):** Address the dominant per-window `cpuExp` (`waitCPU`) and `adapt` latency on Xeon W-2135 (via non-VNNI AVX-512BW/F GEMV for `ty == 16, 17, 18, 21, 22, 20, 42`, CPU/GPU thread scheduling overlap, and `2bdb0049` resident routing cleanup).
