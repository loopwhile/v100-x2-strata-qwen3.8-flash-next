# Stage 12 — Build & Parity Gate Audit (`S12-A1`)

> **Date:** 2026-11-25 KST  
> **Host:** `p520-llm` (Dual Tesla V100-SXM2-16GB, Xeon W-2135, 64 GB RAM)  
> **Gate A Status:** **PASS (`0.1.67` `BUILD_AND_PARITY_PASS`; `0.1.66` GPU parity completed under bounded dims after earlier `15:35 KST` power-off incident)**  
> **`0.1.66` Build (`strata-v100:stage12-0.1.66-stock`):** `sha256:5ee459198a4b9c695183bf5901c17ff6b68019381c6b70c72a138fb76d27e93d` — CPU `20/23` (`pool_determinism` / `pool_determinism_dep_off` fail, `cuda_spill_guard` skip), GPU CTest `14/14` pass, bounded `qsa_prompt_attn_parity 8192 512 2` (`FAILURES: 0`) & `dflash2_q4_parity` (`40/40`) pass  
> **`0.1.67` Build (`strata-v100:stage12-0.1.67-stock`):** `sha256:83a48e7dc321a72e0a13642668a887d179d630d2ff4dd204fd49cb7f674c3b6e` — CPU `22/22` pass (`0` skip, `pool_determinism` `#6754` PASS), GPU CTest `15/15` pass (`0` skip, `gr_write_norm_parity` `#6776` PASS), bounded `qsa_prompt_attn_parity 8192 512 2` (`FAILURES: 0`) & `dflash2_q4_parity` (`40/40`) pass

---

## 1. Preflight Verification (`scripts/135-stage12-prepare.py`)

### 1.1 Initial Run (Before `15:35 KST` Power-Off Incident)
Executed on `p520-llm` at `2026-11-25T15:05:26.902862+09:00` (boot ID `63452ec5-05f7-4a66-94a4-9be2af98c311`):
- **Verdict:** `PREPARATION_PASS_NOT_C2`
- **Serving containers:** `p520-llm-a` = `exited`, `p520-llm-b` = `exited`
- **GPU policy:** `power.limit = 150 W` on both GPUs, `v100-clock-lock.service` active (`gpuClkMin 135, gpuClkMax 1245`)
- **Disk free:** `183,628,029,952` bytes

### 1.2 Resumed Gate A Run (After Power-Off Review & `ad801fa` Fix)
Executed on `p520-llm` at `2026-11-25T16:00:24.548574+09:00` (boot ID `a182c39f-45df-4915-8688-fa33ff83eb03`, commit `ad801fa`):
- **Verdict:** `PREPARATION_PASS_NOT_C2`
- **Serving containers:** `p520-llm-a` = `exited`, `p520-llm-b` = `exited`
- **GPU policy:** `power.limit = 150 W` on both GPUs, `clock_ceiling_mhz = 1245` (`v100-clock-lock.service` active since `15:35:39 KST` boot)
- **Assets:** 15 assets verified; DFlash2 pack SHA256 `4a42b98220ea7880664002c8edda1563aecbae754b762a2e2f31b2b91ee93ecd`; harness SHA256 `a8e42cc5a71421a7287618fd5be0332ae40f312426e4d243ce1c7619fdfc5246`; manifest SHA256 `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`
- **Disk free:** `181,788,454,912` bytes

---

## 2. `0.1.67` Stock Build (`strata-v100:stage12-0.1.67-stock`) — **GATE A PASS**

### 2.1 Provenance & Toolchain

| Field | Verified Value |
|---|---|
| Repository / Ref | `Niko1221/Strata` @ `d46f5f268f8ed797e83a5c63a69bffbd7a581cf6` |
| CMake Engine Version | `0.1.67` |
| Patch | None (stock) |
| Base Image | `nvidia/cuda:12.9.1-devel-ubuntu24.04` (`nvcc` `12.9`, `V12.9.86`) |
| CMake Flags | `-DSTRATA_ENABLE_CUDA=ON -DSTRATA_EXPERIMENTAL_SM60=ON -DCMAKE_CUDA_ARCHITECTURES=70 -DSTRATA_BUILD_TESTS=ON` |
| Docker Image Tag | `strata-v100:stage12-0.1.67-stock` |
| Docker Image ID | `sha256:83a48e7dc321a72e0a13642668a887d179d630d2ff4dd204fd49cb7f674c3b6e` |
| Binary Path | `/opt/strata/engine/strata` |
| Binary SHA256 | `acfe6d530bc970514d0f57c3f5a87fd5b0b77a2666f8bf4095f1ebd33bb0b447` |
| Dynamic Linkage (`ldd`) | `libcudart.so.12`, `libcublas.so.12`, `libcublasLt.so.12` (no CUDA 13 libs) |

- **Built Targets (27):** `strata`, `native_arithmetic_parity`, `pool_determinism`, `iq_avx2_parity`, `iq_avx1_parity`, `q8k_quant_parity`, `q2_bitplane_parity`, `quant_selftest`, `quant_parity`, `type_geometry_oracle`, `native_expert_parity`, `native_multi_parity`, `native_grouped_parity`, `native_i8_parity`, `pf_wmma_parity`, `gr_write_norm_parity`, `qsa_prompt_attn_parity`, `qsa_merge_daily_parity`, `dflash2_parity`, `dflash2_q4_parity`, `file_expert_source_test`, `nv_defaults_test`, `tail_skip_default_test`, `lookup_default_test`, `adapt_async_default_test`, `cgroup_mem_test`, `cgroup_cpu_test`.
- *(Note: `native_arithmetic_parity_{avx,mt1,no512,ggml}` and `pool_determinism_dep_off` are CTest test aliases invoking the compiled `native_arithmetic_parity` and `pool_determinism` binaries.)*

### 2.2 `cuobjdump`, CUDA Spill & CPU ISA Guard Verification (`0.1.67`)

- **`cuobjdump --list-elf /opt/strata/engine/strata`:** Confirmed **58 ELF files**, all `sm_70` (`strata.1.sm_70.cubin` through `strata.58.sm_70.cubin`, `0` non-`sm_70` cubins).
- **`isa_guard_check` (`tools/check_isa_guard.py /opt/strata/build-stage12/libstrata_kernels_cpu.a`):** **Passed** (`890 functions, 170 hold wide-ISA instructions, 0 not allowed`).
- **`objdump -d -C /opt/strata/engine/strata`:** Disassembly matched `311` functions containing `vpdpbusd` / `vpdpwssd` / `vpermb` / `vpermi2b` / `vpmultishiftqb`; all belong to runtime-CPUID-guarded wide-ISA dispatch paths (`avx512`, `vnni`, `s2_expert_*`, `q2_0_gguf_rows_multi`, `iq_avx512.cpp` anonymous namespace `row_dot<...>`, `q2g_row_multi`, `expert_multi`, `row_dot_multi`, `qd_rows_nt`, `rows_m_nt`, `q4k_tile_n`), with `0` unguarded AVX-512 VNNI/VBMI instructions on Xeon W-2135.
- **`no_mmq_symbols`:** **Passed** (`libstrata_kq.so` absent; no MMQ symbols linked).
- **`pf_own_spill_audit` (`tools/check_cuda_spills.py ... libstrata_pf_own.a`):** **Passed** (`167 kernels on sm_70`, `0` use stack / local memory, `0` not allowed).

### 2.3 CPU CTest Gate Results (`0.1.67`)

Executed via `scripts/136-stage12-build.py --version 0.1.67 --tag strata-v100:stage12-0.1.67-stock --out results/stage12/builds/0.1.67-stock` (saved to `results/stage12/builds/0.1.67-stock/ctest-cpu.log`):

- **Result:** **22/22 Passed (`100% tests passed out of 22`, `0` failed, `0` skipped, `Total Test time (real) = 310.89 sec`)**:
  - `file_expert_source_test`, `nv_defaults_test`, `adapt_async_default_test`, `lookup_default_test`, `tail_skip_default_test`, `cgroup_mem_test`, `cgroup_cpu_test`
  - `native_arithmetic_parity`, `native_arithmetic_parity_avx`, `native_arithmetic_parity_mt1`, `native_arithmetic_parity_no512`, `native_arithmetic_parity_ggml`
  - `pool_determinism` (`#6754` fix verified: **Passed** in `310.59 sec`), `pool_determinism_dep_off` (**Passed** in `107.87 sec`)
  - `iq_avx1_parity`, `iq_avx2_parity`, `q8k_quant_parity`, `quant_selftest`, `quant_parity`, `q2_bitplane_parity`
  - `isa_guard_check` (**Passed** in `4.77 sec`), `no_mmq_symbols` (**Passed** in `115.84 sec`)
- **Runner Note (`scripts/136-stage12-build.py:118`):** CTest `4.4.3` in `.venv` prints `100% tests passed out of 22` (omitting `0 tests failed`), causing `scripts/136-stage12-build.py` to raise `AssertionError` at line 118 despite all 22/22 CPU tests passing with 0 skips. GPU parity tests were then executed directly against the built `strata-v100:stage12-0.1.67-stock` image and recorded in `results/stage12/builds/0.1.67-stock/{ctest-gpu.log,progress.json}`.

### 2.4 GPU Parity Results (`0.1.67`, `--gpus device=0`)

Saved to `results/stage12/builds/0.1.67-stock/ctest-gpu.log`:

1. **Mandatory GPU CTest Suite (15 tests): 15/15 Passed (`100% tests passed out of 15`, `0` failed, `0` skipped, `Total Test time (real) = 206.35 sec`):**
   - `qsa_merge_daily_parity_default` (`2.55 sec`), `qsa_merge_daily_parity_daily` (`2.42 sec`)
   - `gr_write_norm_parity` (`#6776`: **Passed** in `4.41 sec`)
   - `native_grouped_parity` (`6.65 sec`), `native_i8_parity` (`72.56 sec`), `pf_wmma_parity` (`78.65 sec`), `native_multi_parity` (`0.26 sec`)
   - All 8 `native_expert_parity_v31_iq{2_xxs,2_xs,2_s,3_xxs}_{q2_0,iq4_nl}` variants (`2.67–6.78 sec` each)
2. **Bounded Direct GPU Parity (`qsa_prompt_attn_parity 8192 512 2`):** **`FAILURES: 0`**
   - `int8 IMMA ctx 8192, 512 queries`: `PASS` (`vs FP64 2.72e-06`, `IMMA vs v2 0`, `3.455 ms/chunk`)
   - `int8 ctx 8192, 512 queries`: `PASS` (`1.79x`, `new output checksum 9b7ca72c4363175e`)
   - `fp16 ctx 8192, 512 queries`: `PASS` (`1.05x`, `new output checksum 3f7311fe9798c2e9`)
   - `int8 IMMA/v2 ctx 1500, 512 queries`: `PASS` (`new output checksum 71e53de9e6ee2bd6`)
   - `int8 IMMA/v2 ctx 2100, 256 queries`: `PASS` (`new output checksum 9ad8786db03e394a`)
   - *(Note: `q4_0 ctx 8192` and `q4_0 ctx 1500` report `SKIP` because the Q4_0 KV tensor-core kernel requires `sm_80+` while V100 is `sm_70`; `FAILURES: 0`.)*
3. **Bounded Direct GPU Parity (`dflash2_q4_parity`):** **`PASS: 40 of 40 cases match the CPU reference`** (max `|kernel - cpu| <= 2.29e-06`).

---

## 3. `0.1.66` Stock Build (`strata-v100:stage12-0.1.66-stock`) — Historical Reference & Bounded GPU Completion

### 3.1 Provenance & Toolchain

| Field | Verified Value |
|---|---|
| Repository / Ref | `Niko1221/Strata` @ `a34979fc94f3d126b9bb8210f4ad311345688b52` (`v0.2.20`) |
| CMake Engine Version | `0.1.66` |
| Patch | None (stock) |
| Base Image | `nvidia/cuda:12.9.1-devel-ubuntu24.04` (`nvcc` `12.9`, `V12.9.86`) |
| CMake Flags | `-DSTRATA_ENABLE_CUDA=ON -DSTRATA_EXPERIMENTAL_SM60=ON -DCMAKE_CUDA_ARCHITECTURES=70 -DSTRATA_BUILD_TESTS=ON` |
| Docker Image Tag | `strata-v100:stage12-0.1.66-stock` |
| Docker Image ID | `sha256:5ee459198a4b9c695183bf5901c17ff6b68019381c6b70c72a138fb76d27e93d` |
| Binary Path | `/opt/strata/engine/strata` |
| Binary SHA256 | `79076b85b0450c86edb5c7bbee54a4c60cd00f564e9adb7058d9e00bc3b50c49` |
| Dynamic Linkage (`ldd`) | `libcudart.so.12`, `libcublas.so.12`, `libcublasLt.so.12` (no CUDA 13 libs) |

- **Built Targets (26):** Same as `0.1.67` minus `gr_write_norm_parity` (introduced in `0.1.67` `#6776`).
- **`cuobjdump` / ISA Guard / `no_mmq_symbols`:** `sm_70` cubins confirmed (`strata.1.sm_70.cubin`..`strata.40.sm_70.cubin`+); `isa_guard_check` passed (`890` functions, `170` wide-ISA, `0` not allowed); `objdump` matched `311` functions all in runtime-CPUID-guarded dispatch paths; `no_mmq_symbols` passed.

### 3.2 CPU CTest Results (`0.1.66`)

- **20/23 Passed, 2 Failed, 1 Skipped:**
  - **Failed (2):** `pool_determinism` (`294 format pairs, 120945 checks, 222 failures`: `gu 12 down 2` gate/up rows differ), `pool_determinism_dep_off` (`294 format pairs, 53570 checks, 188 failures`: `gu 12 down 2` gate/up rows differ) — fixed in `0.1.67` (`#6754`, commit `cd6600bb`).
  - **Skipped (1):** `cuda_spill_guard` (`***Skipped`, exit `77`; NOT a PASS) due to `libstrata_pf_fp4.a` stub having no device code on CUDA 12.9 / `sm_70` and `tools/cuda_spill_baseline.json` lacking an `sm_70` baseline.

### 3.3 GPU Parity Results (`0.1.66`) & `15:35 KST` Power-Loss History

- **CTest GPU suite (`14` tests, run prior to `15:35 KST` incident on `--gpus device=0`):** **14/14 Passed** (`Total Test time (real) = 215.23 sec`, `0` failed, `0` skipped): `qsa_merge_daily_parity_{default,daily}`, `native_grouped_parity`, `native_i8_parity`, `pf_wmma_parity`, `native_multi_parity`, and all 8 `native_expert_parity_v31_*` variants (`results/stage12/builds/0.1.66-stock/ctest-gpu.log` truncated at test `10/14` due to pipe buffering before reset; full `14/14` summary captured on SSH stdout).
- **`15:35 KST` Host Power-Off / Reboot Incident (Historical Record):**
  - Immediately after `ctest` finished (~`15:34:38 KST`), `/opt/strata/build-stage12/qsa_prompt_attn_parity` was invoked with **no CLI arguments**, defaulting (`engine/src/kernels/qsa_prompt_attn_parity.cpp:365-367`) to an unbounded `ctx=32768, nq=2048, reps=5` back-to-back Tensor Core + FP32 prompt-attention burst.
  - At ~`15:35 KST`, **`p520-llm` abruptly lost power and rebooted** (boot timestamp `2026-11-25T15:35:30+09:00`; `journalctl -b -1` and `/var/log/kern.log` show zero shutdown messages/panics after `15:34:05 KST`, consistent with an instantaneous PSU overcurrent/power trip).
  - Harness fix committed at `ad801fa`: `scripts/136-stage12-build.py` now bounds `qsa_prompt_attn_parity` to `["8192", "512", "2"]`, removes un-fixtureable `dflash2_parity` without args, and directly audits `libstrata_pf_own.a` spills on `sm_70`.
- **Resumed Bounded Direct GPU Check on `0.1.66` (`--gpus device=0`, saved to `results/stage12/builds/0.1.66-stock/ctest-gpu-bounded.log`):**
  - **`qsa_prompt_attn_parity 8192 512 2`:** **`FAILURES: 0`** (INT8 IMMA/v2 and FP16 PASS across `ctx=8192`, `1500`, `2100` with identical checksums `9b7ca72c4363175e`, `3f7311fe9798c2e9`, `71e53de9e6ee2bd6`, `9ad8786db03e394a`; Q4_0 skipped on `sm_70`).
  - **`dflash2_q4_parity`:** **`PASS: 40 of 40 cases match the CPU reference`**.

---

## 4. Final Post-Verification Host State (`p520-llm`)

Verified after all `0.1.67` and `0.1.66` Gate A checks completed:
- **GPUs:** Both Tesla V100s completely idle (`0 MiB / 16384 MiB`, `135 MHz`, `38°C / 38°C`, no compute apps).
- **Policies preserved:** `power.limit = 150.00 W` on both GPUs; `v100-clock-lock.service` active (`gpuClkMin 135, gpuClkMax 1245`).
- **Containers & Images:** `docker ps` empty; `p520-llm-a` and `p520-llm-b` remain `Exited (0)` (alongside preserved `archive-*` containers); `strata-v100:stage12-0.1.66-stock` and `strata-v100:stage12-0.1.67-stock` built and intact alongside all `strata-v100:stage11x-*` images.
