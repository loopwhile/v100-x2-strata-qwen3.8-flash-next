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
