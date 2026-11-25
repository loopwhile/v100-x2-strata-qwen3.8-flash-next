# Stage 12 — Final Campaign Review (2026-11-25 KST)

> **Status:** **STAGE 12 COMPLETE (30/30 scored 128K C2 PASS + 1/1 diagnostic PASS + 4/4 A & 4/4 B semantic quality PASS on both `S12-F1` and `S12-C1T`).**  
> **Serving Policy:** **NO automatic production promotion.** `p520-llm-a` and `p520-llm-b` remain preserved in `Exited (0)` on the prior promoted `S11X-D2` release (`s11x-d2-20261119T095616`) pending explicit user promotion approval.

---

## 1. Executive Summary & Promotion Candidates

Stage 12 evaluated upstream Strata **v0.2.20 (`0.1.66`)** and **v0.2.21 (`0.1.67`)** plus selective ports from `S11X-D2` and `jmnargi/Strata-V100` (`v0.1.45.13`) on dual Tesla V100-SXM2-16GB (`sm_70`) + Xeon W-2135 (`IQ3_XXS`, `131,072` context, INT8 KV `--kv-resident 32768`, `--prefill auto:8192`, `--prompt-cache 0`, stock DFlash2 `--spec 8 --draft-conf 0.7 --draft-fallback none`, `135–1245 MHz` clock lock, `150 W` configured power caps).

A pivotal architectural finding separated **exact routing (`STRATA_ROUTE_TAIL_SKIP=0`, upstream default since `0.1.63`)** from `0.1.59`'s `--serve` default (`STRATA_ROUTE_TAIL_SKIP=7`). Under exact routing, `S12-F1` achieved `1032.7 / 1043.2 tok/s` prefill and `31.6 / 35.9 tok/s` decode (`4/4 A & 4/4 B` semantic quality PASS). Under controlled same-route parity (`STRATA_ROUTE_TAIL_SKIP=7`), `S12-C1T` achieved **`1039.4 / 1046.8 tok/s` prefill** and **`41.3 / 45.2 tok/s` decode** (`+4.2 / +4.2 tok/s` over `S11X-D2`, all batches `>= 40.4 / 44.3 tok/s`, `4/4 A & 4/4 B` semantic quality PASS).

### Promotion Candidate Comparison vs `S11X-D2`

| Candidate | Engine / Patch | `ROUTE_TAIL_SKIP` | Prefill A / B (tok/s) | Decode A / B (tok/s) | TTFT A / B (s) | Delta vs `S11X-D2` (Prefill / Decode) | Quality Suite (`141`) |
|---|---|---:|---:|---:|---:|---|---|
| **`S11X-D2`** (`d2-20261119T003753`, Ref) | `0.1.59` + `stage11x-d2.patch` | `7` (default) | `1032.6 / 1037.0` | `37.1 / 41.0` | `123.21 / 122.69` | Baseline | N/A (prior promoted) |
| **`S12-F1`** (`f1-20261125T204131`) | `0.1.67` + `d1`+`d2`+`d3` | **`0` (exact)** | **`1032.7 / 1043.2`** | **`31.6 / 35.9`** | `123.21 / 121.97` | `+0.1 / +6.2` PF, `-5.5 / -5.1` DEC | **PASS (`4/4 A & 4/4 B`)** |
| **`S12-C1T`** (`c1t-20261125T205904`) | `0.1.67` + `d1`+`d2`+`d3` | **`7` (same-route)** | **`1039.4 / 1046.8`** | **`41.3 / 45.2`** | `122.40 / 121.54` | **`+6.8 / +9.8` PF, `+4.2 / +4.2` DEC** | **PASS (`4/4 A & 4/4 B`)** |

- **Exact-routing candidate (`S12-F1`)**: Best verified exact-routing configuration (`ROUTE_TAIL_SKIP=0`) on `0.1.67` with `#6776` (`gr_write_norm_rs`) accuracy fix, `#6747` `gdn_split` fix, `PathC7`, `MmapBounceRing`, `COLD_OVERLAP=5`, `HC_V100=1`, and `OOMD_ROOM=0`. Matches `S11X-D2` prefill (`+0.1 / +6.2 tok/s`) without approximate expert tail skipping; slower decode (`-5.5 / -5.1 tok/s`) solely reflects exact routing of tail experts (`hit_rate 0.773–0.798 / 0.819–0.829` vs `0.864–0.871 / 0.881–0.889` with `ROUTE_TAIL_SKIP=7`).
- **Same-route throughput champion (`S12-C1T`)**: Identical image/binary (`strata-v100:stage12-0.1.67-c1`, `sha256:33b61b0432e81c44a6d212ca38be46b4191a989a65c4a0141e2cbc9b116f10ec`) with `STRATA_ROUTE_TAIL_SKIP=7` restored to match `S11X-D2`. Exceeds `40 tok/s` simultaneously on both agents (`41.3 / 45.2 tok/s`, all 3 batches `>= 40.4 / 44.3 tok/s`) while holding `1039.4 / 1046.8 tok/s` prefill and passing `4/4 A & 4/4 B` quality checks. Because the engine flags `STRATA_ROUTE_TAIL_SKIP=7` as approximate routing (`"answers differ slightly"`), **promotion of either `S12-F1` or `S12-C1T` requires explicit user authorization**.

---

## 2. Full Stage 12 Candidate & Receipt Register

Source of truth: [bench/stage12-candidates.json](../bench/stage12-candidates.json), [artifacts/stage12-results-20261125/summary.md](../artifacts/stage12-results-20261125/summary.md), and per-run `metrics.json` receipts.

| Candidate | Gate | Raw ID | Engine / Image | Prefill A / B (tok/s) | Decode A / B (tok/s) | TTFT A / B (s) | Wall / Overlap (s) | Verdict |
|---|---|---|---|---:|---:|---:|---:|---|
| `S12-U0` | B | `u0-20261125T162444` | `0.1.66` stock (`5ee45919...`) | 876.5 / 881.7 | 21.3 / 24.2 | 145.12 / 144.28 | 234.89 / 68.82 | **PASS** (3/3) |
| `S12-U1` | B | `u1-20261125T164355` | `0.1.67` stock (`83a48e7d...`) | 877.1 / 880.5 | 21.9 / 22.2 | 145.04 / 144.48 | 230.72 / 60.59 | **PASS** (3/3) |
| `S12-R0` | B | `—` | `0.1.59` (`S11X-D2`) | — | — | — | — | **SKIPPED** (Option B) |
| `S12-P0` | B | `p0-20261125T170126` | `0.1.67` stock (diag) | 877.3 / 879.7 | 21.6 / 22.2 | 145.00 / 144.62 | 230.75 / 61.60 | **DIAG PASS** (1/1) |
| `S12-C0` | C | `c0-20261125T170951` | `0.1.67` stock + `OOMD_ROOM=0` | 1034.2 / 1040.5 | 21.9 / 22.3 | 123.04 / 122.30 | 206.72 / 60.51 | **PASS** (3/3) |
| `S12-D1` | C | `d1-20261125T174920` | `0.1.67` + `stage12-d1.patch` | 865.0 / 879.7 | 23.0 / 27.0 | 147.16 / 144.66 | 230.91 / 70.89 | **PASS** (3/3; b3 24.6/28.3) |
| `S12-D2` | C | `d2-20261125T182918` | `0.1.67` + `stage12-d2.patch` | 1012.3 / 1017.1 | 27.6 / 28.3 | 125.69 / 125.11 | 179.86 / 47.22 | **PASS** (3/3) |
| `S12-P1` | C | `p1-20261125T190921` | `0.1.67` + `stage12-p1.patch` | 1014.3 / 1021.7 | 23.1 / 24.2 | 125.44 / 124.54 | 217.18 / 79.01 | **PASS** (3/3; b3 1031.4/1037.1) |
| `S12-D3` | C | `d3-20261125T194836` | `0.1.67` + `stage12-d3.patch` | 894.9 / 898.9 | 21.8 / 21.1 | 142.19 / 141.52 | 239.11 / 66.47 | **PASS** (3/3; b3 22.6/22.6) |
| `S12-C1` | D | `c1-20261125T202739` | `0.1.67` + `d1`+`d2`+`d3` | 965.9 / 970.6 | 30.8 / 34.7 | 131.73 / 131.09 | 195.72 / 46.42 | **PASS** (3/3; b3 31.7/34.7) |
| `S12-F1` | D | `f1-20261125T204131` | `0.1.67` + `d1`+`d2`+`d3` | 1032.7 / 1043.2 | 31.6 / 35.9 | 123.21 / 121.97 | 184.47 / 46.56 | **PASS** (3/3 + Quality 4/4) |
| `S12-C1T` | D | `c1t-20261125T205904` | `0.1.67` + `d1`+`d2`+`d3` | 1039.4 / 1046.8 | 41.3 / 45.2 | 122.40 / 121.54 | 165.99 / 42.54 | **PASS** (3/3 + Quality 4/4) |

---

## 3. Gate A: Source, ISA Mapping, Builds & `15:35 KST` Power-Off Incident

Full details in [STAGE12_SOURCE_AUDIT.md](STAGE12_SOURCE_AUDIT.md) and [STAGE12_BUILD_AUDIT.md](STAGE12_BUILD_AUDIT.md).

1. **`S12-A0` (Source & ISA Audit)**:
   - Pinned git SHAs: `0.1.66` (`v0.2.20`, `a34979fc94f3d126b9bb8210f4ad311345688b52`), `0.1.67` (`v0.2.21`, `d46f5f268f8ed797e83a5c63a69bffbd7a581cf6`), `fork_v100` (`v0.1.45.13`, `49c6cc6fd11291c128a7a62287b50e79d59e247b`).
   - Verified engine reorganization into `engine/` and `terminal/`, mandatory `-DSTRATA_EXPERIMENTAL_SM60=ON -DCMAKE_CUDA_ARCHITECTURES=70` under CUDA `12.9.1` (no CUDA 13), `#6776` (`gr_write_norm_rs` bit-exact shared-memory summation fix in `0.1.67`), `#6747` (`STRATA_GDN_SPLIT` crash guard in `0.1.67`), `#5199` 16.5 GiB bare `--prefill auto` cap (still explicitly locked `--prefill auto:8192`), `i8h_volta` (`TUNE-0216`) replacing `PF_WMMA`, `EXP_MODE=8` via `sm_70` `nv_defaults` across all 48 MoE layers, `STRATA_ROUTE_TAIL_SKIP=0` default since `0.1.63`, and zero AVX-512 usage on Xeon W-2135 (safe `AVX2` fallback due to `cpu_vnni_ok() == false` and zero callers of `cpu_avx512bw_ok()`).
   - Identified `STRATA_HC_V100=1` (`sm_70` K-split down + fused HC read `T<=6`) in `fork_v100` (`v0.1.45.13`, MIT-licensed) as a clean Gate C candidate.
2. **`S12-A2` (`S11X-D2` 19-Override & 4-Hunk Mapping)**:
   - Classified all 19 `S11X-D2` env overrides into `KEEP` (6), `UPSTREAM-EQUIVALENT` (2: `SM70_TABLE`, `SIDE_MIXER`), `REPLACE` (1: `PF_WMMA=1` kills `i8h_volta` in `0.1.67`), `REBASE` (8: `PF_WMMA2/LEAN/SKINNY`, `AVX512BW_IQ`, `IQ_MT_MIN`/wait-free `IQ_GATHER`, `MMAP_ADAPT_ASYNC`, `COLD_OVERLAP=5`), and `DROP` (2: `GU_SWIGLU`, `QSA_ROWS`).
   - Enforced zero silent `S11X-D2` overrides in Gate B (`S12-U0`/`S12-U1`).
3. **`S12-A1` (Independent Builds, Parity & `15:35 KST` Incident)**:
   - **`0.1.66` (`strata-v100:stage12-0.1.66-stock`, `sha256:5ee459198a4b9c695183bf5901c17ff6b68019381c6b70c72a138fb76d27e93d`, engine `79076b85b0450c86edb5c7bbee54a4c60cd00f564e9adb7058d9e00bc3b50c49`)**: CPU CTest `20/23` (`pool_determinism` & `pool_determinism_dep_off` failed `#6754`, `cuda_spill_guard` skipped), GPU CTest `14/14 PASS`, bounded `qsa_prompt_attn_parity 8192 512 2` (`FAILURES: 0`), `dflash2_q4_parity` (`40/40 PASS`).
   - **`15:35 KST` Power-Off Incident & Fix**: Immediately after `0.1.66` GPU CTest (`~15:34:38 KST`), invoking `/opt/strata/build-stage12/qsa_prompt_attn_parity` with no CLI arguments triggered its default `ctx=32768, nq=2048, reps=5` tensor-core/FP32 burst, tripping host PSU over-current protection (`p520-llm` rebooted at `2026-11-25T15:35:30+09:00`). Harness fix committed at `ad801fa` (`scripts/136-stage12-build.py`): explicitly passes bounded `["8192", "512", "2"]` to `qsa_prompt_attn_parity`, removes un-fixtureable bare `dflash2_parity`, and audits `libstrata_pf_own.a` spills directly (`167` `sm_70` kernels, `0` spills).
   - **`0.1.67` (`strata-v100:stage12-0.1.67-stock`, `sha256:83a48e7dc321a72e0a13642668a887d179d630d2ff4dd204fd49cb7f674c3b6e`, engine `acfe6d530bc970514d0f57c3f5a87fd5b0b77a2666f8bf4095f1ebd33bb0b447`)**: CPU CTest `22/22 PASS` (`0` skip, `#6754` fixed), GPU CTest `15/15 PASS` (`0` skip, `#6776` `gr_write_norm_parity` PASS), `isa_guard_check` PASS (`890` functions, `0` disallowed), `cuobjdump` `58` `sm_70` cubins, `pf_own_spill_audit` PASS (`167` kernels, `0` spills), bounded `qsa_prompt_attn_parity 8192 512 2` (`FAILURES: 0`), `dflash2_q4_parity` (`40/40 PASS`).

---

## 4. Gate B: Stock Baselines (`S12-U0`, `S12-U1`), `S12-R0` Disposition & `S12-P0` Profiling

- **`S12-U0` (`u0-20261125T162444`, `0.1.66` stock, 3/3 PASS)**: Medians `876.5 / 881.7 tok/s` prefill, `21.3 / 24.2 tok/s` decode, `145.12 / 144.28 s` TTFT (`batch-1..3` OS reads `28.8–23.4 / 30.2–24.7 GB`, expert hit `0.769–0.775 / 0.820–0.832`, DFlash2 acc `83.25–85.45% / 78.43–80.88%`).
- **`S12-U1` (`u1-20261125T164355`, `0.1.67` stock, 3/3 PASS)**: Medians `877.1 / 880.5 tok/s` prefill, `21.9 / 22.2 tok/s` decode, `145.04 / 144.48 s` TTFT (`batch-1..3` OS reads `23.1–23.9 / 24.2–25.0 GB`, expert hit `0.783–0.791 / 0.787–0.788`, DFlash2 acc `80.49–80.61% / 82.78–83.71%`).
- **`S12-R0` (`SKIPPED_OPTION_B_LARGE_GAP`)**: Stock `0.1.66`/`0.1.67` trailed `S11X-D2` by `-155.5 / -156.5 tok/s` prefill and `-15.2 / -18.8 tok/s` decode, and `U1` logs + `P0` immediately accounted for the entire gap (`oomd_pacer` cache wipe, missing `PathC7`, missing `MmapBounceRing`, and `ROUTE_TAIL_SKIP=0` exact routing). Under Option B, re-running `S11X-D2` as `S12-R0` was skipped to focus GPU budget on `S12-P0` and Gate C fixes.
- **`S12-P0` (`p0-20261125T170126`, `DIAGNOSTIC_PASS_NOT_SCORED`)**: Diag throughput `877.3 / 879.7 tok/s` prefill, `21.6 / 22.2 tok/s` decode, `145.00 / 144.62 s` TTFT, `23,769.3 / 24,337.8 MB` OS read:
  - **Prefill (`126,966 / 126,967` tokens, GPU timeline `143,815 / 143,417 ms`, wall `143,848 / 143,451 ms`, host staging `112,393 / 111,518 ms`)**: `gemm gate/up` `52,385 / 52,228 ms` (`36.4%`), `dequant` `38,538 / 38,494 ms` (`26.8%`), `qsa attn` `9,517 / 9,692 ms` (`6.6% / 6.8%`), `qsa select` `6,257 / 6,340 ms` (`4.4%`), `gdn` `5,904 / 5,954 ms` (`4.1% / 4.2%`), `wait copy` `4,131 / 3,701 ms` (`2.9% / 2.6%`), `combine` `938 / 939 ms` (`0.7%`).
  - **Decode (`509 / 742` windows, `2.61 / 2.58` tok/win)**: `121.25 / 116.23 ms/win` = `verify 98.07 / 94.80 ms` (incl. `CPU 71.63 / 68.58 ms`, `jobs 2.60 / 2.72 ms`, `GPU-reach wait 21.16 / 21.04 ms`) + `adapt join 20.04 / 18.36 ms` + `draft 2.90 / 2.85 ms` (`GPU waitCPU 74.30 / 69.71 ms/win`, expert cache hit `79.1% / 78.9%`, `47.6 / 45.6` swaps/win).

---

## 5. Gate C: Root-Cause Fixes & Single-Feature Port Screening

1. **`S12-C0` (`c0-20261125T170951`, `STRATA_OOMD_ROOM=0`) — 45 GB Cache-Wipe Fix**:
   - `U1` container logs revealed `terminal/serve/oomd_pacer.py:make_room()` (`in_container()` path) issuing `posix_fadvise(POSIX_FADV_DONTNEED)` before launch and evicting up to `45 GB` of warm model page cache (`[strata] memory guard: freed 45 GB of memory...`), forcing `23.1–25.0 GB` of NVMe re-reads per agent in every batch of `U0`/`U1`/`P0`.
   - Setting `STRATA_OOMD_ROOM=0` disabled `make_room()` cache eviction, dropping OS reads to `953.2–1168.8 / 394.4–473.9 MB` and restoring Prefill from `877.1 / 880.5` to **`1034.2 / 1040.5 tok/s`** (`TTFT 123.04 / 122.30 s`) on stock `0.1.67` (`i8h_volta`)—already matching `S11X-D2` prefill (`1032.6 / 1037.0`). Decode remained `21.9 / 22.3 tok/s`.
2. **`S12-D1` (`d1-20261125T174920`, `stage12-d1.patch`) — Rebased CPU `PathC7` (`AVX512BW` non-VNNI)**:
   - Image `sha256:9d5f6364...`, engine `d1010753...`; passed `22/22` CPU + `15/15` GPU + W-2135 `PathC7` parity.
   - Medians `865.0 / 879.7 tok/s` prefill, `23.0 / 27.0 tok/s` decode (`TTFT 147.16 / 144.66 s`). Post-docker-build cold page cache caused `16.2–49.9 GB` OS reads in `batch-1`/`batch-2`; warm `batch-3` reached `953.4 / 952.8 tok/s` prefill and **`24.6 / 28.3 tok/s` decode** (`+2.7 / +6.0 tok/s` over `C0`). Retained for `S12-C1`.
3. **`S12-D2` (`d2-20261125T182918`, `stage12-d2.patch`) — `MmapBounceRing` + `COLD_OVERLAP=5`**:
   - Image `sha256:922ba4eb...`, engine `6082be37...`; passed `22/22` CPU + `15/15` GPU + `file_expert_source_test`.
   - Eliminated synchronous `18–20 ms/win` `adapt join` stall: medians **`1012.3 / 1017.1 tok/s` prefill**, **`27.6 / 28.3 tok/s` decode** (`+5.7 / +6.0 tok/s` over `C0`, `batch-3` `27.6 / 29.0`), `TTFT 125.69 / 125.11 s`. Retained for `S12-C1`.
4. **`S12-P1` (`p1-20261125T190921`, `stage12-p1.patch`) — Volta `WMMA2` + `LEAN` + `SKINNY` vs `i8h_volta`**:
   - Image `sha256:0cbf5d14...`, engine `ec05dafc...`; passed `22/22` CPU + `15/15` GPU + `pf_wmma_parity` 4/4.
   - Medians `1014.3 / 1021.7 tok/s` prefill, `23.1 / 24.2 tok/s` decode (`batch-3` warm `1031.4 / 1037.1 tok/s` prefill, `23.2 / 23.7 tok/s` decode). Tied with stock `0.1.67` `i8h_volta` (`C0`: `1034.2 / 1040.5 tok/s`), proving `0.1.67`'s built-in `i8h_volta` (`TUNE-0216`) is upstream-equivalent for prefill; `stage12-p1.patch` was therefore omitted from `S12-C1`.
5. **`S12-D3` (`d3-20261125T194836`, `stage12-d3.patch`) — `STRATA_HC_V100=1`**:
   - Image `sha256:5693cd7d...`, engine `b29f8132...`; passed `22/22` CPU + `15/15` GPU + `gr_parity`/`gr_multi_parity` + `hc_graph_bench 1.98x–2.13x`.
   - Medians `894.9 / 898.9 tok/s` prefill, `21.8 / 21.1 tok/s` decode (post-build cold cache `14.8–26.5 GB` OS read in `batch-1`/`batch-2`); warm `batch-3` reached `994.3 / 1001.3 tok/s` prefill and `22.6 / 22.6 tok/s` decode (`+0.7 / +0.3 tok/s` over `C0`) with confirmed 2x HC kernel speedup. Included in `S12-C1`.

---

## 6. Gate D: Combined Validation, Quality Suite & Restart/Health Checks

Combined image `strata-v100:stage12-0.1.67-c1` (`sha256:33b61b0432e81c44a6d212ca38be46b4191a989a65c4a0141e2cbc9b116f10ec`, engine `c01770d00bd49985f008e39d722b996f0ad476545c8bd50bb96ad8a66ed52dda`) combines `stage12-d1.patch` + `stage12-d2.patch` + `stage12-d3.patch` with 13 explicit env flags (`STRATA_OOMD_ROOM=0`, `STRATA_AVX512BW_IQ=22`, `STRATA_IQ_MT_MIN=1`, `STRATA_IQ_GATHER=1`, `STRATA_IQ256_GATHER=1`, `STRATA_Q2_BITPLANE=1`, `STRATA_MMAP_ADAPT_ASYNC=1`, `STRATA_COLD_OVERLAP=5`, `STRATA_HC_V100=1`, `STRATA_SELECT_SIMT=1`, `STRATA_ATTN_DAILY=1`, `STRATA_GR_UP75=1`, `STRATA_FUSE_WAIT=2`).

- **`S12-C1` (`c1-20261125T202739`, `ROUTE_TAIL_SKIP=0`, 3/3 PASS)**: First simultaneous `>30 tok/s` dual-agent decode on `0.1.67` with exact routing: medians `965.9 / 970.6 tok/s` prefill, **`30.8 / 34.7 tok/s` decode**, `131.73 / 131.09 s` TTFT (`batch-1..3` page cache warming `10.8 -> 6.1 GB` OS read; `batch-3` `1021.1 / 1029.3 tok/s` prefill, `31.7 / 34.7 tok/s` decode).
- **`S12-F1` (`f1-20261125T204131`, `ROUTE_TAIL_SKIP=0`, 3/3 PASS)**: Warm validation on `S12-C1` image:
  - `batch-1`: PF `1041.0 / 1051.9`, DEC `31.0 / 35.9`, TTFT `122.24 / 120.97 s`, out `1963 / 1752`, overlap `47.49 s`, OS read `1106.7 / 607.7 MB`, hit `0.773 / 0.825`, DFlash2 acc `79.96% / 81.47%` (`1193/1492` & `989/1214`).
  - `batch-2`: PF `1022.1 / 1029.9`, DEC `32.0 / 35.9`, TTFT `124.48 / 123.54 s`, out `1833 / 1598`, overlap `43.43 s`, OS read `1151.4 / 559.9 MB`, hit `0.798 / 0.829`, DFlash2 acc `78.03% / 82.15%` (`1083/1388` & `893/1087`).
  - `batch-3`: PF `1032.7 / 1043.2`, DEC `31.6 / 35.3`, TTFT `123.21 / 121.97 s`, out `1937 / 1691`, overlap `46.56 s`, OS read `795.2 / 439.5 MB`, hit `0.787 / 0.819`, DFlash2 acc `79.15% / 82.57%` (`1154/1458` & `976/1182`).
  - **Medians**: **`1032.7 / 1043.2 tok/s` prefill**, **`31.6 / 35.9 tok/s` decode**, **`123.21 / 121.97 s` TTFT**, wall `184.47 s`, overlap `46.56 s`.
  - **Restart & Health Verification**: Every fresh-process batch (`startup`, `batch-1..3`) plus the post-C2 `quality-logs` launch passed `/health` (`status: ok`, `loaded: true`, `max_context: 131072`) with `restart_check: PASS`.
- **`S12-C1T` (`c1t-20261125T205904`, `STRATA_ROUTE_TAIL_SKIP=7`, 3/3 PASS)**: Controlled same-route comparison:
  - `batch-1`: PF `1024.7 / 1035.6`, DEC `40.4 / 45.5`, TTFT `124.15 / 122.87 s`, out `1577 / 1966`, overlap `38.99 s`, OS read `407.7 / 454.1 MB`, hit `0.864 / 0.889`, DFlash2 acc `78.37% / 80.90%` (`837/1068` & `1063/1314`).
  - `batch-2`: PF `1039.4 / 1046.8`, DEC `41.3 / 45.2`, TTFT `122.40 / 121.54 s`, out `1805 / 1966`, overlap `42.55 s`, OS read `1019.7 / 484.2 MB`, hit `0.868 / 0.889`, DFlash2 acc `77.62% / 80.90%` (`971/1251` & `1063/1314`).
  - `batch-3`: PF `1040.2 / 1048.5`, DEC `42.5 / 44.3`, TTFT `122.31 / 121.34 s`, out `1849 / 1933`, overlap `42.54 s`, OS read `641.1 / 436.2 MB`, hit `0.871 / 0.881`, DFlash2 acc `79.42% / 79.66%` (`992/1249` & `1046/1313`).
  - **Medians**: **`1039.4 / 1046.8 tok/s` prefill**, **`41.3 / 45.2 tok/s` decode**, **`122.40 / 121.54 s` TTFT**, wall `165.99 s`, overlap `42.54 s`.

### Semantic Quality Suite (`scripts/141-stage12-quality.py`)

Executed against live Agent A (`:18086`) and Agent B (`:18087`) containers for both `S12-F1` ([quality.json](../artifacts/stage12-results-20261125/f1-20261125T204131/quality.json)) and `S12-C1T` ([quality.json](../artifacts/stage12-results-20261125/c1t-20261125T205904/quality.json)) (`temperature=0.0`, `top_p=1`, `seed=520`, `reasoning_effort="none"`):

| Check | Prompt / Verification | `S12-F1` (A / B) | `S12-C1T` (A / B) | Anomalies |
|---|---|---|---|---|
| `long_context_anchor_recall` | ~16–20K filler + `ANCHOR_ALPHA=VOLTA-7913`, `BETA=TITAN-4428`, `GAMMA=STRATA-9051` + `check_garbled` | **PASS / PASS** (`VOLTA-7913, TITAN-4428, STRATA-9051`, `garble: ok`) | **PASS / PASS** (`VOLTA-7913, TITAN-4428, STRATA-9051`, `garble: ok`) | None |
| `coding_exec_merge_intervals` | Generate `def merge_intervals(intervals):` + live Python `assert` suite (`[]`, overlapping, touching) | **PASS / PASS** (`garble: ok`, `err: ""`) | **PASS / PASS** (`garble: ok`, `err: ""`) | None |
| `json_schema_parse` | Strict JSON output matching `{"gpu_count": 2, "arch": "sm_70", "kv_type": "int8", "tags": ["v100", "dflash2"]}` | **PASS / PASS** (`detail: ok`) | **PASS / PASS** (`detail: ok`) | None |
| `determinism_and_stop` | `"List integers 1 to 20 separated by commas: 1, 2, "` with `stop=["10"]`, 2 identical calls | **PASS / PASS** (`hash_a=hash_b=f862070e4723`, `finish_reason="stop"`) | **PASS / PASS** (`hash_a=hash_b=f862070e4723`, `finish_reason="stop"`) | None |
| **Total** | **4 checks x 2 agents = 8 checks/arm** | **4/4 A & 4/4 B PASS (0 fail)** | **4/4 A & 4/4 B PASS (0 fail)** | **0 NaN / 0 garble** |

---

## 7. Power, Thermal, VRAM, Page-Cache & Safety Compliance

- **Hardware & Safety Envelope**: All 30 scored C2 batches + 1 diagnostic batch + 6 startup smokes enforced `--prefill auto:8192`, `--prompt-cache 0`, `--draft dflash2 --draft-fallback none` (0 MTP fallbacks), `131,072` context, `INT8` KV (`32,768` resident), `135–1245 MHz` SM clock lock, and `150.00 W` configured caps. Zero Xids, zero OOMs, zero `SIGILL`s, zero NaN/garble events after Gate A's `ad801fa` fix.
- **Peak VRAM**: `15,637 MiB` on `U0`/`U1`/`C0`/`D1`/`D2`, `15,615 MiB` on `P1`, `15,619 MiB` on `D3`, **`15,611 MiB` on `C1`/`F1`/`C1T`** (`15,737 MiB` on `P0` diag), safely within `16,384 MiB` V100 memory (`773 MiB` headroom on `F1`/`C1T`).
- **Thermal & Power (Full-Lifetime Unfiltered Telemetry)**: Across all 10 scored arms, GPU0 mean/peak temperature ranged `52.7–58.8 °C` / `64–68 °C`, GPU1 `54.2–59.3 °C` / `64–66 °C` (well below `85 °C` throttle). Full-lifetime mean power ranged `82.2–104.2 W` on GPU0 and `84.0–106.1 W` on GPU1, with transient prefill peaks `193.5–226.9 W` (max `226.9 W` on GPU1 in `S12-C1T` `batch-1`).
- **Page-Cache Residency**: After `STRATA_OOMD_ROOM=0`, shard 1 + pack `fincore` residency held `43.2–43.8 GiB` in warm runs (`C0`, `F1`, `C1T`), keeping `F1`/`C1T` OS physical reads at `407.7–1151.4 MB/request`.
- **SHA256 Backup Verification**: **1,689 raw evidence files** pulled from P520 to ThinkPad under `results/raw/*20261125*` across **18 SHA256 manifests** (`all_match=True` on `18/18` manifests).

---

## 8. Final Host State (`p520-llm`)

Verified live after Stage 12 completion:
- **Serving containers**: `p520-llm-a` and `p520-llm-b` remain preserved in `Exited (0)` (alongside `p520-llm-{a,b}-archive-s10-d4-20261111T012331` and `p520-llm-{a,b}-archive-name-gate-20261111T0120`); no active serving containers running.
- **GPUs**: GPU 0 (`Tesla V100-SXM2-16GB`, `0 MiB / 16384 MiB`, `135 MHz`, `37 °C`, `26.06 W`, cap `150.00 W`); GPU 1 (`Tesla V100-SXM2-16GB`, `0 MiB / 16384 MiB`, `135 MHz`, `39 °C`, `25.58 W`, cap `150.00 W`).
- **Clock Lock**: `v100-clock-lock.service` `active` (`135–1245 MHz`).
