# Stage 8 — IQ3_XXS 128K dual-agent performance optimization plan

**Status: COMPLETED THROUGH M2 + C0 CONTROL — latest user scope; U1 and C0/C1/C2/C3/M1/M2 each 3/3 C2 PASS (21/21 scored C2 total), D1 separately unscored. Dual-agent 30 tok/s target NOT MET; no verified overall upgrade or promotion. M3 evaluated analytically only and NOT run by user instruction; no combination arms run. No further execution authorized.**
**Created:** 2026-11-07 (Asia/Seoul)  
**Scope:** Qwen3.8-Flash-Next GSQ-RCO **IQ3_XXS**, two independent Tesla V100 16 GB agents, 131072-token context per agent.  
**Decision:** Reuse the completed **S7-XXS-14** 0.1.54 C2 results as the archived baseline; **do not run an S8 0.1.54 baseline**. For each approved, supported new candidate: **preflight → server startup/health and basic inference check → exactly three fresh-process concurrent 128K C2 batches → review**. No one-batch speed-screen stage or mandatory final rerun.

Final execution review: [continuation through M2 + C0](STAGE8_CONTINUATION_REVIEW.md) ·
[full metrics/resources](../artifacts/stage8-followup-results-20261107/summary.md).
Proposed M3 remains unexecuted reference only (evaluated as feasible but unnecessary).

## 1. Goal and limits

Improve Prefill, Decode and TTFT while retaining IQ3_XXS quality, 128K, two independent agents, the original workload and current thermal/power constraints. Focus on upstream engine changes, CPU Expert / GPU wait synchronization, CPU–PCIe expert scheduling and, only when supported by profiling evidence, MTP/KV/expert-cache settings. Prefer maintainable upstream-compatible changes over custom CUDA ports.

**Stretch targets (not predictions):**
- Decode **>=30.0 tok/s for BOTH A and B in EACH of 3 valid concurrent C2 batches** (primary stretch goal).
- Prefill approximately **>=1100 tok/s per agent**, TTFT approximately **<=115 s** for the frozen ~127K input (secondary stretch goals).
- A repeatable smaller gain (for example ~5% Decode) with no meaningful Prefill/TTFT/quality/stability regression is a useful partial result, not a 30 tok/s success.

A C2 mechanical PASS is not evidence of coding-agent semantic quality. Keep tool-call/coding quality validation separate and require it before any future production promotion.

### 1.1 Archived baseline: S7-XXS-14 — do NOT rerun

Source: [S7-XXS-14/15/16 results](../artifacts/stage7-results-20261101/stage7-iq3xxs-14-16-report.md) and [source/build audit](../artifacts/stage7-results-20261101/stage7-iq3xxs-port-source-audit.md).

| Archived 3-batch median | Agent A / GPU0 | Agent B / GPU1 |
| --- | ---: | ---: |
| Prefill (tok/s) | 997.6 | 1006.6 |
| Decode (tok/s) | 26.4 | 26.2 |
| TTFT (s) | 127.53 | 126.48 |
| Concurrent 128K C2 | 3/3 PASS | 3/3 PASS |

- Engine: upstream Qwen engine **0.1.54** (Strata release v0.2.8), pinned source `870aedd9e1ebe1c91f94da93b59af17729f6c5c0`.
- Existing immutable Docker image ID: `sha256:2095eed79b0038ef23d602a0490bf0d89c63ad8e84ace8654c5016b2a51d2246`.
- Flags: `STRATA_SELECT_SIMT=1`, `STRATA_SM70_TABLE=1`, `STRATA_PF_WMMA=1`.
- Existing run args: `--max-context 131072 --kv int8 --kv-resident 32768 --expert-cache auto --prefill auto --spec 4 --spec-min-p 0.5 --mmap-experts` with pinned IQ3_XXS/native pack/MTP inputs.
- All historical S7 arms, including 14/15/16, remain **CLOSED**; never reuse their IDs, overwrite receipts, or rerun them under a new label.

**Comparison limit:** Stage 8 measurements versus archived S7-XXS-14 are useful descriptive differences, **not controlled causal version/flag speedups**, because clock/cache/swap/run-date and output/MTP-acceptance conditions may differ. Record these confounders explicitly. Do not claim a proven kernel speedup from a cross-date comparison.

## 2. Frozen hardware and C2 contract

| Item | Required state |
| --- | --- |
| Host | Lenovo P520, Xeon W-2135 (6C/12T), 64 GB DDR4-2400 ECC |
| Agents | A: physical V100 GPU0 / cpuset `0-2,6-8`; B: V100 GPU1 / cpuset `3-5,9-11` |
| Topology | Two independent one-GPU processes; **no** layer split, VRAM pooling, mixed quantizations |
| Context / KV | 131072 each; `--kv int8 --kv-resident 32768` unless an expressly designated KV candidate changes *only* resident allocation |
| Model | Original pinned IQ3_XXS GSQ-RCO GGUF/native pack, shared read-only MTP; no re-quantization |
| Workload | `bench/workloads/v100-performance-v1.json`, A 126967 / B 126968 prompt tokens |
| Manifest SHA-256 | `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca` |
| C2 harness | `bench/c2_v100_contract.py`; record and verify the committed harness hash |
| Runtime default | `--expert-cache auto --prefill auto --spec 4 --spec-min-p 0.5 --mmap-experts` unless the specific arm explicitly changes one setting |
| Power/clocks | Preserve existing 150 W configured limit and 1110 MHz SM ceiling; **no** power/clock/host tuning |
| Per-batch validity | Fresh Strata processes for BOTH agents; `cache_n=0` and `cached_tokens=0`, concurrent decode overlap, >=1024 generated tokens for each, `finish_reason=stop`, post-health PASS |
| Repetition | **3 independently recorded valid concurrent 128K C2 batches for every executed candidate**; never substitute a boot smoke or a single-batch screen |

Do not touch existing 8080/8081 production/serving endpoints, ThinkPad `strata-tunnel.service` or 18080/18081 forwarding. Use isolated Stage 8 names, ports verified free during preflight, and pinned image IDs; check live GPU users and active requests before attempting any test. Never silently stop an active service. Preserve all models, historical Docker images/containers and raw receipts. Use CUDA 12.x with explicit Volta `sm_70`; do not use CUDA 13.

## 3. Workflow for EACH candidate

1. **Offline/source preflight:** verify actual upstream source SHA and relevant feature availability for `sm_70` and IQ3_XXS; check code-path dispatch rather than assuming a named switch works. Check pinned model/pack/MTP, config, image ID, workload/hash, GPU affinity, RAM/swap/page-cache and available ports; ensure no conflicting workload or active serving interruption. If incompatible or unsafe, record **SKIPPED** with reason and do not allocate C2 IDs.
2. **Server startup / readiness (NOT a scored C2):** boot only dedicated Stage 8 A/B containers; inspect effective engine and flags, GPU mapping/cpuset, `/health` with loaded state, context 131072, model/MTP checks and a short inference smoke. Confirm no OOM, VRAM planning or source dispatch errors. Boot smoke cannot be reported as 128K speed evidence.
3. **Concurrent C2 x3:** only after startup gate passes, use three **fresh-process** dual-agent batches against the frozen workload; record each as a unique ID. No prompt-prefix reuse, no benchmark warmup disguised as a score. Collect A/B throughput, time and counters separately.
4. **Review:** report all three batch results, medians, ranges, A/B minimum Decode, C2 correctness, power/temperature and host-memory conditions against the archived S7-XXS-14 reference. Advance to another candidate only after reviewing this result; do not automatically stack unproven options.

**Failure handling:** preserve startup errors, invalid/failed runs and raw logs unchanged. If a scored batch fails C2 or produces <1024 tokens, never call the arm `3/3 PASS`. Do not silently retry or reuse IDs; any recovery measurement uses new unique IDs and requires separately approved scope. Stop an unsafe/OOM/swap-thrashing candidate.

**No extra baseline / screening runs:** No S8-B0, no baseline 0.1.54 C2 remeasurement, no mandatory 1-run tuning screens and no mandatory final candidate-vs-baseline rerun. Instrumentation or a semantic coding suite is a separately scoped diagnostic, not part of the approved candidate's three C2 runs.

## 4. Candidate registry (conditional; P0/U1 authorized by user 2026-11-07)

The following are **conditional candidate slots**, not a command to execute all of them. Exactly 3 scored C2 batches **if and only if** the slot is approved and passes source/startup gates.

Execution update: user requested Stage 8 and confirmed proceeding/recording on
2026-11-07. P0 audit and U1's three scored batches are complete. U1 decode
medians A 25.2 / B 27.7 tok/s; no verified overall upgrade. Additional slots
were not selected after review and remain evidence-gated/unexecuted.
That initial stop decision was challenged by the user and is superseded by
the [continuation plan](STAGE8_CONTINUATION_PLAN.md): obtain necessary diagnostic
evidence and advance eligible C/M arms instead of stopping at missing evidence.
See [review](STAGE8_REVIEW.md), [measured report](../artifacts/stage8-results-20261107/stage8-u1-report.md),
[source/host audit](STAGE8_SOURCE_AUDIT.md) and [current handoff](../state/current.md).

| ID | Candidate / single primary change | Entry condition | Scored C2 |
| --- | --- | --- | ---: |
| **S8-P0** | Source-level 0.1.54 → candidate 0.1.57 audit, prior profiling review, feasibility checks | Offline only; resolve exact upstream tag/SHA, effective defaults and V100 support before any build | 0 |
| **S8-U1** | Upstream Qwen engine **0.1.57** (or exact separately approved pinned successor); preserve S7-XXS-14 runtime semantics | Build unique CUDA12/sm70 image; confirm supported kernels and effective MTP/cache defaults | 3 |
| **S8-C1** | CPU Expert workers / physical-core placement | Evidence of actual CPU compute/thread contention; historical IQ3_S pool-worker tests do not justify blind reruns | 3 |
| **S8-C2** | CPU–PCIe Expert work-split policy | Verified active applicable 0.1.57/0.1.54 code path, measurable CPU-vs-transfer bottleneck | 3 |
| **S8-C3** | CPU/GPU synchronization or host-expert scheduling code optimization | Isolated serialized wait confirmed; minimal source patch, parity and separate source-change approval required | 3 |
| **S8-M1** | MTP `--spec` / `--spec-min-p` candidate | Per-window acceptance/verify evidence suggests benefit; no guessing from Q2_0/fork data | 3 |
| **S8-M2** | Expert-cache strategy / allocation candidate | Quantified cache-miss or residency bottleneck with safe VRAM and host RAM headroom | 3 |
| **S8-M3** | KV resident allocation candidate | Proven spare VRAM, 128K compatibility and no swap/page-cache degradation; lowest priority | 3 |

If all 7 scored slots proceed, the **maximum planned budget is 21 concurrent dual-agent C2 batches** (3 per slot) plus non-scored startup checks. Most should be skipped unless earlier findings justify them. Neither P0 nor startup checks are counted as C2. Do not independently generate unlisted combination arms, new quantizations, different topology, or extra diagnostics. Stage 7 IQ2_XS and IQ3_S tracks remain separate; this plan does not close or reopen them.

### Ordering and selection

- First, **S8-P0** (no GPU execution): review the S7-XXS-DIAG-1 and Stage 6 profiling archives and the actual upstream release diff. Old measurements found significant CPU wait in Decode Verify; this is a diagnosis clue, **not proof that wait is entirely removable**. Confirm whether prospective 0.1.57 scheduling improvements reach V100 `sm_70`; do not assume DFlash2, newer GPU-specific kernels or automatic draft defaults work on Volta.
- Next, **S8-U1** if its compatibility checks pass. Fix existing `--spec 4 --spec-min-p 0.5`, KV and IQ3_XXS assets when evaluating the engine-version delta; explicitly log changes in upstream defaults.
- Then choose only justified **C1/C2/C3** or **M1/M2/M3** slots, one primary change at a time. Do not repeat already-negative Stage 6/7 arms without a specific IQ3_XXS source/path hypothesis.
- Existing S7-XXS-14 remains the rollback/operational reference regardless of Stage 8 results. A benchmark winner is not automatically deployed.

## 5. Measurement and report requirements

Per **batch** and **agent**, retain:
- Prefill tok/s, Decode tok/s, TTFT s, completion wall time, generated token count, overlap time, stop reason, C2 validity and all effective runtime flags.
- MTP draft proposals/acceptances, per-window verify or CPU wait timings when already available without changing scored timing, expert-cache behavior and GPU memory occupancy.
- GPU0/GPU1 temperature and power **mean + peak**, SM clocks/utilization, VRAM mean/peak; distinguish full-run averages from Prefill/Decode-only samples.
- Host RAM available/used, Swap in/out, page-cache residency, major faults, CPU utilization, PCIe/storage observations when available; do not infer a PCIe bottleneck solely from mean GPU power.
- Docker image ID, engine/source SHA, config/model/pack hashes, GPU mapping, CPU pinning, runner/harness/workload hashes, exact test timestamps and raw-log location.

Report **A and B separately**; a pooled average or fastest GPU is not enough for the 30 tok/s goal. Show all individual batch measurements and medians; identify memory/cache/clock confounders. Compare with the archived S7-XXS-14 medians honestly, without labeling cross-date deltas as proven causal wins. If different MTP acceptance or token counts make timings non-comparable, disclose this. Prefer identical-output comparisons when possible; do not demand extra scoring runs to obtain them.

**Acceptance levels:**
- **Stretch success:** each of the 3 valid C2 batches has Decode >=30 tok/s on A *and* B, no meaningful Prefill/TTFT/thermal/memory regression, and later separate coding-agent quality check passes.
- **Partial gain:** repeatable, practically useful improvement (target ~5%+ Decode or clear Prefill/TTFT gain), safe and maintainable; report it as partial, not as stretch success.
- **No verified gain:** unstable/within noise, incomplete 3/3, incorrect output, missing source-path proof, OOM/swap regressions, or no meaningful total-system advantage.

Any production promotion requires **a new explicit authorization**, independent coding/tool-call quality testing, rollback procedure and live-host check. No such promotion is authorized here.

## 6. Preservation, IDs and documentation outputs

- Unique run path, e.g. `results/stage8/<arm>/<new-run-id>/`; never overwrite or rename historical S6/S7 runs. Keep failed attempts and immutable receipts. Stage 8 script/image/container names must be independent of Stage 7.
- Proposed documentation outputs only **if future work is approved**: Stage 8 source audit, per-arm measured result receipts, an aggregated comparison report, and separately a coding-agent quality report. Do not create placeholder PASS reports.
- Preserve existing GitHub files, Docker images, `strata-s7-xxs14-serve-a/b`, previous-stage services, models, ports, SSH tunnel and 150 W / 1110 MHz constraints. GitHub documentation work does not establish P520's present running state.
- This plan is **not an execution authorization**. Before any P520 GPU run, separately confirm scope, live service state, candidate list, resource impacts and rollback path.

## 7. References

- [Stage 7 plan and frozen C2 contract](STAGE7_PLAN.md)
- [S7-XXS-14/15/16 executed C2 and cache/swap caveats](../artifacts/stage7-results-20261101/stage7-iq3xxs-14-16-report.md)
- [S7-XXS-8..13 and CPU-wait profiling](../artifacts/stage7-results-20261101/stage7-iq3xxs-opt-report.md)
- [Stage 6 final report: negative MTP/PCIe/KV screens](STAGE6_FINAL_REPORT.md)
- [Current recorded host/serving handoff](../state/current.md)
