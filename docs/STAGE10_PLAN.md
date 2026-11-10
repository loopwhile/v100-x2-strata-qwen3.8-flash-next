# Stage 10 — S9-D1 performance optimization on dual Tesla V100 (PLAN ONLY)

**Status: PLANNED / NOT EXECUTED (2026-11-10 KST).** This document is a research-backed candidate plan, not a benchmark authorization or an active runner. No Stage 10 C2 results, builds, P520 activity, serving changes, or production promotion are claimed. Prior stages and all their IDs remain CLOSED.

## Objective, baselines, and evidence limits

Optimize the **same independent GPU0/A and GPU1/B IQ3_XXS + DFlash2** setup used by [S9-D1](../artifacts/stage9-results-20261110/d1-20261110T175220/report.md), retaining upstream **Strata 0.1.59**. The first target is **Prefill >= 1100 tok/s AND Decode >= 30.0 tok/s on EACH agent** in concurrent 128K C2; stretch goal Prefill 1200 tok/s on each agent without falling below Decode 30. TTFT, power, temperature, stability, and coding-agent quality are constraints, not expendable metrics.

| Archived reference | Prefill A/B tok/s | Decode A/B tok/s | TTFT A/B s | Status |
| --- | ---: | ---: | ---: | --- |
| S7-XXS-14, 0.1.54 + MTP | 997.6 / 1006.6 | 26.4 / 26.2 | 127.53 / 126.48 | CLOSED operational reference; never rerun |
| S8-C0, 0.1.57 + MTP | 997.2 / 1006.3 | 25.6 / 27.9 | 127.57 / 126.42 | CLOSED |
| S8-C1, 0.1.57 + MTP | 998.1 / 1007.2 | 26.2 / 28.3 | 127.45 / 126.32 | CLOSED |
| **S9-D1, 0.1.59 + stock DFlash2** | **1026.5 / 1032.6** | **28.2 / 29.4** | **123.92 / 123.21** | **CLOSED 3/3 C2 PASS; Stage 10 baseline** |

Numbers are per-agent **three-batch medians**, not new measurements. D1 needs Prefill +7.16%/+6.53% for 1100, +16.90%/+16.21% for 1200, and Decode +6.38%/+2.04% for 30 (A/B respectively). **No verified dual-agent 1100 Prefill or dual-agent 30 Decode result exists in the consolidated record.** S5-XXS-T7-Fixed's higher historical mean Prefill (~1037.8 combined) is from a different engine/clock/cache setup and does not prove a current recipe.

Sources: [147-record consolidated database](CONSOLIDATED_BENCHMARKS.md), [machine-readable CSV](consolidated-benchmarks.csv), [Stage 9 review](STAGE9_REVIEW.md), [Stage 9 D1 receipts](../artifacts/stage9-results-20261110/d1-20261110T175220/receipts.json), [Stage 8 diagnosis](STAGE8_D1_FINDINGS.md), [Stage 8 continuation](STAGE8_CONTINUATION_REVIEW.md).

### D1 forensic starting point (observed, not a performance forecast)

- Pinned engine source `712fec6b4297c9cfd32ab43daaa2979a9aa01edf`, immutable upstream image `sha256:dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d`, engine binary `ccca488231f12da422be4a80b5c7f165b7593f6388907cac92d3c3f0d4229031`; CUDA 12.9.1 / sm_70.
- Verified **stock Q4_0-selector DFlash2 pack**, 339,694,592 bytes, SHA256 `4a42b98220ea7880664002c8edda1563aecbae754b762a2e2f31b2b91ee93ecd`. Explicit `--draft dflash2 --spec 6 --draft-conf 0.7 --draft-fallback none`; no MTP drafter/fallback. DFlash2-only acceptance medians A/B ~84.05% / ~78.41%; expert-hit medians 0.822 / 0.855; KV VRAM hits ~98%.
- Scored prefill A 1026.3–1027.0, B 1032.0–1033.7 tok/s across all three batches: this is a stable **warm page-cache** regime, not evidence that another cache-warmup will deliver 1100. Stage 9 D1 startup logs: **chunk 8192, ring 96**, 2489 borrowed prompt expert slots (~3.99 GiB), two expert-pool workers per process, AVX2 CPU expert kernels, no material cold-file reads. The last D1 run is not a new Stage 10 baseline test.
- In Stage 8's **different 0.1.57 + MTP** diagnostic, CPU experts were ~53.52 / 41.29 ms per window; these timings MUST NOT be ascribed to Stage 9 DFlash2. D1 draft, verify, CPU expert, adaptive join and launch stage times are **not measured**. S10-P0 must resolve these.
- Historical S7/S8 ran under up-to-1110 MHz conditions; S9 scored after user-authorized 135–1245 MHz host clock policy. Different clocks, outputs, cache, swap and temperature prevent causal cross-stage version comparisons. S9-D1 showed increased mean GPU power/temperature relative to S7; do not relabel it as an across-the-board production win.

## Frozen workload, assets, host and safety contract

1. Two independent one-V100-per-agent engines; GPU0/A uses cpuset `0-2,6-8`, GPU1/B `3-5,9-11`. Do **not** GPU-pool, layer-split, change CPU bindings or launch extra GPU consumers. Lenovo P520 Xeon W-2135, shared RAM/NVMe.
2. Same original Qwen3.8-Flash-Next GSQ-RCO **IQ3_XXS** GGUF shards, native pack, tokenizer, DFlash2 pack for stock arms, expert profile, `--mmap-experts`, `--expert-cache auto`, `--prefill auto`, 131072 context, INT8 KV and `--kv-resident 32768`. The three archived Volta environment switches remain **`STRATA_SELECT_SIMT=1`, `STRATA_SM70_TABLE=1`, `STRATA_PF_WMMA=1`**. No silently inherited V100 fork defaults.
3. Use the exact [C2 manifest](../bench/workloads/v100-performance-v1.json) SHA256 `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca` and [harness](../bench/c2_v100_contract.py) SHA256 `a8e42cc5a71421a7287618fd5be0332ae40f312426e4d243ce1c7619fdfc5246`. A/B prompts 126967/126968 tokens, 0 prefix reuse, >=1024 output tokens on **both**, finish_reason=stop, overlapping decode, pre/post health, and saved full telemetry.
4. **Preserve the host's currently documented 135–1245 MHz clock service and configured 150 W GPU power limit without issuing ANY clock/power/BIOS/systemd change.** Short sensor peak readings above 150 W are observations, not a changed cap. Do not change RAM, swap, BIOS, PCIe or IOMMU settings. The Stage 9 final audit is an archived snapshot, **not evidence that today's host is idle**; require fresh live inspection before a future authorized run.
5. Preserve historical images, 278 pre-existing containers, original weights and MTP assets, all Stage 2–9 logs, raw backups and the 147-row consolidated benchmark untouched. Never reuse archived IDs. Preserve 8080/8081 serving endpoints and ThinkPad SSH tunnel 18080/18081. Use unique Stage 10 images/containers and separate verified-free test ports. Do not stop active serving without separate approval and rollback plan.
6. No performance run, source patch, model fetch, Docker build, P520 command, production start, or Git synchronization with local hosts is authorized by **this planning commit alone**. A subsequent **separately approved execution scope** must specify candidates, batch budget, artifact locations, host preflight and rollback.

## Candidate register — planned, NOT measured

Every candidate inherits the **exact archived S9-D1 recipe** unless its delta explicitly says otherwise. One isolated change per candidate, except labeled sequenced combinations. Do not execute lower-priority candidates automatically merely because this table lists them.

| ID | Exact change against S9-D1 | Primary question | Gate / dependency |
| --- | --- | --- | --- |
| **S10-P0** | Instrumented diagnostic only (separate non-scored run): `STRATA_DECODE_TIMING=1`, `STRATA_VERIFY_PROFILE=1`, and separately `STRATA_DF2_PROFILE=1` where compatible | Is D1 limited by CPU experts, verify kernels, DFlash2, adaptive join, PCIe, or prompt layout? | Profiling changes timing; **never use its tok/s as a scored result**. Validate flags and isolate instrumented modes. |
| **S10-D2** | `--draft-conf 0.5` (spec 6 unchanged) | More draft proposals vs rejection/verify cost | Verify DFlash2 active, no MTP fallback, acceptance and effective tokens/window. |
| **S10-D3** | `--draft-conf 0.6` (spec 6 unchanged) | Intermediate DFlash2 gate | Same as D2. |
| **S10-K1** | `STRATA_ADAPT_LAG=2` only | Does delayed adaptive swap application remove waiting? | Verify active source path and adaptive logs in *mmap* mode; a no-op is SKIPPED/INCONCLUSIVE. |
| **S10-K2** | K1 **plus** `STRATA_ADAPT_NOWAIT=1` | Does a two-switch scheduler configuration help? | **Explicit dependent combination**, not independent single-flag attribution; reject incompatible paths. Do not combine with `STRATA_ADAPT_OVERLAP=1`. |
| **S10-D4** | `--spec 8` with **best validated D2/D3 or baseline confidence** | Do longer DFlash2 speculative windows pay on sm_70? | Only after confidence evidence; verify all draft/verify graphs fit and all requested windows are captured; otherwise SKIP. |
| **S10-D5** | Replace **only** stock DFlash2 drafter with pinned, validated **tuned DFlash2** pack | Do different draft weights improve accepted tokens and Decode? | Separate size/SHA/licence/compatibility/VRAM/startup gates; no other flag changes; semantic quality follow-up mandatory. |
| **S10-P1** | `STRATA_PF_HC_REGION=1` | Can HC scratch alias reduce prompt allocation? | Require source-path activation and actual allocation/chunk evidence; benchmark only if active. |
| **S10-P2** | `STRATA_EMB_REUSE_ACCOUNT=1` | Does planner-accounted buffer reuse increase real prompt efficiency? | Record actual chunk, ring, borrowed slots, cache and output changes; affects rounding. |
| **S10-P3** | `--prefill auto:16384` only | Does lifting the auto-chunk ceiling improve 128K prompt throughput? | Verify real chosen chunk, ring and VRAM margin; reject no-op, OOM or material Decode regression. |
| **S10-K3** | `STRATA_SIDE_MIXER=2` only | Does branch scheduling help D1 Verify? | Source guard + actual sm_70 dispatch + parity gate; fork F1's bundled defaults are **not** evidence of this flag's individual benefit. |
| **S10-C1** | Combine **only independently verified non-regressing** Prefill and Decode winners | Can >=1100 Prefill and >=30 Decode hold simultaneously? | **New explicit combination approval** after per-arm reviews; never assume improvements add. |
| **S10-R1** | Read-only final review and decision | Operational candidate vs archived S7/S8/S9 and Stage 10 | No automatic promotion. |

Stock DFlash2 **spec 6/conf 0.7** is the *measured baseline*, not evidence that other confidences/specs will win. Upstream 0.2.13 reported tuned-DFlash2 and larger speculative-window improvements on **other hardware/models**, **not on dual V100**. P100 adaptive gains and RTX 3060 prefill gains are hypotheses to test, not performance projections. `STRATA_PF_GROUP_SCRATCH=1` conflicts with a `STRATA_PF_WMMA=1` prompt path and can be ignored; native IQ3_XXS fused-int8 prefill kernels require sm_80+ on CUDA and cannot simply be enabled on V100. Do not spend scored C2 budgets on known-ineligible switches.

**Not prioritized:** Stage 8 `--resident-budget-gib 2`+`--adapt-async 1` improved Decode but cut Prefill to ~823 tok/s and worsened TTFT; `--expert-cache-per-layer` and larger KV resident budget have no good expected trade-off. Old `--prefill 4096` substantially reduced prompt throughput. `--pool-workers 3` can be considered later only after CPU-thread/host-core profiling, because two workers plus a host thread already occupy the current three physical cores in each cpuset.

## Execution gates for any separately authorized Stage 10 campaign

1. **P0 first, before scored work:** fresh P520/ThinkPad checkout/head checks, no unintended serving workloads, current Docker/GPU/CPU/RAM/swap/temperature, 150 W caps and **135–1245 clock-policy observation**, SSH tunnel/ports, model and draft checksum integrity, exact source SHA and CUDA 12/sm_70 image. Preserve existing processes. Resolve baseline startup paths and safety; do not touch host settings.
2. **Score control:** every viable candidate gets exactly **three valid fresh A+B concurrent 128K C2 batches** at unchanged harness and model. No reruns of Stage 9 D1 as a baseline; if a controlled same-day S10 control becomes essential due to cache/clock confounding, request a **separately approved, uniquely named Stage 10 control** instead. Each batch gets unique IDs and fresh processes; no silently discarded cold batches, failed batches or retries. A failure is recorded, not retroactively omitted.
3. **Fail-fast feasibility gates:** unique image and port, effective argv/env, DFlash2 head/model/hash and proposals, graph-window capture, GPU post-capture safety margin, same prompt counts, correct cpusets, no VRAM OOM, all required telemetry, no loss of health. Unsupported/no-op changes are recorded as SKIPPED, not credited with a speedup.
4. **Collect per agent, per batch:** Prefill, Decode, TTFT, wall time, output length/hash/finish reason, simultaneous Decode overlap, DFlash2 proposals/accepted **and accepted tokens per verify window**, expert/KV hit and misses, swap/IO/page-cache/major faults, CPU pool and host-thread timings, prefilling chunk/ring/borrowed slots, GPU VRAM/SM clock/utilization, mean **and peak** GPU temperature/power. Distinguish >60W-filtered historical means from full-lifetime unfiltered means and phase-specific measurements. Keep raw time series and provenance.
5. **Reporting:** each candidate's 3 batch rows, A/B medians and ranges, slower agent, C2 verdict, 95% evidence limits when applicable, descriptive difference vs archived S9-D1 and S7, alternative hypotheses for drift and any rounding/semantic differences. Do not invent profiling-only timings when not run. Archive raw and SHA256 verification in a new Stage 10 namespace only after execution approval.
6. **Progression gates:** reject materially worse Prefill/TTFT or thermals/power even if Decode rises; avoid treating mean A/B as a replacement for the slower agent. A **target hit** requires per-agent median Prefill >=1100 and Decode >=30 with all three valid batches; **stable target** additionally requires both agents meeting the thresholds in **each** scored batch. Stretch 1200 is separately marked. Quality-gate representative coding/tool calls and long sessions before recommending any production upgrade.
7. **Sequencing:** review D2/D3/K1 and P1/P2 diagnostic evidence before dependent spec/combination work. Maximum initial *proposal* is ten scored single/defined-sequence candidates (**30 batches if all ten are individually approved and viable**), plus separate non-scored P0. C1 is **outside** that 30-batch budget pending explicit approval; do not use this paragraph as run authorization.

## Source verification and next actions

- Upstream pinned source documentation: [Strata 0.1.59 `docs/DETAILS.md`](https://github.com/Niko1221/Strata/blob/712fec6b4297c9cfd32ab43daaa2979a9aa01edf/docs/DETAILS.md), [`src/prefill/prefill.cpp`](https://github.com/Niko1221/Strata/blob/712fec6b4297c9cfd32ab43daaa2979a9aa01edf/src/prefill/prefill.cpp), [native fused source](https://github.com/Niko1221/Strata/blob/712fec6b4297c9cfd32ab43daaa2979a9aa01edf/src/prefill/moe_fused_iq.cu), [0.2.13 release](https://github.com/Niko1221/Strata/releases/tag/v0.2.13).
- Verify all switches against **the actual pinned engine binary** and live logs at a future P0. Do not import a moving upstream main or fork code without an independently reviewed source/build/parity and benchmark scope.
- As of this planning commit, the **only completed work is this documentation**. Stage 10 has no scored tests, results, runner, Docker image, or production recipe. Await a distinct experiment authorization.
