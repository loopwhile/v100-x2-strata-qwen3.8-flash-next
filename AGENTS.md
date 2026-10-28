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

## Stage 6 (S6-0 COMPLETE; continue S6-1..S6-7)

**Mandatory: read [full Stage 6 S6-0..S6-7 plan](docs/STAGE6_PLAN.md), [Codex continuation handoff](docs/STAGE6_CODEX_HANDOFF.md) and [Stage 6 isolated-container prep](docs/STAGE6_PREP.md).** S6-0 completed and is recorded in [baseline](artifacts/stage6-results-20261028/s6-baseline.md); **next is S6-1, not another baseline test**. Do not stop after S6-0; progress to S6-7, marking tested/rejected/skipped arms with evidence. No production change without explicit authorization.  Stage 6 holds GPU0/A and GPU1/B independent with the existing CPU affinities, 64 GB shared RAM, same model/SSD, 128K context and 150W GPU caps. No layer split or single-agent promotion. Treat the Stage 5 T7-Fixed image/recipe as a pinned baseline; reserved host loopback ports are 18082/18083, not production 8080/8081. The new scripts must never stop or delete preserved agents; P520 execution requires a separately approved test window.

Stage 6 candidate config rule: Generate independent ignored `results/stage6/arms/<arm-id>/` A/B configs with `scripts/93-stage6-prepare-arm.py`; never overwrite committed baseline JSON or old results. Select via `STRATA_S6_ARM_DIR` only when creating Stage 6 test containers. `scripts/91-bench-stage6-c2.sh` auto-detects the running config bind mount and refuses scored C2 with profiler flags; a deliberate third argument `--diagnostic` distinguishes S6-1 timing measurements. A Stage 6 test iteration may stop/remove **Stage 6-only** containers; no code may stop/remove production or preserved Stage 2–5 containers. Keep the user's same GPU/CPU/RAM/SSD topology in every Phase.
