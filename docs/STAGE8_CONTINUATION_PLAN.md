# Stage 8 continuation — user requested remaining candidates, 2026-11-07

**Status: completed through M2, 15/15 scored follow-up C2 PASS (C1/C2/C3/M1/M2) plus D1 diagnostic.
Latest scope: user authorized M1 → M2 single-change execution and M3 evaluation only (M3 NOT executed; no combinations). Do NOT launch M3,
new diagnostics, retries, combinations or further candidates. M3 below is
retained as unexecuted reference, not an execution order.**

The user challenged the earlier decision to stop after U1: “추가 후보 미실행
사유가 뭐야? 나머지도 진행해야 하는거 아니야?” This reopens candidate
selection/execution, not the completed U1 IDs. The previous NOT SELECTED table
records an initial decision, not evidence that the remaining settings fail.

Final results: [review](STAGE8_CONTINUATION_REVIEW.md) and
[full metric summary](../artifacts/stage8-followup-results-20261107/summary.md).
The order below records the executed protocol and superseded M proposals; it
is not an active execution order.

## Bounded scope and order

1. **S8-D1**, separately scoped diagnostic: one startup/short inference check,
   then **one non-scored fresh-process concurrent 128K C2** on the unchanged
   U1 image/recipe with `STRATA_DECODE_TIMING=1`,
   `STRATA_PREFILL_TIMING=1`, `STRATA_VERIFY_PROFILE=1`. Purpose: collect
   current 0.1.57 wait/CPU/verify-window evidence needed by C1/C2/C3/M1.
   This is instrumentation, not a new baseline, speed screen, candidate score
   or extra U1 repetition. Preserve it with diagnostic labels, no retries.
2. Select and execute **C1 then C2**, one primary setting each, with their own
   startup gates and exactly three scored fresh-process C2 batches per arm.
3. Review D1 and runtime results, then execute supported **M1/M2/M3** settings
   below. Settings are hypotheses, not promised improvements. No option stack.
4. **C3:** inspect the actual serialized wait from D1; prepare a minimal,
   reviewable source change only if evidence supports one. A source patch still
   requires the plan's separate source-change/parity approval gate before a
   scored candidate. Do not fabricate a patch just to fill the row.

U1 remains completed/closed, three scored batches. The continuation's runtime
arms add at most 15 scored C2 batches, C3 at most three after its gates; thus
the original total budget of 21 scored C2 batches is preserved. D1 is separately
counted and never included in candidate medians. No diagnostic rerun or failed
scored retry is automatic. Inspect/review each completed arm before the next.

## Concrete runtime hypotheses

All settings are relative to U1 0.1.57; model, native pack, MTP, context 131072,
INT8 KV, base runtime switches, GPU/CPU isolation, hardware and workload remain
fixed except the one primary change explicitly listed.

| Arm | Primary change | Source/evidence and gate |
| --- | --- | --- |
| C1 | `--pool-workers 3` | U1 uses 2 workers plus a draining host on 3 physical cores/6 logical CPUs per agent. Test whether a third worker fills host submission/drain gaps under the new 0.1.57 0.70–0.75 PCIe policy. This is an explicit SMT contention/overlap hypothesis on IQ3_XXS, not a claim that older IQ3_S screens transfer. On this Linux topology the third worker may be unpinned within the fixed container cpuset, rather than pinned to a new physical core; record that explicitly. Verify actual workers/placement; container CPU affinity stays unchanged. |
| C2 | `--resident-budget-gib 2`, keep auto PCIe fraction | D1 proved the plain mmap source has zero actual PCIe experts despite changing fraction logs. FileExpertSource::pcie_layer/pinned require a mapped pinned complement. A bounded 2 GiB resident/pinned expert budget per agent activates that path while retaining mmap and a 4 GiB per-agent headroom rule. Maximum proposed added resident budget is 4 GiB across the host; do not copy the whole model. Verify actual pinned complement and capture effective offload counters. A fixed fraction alone would be inactive in the current mapping. |
| C3 | proposed `--adapt-async 1` on the validated C2 resident-budget recipe | D1 measured adaptive-thread join A/B 9.67/9.23 ms per decode window. Upstream already implements asynchronous adaptive scheduling, but explicitly requires the resident/arena path. After C2 passes three batches and is reviewed as a safe reference, test that existing upstream scheduler with one extra primary change. Require the actual asynchronous activation log and reject fallback. This is a runtime use of existing upstream code, not a claimed new source patch; the custom-source approval/parity gate is not bypassed by inventing a patch. |
| M1 | proposed `--spec 6`, min-p remains 0.5 | D1 verify-window/draft evidence must support testing the larger cap. Source supports narrow MTP windows <=8; existing lookup default may stay 12. This is a new IQ3_XXS/0.1.57 scheduling hypothesis; validate actual MTP cap and output contract. |
| M2 | `--expert-cache-per-layer`, keep `--expert-cache auto` | U1 decode cache misses are roughly 12–17%. Native mixed-format pack has variable-sized slots and the source has an explicit per-layer allocation branch. Test quota coverage instead of the profile-sized global allocation. The same VRAM budget/reserve applies; this avoids equating a cache-policy trial with unsafe enlargement. Require actual per-layer dispatch/allocation log. |
| M3 | `--kv-resident 40960` | Keep INT8 and total context 131072. Test a modest larger resident window reducing KV transfers; the automatic expert cache must resize within the existing reserve. Reduced cache capacity is an allocation consequence, not an independently forced setting. Verify actual KV plan, headroom, 128K compatibility and unchanged reserve before scoring; stop on unsafe startup/OOM/swap behavior. |

M2/M3 are feasibility-gated: if the actual planner cannot retain safe headroom,
archive SKIPPED/UNSUPPORTED with its receipt and do not allocate scored batches.
Passing a short boot alone is not throughput or semantic-quality evidence.

## D1 findings and protocol correction

D1 completed on 2026-11-07, **PROFILE_PASS_NOT_SCORED**, one diagnostic only.
A/B per-window CPU work was 53.52/41.29 ms; GPU waitCPU GDN+QSA was
40.12+8.73 / 31.49+5.89 ms, within 83.00/70.56 ms verify. These timings
overlap and must not be added as independent costs. Adaptive join was
9.67/9.23 ms/window. Average T was 3.20/3.09 with 2.45/2.29 output tokens per
window; draft cost was 4.17/4.10 ms. This supports CPU scheduling, a larger
MTP window hypothesis and investigation of the serialized adaptive join.

Actual per-layer PCIe expert counters were **0.00** and API `pcie_share=0`.
The profile's nonzero `PCIe grp` kernel time does not prove useful offloaded
expert work: empty/static graph work is still timed. Source confirms that
plain mmap FileExpertSource has no mapped pinned complement, so pcie_layer
returns false. The earlier audit identified the controller but did not prove
this final dispatch gate. C2's original fixed-0.85 proposal is withdrawn before
execution (zero scored runs). The replacement above changes only the bounded
resident budget to enable meaningful CPU/PCIe work sharing.

Likewise, `--adapt-async 1` alone on U1 is explicitly disabled by the source.
The existing upstream async path becomes eligible on C2's resident mapping;
C3 therefore requires C2's completed 3/3 receipt and explicit result review.
The agent will not stack the two settings without that gate. No source patch
is made or falsely represented as tested. If resident mapping is unsafe or
unsupported, record that constraint rather than running an ineffective flag.

## Preservation and recovery

Initial continuation preflight at 14:04 KST: P520 idle, no running containers,
GPU0/GPU1 0 MiB, 150 W limits; existing 1110 MHz lock active. Roughly 59 GiB
RAM available, 172 MiB swap used. Same physical cores and fixed cpusets remain.

Use new script 107 and new `d1/c1/c2/m1/m2/m3-<timestamp>` IDs under
`results/stage8/S8-<arm>/<id>/`. Retain original scripts 104–106 and all U1
receipts. The pinned image remains
`sha256:590b604d9bcf5268ea03f6ab5b786e4051e69884eee8a328b6de54a4c55033d2`.
No existing serving container is started/stopped. Ports 18086/18087 only;
8080/8081, tunnel, models, images, power and clocks stay untouched. Each launch
has locks, process/boot identity, timeout, progress and owned-container cleanup.

Record the current arm/ID and exact inspection path in state/current.md before
launch. Back up and hash-verify completed or failed raw evidence. Preserve
invalid runs; do not retry/reuse IDs or silently label incomplete arms 3/3.
