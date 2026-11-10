# Repository agent instructions

This repository is a live dual-V100 inference deployment and benchmark harness.
Before changing code or running P520 commands, read [Stage 4 plan](docs/STAGE4_PLAN.md)
and [Antigravity handoff](docs/STAGE4_ANTIGRAVITY_HANDOFF.md).

- Work from the ThinkPad E14 checkout. Use `ssh p520` for P520 inspection, build and tests.
- **Do not change GPU power limits, GPU clocks or host power settings.** No power-cap experiments.
- Preserve existing `strata-jmn-iq2xs-agent-a/b`, historical `strata-iq2xs-*`
  containers, their images, configurations, model shards and MTP.
- Preserve the ThinkPad `strata-tunnel.service` and existing 18080/18081 endpoints.
- Stage 4-A is **upstream v0.1.44.1 only**, **not** automatic production promotion.
  Stage 4-B (engine 0.1.47) and tuning require separate review.
- Keep `IQ2_XS`, INT8/`q8_0` KV, 131072 context, the two independent
  symmetric 1-GPU agents and frozen C2 128K workload unchanged in the primary arm.
- Do not run destructive Docker cleanup, alter the existing Stage 3-A build/benchmark
  scripts, or update an existing container's image in place.
- Before stopping live serving agents to free GPUs/8080/8081 for Stage 4 tests,
  ask the user for explicit approval and document rollback.
- Record empirical results distinctly from unverified optimization claims.

## Explicit Stage 4-B mixed-quant exception

The existing IQ2_XS symmetric agent recipe remains the **historical primary
comparison** only. The user expressly requested an **isolated** mixed trial:
host GPU0/A = IQ3_XXS, host GPU1/B = IQ2_XS, both vanilla Strata 0.1.47.
See [mixed AGY handoff](docs/STAGE4B_MIXED_AGY_HANDOFF.md). This does not
authorize changing power, overwriting live containers, deleting historical
agents, enabling SM70_TABLE or modifying the ThinkPad SSH tunnel.
The mixed test has not been measured or promoted.

## Stage 6 (CLOSED — 2026-10-28; dual-agent 30 tok/s goal NOT MET)

**Read first:** [Stage 6 final report](docs/STAGE6_FINAL_REPORT.md) and immutable [S6-0..S6-7 result receipts](artifacts/stage6-results-20261028/). The [original plan](docs/STAGE6_PLAN.md), [Codex handoff](docs/STAGE6_CODEX_HANDOFF.md) and [container setup](docs/STAGE6_PREP.md) are **archived reference documents, not active execution orders**.

- S6-0 completed 3 valid concurrent 128K C2 batches (per-agent decode medians A 22.3 / B 21.2 tok/s). S6-1 profiling complete. S6-2 through S6-6 candidate screens and failures recorded. S6-7 was **assessment only; no combination or 3-batch candidate validation**.
- No Stage 6 speedup or 30 tok/s result was validated and nothing was promoted to production. The best replicated Stage 6 reference remains the unchanged Stage 5 T7-Fixed recipe.
- Preserve GPU0/A and GPU1/B independently, their existing CPU affinities, shared 64 GB RAM and NVMe/model, 150W GPU caps and 131072 context. Do not pool/layer-split the GPUs. Preserve IQ2_XS deployment, prior stage containers, models, images, all benchmark evidence and the ThinkPad SSH tunnel.
- The Stage 6 runners (scripts/88-92) and isolated-arm generator (scripts/93-stage6-prepare-arm.py) are retained for audit. **Do not execute or resume tests automatically because the archived plan or handoff says NEXT or proceed.** New experiments or production operations require separately approved scope.
- This documentation closure is GitHub-only; no container, GPU, power, server, model or tunnel change is implied.

## Stage 7 (IN PROGRESS — Strata Qwen engine 0.1.54, NOT IQ3_XXS-only)

**Read first:** [Stage 7 plan](docs/STAGE7_PLAN.md). Stage 7 tests the **upstream 0.1.54 engine** across distinct Qwen3.8-Flash-Next GGUF quantizations. Candidate arms include **IQ2_XS, IQ3_XXS and IQ3_S**; UD-Q4_K_XL is optional and capacity-gated. IQ3_XXS's Stage 5 T1–T8 history is only one model's comparison, not the definition of Stage 7.

- **Verified existing progress:** upstream 0.1.54 was built and IQ3_XXS S7-XXS-1..6 completed 18/18 valid C2 batches; see [final report](artifacts/stage7-results-20261101/stage7-iq3xxs-final-report.md). The **new** S7-XXS-8..13 experiments were **executed on 2026-11-01** (17 scored + 1 non-scored diagnostic C2, all mechanical PASS; S7-XXS-12 stopped at 2 batches); see [S7-XXS-8..13 report](artifacts/stage7-results-20261101/stage7-iq3xxs-opt-report.md). Do not rerun or reuse those IDs. No model restoration, service interruption or production promotion is authorized by this result. New executions still require separate approval and live-host preflight.
- Pin upstream v0.2.8's **Qwen engine 0.1.54** source SHA and use CUDA 12.x / `sm_70` in a **new** Docker image, preserving all existing images, containers, ports and model assets. Do not use CUDA 13 on V100.
- Keep two independent single-V100 131072-context agents, original C2 workload/hash, CPU pinning, INT8 KV and model-matched native packs. Use **three valid fresh-process 128K C2 batches per selected arm**, with no prompt-prefix reuse and decoded overlap; archive invalid runs.
- **Do not rerun older 0.1.47/0.1.50/fork arms just for a new baseline.** Compare against historical results with the known GPU-clock and Linux page-cache caveats; do not claim causal version wins from non-interleaved data.
- IQ3_XXS S7-XXS-1..6, 8..13 and **14..16 are completed and closed**. Historical scripts/97 and scripts/99 and all results remain unchanged. S7-XXS-14/15/16 each passed **3/3 C2 (9/9 total)**; see [execution report](artifacts/stage7-results-20261101/stage7-iq3xxs-14-16-report.md) and [source/build audit](artifacts/stage7-results-20261101/stage7-iq3xxs-port-source-audit.md). Runner 100 pins the original 14 image and separate verified 15 WMMA2 / 16 LEAN images; source, compile, parity, dispatch and allocation gates were satisfied before enabling them. **Never rerun/reuse their IDs or treat retained runners as new execution orders.** No causal speedup or quality/promotion claim follows from these mechanical results. New experiments require separately approved scope and unique IDs. S7-XXS-7 remains optional/unauthorized. Do not silently inject SSD, WMMA2 or other flags into baseline arms.
- Choose **separate** runtime candidate settings for IQ2_XS and IQ3_S; do not copy IQ3_XXS defaults blindly. IQ3_S archive restoration requires disk/hash and active-service checks, not deletion of other models. Stage 6 is closed and is not reopened by Stage 7.
- Preserve power/clock settings, operating tunnel, serving ports, Stage 3–6 results and rollback paths. Use dedicated Stage 7 names and keep empirical metrics separate from claims.

## Stage 8 through M2 + C0 control (CLOSED BY USER SCOPE — 2026-11-07)

Read [final continuation review](docs/STAGE8_CONTINUATION_REVIEW.md),
[full metric summary](artifacts/stage8-followup-results-20261107/summary.md),
[Stage 8 plan](docs/STAGE8_PLAN.md) and [current state](state/current.md).

- U1 completed 3/3; follow-up C0/C1/C2/C3/M1/M2 each completed 3/3 concurrent 128K C2
  (**18/18 follow-up scored batches; 21/21 total Stage 8 scored batches**) plus
  one separately unscored D1 diagnostic. C3 medians: Prefill A/B 820.5/825.0 tok/s,
  Decode 29.0/28.7 tok/s, TTFT 155.00/154.14 s; C0 (`C1` minus `--pool-workers 3`,
  warm cache) Prefill 997.2/1006.3 tok/s, Decode 25.6/27.9 tok/s, TTFT 127.57/126.42 s;
  C1 (`--pool-workers 3`) Prefill 998.1/1007.2 tok/s, Decode 26.2/28.3 tok/s;
  M1 (`--spec 6`) Decode 25.3/26.1 tok/s; M2 (`--expert-cache-per-layer`) Decode
  25.8/26.2 tok/s. Dual-agent 30 tok/s goal NOT MET; no overall upgrade,
  semantic-quality validation or production promotion.
- M3 was evaluated analytically/empirically as feasible (~113 MiB VRAM trade-off)
  but unnecessary (KV VRAM hit already 97.7–98.9%, `kv-resolve` ~0.43 ms/window)
  and was NOT launched; no combination arms were run. Scripts 107–112 are
  retained as audit/reference, not permission to resume. All
  U1/D1/C0/C1/C2/C3/M1/M2 IDs and preparation-only u1-20261107T124317 are CLOSED;
  never reuse them.
- C0 isolates `C1` without `--pool-workers 3` (default 2 pool workers) via
  dedicated runner 112 while preserving scripts 107 and 111 unchanged. C2 uses a
  bounded 2 GiB pinned-resident budget per agent because D1 proved plain mmap
  has zero useful PCIe expert work despite fraction logs. C3 adds existing
  upstream --adapt-async 1 relative to completed C2; M1 and M2 each apply one
  single setting relative to U1 using dedicated runner 111. Keep these
  definitions explicit.
- Preserve all 1125 follow-up raw files, earlier U1/preparation receipts, runner
  snapshots, images, historical serving containers, original models/native
  pack/MTP, cpusets, independent GPU mapping, 131072 context and INT8 KV.
  Never rerun archived S7-XXS-14 for a new baseline.
- Initial/final serving state was empty. All owned experiment containers are
  stopped and retained; historical serving pair stays stopped/preserved.
  Keep existing 150 W limits, 135–1110 MHz lock, host settings, serving ports
  and ThinkPad tunnel. Application clocks of 1312 MHz do not alone indicate a
  missing GPU lock; inspect boot-service receipts and actual telemetry.
- New work or promotion requires a new user scope and fresh live preflight;
  no completed run or retained NEXT instruction authorizes it automatically.

## Stage 9 (CLOSED 2026-11-10; 9/9 C2 PASS, dual-agent 30 tok/s NOT MET)

Read [Stage 9 plan](docs/STAGE9_PLAN.md), [source audit](docs/STAGE9_SOURCE_AUDIT.md) and [candidate contract](bench/stage9-candidates.json) before proposing any execution. A GitHub documentation commit does NOT authorize P520 GPU work, server interruption, image replacement or production promotion.

- Operational reference remains **S7-XXS-14**, already CLOSED. No reference rerun. Stage 8 C1 is the speed-oriented alternative and C0 the lower-CPU alternative; neither is a proven balanced all-metric upgrade. Do not promote C3 for Decode alone at the expense of Prefill/TTFT.
- **S9-P0** source/host gate; **S9-U1** upstream engine 0.1.59 + baseline MTP recipe; **S9-D1** same pinned 0.1.59 engine + explicitly loaded, hash-verified DFlash2 (no MTP/fallback); **S9-F1** pinned V100 fork 8b4c09bd... + baseline MTP. Three independently valid, fresh dual-agent 128K C2 batches per supported scored arm (9 maximum), without any S7 baseline test. No new combinations or unapproved tuning.
- Verify full 0.1.59 *engine* source SHA rather than substituting v0.2.13's app tag, CUDA12/sm_70 build compatibility, fork WMMA2 default versus S7-XXS-14's no-port path, and DFlash2 head/pack/VRAM and actual active draft counters before scoring. Fork and upstream binaries are separate sources and images.
- Preserve original model/pack/KV/MTP assets, CPU/GPU mapping, frozen C2 workload, 150 W cap/1110 MHz limit, serving ports, historical containers/results and ThinkPad tunnel. Inspect live host before any possible new run; the Nov 7 state is not proof of idleness on Nov 10.
- Evaluate **both agents' Prefill, Decode, TTFT, full-lifetime GPU thermal/power mean and peak, CPU/RAM/swap/page-cache/I/O and acceptance**. No score or promotion claim without raw receipts; no semantic-quality claim from mechanical C2 PASS.

## Stage 9 execution amendment — 2026-11-10 user instruction

The user explicitly said “중단하지마!” and “1245로 진행할거야!” after observed startup SM clocks reached 1245 MHz. For this authorized Stage 9 campaign, accept observed SM clocks up to **1245 MHz** while preserving the existing 150 W limits and all hardware/host settings; this does not authorize a clock/power command. The original `u1-20261110T173436` is CLOSED, startup-only, zero scored C2, automatically failed under the previous 1110 MHz gate. Preserve it and use a new ID under the amended clock observation criterion. No scored retries, baseline reruns, tuning combinations or promotion. Historical clock envelopes differ and must remain explicit in comparisons.

## Stage 9 closure — read before any new work

Read [final review](docs/STAGE9_REVIEW.md), [full metrics](artifacts/stage9-results-20261110/summary.md) and [final host audit](artifacts/stage9-results-20261110/final-host-check.json). U1 `u1-20261110T173748`, D1 `d1-20261110T175220` and F1 `f1-20261110T180620` each completed 3/3 concurrent 128K C2, **9/9 total**. All IDs, first startup-only `u1-20261110T173436`, and P0 preparation attempts are CLOSED. Never rerun/reuse them. Scripts 113–119 and original plan are audit/reference only; the candidate manifest is no longer execution-authorized. No extra tuning, reference rerun or promotion.

Decode medians A/B: U1 26.1/28.8, D1 28.2/29.4, F1 26.3/26.0. No dual-agent 30 result, all-metric upgrade, or semantic quality validation. D1 improved descriptive speed but had higher full-lifetime mean power/temperatures; S7-XXS-14 remains the unrerun archived operational reference.

The host clock journal changed separately after initial inspection: 17:14:21 fixed 1245, then 17:15:59 **135–1245 MHz**. The agent issued no clock/power command; the user explicitly approved continuing at 1245. All scored batches occurred afterward. Final host policy is 135–1245, configured caps 150 W, GPUs idle, all serving stopped/preserved and tunnel active. **Do not restore 1110 or change clocks/power/host settings automatically.** Preserve 675 SHA-matched backed-up evidence files, original assets/native pack/MTP, all 278 initial containers and prior images. New work requires a new explicit scope and live preflight.
