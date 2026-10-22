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
