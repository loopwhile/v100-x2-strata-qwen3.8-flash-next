# Stage 11X Gate C Step 1: CPU Expert Parity & Microbenchmark Report (`cpu-microbench-20261119T060426`)

- **Host CPU**: Intel Xeon W-2135 (6 physical cores / 12 threads, Skylake-W; `avx512f`, `avx512dq`, `avx512cd`, `avx512bw`, `avx512vl`; NO `avx512vnni`, NO `avx512vbmi`, NO `avx512vpopcntdq`; `intel_pstate` / `powersave`, `no_turbo=1`, 8.25 MiB L3, quad-channel DDR4).
- **Arena**: Authentic 48-layer `IQ3_XXS` GGUF expert arena (`192` experts, `319.7 MiB` > `8.25 MiB` L3), compiled with exact `0.1.59` `/opt/strata/build-stage9/build.ninja` flags (`-O3 -DNDEBUG -std=c++20`), with `iq_avx512.cpp` and `expert.cpp` compiled **without** `-mavx512vnni`, `-mavx512vbmi`, or `-mavx512vpopcntdq`.
- **ISA Guard & Disassembly Verification**:
  - `check_isa_guard.py`: `850 functions, 180 hold wide-ISA instructions, 0 not allowed` (`PASS`).
  - `objdump -d` on `iq_avx512.cpp.o` and `expert.cpp.o`: `0` forbidden instructions (`vpdp*`, `vpmultishift*`, `vpopcnt*`, `vpermb*`), `12,884` ZMM instructions in `iq_avx512.cpp.o`, `4,131` ZMM instructions in `expert.cpp.o`.
  - Host `perf_event_paranoid=4` (and no `perf` binary inside container); hardware PMU counters were not read unprivileged. Clock (`3300 MHz`), CPU utilization (`300%` across 3 threads), and wall timings were recorded cleanly.

## 1. Resolution of Earlier Discrepancy (`task-287` vs `task-387` vs `task-399`)

- Earlier microbenchmark runs called `ExpertPool(pool_workers, true, true)` without pinning the host thread (`cpu::pin_current_thread(cpu::planned_host_core())`), unlike production (`src/core/session.cpp:558`).
- Under `--cpuset-cpus="0-2,6-8"`, the unpinned host thread frequently landed on CPUs `1, 2, 7, 8` (colliding on physical cores 1 and 2 with the two pinned pool workers), inflating `win_48L` by ~`1.62x` (`35 ms -> 56 ms`, `28 ms -> 46 ms`). In `task-399`, `PathA` and `PathB1d+B2` experienced core collision (`55.7 ms`, `45.4 ms`) while `PathC4` happened to avoid collision (`27.8 ms`).
- Pinning the host thread to `planned_host_core()` (`0` for A, `3` for B), removing `getenv` from hot loops (`strata_cpu_reload_env()`), and linking all 17 `libstrata_kernels_cpu.a` objects cleanly eliminated variance (<1% spread across repeats).

## 2. Parity Results (10 Representative `(gu_type, d_type)` Pairs, `nt=1..4`, Real GGUF Weights)

All 15 configurations passed numerical parity (`max_abs_diff <= 2.980e-08`, `max_rel_l2 <= 3.013e-07`):
- `PathA_Baseline_0.1.59`: `256000/256000` bit-exact (`0.000e+00`)
- `PathB1b_AVX2_Exact1`: `256000/256000` bit-exact (`0.000e+00`)
- `PathB1d_B2_Combined_Gather`: `140177/256000` bit-exact, `max_abs=2.608e-08`, `max_rel_l2=2.180e-07`
- `PathC4_AVX512BW_IQ_Q2Bitplane`: `136403/256000` bit-exact, `max_abs=2.608e-08`, `max_rel_l2=2.665e-07`
- `PathC7_Hybrid_512BW_IQ2S_AVX2_Q2BP`: `139346/256000` bit-exact, `max_abs=2.608e-08`, `max_rel_l2=2.665e-07`

## 3. Single-Agent & Synchronized Dual-Agent Concurrent Results (`spec8_mix_2x1_1x2`, 3 Reps)

| Config | Single `win_48L` (ms) | Single `us/exp` / `GB/s` | Dual A `win_48L` (ms) | Dual B `win_48L` (ms) | Dual Mean `us/exp` / `GB/s` | Delta vs PathA |
|---|---:|---:|---:|---:|---:|---:|
| `PathA_Baseline_0.1.59` | `35.11` | `243.8` / `7.16` | `35.08` | `34.61` | `242.0` / `7.22` | `0.0%` |
| `PathB1a_AVX2_MT1` | `34.83` | `241.9` / `7.22` | `34.68` | `34.21` | `239.2` / `7.30` | `-1.1%` |
| `PathB1b_AVX2_Exact1` | `34.97` | `242.9` / `7.19` | `35.11` | `34.43` | `241.5` / `7.23` | `-0.2%` |
| `PathB1c_Fork_NT1` | `34.88` | `242.2` / `7.21` | `34.97` | `33.96` | `239.4` / `7.30` | `-1.1%` |
| `PathB1d_AVX2_MT1_Gather` | `31.44` | `218.3` / `8.00` | `31.33` | `30.39` | `214.3` / `8.15` | `-11.4%` |
| `PathB2_Q2_Bitplane` | `32.18` | `223.5` / `7.81` | `32.17` | `32.00` | `222.8` / `7.84` | `-7.9%` |
| `PathB1a_B2_Combined` | `32.06` | `222.7` / `7.84` | `31.57` | `31.67` | `219.6` / `7.95` | `-9.2%` |
| `PathB1d_B2_Combined_Gather` | `28.68` | `199.1` / `8.77` | `28.45` | `28.41` | `197.5` / `8.85` | `-18.4%` |
| `PathC1_AVX512BW_MT2` | `39.22` | `272.4` / `6.41` | `38.91` | `39.12` | `271.0` / `6.45` | `+12.0%` |
| `PathC2_AVX512BW_MT1` | `43.93` | `305.1` / `5.72` | `43.93` | `43.38` | `303.2` / `5.76` | `+25.3%` |
| `PathC3_AVX512BW_MT1_Gather` | `34.07` | `236.6` / `7.38` | `33.92` | `33.54` | `234.3` / `7.46` | `-3.2%` |
| `PathC4_AVX512BW_IQ_Q2Bitplane` | `28.23` | `196.0` / `8.91` | `28.11` | `28.00` | `194.8` / `8.97` | `-19.5%` |
| `PathC5_AVX512BW_IQ_NoGather_Q2BP` | `38.15` | `265.0` / `6.59` | `38.03` | `37.74` | `263.1` / `6.64` | `+8.8%` |
| `PathC6_AVX2_IQ_AVX512BW_Q2` | `34.67` | `240.8` / `7.25` | `33.69` | `34.39` | `236.4` / `7.39` | `-2.3%` |
| **`PathC7_Hybrid_512BW_IQ2S_AVX2_Q2BP`** | **`26.96`** | **`187.2` / `9.33`** | **`26.20`** | **`26.74`** | **`183.9` / `9.50`** | **`-24.0%`** |

## 4. Winner Selection

- **Selected Winning Path for `S11X-D1`**: **`PathC7_Hybrid_512BW_IQ2S_AVX2_Q2BP`** (`STRATA_AVX512BW_IQ=22`, `STRATA_IQ_MT_MIN=1`, `STRATA_IQ_GATHER=1`, `STRATA_IQ256_GATHER=1`, `STRATA_Q2_BITPLANE=1`).
- **Why**:
  1. `Q2_0` (30/48 down layers): AVX2 Bitplane (`STRATA_Q2_BITPLANE=1`) beats both legacy AVX2 and non-VNNI AVX-512BW by `~45 us/expert`.
  2. `IQ2_XXS (16), IQ2_XS (17), IQ3_XXS (18), IQ3_S (21)` (38/48 gate/up layers): AVX2 (`STRATA_IQ_MT_MIN=1 + STRATA_IQ256_GATHER=1`) beats non-VNNI AVX-512BW by `15–40 us/expert`.
  3. `IQ2_S (22)` (10/48 gate/up layers): non-VNNI AVX-512BW (`vpmaddubsw + vpmaddwd + vpgatherqd`) beats AVX2 by `~60 us/expert` (`125 us` vs `188 us`), with zero clock throttling (`3300 MHz` sustained on all 6 cores concurrently).
- **Receipts**: `results/raw/cpu-microbench-20261119T060426/` (`sha256-manifest.txt`).
