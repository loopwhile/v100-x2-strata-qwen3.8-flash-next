# Stage 8 continuation through C3 — completed 2026-11-07

**C1, C2 and C3 each passed 3/3 concurrent 128K C2 (9/9 total). One separate
D1 diagnostic passed, unscored. Dual-agent 30 tok/s target NOT MET. No verified
overall upgrade or promotion. M1/M2/M3 were not executed at the user's request.**

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
| U1 (earlier session) | 0.1.57, SIMT+SM70_TABLE+WMMA | 871.0 / 877.2 | 25.2 / 27.7 | 146.02 / 145.01 |
| C1 | `--pool-workers 3`, relative to U1 | 998.1 / 1007.2 | 26.2 / 28.3 | 127.45 / 126.32 |
| C2 | `--resident-budget-gib 2`, relative to U1 | 823.4 / 827.2 | 26.6 / 27.9 | 154.44 / 153.75 |
| C3 | `--adapt-async 1`, relative to the validated C2 mapping | 820.5 / 825.0 | 29.0 / 28.7 | 155.00 / 154.14 |

C3's individual Decode A/B results were **30.0/28.3, 29.0/30.4,
29.0/28.7 tok/s**. No batch had both agents at >=30; the required three-batch
dual-agent result was not achieved. C3's decode medians were descriptively
about +9.0%/+2.9% against C2, while prefill and TTFT stayed near C2's slower
level. This is not a verified total-system win. No semantic coding/tool-call
quality suite was run, and no quality or promotion claim follows from C2 PASS.

The full summary includes request/batch wall times, output counts and ranges,
decode overlap, GPU temperature/power/clock/utilization/VRAM means and peaks,
CPU utilization, RAM before/after cleanup and active serving snapshots,
trailing RAM-sensor history, swap, major faults, tracked page-cache residency,
MTP acceptance, expert/KV hit rates, logical reads and engine-reported physical
reads. Raw iostat/vmstat/GPU time series and all request/health receipts remain
available. Full-lifetime GPU/CPU averages and trailing RAM peaks are explicitly
distinguished from phase-specific or whole-lifetime measurements.

## What changed after the initial stop decision

The initial review treated insufficient selection evidence too broadly as a
reason to stop at U1. The user asked to advance the remaining candidates. D1
then supplied current 0.1.57 CPU/wait evidence rather than relying only on old
IQ3_S profiling or promising unmeasured improvements.

D1 found CPU execution A/B 53.52/41.29 ms per window and an adaptive-thread
join of 9.67/9.23 ms. GPU waitCPU and host timings overlap; they must not be
summed as independent costs. D1 was instrumented and excluded from all scored
candidate comparisons.

The actual PCIe expert share in plain mmap U1/D1 was zero, despite controller
fraction messages. Source proved that FileExpertSource needs a mapped pinned
complement for useful PCIe dispatch. Therefore the fixed-0.85 proposal was
withdrawn before execution and replaced by the single bounded resident-budget
change in C2. Startup proved 2.00 GiB mapped/pinned per agent and real offload;
C2's measured API offload-share medians were 0.015/0.012. No whole-model RAM
copy, model restore or change to the frozen workload/context was introduced.

C2 also exposed a substantial file-tier/prefill cost: engine-reported physical
read medians were approximately 24.2/23.1 GB per agent versus 1.1/0.35 GB in C1.
Those process counters cannot be summed as unique device I/O. Cache and RAM
conditions shifted along with this policy, so do not turn these observations
into a controlled causal kernel/version claim. The read/loan warnings were
preserved rather than hidden by tuning additional options.

C3 used the **existing upstream asynchronous scheduler**, not a custom source
patch. Its resident/arena prerequisite was satisfied by completed C2, whose
3/3 receipt the runner required. Only `--adapt-async 1` was added relative to
that explicit reference. Each agent in each scored batch logged actual
nonzero asynchronous rounds; merely setting an environment variable was not
accepted as dispatch proof. No new source-port or kernel-parity claim is made.

C1's extra Linux worker could be unpinned within the unchanged container
cpuset; the actual placement/count logs are retained. It was not silently
represented as an extra physical CPU core.

## Limits and scope closure

Measurements were sequential, not interleaved with U1 or archived S7-XXS-14.
File cache, swap, physical I/O, output hashes/lengths, MTP acceptance and clock
throttling differ. Thus the observed percentage differences are descriptive.
Batch wall time also depends on output length. The earlier U1 results and
all S6/S7 data remain unchanged; no old baseline was rerun or ID reused.

The latest user instruction was **“C3까지만 진행해줘.”** M1, M2 and M3 were
never launched, allocated no scored IDs and have no result placeholders.
Their proposed settings remain reference only. No additional diagnostic,
candidate, quality run or production operation follows from this report.

| ID | Result | Scored C2 |
| --- | --- | ---: |
| `d1-20261107T140752` | PROFILE_PASS_NOT_SCORED | 0 (one diagnostic) |
| `c1-20261107T141343` | 3/3 PASS | 3 |
| `c2-20261107T142619` | 3/3 PASS | 3 |
| `c3-20261107T144114` | 3/3 PASS | 3 |
| M1 / M2 / M3 | NOT RUN — user scope limit | 0 |

All **606 follow-up raw files** match the P520 originals by SHA-256: D1 87,
and C1/C2/C3 173 each. [Hash manifest](../artifacts/stage8-followup-results-20261107/raw-backup-sha256.json).
Raw P520: `results/stage8/S8-<arm>/<id>/`; ThinkPad backup
`results/raw/<id>/`. Earlier U1 and preparation-failure raw receipts are
separately preserved. Runner snapshots are retained by their execution hash.

Final host check: no running containers/GPU work, GPU0/GPU1 0 MiB, configured
limits 150 W; all scored SM peaks <=1110 MHz. Initial serving state was empty
and remains empty; historical serving containers and all prior images/models
are preserved. ThinkPad tunnel remains active with its original start time.
Power/clocks/host settings and serving 8080/8081 and forwarding 18080/18081
were untouched. [Final receipt](../artifacts/stage8-followup-results-20261107/final-host-check.json).

The user subsequently requested committing and pushing these results/code.
This Git/GitHub publication does not synchronize the P520 checkout or authorize
any host operation. Do not resume or reuse any completed ID or launch the
unexecuted M arms from retained scripts without a new user scope.
