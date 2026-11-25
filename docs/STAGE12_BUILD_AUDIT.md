# Stage 12 — Build & Parity Gate Audit (`S12-A1`)

> **Date:** 2026-11-25 KST  
> **Host:** `p520-llm` (Dual Tesla V100-SXM2-16GB, Xeon W-2135, 64 GB RAM)  
> **Gate A Status:** **HALTED (`STOP/FAIL` — Unexpected host power-off/reboot during `0.1.66` `qsa_prompt_attn_parity`)**  
> **`0.1.66` Build:** Built (`strata-v100:stage12-0.1.66-stock`), CPU `20/23` pass (`2` fail, `1` skip), GPU CTest `14/14` pass, aborted during `qsa_prompt_attn_parity`  
> **`0.1.67` Build:** **NOT EXECUTED** (halted after P520 power-off incident per `docs/STAGE12_PLAN.md` §6 Rule 4)

---

## 1. Preflight Verification (`scripts/135-stage12-prepare.py`)

Executed on `p520-llm` at `2026-11-25T15:05:26.902862+09:00` (initial boot ID `63452ec5-05f7-4a66-94a4-9be2af98c311`):

- **Verdict:** `PREPARATION_PASS_NOT_C2`
- **Serving containers:** `p520-llm-a` = `exited`, `p520-llm-b` = `exited`
- **GPU policy:** `power.limit = 150 W` on both GPUs, `v100-clock-lock.service` active (`gpuClkMin 135, gpuClkMax 1245`)
- **Assets:** 15 assets verified; DFlash2 pack SHA256 `4a42b98220ea7880664002c8edda1563aecbae754b762a2e2f31b2b91ee93ecd`; harness SHA256 `a8e42cc5a71421a7287618fd5be0332ae40f312426e4d243ce1c7619fdfc5246`; manifest SHA256 `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`
- **Disk free:** `183,628,029,952` bytes

---

## 2. `0.1.66` Stock Build (`strata-v100:stage12-0.1.66-stock`)

### 2.1 Provenance & Toolchain

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

- **Built Targets (26):** `strata`, `native_arithmetic_parity`, `pool_determinism`, `iq_avx2_parity`, `iq_avx1_parity`, `q8k_quant_parity`, `q2_bitplane_parity`, `quant_selftest`, `quant_parity`, `type_geometry_oracle`, `native_expert_parity`, `native_multi_parity`, `native_grouped_parity`, `native_i8_parity`, `pf_wmma_parity`, `qsa_prompt_attn_parity`, `qsa_merge_daily_parity`, `dflash2_parity`, `dflash2_q4_parity`, `file_expert_source_test`, `nv_defaults_test`, `tail_skip_default_test`, `lookup_default_test`, `adapt_async_default_test`, `cgroup_mem_test`, `cgroup_cpu_test`.
- **Missing Targets Expected in `0.1.66`:** `gr_write_norm_parity` (introduced in `0.1.67` `#6776`); the 4 `native_arithmetic_parity_*` and `pool_determinism_dep_off` names are CTest test aliases invoking the compiled `native_arithmetic_parity` and `pool_determinism` binaries.

### 2.2 `cuobjdump` & CPU ISA Guard Verification

- **`cuobjdump --list-elf /opt/strata/engine/strata`:** Confirmed `strata.1.sm_70.cubin` through `strata.40.sm_70.cubin`+ (`sm_70` cubins present).
- **`isa_guard_check` (`tools/check_isa_guard.py /opt/strata/build-stage12/libstrata_kernels_cpu.a`):** **Passed** (`890 functions, 170 hold wide-ISA instructions, 0 not allowed`).
- **`objdump -d -C /opt/strata/engine/strata`:** Disassembly matched `311` functions containing `vpdpbusd` / `vpdpwssd` / `vpermb` / `vpermi2b` / `vpmultishiftqb`; all inspected symbols belong to runtime-CPUID-guarded wide-ISA dispatch paths (`strata::kernels::cpu::s2_expert_vnni_*`, `q2_0_gguf_rows_multi`, `iq_avx512.cpp` anonymous namespace `row_dot<...>`, `vnni::rows_nt`).
- **`no_mmq_symbols`:** **Passed** (`libstrata_kq.so` absent; no MMQ symbols linked).

### 2.3 CPU CTest Gate Results (`0.1.66`)

`scripts/136-stage12-build.py` aborted with `ctest` exit status `8` (`results/stage12/builds/0.1.66-stock/progress.json` remained at `"phase": "building"`, and `ctest-cpu.log` was not written by the script). Running the exact 23-test CPU CTest selection directly inside `strata-v100:stage12-0.1.66-stock` yielded:

| Outcome | Count | Tests |
|---|---:|---|
| **Passed** | **20** | `file_expert_source_test`, `nv_defaults_test`, `adapt_async_default_test`, `lookup_default_test`, `tail_skip_default_test`, `cgroup_mem_test`, `cgroup_cpu_test`, `native_arithmetic_parity`, `native_arithmetic_parity_avx`, `native_arithmetic_parity_mt1`, `native_arithmetic_parity_no512`, `native_arithmetic_parity_ggml`, `iq_avx1_parity`, `iq_avx2_parity`, `q8k_quant_parity`, `quant_selftest`, `quant_parity`, `q2_bitplane_parity`, `isa_guard_check`, `no_mmq_symbols` |
| **Failed** | **2** | `pool_determinism` (`294 format pairs, 120945 checks, 222 failures`: `gu 12 down 2` gate/up rows differ), `pool_determinism_dep_off` (`294 format pairs, 53570 checks, 188 failures`: `gu 12 down 2` gate/up rows differ) |
| **Skipped** | **1** | `cuda_spill_guard` (`***Skipped`, exit `77`; NOT a PASS) |

#### Root Causes Observed in `0.1.66` CPU Tests
1. **`pool_determinism` / `pool_determinism_dep_off` failure (`gu 12 down 2`):** `0.1.66` `pool_determinism.cpp:63` compares floats with `std::memcmp` and fails on `Q4_K` (`gu 12`) + `Q4_0` (`down 2`) on AVX2-only CPUs; upstream `0.1.67` commit `cd6600bb` (`#6754`) specifically fixes NaN equality and the `Q4_K` gate/up check on AVX2-only CPUs.
2. **`cuda_spill_guard` skip (`exit 77`):**
   - `engine/cmake/backends/cuda.cmake:299` passes `libstrata_pf_fp4.a` to `tools/check_cuda_spills.py`, but on CUDA 12.9 / `sm_70` `libstrata_pf_fp4.a` is built from `*_absent.cpp` stubs and contains no device code (`cuobjdump info: File '.../libstrata_pf_fp4.a' does not contain device code`), causing `check_cuda_spills.py` to return `77` (`SKIP_RETURN_CODE`).
   - Additionally, `tools/cuda_spill_baseline.json` contains baselines only for `sm_120, sm_75, sm_86` and **no baseline for `sm_70`** (`check_cuda_spills.py` reported `475` unbaselined stack violations in `libstrata_kernels.a`, `8` in `libstrata_prefill.a`, `6` in `libstrata_qwen35.a`, `0` in `libstrata_pf_own.a`).

### 2.4 GPU Parity Results (`0.1.66`) & Power-Loss Incident

Because `136-stage12-build.py` halted on the CPU CTest failure, the GPU CTest suite + direct GPU executables were invoked on `--gpus device=0` to collect `0.1.66` GPU parity data:

- **CTest GPU suite (`14` tests):** **14/14 Passed** (`Total Test time (real) = 215.23 sec`, 0 failed, 0 skipped):
  `qsa_merge_daily_parity_default`, `qsa_merge_daily_parity_daily`, `native_grouped_parity`, `native_i8_parity`, `pf_wmma_parity`, `native_multi_parity`, and all 8 `native_expert_parity_v31_iq{2_xxs,2_xs,2_s,3_xxs}_{q2_0,iq4_nl}` variants.
  *(Note: on-disk `results/stage12/builds/0.1.66-stock/ctest-gpu.log` was truncated at test `10/14` due to pipe buffering prior to the abrupt host reset; full `14/14` pass summary was captured on SSH stdout before `qsa_prompt_attn_parity` launched.)*
- **Direct GPU executable `qsa_prompt_attn_parity` -> HOST POWER-OFF / REBOOT:**
  - Immediately after `ctest` finished (~`15:34:38 KST`), `/opt/strata/build-stage12/qsa_prompt_attn_parity` started with **no CLI arguments**.
  - Inside `engine/src/kernels/qsa_prompt_attn_parity.cpp:365-367`, omitting CLI arguments defaults to `ctx=32768, nq=2048, reps=5` (whereas `sycl/CMakeLists.txt:588` passes `8192 512 2`, and `strata_gpu_engine.cmake` does not register it as a default CTest). At `32768 x 2048 x 5`, `qsa_prompt_attn_parity` executes back-to-back full-chunk Tensor Core (`qsa_prompt_attn_batch`, IMMA/v2) and FP32 prompt-attention bursts across INT8 and FP16 KV pools.
  - At ~`15:35 KST`, **`p520-llm` abruptly lost power and rebooted** (new kernel boot timestamp `2026-11-25T15:35:30+09:00`; `journalctl -b -1` and `/var/log/kern.log` show zero shutdown messages, oops, or kernel panics after `15:34:05 KST`, consistent with an instantaneous PSU overcurrent/power trip similar to the Stage 10 `16384`-token prefill trip).
- **Additional script bug found in `scripts/136-stage12-build.py`:**
  - `DIRECT_GPU_EXES` (`scripts/136-stage12-build.py:35`) runs `qsa_prompt_attn_parity` with no args (defaulting to unsafe `32768 2048 5` burst instead of bounded e.g. `8192 512 2`) and runs `dflash2_parity` with no args (`src/core/dflash2_parity.cpp:23` requires `<pack> <case.bin> [rounds]` and exits `2` without them).

---

## 3. `0.1.67` Stock Build Status (`strata-v100:stage12-0.1.67-stock`)

- **Status:** **NOT BUILT / NOT TESTED.**
- Per `docs/STAGE12_PLAN.md` §6 Rule 4 (**STOP/FAIL**: immediately halt experiments on power loss/instability, preserve evidence, no automatic retries, and no resumption of high load without separate root-cause investigation and approval), `0.1.67` was not started after the `15:35 KST` reboot.

---

## 4. Post-Reboot Host Verification (`p520-llm`)

Verified read-only at `15:46–15:48 KST` after reboot:
- **Uptime:** Up ~11–13 min (booted `15:35:30 KST`).
- **GPUs:** Both Tesla V100s idle (`0 MiB / 16384 MiB`, `0%`, `34C / 37C`, `25W / 150W`, `135 MHz`).
- **Policies preserved:** `power.limit = 150.00 W` on both GPUs; `v100-clock-lock.service` active (`gpuClkMin 135, gpuClkMax 1245` applied on boot at `15:35:39 KST`).
- **Containers & Images:** `docker ps` empty; `p520-llm-a` and `p520-llm-b` remain `exited`; all historical `strata-v100:stage11x-*` images intact; `strata-v100:stage12-0.1.66-stock` (`sha256:5ee459198a4b9c695183bf5901c17ff6b68019381c6b70c72a138fb76d27e93d`) retained on P520.

---

## 5. Required Actions Before Resuming `S12-A1`

1. **User/Owner Review & Approval:** Acknowledge the `15:35 KST` hard reboot during `qsa_prompt_attn_parity` (`32768 x 2048 x 5`) and authorize resuming Gate A.
2. **Fix `scripts/136-stage12-build.py` (Stage 12 harness only):**
   - Pass bounded safe arguments to `qsa_prompt_attn_parity` (e.g. `["8192", "512", "2"]` matching `sycl/CMakeLists.txt`, or `4096 512 1`) — never bare `32768 2048 5` on P520 V100.
   - Remove or provide a valid fixture `<pack> <case.bin>` for `dflash2_parity` (and note `dflash2_q4_parity` takes no args).
   - Fail explicitly if `"Skipped"` appears in `ctest-cpu.log` (or record `cuda_spill_guard` as an expected upstream `sm_70` skip only if explicitly waived by Gate A, noting `skip != PASS`).
3. **Complete `0.1.67` (`d46f5f268f8ed797e83a5c63a69bffbd7a581cf6`) Build & Parity:** Re-verify `pool_determinism` (`#6754`) and `gr_write_norm_parity` (`#6776`) under approved bounded GPU parity settings.
