# Stage 8 continuation through M2 + C0 control — completed 2026-11-07

**C0, C1, C2, C3, M1 and M2 each passed 3/3 concurrent 128K C2 (18/18 follow-up
scored batches; 21/21 total Stage 8 scored batches including U1). One separate
D1 diagnostic passed, unscored. Dual-agent 30 tok/s target NOT MET. No verified
overall upgrade or promotion. M3 was evaluated for necessity/feasibility only
and NOT executed at the user's instruction; no combination arms were run.**

[Full metric summary](../artifacts/stage8-followup-results-20261107/summary.md) ·
[CSV with medians/ranges](../artifacts/stage8-followup-results-20261107/summary.csv) ·
[Protocol and amendments](STAGE8_CONTINUATION_PLAN.md) ·
[D1 source/dispatch findings](STAGE8_D1_FINDINGS.md).

## Measured results

All numbers below are separate per-agent three-batch medians; no runs are
discarded as warmup. All agents keep original IQ3_XXS/native pack/MTP, 131072
context, INT8 KV/resident 32768, unchanged cpusets and independent single GPUs.

| Arm | Actual primary change / reference | Prefill A/B tok/s | Decode A/B tok/s | TTFT A/B s |
| --- | --- | ---: | ---: | ---: |
| U1 (earlier session) | 0.1.57, SIMT+SM70_TABLE+WMMA (post-reboot cache warming) | 871.0 / 877.2 | 25.2 / 27.7 | 146.02 / 145.01 |
| C0 | `C1` minus `--pool-workers 3` (default 2 pool workers, warm cache) | 997.2 / 1006.3 | 25.6 / 27.9 | 127.57 / 126.42 |
| C1 | `--pool-workers 3`, relative to U1 | 998.1 / 1007.2 | 26.2 / 28.3 | 127.45 / 126.32 |
| C2 | `--resident-budget-gib 2`, relative to U1 | 823.4 / 827.2 | 26.6 / 27.9 | 154.44 / 153.75 |
| C3 | `--adapt-async 1`, relative to the validated C2 mapping | 820.5 / 825.0 | 29.0 / 28.7 | 155.00 / 154.14 |
| M1 | `--spec 6`, relative to U1 | 996.7 / 1003.7 | 25.3 / 26.1 | 127.64 / 126.77 |
| M2 | `--expert-cache-per-layer`, relative to U1 | 994.6 / 1000.9 | 25.8 / 26.2 | 127.89 / 127.12 |

C3's individual Decode A/B results were **30.0/28.3, 29.0/30.4,
29.0/28.7 tok/s**. No batch in any arm had both agents at >=30; the required
three-batch dual-agent result was not achieved. C3's decode medians were
descriptively about +9.0%/+2.9% against C2, while prefill and TTFT stayed near
C2's slower level. C0 (`C1` without `--pool-workers 3`, default 2 workers)
matched C1's ~1000 tok/s prefill and ~127 s TTFT (**997.2/1006.3** vs
**998.1/1007.2 tok/s**), with **25.6/27.9 tok/s** decode vs C1's
**26.2/28.3 tok/s** and 5.0 percentage points lower whole-host CPU user load
(27.1% vs 32.1%). Neither M1 nor M2 improved decode over C0/C1/C3. No
semantic coding/tool-call quality suite was run, and no quality or promotion
claim follows from mechanical C2 PASS.

The full summary includes request/batch wall times, output counts and ranges,
decode overlap, GPU temperature/power/clock/utilization/VRAM means and peaks,
CPU utilization, RAM before/after cleanup and active serving snapshots,
trailing RAM-sensor history, swap, major faults, tracked page-cache residency,
MTP acceptance, expert/KV hit rates, logical reads and engine-reported physical
reads. Raw iostat/vmstat/GPU time series and all request/health receipts remain
available. Full-lifetime GPU/CPU averages and trailing RAM peaks are explicitly
distinguished from phase-specific or whole-lifetime measurements.

## Findings across D1, C0–C3 and M1–M2

D1 found CPU execution A/B 53.52/41.29 ms per window and an adaptive-thread
join of 9.67/9.23 ms (within 83.00/70.56 ms verify; draft 4.17/4.10 ms). GPU
waitCPU and host timings overlap and must not be summed as independent costs.
D1 was instrumented and excluded from all scored candidate comparisons.

The actual PCIe expert share in plain mmap U1/D1/C0/C1/M1/M2 was zero, despite
controller fraction messages, because `FileExpertSource` requires a mapped
pinned complement for `pcie_layer`. C2 added `--resident-budget-gib 2` per
agent (2.00 GiB mapped/pinned proven in startup logs; API offload-share medians
0.015/0.012), which also exposed ~24.2/23.1 GB engine-reported physical reads
per agent and slower prefill/TTFT because lent prompt slots fell outside the
2 GiB ranked complement. C3 added existing upstream `--adapt-async 1` on top of
validated C2 and logged nonzero asynchronous adaptive rounds in every scored
batch, lifting decode medians to 29.0/28.7 tok/s while retaining C2's prefill
cost. No custom source patch or new-kernel parity claim is made.

**C0 (`C1` minus `--pool-workers 3`; default 2 pool workers under warm cache):**
Executed at the user's request (`c0-20261107T192030`) to isolate `C1` without
`--pool-workers 3` on Strata 0.1.57 (`STRATA_SELECT_SIMT=1`,
`STRATA_SM70_TABLE=1`, `STRATA_PF_WMMA=1`). Startup and all 3 scored batches
verified child `/opt/strata/engine/strata` had no `--pool-workers` flag,
`2 pool workers on logical processors` (`0,1` on A, `3,4` on B), no SMT sibling
worker warning, and `MTP windows up to 4 tokens`. Under warm OS page cache
(43.81 GiB tracked, ~290.5/337.9 MB physical OS reads, 5 major faults, 1/0 swap
pages), C0 achieved **997.2 / 1006.3 tok/s** prefill and **127.57 / 126.42 s**
TTFT — matching `C1` (**998.1 / 1007.2 tok/s**, **127.45 / 126.32 s**) and
archived `S7-XXS-14` (**997.6 / 1006.6 tok/s**) within 0.1%, directly confirming
that `C1`'s ~127 tok/s prefill gap over `U1` (`871.0 / 877.2 tok/s`) came from
OS page-cache residency rather than `--pool-workers 3`. On decode, C0 reached
**25.6 / 27.9 tok/s** (ranges `25.3–26.3 / 27.7–28.2`) vs `C1`'s
**26.2 / 28.3 tok/s** (`25.7–26.6 / 28.0–28.6`), while whole-host CPU user load
dropped from **32.1%** in `C1` to **27.1%** in `C0` (−5.0 percentage points).

**M1 (`--spec 6` on U1):** Startup and all scored batches verified child
`--spec 6` and `strata serve: --lookup-max-t 12: MTP windows up to 6 tokens,
window sizes 1,2,3,4,5,6,7,8,12` with 721 MiB VRAM free at readiness and no
dropped CUDA graph windows. MTP acceptance medians fell to **49.4% / 52.6%**
(675/1367 on A, 1009/1917 on B) versus ~60–68% at `--spec 4`; verifying deeper
rejected draft tokens consumed extra CPU-expert routing without raising decode
speed (25.3 / 26.1 tok/s; shorter 1189-token outputs on A also reduced overlap
to 46.85 s). Under warm Linux page cache (43.81 GiB tracked, ~291/326 MB
physical OS reads, 10 major faults, 8/0 swap pages), M1 prefill reached
996.7 / 1003.7 tok/s and TTFT 127.64 / 126.77 s — consistent with C0's warm-cache
prefill result.

**M2 (`--expert-cache-per-layer` on U1):** Startup and all scored batches
verified child `--expert-cache-per-layer` and `per-layer slots use each layer's
blob: 4107 uniform slots (8.91 GiB) -> 5472 slots, 114 per layer (8.90 GiB)`,
leaving 731 MiB VRAM free at readiness and borrowing 2128 cache slots (3.99 GiB)
for prefill. Compared with global profile ranking (5499 slots, 8.91 GiB),
uniform 114-slot per-layer quotas held 27 fewer total slots due to 48-layer
integer division and yielded expert hit-rate medians of **0.840 / 0.864**
(versus 0.881 / 0.874 in M1 under similar warm-cache conditions), with decode
medians of 25.8 / 26.2 tok/s and prefill 994.6 / 1000.9 tok/s. Per-layer quota
allocation did not outperform global profile ranking on IQ3_XXS.

## S8-M3 (`--kv-resident 40960`) necessity and feasibility assessment — NOT EXECUTED

Per user scope instruction, **S8-M3 was evaluated analytically/empirically and
was NOT executed** (zero startup or C2 runs; no `S8-M3` directory allocated).

1. **Technical feasibility (PASS — offline source/planner analysis):**
   In `strata_control/vram_fit.py` and `src/program/generate.cpp`, Qwen3.8-Flash-Next
   has 13 QSA attention layers using `1056` INT8 bytes per cell per QSA layer
   (`× 1.054` scale overhead ≈ `14.13 KiB/cell` across QSA layers). Increasing
   `--kv-resident` from `32768` to `40960` (`+8192` cells) adds **~113.0 MiB of
   VRAM** per agent prior to `--expert-cache auto`. The authoritative host KV
   copy (`1.55 GiB` pinned RAM per agent) already spans all `131072` context
   cells in identity layout and does not grow; `59.6 GiB` available host RAM has
   ample headroom. `--expert-cache auto` preserves the `700 MiB` VRAM reserve
   (`+186 MiB` draft head `+256 MiB` post-cache) by shrinking the GPU expert
   cache by ~113 MiB (~65–70 slots, ~1.3% of `8.91 GiB`), so 128K startup and
   CUDA window-graph capture (~487–551 MiB post-capture margin) remain feasible.
2. **Necessity and expected trade-off (NOT RECOMMENDED):**
   Across every measured 128K C2 arm (`D1`, `C0–C3`, `M1–M2`), `--kv-resident
   32768` already achieves **97.7%–98.9% QSA KV VRAM hit rate**, and `D1`
   measured QSA `kv-resolve` at just **0.41 / 0.45 ms per window** (~0.5% of the
   84–97 ms decode window). Conversely, host CPU expert execution on cache
   misses dominates decode (`53.52 / 41.29 ms/window`, ~316–326 us per missed
   expert). Sacrificing ~65–70 GPU expert-cache slots (~113 MiB VRAM) to trim a
   sub-0.5 ms KV streaming path offers negligible upside (<0.05 ms/window) while
   risking additional CPU-expert misses. Leaving M3 unexecuted avoids spending 3
   dual-GPU 128K C2 batches on a negative expected trade-off.

## Limits, preservation and scope closure

Measurements were sequential across changing file-cache, swap, physical I/O,
output-length/hash, MTP-acceptance and thermal states (`U1` warmed page cache
from 38.27 to 42.83 GiB; `C2/C3` released file-cache pages for 2 GiB pinned
complements and incurred ~24/23 GB physical reads; `C0/M1/M2` ran with 43.81 GiB
tracked page cache and ~0.27–0.34 GB physical reads). Observed deltas are
descriptive, not controlled causal speedups. Earlier U1, S6 and S7 data remain
unchanged; no completed ID was reused.

Existing `scripts/107-stage8-followup.py` (`cec637b7...`),
`scripts/111-stage8-m1-m2.py` (`ba69cf7a...`) and earlier runner snapshots
(`166f06ad...`, `14290dbf...`) are preserved untouched. `S8-C0` used dedicated
runner `scripts/112-stage8-c0.py` (SHA-256
`85e1575f621d89d033c17af908ac5af01ab3de00e1d89ce4089b2a3d617516b4`), also
retained in `results/stage8-followup-runners/`. Combination candidates (such as
`C1+C3`, `C1+M1`, `C3+M1`) were not authorized or executed.

| ID | Result | Scored C2 |
| --- | --- | ---: |
| `d1-20261107T140752` | PROFILE_PASS_NOT_SCORED | 0 (one diagnostic) |
| `c0-20261107T192030` | 3/3 PASS | 3 |
| `c1-20261107T141343` | 3/3 PASS | 3 |
| `c2-20261107T142619` | 3/3 PASS | 3 |
| `c3-20261107T144114` | 3/3 PASS | 3 |
| `m1-20261107T170315` | 3/3 PASS | 3 |
| `m2-20261107T171915` | 3/3 PASS | 3 |
| S8-M3 | NOT RUN — evaluated only (unnecessary trade-off) | 0 |

All **1125 follow-up raw files** match the P520 originals by SHA-256: D1 87, and
C0/C1/C2/C3/M1/M2 173 each. [Hash manifest](../artifacts/stage8-followup-results-20261107/raw-backup-sha256.json).
Raw P520: `results/stage8/S8-<arm>/<id>/`; ThinkPad backup `results/raw/<id>/`.
Earlier U1 (`u1-20261107T124518`, 173 files) and preparation-failure
(`u1-20261107T124317`, 43 files) backups remain separately preserved.

Final host check (`2026-11-07T19:36:29+09:00`): no running containers or GPU
work, GPU0/GPU1 0 MiB, configured limits 150 W, all scored SM peaks <=1110 MHz,
`v100-clock-lock.service` active, no `S8-M3` directory created. Initial serving
state was empty and remains empty; historical serving containers
(`strata-s7-xxs14-serve-a/b`, `strata-jmn-iq2xs-agent-a/b`) and all prior
images/models are preserved. ThinkPad `strata-tunnel.service` remains active.
Power/clocks/host settings and serving 8080/8081 and forwarding 18080/18081
were untouched.
[Final receipt](../artifacts/stage8-followup-results-20261107/final-host-check.json).
