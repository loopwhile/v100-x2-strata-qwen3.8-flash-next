# Stage 12 — Source & ISA Audit Report (`S12-A0` + `S12-A2` Placeholder)

> **Date:** 2026-11-25  
> **Campaign:** Stage 12 Dual-V100 (`sm_70`) + Xeon W-2135 `IQ3_XXS` Optimization  
> **Status:** Part 1 (`S12-A0`) & Part 2 (`S12-A2`) Complete (Read-Only Source Audit)  
> **Clones Checked Out Under:** `/tmp/stage12-src-audit` (preserved intact for `S12-A2` & build prep)

---

## Part 1 — Read-Only Source & ISA Audit (`S12-A0`)

### 1. Verified Git Refs & Exact SHAs

| Label | Repository | Tag / Ref | Verified Commit SHA | Engine Version (`CMakeLists.txt`) |
|---|---|---|---|---|
| `upstream-0.1.59` | `Niko1221/Strata` | `712fec6b` (`v0.2.13`) | `712fec6b4297c9cfd32ab43daaa2979a9aa01edf` | `0.1.59` |
| `upstream-0.1.66` | `Niko1221/Strata` | `v0.2.20` | `a34979fc94f3d126b9bb8210f4ad311345688b52` | `0.1.66` (`engine/CMakeLists.txt:13`) |
| `upstream-0.1.67` | `Niko1221/Strata` | `v0.2.21` | `d46f5f268f8ed797e83a5c63a69bffbd7a581cf6` | `0.1.67` (`engine/CMakeLists.txt:13`) |
| `fork-v100` | `jmnargi/Strata-V100` | `HEAD` (`v0.1.45.13`) | `49c6cc6fd11291c128a7a62287b50e79d59e247b` | `0.1.45.13` (vs `776e1755` `v0.1.45.10`) |

All repositories carry the MIT License (`upstream-0.1.67/LICENSE`, `fork-v100/LICENSE`).

---

### 2. Directory Layout, Build System & Test Mapping (`0.1.66` / `0.1.67`)

#### 2.1 Structural Reorganization vs `0.1.59`
Since `v0.2.16` (engine `0.1.62`), the C++ / CUDA engine moved from the repository root into `engine/` (`engine/CMakeLists.txt`), while the Python installer/launcher moved into `terminal/` (`terminal/setup.py`, invoked by top-level `setup.sh`):
- Top-level (`upstream-0.1.67/`): `app/`, `docs/`, `engine/`, `terminal/`, `tools/`, `setup.sh`.
- Engine (`upstream-0.1.67/engine/`): `CMakeLists.txt`, `CMakePresets.json`, `cmake/` (`strata_geometry.cmake`, `strata_ggml.cmake`, `strata_gpu_engine.cmake`, `backends/{cpu,cuda,hip,metal,quant,sycl}.cmake`), `include/`, `src/`, `tests/`, `bench/`, `third_party/`.
- No `.gitmodules` file exists; `ggml` is vendored in `engine/third_party/strata-ggml` (`engine/cmake/strata_ggml.cmake:15`).
- `terminal/setup.py` is the user-facing installer/launcher (formerly root `setup.py` in `0.1.59`); engine CMake builds invoke `cmake -S engine -B <build_dir>`.

#### 2.2 CUDA / `sm_70` CMake Switches & Build Behavior
- **Required Volta switches (`engine/cmake/backends/cuda.cmake:20-80`):**
  - `-DSTRATA_ENABLE_CUDA=ON`
  - `-DSTRATA_EXPERIMENTAL_SM60=ON` (mandatory: `cuda.cmake:53-57` raises `FATAL_ERROR` if any arch in `CMAKE_CUDA_ARCHITECTURES` is `< 75` without `STRATA_EXPERIMENTAL_SM60=ON`; also defines `STRATA_EXPERIMENTAL_SM60=1` at `cuda.cmake:79`, enabling Volta `m8n8k4` prompt attention in `qsa_prompt_attn.cu:2501`).
  - `-DCMAKE_CUDA_ARCHITECTURES=70` (default if unset is `120` at `cuda.cmake:21`; CUDA 12.x required because CUDA 13 dropped `sm_70` per `cuda.cmake:51-52`).
- **MMQ removed / Own Prompt Kernels (`cuda.cmake:94,135-154`, `src/prefill/prefill.cpp:223-225`):**
  - `strata_pf_own` (`moe_fused.cu`, `moe_fused_iq.cu`, `moe_helpers.cu`, `moe_fused_iq_q36.cu`, `mmq_absent.cpp`) is built without llama.cpp's MMQ, defining `STRATA_PREFILL_FUSED=1` and `STRATA_PF_OWN_ONLY=1` (`prefill.cpp:225`).
  - Blackwell `strata_pf_fp4` (`cuda.cmake:101-131`) builds `*_absent.cpp` stubs when CUDA `< 13.0` or arch is `70`.
- **Window Width (`engine/CMakeLists.txt:121-137`):**
  - `STRATA_WINDOW_MAX_T` defaults to `"auto"`, which resolves to `8` (`STRATA_VERIFY_MAX_T=8`) for CUDA (`CMakeLists.txt:131`).
- **Own CPU Quant Layer (`engine/CMakeLists.txt:184,729-736`, `cmake/backends/quant.cmake`):**
  - `STRATA_OWN_CPU_QUANT=ON` by default (`CMakeLists.txt:184`): CPU expert pool uses `src/quant` (`strata_quant`) rather than `ggml-cpu`.
  - When `STRATA_BUILD_TESTS=ON` (default `ON` on x86_64 when `tests/core` and `bench/micro` exist, `CMakeLists.txt:159-162`), `strata_ggml_configure_root()` configures vendored `third_party/strata-ggml` (`ggml-base`, `ggml-cpu`) with `GGML_NATIVE=ON` (`strata_ggml.cmake:57`) as test oracle. When `STRATA_BUILD_TESTS=OFF`, no `ggml` is compiled (`CMakeLists.txt:732-733`).
- **Main Qwen binary target:** `strata` (`engine/cmake/strata_gpu_engine.cmake:548`, source `src/program/generate.cpp`).

#### 2.3 Gate A Parity & Safety Test Targets (`0.1.67`)
Legacy Stage 7–11X targets map cleanly in `0.1.67` (`CMakeLists.txt`, `cpu.cmake`, `cuda.cmake`, `quant.cmake`, `strata_gpu_engine.cmake`):
- **CPU / Quant Parity & ISA Safety:**
  - `native_arithmetic_parity` (+ `_avx`, `_mt1`, `_no512`, `_ggml` variants; `cpu.cmake:398-411`)
  - `pool_determinism` & `pool_determinism_dep_off` (`cpu.cmake:413-419`)
  - `iq_avx2_parity`, `iq_avx1_parity`, `q8k_quant_parity`, `q2_bitplane_parity` (`cpu.cmake:440-482, 514-517`)
  - `quant_selftest`, `quant_parity`, `type_geometry_oracle`, `sk_tier_test` (`quant.cmake:109-135`)
  - `isa_guard_check` (`tools/check_isa_guard.py` on `strata_kernels_cpu`, `cpu.cmake:618-621`)
  - `tail_skip_default_test`, `lookup_default_test`, `cgroup_mem_test`, `cgroup_cpu_test`, `adapt_async_default_test`, `nv_defaults_test` (`cpu.cmake:49-68, 137-150, 570`)
- **GPU / Prefill / Policy Parity & Safety:**
  - `native_expert_parity` (e.g. `native_expert_parity_v31_iq{1_m,2_xxs,2_xs,2_s,3_xxs,4_xs}_{q2_0,iq4_nl,q5_0,q8_0}`, `CMakeLists.txt:831-835`)
  - `native_multi_parity`, `native_grouped_parity`, `native_i8_parity`, `pf_wmma_parity` (`strata_gpu_engine.cmake:954-981, 1136`)
  - `gr_write_norm_parity` (new in `0.1.67` for `#6776`, `strata_gpu_engine.cmake:935`), `qsa_prompt_attn_parity`, `fused_gr_bench` (`strata_gpu_engine.cmake:140, 1005`)
  - `prefill_expert_paths_bench` (`cuda.cmake:198-200`; note `prefill_decode_golden` is skipped when arch `< 75` per `cuda.cmake:174-175`, and `prefill_fused_*` tests skip with code 77 below `sm_80`)
  - `file_expert_source_test` (`strata_gpu_engine.cmake:343`), `no_mmq_symbols` (`cuda.cmake:165-167`), `strata_cuda_spill_guard` (`cuda.cmake:292-313`, `CMakeLists.txt:909`)

---

### 3. `0.1.66 -> 0.1.67` Full Diff (`v0.2.20` -> `v0.2.21`)

Directory diff across the full tree shows 411 changed/added files, concentrated heavily in `docs/`, `app/`, `terminal/`, `engine/src/inkling2/`, `engine/src/hy4flash/`, and `engine/tests/`. Isolating changes affecting the Qwen `strata` engine on `sm_70` / x86_64:

| Commit (`v0.2.20..v0.2.21`) | Files Changed | Impact on Qwen `strata` / Dual-V100 `sm_70` |
|---|---|---|
| `ed5bff88` (`#6776`) | `engine/src/prefill/kernels.cu:193-229`, `engine/cmake/strata_gpu_engine.cmake:692,935`, `tests/hip/prefill_gr_write_norm_parity.cpp` | **CRITICAL ACCURACY FIX:** `gr_write_norm_rs` vector path (`float4` added in `0.1.66`) summed `x*x` in 4-contiguous-element order, flipping last bit of `rs` on ~20% of rows and changing 10/300 JamC-QA answers. `0.1.67` stages `xs[N]` in shared memory and sums `d = t + 256*k` to match `gr_norm_rs_kernel` bit-for-bit. |
| `e6c2d002` (`#6747`) | `engine/src/program/generate.cpp:5061-5075`, `engine/include/strata/core/nv_defaults.hpp:56-70`, `engine/src/core/nv_defaults.cpp:226-239`, `docs/NVIDIA_V100.md:59` | **CRITICAL V100 CRASH FIX:** `0.1.66`'s `sm_70` table sets `STRATA_GDN_SPLIT=1` (`nv_defaults.cpp:151`), which only handles `<= kVerifyMaxT` (8) rows, while 8-row CUDA builds default `--lookup-max-t` to `12` — causing `0.1.66` to crash with `gdn_step_norm_multi: invalid arguments` on the first 12-token lookup window. `0.1.67` automatically drops the table's `STRATA_GDN_SPLIT=1` when `lookup_max_t > verify_max_t`. |
| `f5da7896` (`#6713`) | `engine/src/kernels/cuda/fused_gr.cu:2200,3407-3850` | Introduces `q8_smem_ld16` (plain load instead of `__ldg`) for `__shared__` staged rows in `gr_{down,up}_q8_{bf16tc,tc}` (`sm_80+` only; prevents illegal address-space trap on Ampere+ Q8_0 HC projections; does not touch `sm_70` path). |
| `66f2ee2b` (`#6552`) | `engine/include/strata/quant/dot_x4_policy.hpp`, `engine/src/kernels/cpu/native_expert.cpp:736,861`, `engine/CMakeLists.txt:503` | Makes `strata::quant` 4-row shared-activation `dot_x4` kernels opt-in (`STRATA_DOT_X4=1`) because DRAM-bound experts were slower than 1-row dots. |
| `724bbbed` (`#6782/#6799`) | `engine/include/strata/core/low_vram_rules.hpp`, `engine/src/program/generate.cpp:14965,14979` | Makes Track 6A tiny-cache swap dampening & profile pinning (`<15%` residency) opt-in via `STRATA_TINY_CACHE=1`. (Our V100 `IQ3_XXS` cache is ~25% resident, in mid-coverage `15%-65%`.) |
| `af9bf52f` / `ddac45d0` (`#6791`) | `engine/include/strata/core/adapt_coverage_rules.hpp`, `engine/src/program/generate.cpp:12153,14954` | `#4870` mid-coverage curve (`15%..65%`: `every 2, swaps 192, decay 0.92`) remains **ON by default for CUDA** (`adapt_mid_default_on()`), OFF for HIP; `STRATA_ADAPT_MID=1/0` overrides. |
| `878ee1a3` (`#6687`) | `engine/include/strata/core/gfx12_chunk.hpp:24-45`, `engine/src/program/generate.cpp:11273-11287` | `#2090` prompt-chunk RAM guard counts 50% of `extra_mib` and 3072 MiB reserve (instead of 6144 MiB) when `--resident-experts` is off. |
| `cd6600bb` (`#6754`) | `engine/src/kernels/cpu/pool_determinism.cpp` | Test fix: two NaNs compare equal; Q4_K gate/up check on AVX2-only CPUs. |
| `d528772f` / `a82cb7c0` / `f8712105` / `dca06a36` | `inkling2/*`, `conversation_spill`, `watchdog_limits` | Inkling2-only (DSpark/BF16-MTP), SSD conversation spill drop, watchdog UB parse fix (`#6861`). |

*(Note: `ink_*`, `hy4_*`, `faceebb5`, `751d5564`, `0c655e75`, `f42a9aa7` affect `strata-inkling` / `strata-hy4`, not the Qwen `strata` binary.)*

---

### 4. Prefill Chunk Safety (`--prefill auto` vs `--prefill auto:8192`)

- **CLI Parsing (`src/program/generate.cpp:4000-4032`):**
  - `--prefill auto`: sets `o.prefill_auto = true`, `o.prefill_auto_bare = true` (when `STRATA_PREFILL_AUTO_MAX` is unset), `o.prefill_auto_max = 8192`, `o.prefill_chunk = 8192`.
  - `--prefill auto:8192`: sets `o.prefill_auto = true`, `o.prefill_auto_bare = false`, `want_max = 8192`, `o.prefill_auto_max = 8192`, `o.prefill_chunk = 8192` (`generate.cpp:4005-4017`).
- **Single-V100 (`sm_70`) Bare `auto` Behavior (`src/program/generate.cpp:4495-4535`, `include/strata/core/nv_chunk.hpp:23-44`):**
  - `nv_chunk_card_ok(7, 0)` returns `true` (`nv_chunk.hpp:43`), which in `0.1.60` raised bare `auto` to `32768` on `sm_70`.
  - In **`0.1.66` and `0.1.67`**, `#5199` (`nv_chunk_ceiling_for_vram`, `nv_chunk.hpp:35-39`) checks `min_vram_bytes <= (16ull << 30) + (512ull << 20)` (`16.5 GiB`). On a 16 GiB V100 (`totalGlobalMem` ~15.77 GiB) with `STRATA_NV_CHUNK` unset, it returns `0`, keeping bare `--prefill auto` at `8192` and emitting:
    `strata generate: NVIDIA (15.8 GiB): --prefill auto stays at 8192 so prompt loans do not cannibalize hot expert slots (#5199; STRATA_NV_CHUNK=16 or 1 raises it)` (`generate.cpp:4529-4531`).
- **Safety Verdict:** Even though `#5199` caps 16 GiB V100 bare `auto` at `8192`, **`--prefill auto:8192` MUST still be passed explicitly** (setting `prefill_auto_bare = false` so `generate.cpp:4495` is completely bypassed and `auto_ceiling` at `generate.cpp:11248` is locked at `8192`), preventing any env (`STRATA_NV_CHUNK` / `STRATA_PREFILL_AUTO_MAX`) or threshold surprise from causing a `16384`+ PSU power trip.

---

### 5. GPU MoE, `EXP_MODE=8`, `dense_i8_tc`, Volta Prefill & 48-Layer `IQ3_XXS` Coverage

Our P520 `IQ3_XXS` native map (`docs/STAGE11X_SOURCE_AUDIT.md:14-29`) has 48 MoE layers:
- **Gate/Up (`gu_type`):** `16` (`IQ2_XXS`, 9L), `17` (`IQ2_XS`, 10L), `18` (`IQ3_XXS`, 6L), `21` (`IQ3_S`, 13L), `22` (`IQ2_S`, 10L).
- **Down (`d_type`):** `20` (`IQ4_NL`, 18L), `42` (`Q2_0`, 30L).

Verified `sm_70` dispatch in `0.1.66` and `0.1.67`:

1. **`sm_70` Default Table (`src/core/nv_defaults.cpp:136-163`):**
   Applies 21 switches by default on single-GPU / uniform `sm_70`:
   `STRATA_ADAPT_OVERLAP=1`, `STRATA_SM70_TABLE=1`, `STRATA_B6_MMVQ_ROWS=1`, `STRATA_TSUM=1`, `STRATA_SMALL_UNR=3`, `STRATA_GR_NORM_FAST=1`, `STRATA_SIDE_MIXER=2`, `STRATA_ARGMAX_ROWS_SM70=1`, `STRATA_LFUSE=1`, `STRATA_GDN_SPLIT=1` *(dropped in `0.1.67` when `--lookup-max-t > 8` per `#6747`; crashes `0.1.66` unless overridden)*, `STRATA_SH_STREAM=1`, `STRATA_Q80_ROWS1=1`, `STRATA_NO_MMVQ_ROWS2=1`, `STRATA_CPU_IQ_ALL_EXACT1=1`, `STRATA_GR_Q8_DOWN_MODE=2`, `STRATA_GR_Q8_UP_COLS=16`, `STRATA_GR_Q8_UP_MODE=2`, `STRATA_SCORES_HALVE=1`, `STRATA_SCORES_THREAD=1`, `STRATA_TOPK_SAMPLE=1`, `STRATA_SELECT_LONG=1`.
   - **Notable exclusions from `sm_70` table (compared to `S11X-D2`):** `STRATA_SELECT_SIMT`, `STRATA_PF_WMMA*`, `STRATA_ATTN_DAILY`, `STRATA_GR_UP75`, `STRATA_GU_SWIGLU`, `STRATA_QSA_ROWS`, `STRATA_FUSE_WAIT`.

2. **GPU Decode MoE (`EXP_MODE=8`, `src/kernels/cuda/iq_kernels.cu:6764-6803, 7200-7386`):**
   - `exp_mode()` (`iq_kernels.cu:6782,6800`) automatically selects **mode `8`** on `sm_70` whenever `STRATA_SM70_TABLE` is non-zero (which `nv_defaults.cpp:143` sets to `"1"` by default). For partial/strided PCIe calls (`grid_groups > 0 && grid_groups < cap_groups`), CUDA falls back to mode `0` (`iq_kernels.cu:7202`).
   - Under `em0 == 8`, `fused_gu` (`native_gu_fused_kernel<T>`, `iq_kernels.cu:7206-7237`, with `kExpLds16 = true` at `iq_kernels.cu:5897`) covers **48/48 Gate/Up layers** (`16, 17, 18, 21, 22`) and `native_down_lds_kernel<T>` (`iq_kernels.cu:7360-7385`) covers **48/48 Down layers** (`20, 42`).

3. **Dense INT8 Tensor Core Guard (`src/kernels/cuda/dense_i8_tc.cu:49-53, 1701-1703`):**
   - `dense_i8_tc_supported()` requires `current_cc() >= 75` (`sm_75+`), and `STRATA_DENSE_I8_SM80` device code is compiled out below `__CUDA_ARCH__ >= 750`. **Inactive on V100 `sm_70`; falls back safely to `native_mmvq` / cuBLAS FP16.**

4. **Fused Prompt Kernels (`src/prefill/moe_fused_iq.cu:2901`):**
   - `if (major < 8 && !(major == 7 && minor == 5 && sm75)) return d;` — **`STRATA_PF_FUSED` is inactive on `sm_70`.**

5. **NEW Default Volta Prefill Path (`i8_expert.cuh` + `i8h_volta.cuh` (`TUNE-0216`)) vs `STRATA_PF_WMMA*`:**
   - Because MMQ was removed (`STRATA_PF_OWN_ONLY=1`), `prefill.cpp:234` calls `native_expert_i8_set_mmq_free()`, making `native_expert_i8` the **default prompt-expert path** (`i8_expert_rule.hpp:37`).
   - On `sm_70` (`STRATA_I8_SM70` unset/!=0), `i8_volta()` (`iq_kernels.cu:6866-6887`) enables **`i8h_kernel`** (`src/kernels/cuda/i8h_volta.cuh:50-56,59`), a brand-new Volta FP16 Tensor Core (`mma.sync.aligned.m8n8k4.row.col.f32.f16.f16.f32`) kernel that is bit-identical to `i8_kernel` (`i8h_volta.cuh:12`) and engages when `avg >= kI8hMinAvg` (`160`, `i8_expert_rule.hpp:115-117`) across **all 48 Gate/Up (`16,17,18,21,22`) and all 48 Down (`20,42`) layers** (`i8h_volta.cuh:28`, `i8_expert.cuh:61-62`). Below `avg = 160`, `i8_tile_two_blocks` picks 2-block-per-SM `dp4a` tiles (`2` or `3`), or `native_expert_grouped` below `STRATA_I8_FEWROWS` (default `7`, `i8_expert_rule.hpp:65`).
   - By contrast, opt-in `STRATA_PF_WMMA=1` (`prefill.cpp:1970-1986, 6370`) **disables `i8_l`** and routes to `gemm_iq_f16_grouped` (`iq_kernels.cu:7921-7974`, covering `16,17,18,21,22` + `20,42`), while upstream `STRATA_PF_WMMA2=1` (`iq_kernels.cu:7915-7944`) only covers `ty == 22` (`IQ2_S`, 10/48 GU) and `ty == 20` (`IQ4_NL`, 18/48 Down). `STRATA_PF_WMMA_LEAN` and `STRATA_PF_WMMA_SKINNY` are **not** in upstream `0.1.66`/`0.1.67`.
   - **Volta Prompt Attention (`src/kernels/cuda/qsa_prompt_attn.cu:2501-2547`):** When built with `-DSTRATA_EXPERIMENTAL_SM60=ON`, `volta = true` on `sm_70` (`cc < 75`), dispatching INT8 KV prompt attention to `launch70<1>` (`m8n8k4` tensor cores).

---

### 6. CPU SIMD & Xeon W-2135 (`AVX512F/BW/DQ/VL/CD` only) Safety

Xeon W-2135 lacks `AVX512VNNI`, `AVX512VBMI`, `AVX512VPOPCNTDQ`, and `AVX-VNNI`.

1. **Compile Flags (`engine/cmake/backends/cpu.cmake`, `engine/cmake/backends/quant.cmake`):**
   - `cpu.cmake:267-268`: `expert.cpp` compiled with `-mavx512f;-mavx512bw;-mavx512vl;-mavx512dq;-mavx512vnni;-mavx512vbmi;-mf16c;-mfma`.
   - `cpu.cmake:336-346`: `iq_avx512.cpp`, `nvfp4_avx512.cpp` compiled with `...;-mavx512vnni;-mavx512vbmi;-mavx512vpopcntdq;-mbmi2;...`; `kq_avx512.cpp` and `tq_avx512.cpp` also include `-mavx512vnni;-mavx512vbmi`.
   - `quant.cmake:45-46, 74-75`: `sk_codecs_avx512.cpp`, `dot_avx512.cpp`, `act_avx512.cpp` compiled with `-mavx512f;-mavx512bw;-mavx512vl;-mavx512dq;-mavx512vnni;...` (no VBMI).
   - `strata_ggml.cmake:57`: when `STRATA_BUILD_TESTS=ON`, `GGML_NATIVE=ON` builds `ggml-cpu` for the build host; `STRATA_PORTABLE` sets `AVX2` baseline.
2. **Runtime CPUID / OSXSAVE Guards:**
   - `src/kernels/cpu/expert_layout.cpp:80-112` (`cpu_avx512_ok()`): checks `OSXSAVE` (`xcr0 & 0xE6 == 0xE6`), `F(16)`, `BW(30)`, `VL(31)`, `AVX512VNNI(ECX[11])`, `AVX512VBMI(ECX[1])` -> **`false` on W-2135**.
   - `expert_layout.cpp:188-204` (`cpu_vnni_ok()`): checks `F, DQ, BW, VL` + `AVX512VNNI(ECX[11])` -> **`false` on W-2135**.
   - `expert_layout.cpp:114-146` (`cpu_avx512bw_ok()`): checks `F, DQ, BW, VL` without VNNI/VBMI (`true` on W-2135), **but has ZERO callers anywhere in `0.1.66` or `0.1.67`**.
   - `src/quant/isa.cpp:62-83, 114-121, 138`: checks `OSXSAVE`, `zmm` XCR0 (`0xE0`), `F/DQ/BW/VL`, and `avx512_vnni` (`ECX[11]`). Both `best_isa()` (`isa.cpp:116`) and `isa_ok(Isa::Avx512)` (`isa.cpp:138`) require `c.avx512_vnni` -> **falls back to `Isa::Avx2` on W-2135**.
3. **Actual Execution Path on W-2135 for `IQ3_XXS` (`pool.cpp`, `native_expert.cpp`):**
   - **30/48 `Q2_0` (`d_type == 42`) down layers:** `q2_native_kernels(42)` (`expert_layout.hpp:93`) is `true` -> skips `STRATA_POOL_DEP` (`pool.cpp:1568`) and calls `q2_rows_any()` -> `q2_rows_512_ok()` (`expert.cpp:678`) is `false` -> falls back to **`q2_0_gguf_rows_multi_avx2`** (`q2_avx2.cpp`).
   - **18/48 `IQ4_NL` (`d_type == 20`) down layers:** `STRATA_POOL_DEP` (`mode_ == 7`, `pool.cpp:923,1568`) is ON by default; dispatches `iq4nl256_down_rows` (`iq_avx2.cpp`, `nt >= mt_min`) or `strata_quant` AVX2 `dot_iq4_nl_q8_0` (`nt == 1`).
   - **48/48 Gate/Up (`16,17,18,21,22`):** `cpu_vnni_ok()` is `false` -> dispatches `iq256_gu_rows` (`iq_avx2.cpp`, `nt >= mt_min`) or `strata_quant` AVX2 dot (`nt == 1`; note `STRATA_DOT_X4` is OFF by default in `0.1.67`).
   - **Verdict:** **Safe against `SIGILL`**, but **W-2135 gets ZERO AVX-512 speedup on stock `0.1.66`/`0.1.67`** (falls back to `AVX2`). Custom non-VNNI AVX-512BW (`PathC7` / `cpu_avx512bw_ok()`) porting is required to exploit W-2135's 512-bit ZMMs.

---

### 7. Memory Planner, mmap, Adaptive Cache, cgroup, DFlash2, `ROUTE_TAIL_SKIP` & Prefix Reuse

- **`STRATA_ROUTE_TAIL_SKIP` (`generate.cpp:14934-14942`, `include/strata/core/tail_skip_default.hpp:1-11`):**
  - **Major change vs `0.1.59`:** In `0.1.59`, `--serve` defaulted `STRATA_ROUTE_TAIL_SKIP=7` on CUDA (`0.1.59/src/program/generate.cpp:12776-12823`). Since `0.1.63` (owner decision 2026-11-19), **`STRATA_ROUTE_TAIL_SKIP` is OFF (`0`) by default** on every backend in both `0.1.66` and `0.1.67`. Comparisons vs `S11X-D2` must account for this exact-routing default.
- **Prefix Reuse (`generate.cpp:1089, 4072, 4763, 13853, 13882`):**
  - `--prompt-cache N` defaults to `6`. Passing **`--prompt-cache 0`** disables conversation prefix checkpoints cleanly (`prefix reuse = 0` for C2).
- **DFlash2 (`generate.cpp:6494-6530, 8267-8327, 8404-8433`, `src/core/dflash2.cpp:187-269`, `include/strata/core/draft_cap.hpp:28-32`):**
  - Pack format remains `DF2P` v1 (`dflash2.cpp:194`), Flash-Next shape `N=2560, NH=32, NKV=8, HD=128, rank=256, L<=8` (`dflash2.cpp:232`) — compatible with our stock DFlash2 selector pack.
  - `dflash2_auto_cap(false, 7, 0, card_bytes)` returns `0` (`draft_cap.hpp:28-32`), so `--spec 8 --draft-conf 0.7` is **not** capped on V100.
  - `--draft-fallback none`: verified (`generate.cpp:6507, 8310, 13601`); MTP is not loaded, and startup aborts if DFlash2 fails. Note: `draft_vocab.bin` is still required via `--mtp DIR` or `--mtp-draft-vocab FILE` (`generate.cpp:6498-6507`).
- **KV, mmap & Expert Cache (`generate.cpp:4000-4170, 8597-8886`):**
  - `--kv-resident 32768`, `--mmap-experts`, `--expert-cache auto` keep identical semantics.
- **Adaptive Cache & Overlap:**
  - `STRATA_ADAPT_OVERLAP=1` is ON in the `sm_70` table (`nv_defaults.cpp:142`) and works with `adapt_lag() == 1 && !adapt_nowait()` (`generate.cpp:15129`).
  - `STRATA_ADAPT_MID` (`adapt_coverage_rules.hpp`, `generate.cpp:14954`) is ON by default for CUDA (`15%..65%` coverage -> `every 2, swaps 192, decay 0.92`, unless `--adapt-*` flags override).
  - `STRATA_TINY_CACHE` is opt-in in `0.1.67` (`low_vram_rules.hpp`, `generate.cpp:14965`, N/A at ~25% residency).
  - `STRATA_COLD_OVERLAP` defaults to `4` (`generate.cpp:8691`, `expert_source.cpp:5465`); `STRATA_MMAP_ADAPT_ASYNC` does **not** exist upstream (was an `S11X-D2` custom patch); upstream `--adapt-async` (`generate.cpp:11774-11805`, `adapt_async_default.hpp:42-60`) self-trials only in arena mode (`srcp == &arena_src`), not with `--mmap-experts` unless explicitly patched.
- **cgroup Memory (`src/core/conversation_memory.cpp:378-425`):**
  - `sample_host_memory()` walks Linux cgroup v1/v2 limits, subtracts evictable mapped file pages (`own_evictable_mapped_bytes`), and respects `MemAvailable` + `--memory-limit-mib`.

---

### 8. `jmnargi/Strata-V100` Fork Audit (`776e1755` `v0.1.45.10` -> `49c6cc6` `v0.1.45.13`)

| Tag / Commit | Key Change | `sm_70` / Stage 12 Applicability |
|---|---|---|
| `v0.1.45.11` (`7567e2d`, `79c7f15`, `4b69544`) | Register prefetch in Volta INT8 prompt attention (`qsa_prompt_attn.cu`); avoid clearing suffix lookup index on reset. | `79c7f15` gave +8-10% kernel speed but "no meaningful throughput gain" on 2-V100 model; optional low-priority port. |
| `v0.1.45.12` (`af0c8ca`, `537aa5c`, `a17046c`, `b6e730d`) | Opt-in `STRATA_UNBUFFERED_LOAD=1` (`O_DIRECT` for packed expert arenas); adopts `STRATA_PF_WMMA_LEAN` prompt buffers (already proven in `S7-XXS-16`/`S11X-D2`). | `PF_WMMA_LEAN` already in `S11X-D2` (`stage11x-d2.patch`); `O_DIRECT` arena inapplicable to `--mmap-experts`. |
| `v0.1.45.13` (`49c6cc6`, `1482c5a`, `e03e868`, `168ffb0`) | **`STRATA_HC_V100=1`** (opt-in `sm_70` K-split + one-launch fused HC read for `T <= 6` in `fused_gr.cu`: `hc_graph_bench` T1 `32.1 -> 26.0 us`, T6 `64.8 -> 45.0 us`); conv-cache leaked-pin eviction (`168ffb0`). | **`STRATA_HC_V100`** is a clean MIT-licensed `sm_70` decode candidate (note: deterministic, not bitwise identical, rel RMS `2e-7`); evaluate in Gate C against `0.1.67`'s `sm_70` `STRATA_GR_Q8_*` defaults. |

---

## Part 2 — `S11X-D2` Patch & 19-Override Functional Mapping (`S12-A2`)

> **Status:** Complete (Read-Only Audit against `0.1.66` `a34979fc` and `0.1.67` `d46f5f26`)  
> **Source Inputs:** [stage11x-d2.patch](../docker/patches/stage11x-d2.patch) (2,536 lines across 13 files) and the 19 `S11X-D2` env overrides in [STAGE12_PLAN.md](STAGE12_PLAN.md#L91-L101).  
> **0.1.66 vs 0.1.67 Parity Note:** Of the 19 target files, 16 have **0 diff lines** between `0.1.66` and `0.1.67`. The only 3 files with diffs relevant to this mapping are `engine/cmake/backends/cpu.cmake` (+`dot_x4_bench`), `engine/src/core/nv_defaults.cpp` (`#6747` `gdn_split_default_flag()`), and `engine/src/kernels/cpu/native_expert.cpp` (`#6552` `STRATA_DOT_X4=1` opt-in). (`fused_gr.cu` `#6713` affects `sm_80+` only; `prefill.cpp` has 0 diff lines.)

---

### 1. 19 `S11X-D2` Env Override Mapping (`0.1.66` / `0.1.67`)

#### Classification Legend
- **`KEEP`**: Env var is read upstream (`0.1.66`/`0.1.67`), not overridden by `sm_70` defaults, and retains valid functional semantics. (Do **not** inject into pure Gate B `S12-U0`/`S12-U1`; evaluate in Gate C.)
- **`UPSTREAM-EQUIVALENT`**: Upstream `0.1.66`/`0.1.67` already enables the exact behavior by default on `sm_70` (via `nv_defaults.cpp` or build-time `STRATA_EXPERIMENTAL_SM60`). Explicit override is a no-op.
- **`REBASE`**: Env var or behavior is missing, truncated, or unsafe/incompatible without porting/rewriting `stage11x-d2.patch` onto `0.1.66`/`0.1.67`.
- **`REPLACE`**: Env var still exists upstream, but upstream `0.1.66`/`0.1.67` introduced a new default `sm_70` path that the old override would **disable or regress**. Omit in Gate B; test against new default in Gate C.
- **`DROP`**: Superseded on `sm_70` by `0.1.66`/`0.1.67` defaults (`EXP_MODE=8` / `SCORES_HALVE=1`).
- **`BLOCKED`**: Unsafe/broken on `sm_70` or W-2135.

| # | Group | Override (`S11X-D2`) | Upstream Read (`0.1.67` `file:line`) | Upstream Behavior on `sm_70` + W-2135 | Class | Parity / Risk & Gate Mapping |
|---|---|---|---|---|---|---|
| 1 | Baseline D4 | `STRATA_SELECT_SIMT=1` | `src/kernels/cuda/qsa_select.cu:2395-2422`, `src/prefill/prefill.cpp:5377` | Opt-in FP32 tiled QSA scorer (`cc < 8`). Unset defaults to `0` (warp kernel). (`=2` `simt2` also available, bitwise equal to `=1`.) | **`KEEP`** | Not bitwise vs warp kernel (`qsa_select.cu:2392`). Omit in Gate B; test `=1`/`=2` vs warp in Gate C (`S12-P1`/`S12-P2`). |
| 2 | Baseline D4 | `STRATA_SM70_TABLE=1` | `src/core/nv_defaults.cpp:143`, `iq_kernels.cu:6782,6800`, `fused_gr.cu:4082`, `native_mmvq.cu:4193` | **Already ON by default** in `sm_70` `nv_defaults` (`apply_nv_defaults`, `generate.cpp:4448`). Enables `EXP_MODE=8`, `gr_fast`, `native_mmvq_il`. | **`UPSTREAM-EQUIVALENT`** | Bit-exact (`nv_defaults.cpp:137-138`, `nv_defaults_test.cpp:152`). No-op override unless `STRATA_SM70_PERF=0`. |
| 3 | Baseline D4 | `STRATA_PF_WMMA=1` | `src/prefill/prefill.cpp:1970-1986,2053,2192,6323,6370` | **HARMFUL IN GATE B:** `0.1.66`/`0.1.67` (`STRATA_PF_OWN_ONLY=1`) defaults `sm_70` to `native_expert_i8` + **`i8h_kernel`** (`i8h_volta.cuh:59`, `TUNE-0216`). Setting `STRATA_PF_WMMA=1` forces `!wmma_l` false -> **kills `i8_l`/`i8h_volta`** (`prefill.cpp:6370`), allocates `Xs`/`Hh`, and routes to unpatched generic WMMA. | **`REPLACE`** | **Do NOT pass in Gate B (`S12-U0`/`S12-U1`)**; let `i8h_volta` run. In Gate C (`S12-P1`), benchmark `i8h_volta` vs ported `WMMA2+LEAN+SKINNY`. |
| 4 | Volta P1 | `STRATA_PF_WMMA2=1` | `src/kernels/cuda/iq_kernels.cu:7915-7944` | Upstream `WMMA2` only covers `ty == 22` (`IQ2_S`, `K%512==0`, 10/48 GU) and `ty == 20` (`IQ4_NL`, 18/48 Dn) with 4B-aligned `W`/`rb` and no `N64`/`ids`/`GroupedWeightTable`. Lacks `S11X-P1` `ty==18,21` + 2B align + FP16-FMA scale. Only active if `STRATA_PF_WMMA=1`. | **`REBASE`** | Dead under `i8h_volta`. Port `S11X-P1` `WMMA2` (18/20/21/22 + `N64` + 2B align) into Gate C **`S12-P1`** if `S12-P0` warrants; gate with `pf_wmma_parity`. |
| 5 | Volta P1 | `STRATA_PF_WMMA_LEAN=1` | *(not present in `0.1.66` or `0.1.67`)* | Dead/ignored env var upstream. (`i8_l` / `i8h_volta` already reads cache/ring slots directly via `i8_rec` without `Xs`/`Hh` or `grp_gu`/`grp_d` copies, though `dq_gu`/`dq_d` still reserve `prefill.cpp:2844`.) | **`REBASE`** | Coupled with `WMMA2` in Gate C **`S12-P1`** (`GroupedWeightTable`, skip `Xs`, alias `Hh` to `xn16`, omit `dq_*`). |
| 6 | Volta P1 | `STRATA_PF_WMMA_SKINNY=1` | *(not present in `0.1.66` or `0.1.67`)* | Dead/ignored env var upstream. `w2_iq4_skinny` (`major==7 && minor==0`, `max_rows <= 8`, `ty==20` Down) is custom `stage11x-d2.patch`. | **`REBASE`** | Coupled with `WMMA2` in Gate C **`S12-P1`** (`sm_70`-guarded `m8n8k4` direct MMA); gate with `pf_wmma_parity`. |
| 7 | CPU PathC7 | `STRATA_AVX512BW_IQ=22` | *(not present; `cpu_avx512bw_ok()` at `expert_layout.cpp:114-146` has 0 callers)* | `native_expert.cpp:568,684` requires `cpu_vnni_ok()` (`false` on W-2135) -> **0% AVX-512 used**; all `IQ2_S` (and other IQ) rows stay on AVX2 (`iq256_gu_rows`) or `strata::quant` AVX2 (`isa.cpp:116` requires `avx512_vnni`). | **`REBASE`** | High-priority Gate C **`S12-D1`**. Must patch `cpu.cmake` (drop VNNI/VBMI/VPOPCNTDQ on `expert.cpp` & `iq_avx512.cpp`), guard new `0.1.67` `iq512x`/`iq512f`/`qd_rows` VNNI/VPOPCNTDQ ops, and pass `isa_guard_check` + `native_arithmetic_parity` + `iq_avx2_parity`. |
| 8 | CPU PathC7 | `STRATA_IQ_MT_MIN=1` | `src/kernels/cpu/native_expert.cpp:545-557,798` | Still read for Gate/Up and `IQ4_NL` Down. At `=1`, forces multi-token kernels for `nt==1` (bypassing `STRATA_CPU_IQ_ALL_EXACT1=1` from `sm_70` table at `native_expert.cpp:594` and `strata::quant` 1-row/x4 dots at `736,861`). | **`KEEP`** | Window-invariant CPU rounding (`verify.hpp:245`, `native_expert_parity.cpp:924`). Omit in Gate B; enable in Gate C **`S12-D1`**. |
| 9 | CPU PathC7 | `STRATA_IQ_GATHER=1` | `src/kernels/cpu/iq_avx512.cpp:42-45,668` | Unset defaults to `cpu_gather_fast()` (`expert_layout.cpp:320-340`), which requires `AVX-VNNI` (`false` on W-2135). **No-op in unpatched `0.1.66`/`0.1.67`** because `iq_avx512.cpp` is never reached on W-2135. | **`REBASE`** | Active once `PathC7` (`S12-D1`) enables `iq_avx512.cpp`. Must also eliminate static initializer `iq_avx512.cpp:42` (`strata_cpu_reload_env`) to satisfy `check_isa_guard.py:49,126` (`INIT_FREE_OBJECTS`). |
| 10 | CPU PathC7 | `STRATA_IQ256_GATHER=1` | `src/kernels/cpu/expert_layout.cpp:310-317`, `iq_avx2.cpp:491-496` | Still read. Unset uses `cpu_gather_fast_here()` (`false` on W-2135). `=1` forces `_mm256_i32gather_*` grid loads in `iq_avx2.cpp` for `IQ2_XXS/XS/S` and `IQ3_XXS/S` (48/48 GU). | **`KEEP`** | Bit-exact with scalar decode (`iq_avx2.cpp:277`). Omit in Gate B; measure gather vs scalar on W-2135 AVX2 in Gate C **`S12-D1`**. |
| 11 | CPU PathC7 | `STRATA_Q2_BITPLANE=1` | `src/kernels/cpu/q2_avx2.cpp:146-149,174`, `q2_avx1.cpp:199` | Still read; engages AVX2 `rows_bp<NT>` for `Q2_0` (30/48 Down layers on W-2135). (Note: `STRATA_AVX512BW_Q2` was not in `S11X-D2`.) | **`KEEP`** | Verified by `q2_bitplane_parity` (`cpu.cmake:514-517`). Omit in Gate B; test in Gate C **`S12-D1`**. (If refactored with `S12-D1`, move static init `q2_avx2.cpp:146` to `strata_cpu_reload_env`.) |
| 12 | GPU Defaults | `STRATA_SIDE_MIXER=2` | `src/core/nv_defaults.cpp:148`, `src/core/verify.cpp:275-293` | **Already `"2"` by default** in `sm_70` `nv_defaults` (`nv_defaults.cpp:148`). Runs GDN/QSA input-only mixer work on verify graph branches. | **`UPSTREAM-EQUIVALENT`** | Bitwise equal (`verify.cpp:273`). No-op override on `sm_70`. |
| 13 | GPU Defaults | `STRATA_ATTN_DAILY=1` | `src/kernels/cuda/qsa_decode_attn.cu:902-963,1005-1021` | **Partial overlap:** With `-DSTRATA_EXPERIMENTAL_SM60=ON`, `pre75_attn()` (`cc < 75` at `962`) **already selects `attn_chunk_kernel_pre75`** on `sm_70`. However, `attn_merge_v2()` (`1005-1011`) checks `daily_attn()`, so `STRATA_ATTN_DAILY=1` additionally switches `launch_merge` to `attn_merge_v2_kernel`. | **`KEEP`** | Bitwise equal (`qsa_decode_attn.cu:1013`, `qsa_merge_daily_parity`). Omit in Gate B; optional Gate C decode micro-opt if `S12-P0` shows QSA merge cost. |
| 14 | GPU Defaults | `STRATA_GR_UP75=1` | `src/kernels/cuda/fused_gr.cu:1560-1579` | Not in `sm_70` `nv_defaults` (which instead sets `STRATA_GR_Q8_UP_MODE=2`, `STRATA_GR_Q8_UP_COLS=16`, `STRATA_GR_Q8_DOWN_MODE=2`). When set on `sm_70`, runs `gr_up75_kernel` for `T >= 3` (`LR == 320`). | **`KEEP`** | Bitwise equal (`fused_gr.cu:574`, `fused_gr_bench`). Omit in Gate B; optional Gate C decode micro-test vs `0.1.67` `sm_70` `GR_Q8_*` table. |
| 15 | GPU Defaults | `STRATA_GU_SWIGLU=1` | `src/kernels/cuda/iq_kernels.cu:4578-4609,7241-7256` | Not in `sm_70` `nv_defaults`. Because `sm_70` defaults to `EXP_MODE=8` (`fused_gu = true` for 48/48 GU in VRAM, `iq_kernels.cu:7206-7237`), `gs_layout` (`!fused_gu`, `7244`) is **skipped** on all resident calls; only fires on strided PCIe calls (`em0 = 0`, `7202`). | **`DROP`** | Superseded on VRAM experts by `EXP_MODE=8` (`STRATA_SM70_TABLE=1`). Omit in Gate B & C unless `EXP_MODE=8` is disabled. |
| 16 | GPU Defaults | `STRATA_QSA_ROWS=1` | `src/kernels/cuda/qsa_select.cu:2203-2224` | Not in `sm_70` `nv_defaults`, which instead sets **`STRATA_SCORES_HALVE=1`** (`nv_defaults.cpp:159`). At `qsa_select.cu:2204-2206`, `STRATA_QSA_ROWS=1` preempts `scores_halve_on()` for `nq <= 4`. | **`DROP`** | Both bitwise equal (`qsa_select.cu:2203,2206`). Omit in Gate B to preserve `0.1.67` `sm_70` default (`SCORES_HALVE=1`); only A/B in Gate C if `S12-P0` warrants. |
| 17 | GPU Defaults | `STRATA_FUSE_WAIT=2` | `src/core/verify.cpp:507-513` | Not in `sm_70` `nv_defaults` (defaults to `device_is_sm75()`, `false` on `sm_70`). `=2` folds only the plan wait in verify (`=1` folds plan + CPU rows). | **`KEEP`** | Bitwise equal (`verify.cpp:507`). Omit in Gate B; optional Gate C decode micro-test. |
| 18 | Cache / Sched | `STRATA_MMAP_ADAPT_ASYNC=1` | *(not present; `generate.cpp:11803,15586-15615`)* | Dead/ignored upstream. `0.1.67` `--adapt-async 1` still refuses `--mmap-experts` without `--resident-cpu-experts` (`generate.cpp:11803`), falling back to **blocking** adaptive swaps (`15611`), even though `STRATA_ADAPT_OVERLAP=1` and `STRATA_ADAPT_MID` (`192` swaps/2 win) are ON. | **`REBASE`** | High-priority Gate C **`S12-D2`** (`MmapBounceRing` 2-slot pinned host bounce + `JobThread` `aux_cpus::plan()` fallback). Must check `a_cap` (`96` vs `192` at `generate.cpp:15588`) & async race/lifetime. |
| 19 | Cache / Sched | `STRATA_COLD_OVERLAP=5` | `src/core/expert_source.cpp:5462-5468,5771-5845` | Upstream clamps `STRATA_COLD_OVERLAP` to `[0, 4]` (`expert_source.cpp:5466`) and defaults to `4` on Linux (`5468`). Passing `=5` unpatched silently clamps to **`4`** (`claim_todo` `mincore` + `zc_keys_` linear scan). | **`REBASE`** | Gate C **`S12-D2`** (`fast_zc_ready` + `zc_roles_fast` zero-`mincore` O(1) role pointers). Must gate with `file_expert_source_test` + cold/warm residency & page-fault checks. |

---

### 2. `stage11x-d2.patch` Hunk-by-Hunk Disposition & Port Plan

All 13 patched files in [stage11x-d2.patch](../docker/patches/stage11x-d2.patch) collapse into 4 logical hunk groups:

| Logical Hunk Group | Patched Files & Lines (`stage11x-d2.patch`) | Upstream `0.1.67` Conflict / Delta | Disposition | Target Gate / Parity Requirements |
|---|---|---|---|---|
| **H1: CPU `PathC7` (`AVX512BW` non-VNNI + Init-Free Env Reload + Log)** | `cmake/backends/cpu.cmake:1-24`; `expert_layout.hpp:48-60`; `expert.cpp:145-316`; `expert_layout.cpp:317-485`; `iq_avx512.cpp:486-691`; `native_expert.cpp:692-849`; `q2_avx2.cpp:850-896`; `generate.cpp:2320-2326` | **Medium-High Rebase:** `0.1.67` `iq_avx512.cpp` added `iq512x_rows`, `iq512_fused_gu_rows`, `qd_rows` with `_mm512_dpwssd_epi32` / `_mm512_dpbusd_epi32` / `_mm256_popcnt_epi32`; `native_expert.cpp` added `STRATA_DOT_X4` (`#6552`), `kq512_*`, `tq_*`; `generate.cpp` startup log moved to `5629-5634`; `isa_guard_check` (`tools/check_isa_guard.py:32-49,126`) forbids wide COMDAT/unguarded ops and static initializers in `INIT_FREE_OBJECTS`. | **`REBASE`** | **`S12-D1`** — Gate with `isa_guard_check`, `native_arithmetic_parity` (all variants), `iq_avx2_parity`, `q2_bitplane_parity`, `iq512_gather_parity`. *(Note: `STRATA_FORK_AVX2_NT1` in `expert_layout.cpp`/`native_expert.cpp` was unused by `S11X-D2` and can be omitted.)* |
| **H2: Volta `WMMA2` (18/20/21/22, `N64`, 2B align, FP16 FMA scale) + `SKINNY` + `LEAN` (`indirect_w`)** | `iq_kernels.hpp:61-85`; `iq_kernels.cu:897-2043`; `prefill.cpp:2044-2298` | **Conditional Rebase:** `0.1.67` removed MMQ and made `i8h_volta.cuh` (`TUNE-0216`) the `sm_70` default, which already avoids `Xs`/`Hh`/`grp_*` copies via `i8_rec`. Upstream `gemm_iq_f16_grouped` (`iq_kernels.cu:7572-7982`) still lacks `18/21` `WMMA2`, `N64`, 2B `row_bytes`, `SKINNY`, `GroupedWeightTable`, and `LEAN`. | **`REBASE` (Conditional)** | **`S12-P1`** — First profile `i8h_volta` in `S12-B`/`S12-P0`. Only port H2 if `S12-P0` shows `i8h_volta` underperforms `S11X-P1` prefill. Gate with `pf_wmma_parity`, `native_multi_parity`, chunk-size `<=8192`, and VRAM `<=15.8 GiB` check. |
| **H3: `mmap` Async Adaptive Tier (`MmapBounceRing` + `JobThread` `aux_cpus::plan()`)** | `generate.cpp:2299-2319, 2330-2536` | **Clean Rebase:** Target blocks at `generate.cpp:2503-2513`, `11794-11812`, `15586-15920` match `0.1.59` structure closely. Note `a_cap` in `0.1.67` increased from `96` to `192` (`generate.cpp:15588`), and `STRATA_ADAPT_MID` (`every 2, swaps 192, decay 0.92`) is ON by default. | **`REBASE`** | **`S12-D2`** — Verify `MmapBounceRing` (`2 * max_blob` pinned alloc), `cudaEventSynchronize` lifecycle, `adapt_quiesce`, and `JobThread` CPU pinning inside agent cpuset. |
| **H4: Zero-`mincore` Fast Zero-Copy (`STRATA_COLD_OVERLAP=5`)** | `expert_source.hpp:25-47`; `expert_source.cpp:86-144` | **Clean Rebase:** `FileExpertSource` (`expert_source.hpp:299,989`, `expert_source.cpp:2632,5464-5468,5771-5845`) has unchanged structure and `0` diff lines between `0.1.66` and `0.1.67`. | **`REBASE`** | **`S12-D2`** — Gate with `file_expert_source_test`, `!unmapped_ && direct_.empty() && tail_off == 0` guard, and cold/warm page-fault verification. |

---

### 3. Gate B vs Gate C Execution Contract Derived from `S12-A2`

1. **Gate B (`S12-U0` `0.1.66`, `S12-U1` `0.1.67` Pure Baselines):**
   - **Must NOT pass any of the 19 `S11X-D2` env overrides** (especially **NOT `STRATA_PF_WMMA=1`**, which would disable `i8h_volta` (`TUNE-0216`)).
   - **Mandatory safety / workload CLI flags:** `--prefill auto:8192 --kv int8 --kv-resident 32768 --ctx 131072 --mmap-experts --expert-cache auto --spec 8 --draft-conf 0.7 --draft-fallback none --prompt-cache 0` (plus `--mtp` / `--mtp-draft-vocab` and `--expert-profile`).
   - Note that on `0.1.66`, `nv_defaults.cpp:151` sets `STRATA_GDN_SPLIT=1` while `--lookup-max-t` defaults to `12` (`#6747`); if `--lookup-max-t 0` is not set by DFlash2 (`lookup_default.hpp` disables lookup when `dflash2 == true` at `generate.cpp:5049`, so `S12-U0` with `--draft dflash2` avoids the `#6747` crash — verify on startup).
   - Note that `STRATA_ROUTE_TAIL_SKIP` is **`0` (OFF)** by default in `0.1.66`/`0.1.67` (vs `7` in `0.1.59`).
2. **Gate C Prioritized Port Targets (after `S12-P0` profiling):**
   - **`S12-D1` (High Priority — CPU `PathC7`):** Rebase H1 (`STRATA_AVX512BW_IQ=22`, init-free env reload, W-2135 VNNI/VBMI/VPOPCNTDQ software guards) + `STRATA_IQ_MT_MIN=1`, `STRATA_IQ_GATHER=1`, `STRATA_IQ256_GATHER=1`, `STRATA_Q2_BITPLANE=1`.
   - **`S12-D2` (High Priority — `mmap` Async Adapt + Zero-`mincore`):** Rebase H3 (`STRATA_MMAP_ADAPT_ASYNC=1` + `JobThread` aux-CPU pinning) and H4 (`STRATA_COLD_OVERLAP=5`).
   - **`S12-D3` (Upstream `sm_70` GPU Decode):** Verify `EXP_MODE=8` + `sm_70` `nv_defaults` behavior in `S12-P0`; optionally evaluate `fork-v100` `STRATA_HC_V100=1` (`49c6cc6`) and `S11X-D2` GPU micro-opts (`STRATA_ATTN_DAILY=1`, `STRATA_GR_UP75=1`, `STRATA_FUSE_WAIT=2`, `STRATA_QSA_ROWS=1`).
   - **`S12-P1` (Conditional — Volta Prefill):** Compare `0.1.67` `i8h_volta` vs rebased H2 (`STRATA_PF_WMMA=1` + `WMMA2` + `LEAN` + `SKINNY`) and `STRATA_SELECT_SIMT=1`/`2`.

