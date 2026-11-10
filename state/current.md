# Current operation — stable P520 serving STOPPED BY USER (2026-11-11 KST)

The user selected **S10-D4** for the fixed operating containers/API model IDs
`p520-llm-a` and `p520-llm-b`. P520 loopback ports remain 8080/8081 and the
unchanged ThinkPad tunnel remains 18080/18081. OpenCode is migrated once to
`p520-a/p520-llm-a` (default) and `p520-b/p520-llm-b`.
See [operating guide](../docs/P520_SERVING.md) for start/stop/status/rollback.
Both containers are configured from release `s10-d4-20261111T012331`, using native
API aliases to preserve the Qwen family identification needed by DFlash2.
Health, exact D4 engine-argument parity, tunnel chat and OpenCode A/B smoke
requests passed. [Deployment verification](../artifacts/p520-serving-20261111/summary.md)
is separate from benchmark results. The initial name-detection startup attempt
is stopped/preserved under separate archive names. No archived C2 was rerun.
After these checks, the user stopped `p520-llm-a` and `p520-llm-b`; live
inspection confirmed both are `exited`. Keep them stopped during commit/push
and checkout synchronization. Starting serving is a separate operating action.

## Archived Stage 10 completion — 2026-11-10 KST, 27 scored + 1 diagnostic C2 PASS

**Status: Stage 10 optimization completed. All 27 scored batches and 1 diagnostic batch completed 100% PASS with 0 retries across 10 arms. All evidence backed up to ThinkPad and verified with SHA256.**

## Executive Summary of Stage 10 Findings

Dual-V100 SXM2 (150 W limit, 135-1245 MHz clock lock, 131072 context, INT8 KV, GSQ-RCO IQ3_XXS + DFlash2 stock selector pack):

| Candidate | Configuration Delta | Valid C2 | Prefill A / B (tok/s) | Decode A / B (tok/s) | TTFT A / B (s) | Verdict | Key Finding |
|---|---|:---:|---:|---:|---:|:---:|---|
| **S9-D1 (Baseline)** | Stock DFlash2 (conf 0.7, spec 6) | 3/3 | 1026.5 / 1032.6 | 28.2 / 29.4 | 123.92 / 123.21 | PASS | Stage 10 reference point |
| **S10-P0** | Timing/GPU stage profiling | 1 diag | 954.1 / 959.7 | 27.4 / 27.7 | 133.35 / 132.57 | DIAG PASS | Profiling shows `waitCPU`: 50.64 ms, `adapt join`: 9.66 ms, `draft`: 2.85 ms |
| **S10-D2** | `--draft-conf 0.5` | 3/3 | 1027.0 / 1033.4 | 27.6 / 27.5 | 123.87 / 123.11 | PASS | Lower threshold causes verification overhead regression |
| **S10-D3** | `--draft-conf 0.6` | 3/3 | 1027.8 / 1032.2 | 28.3 / 29.3 | 123.77 / 123.25 | PASS | Intermediate threshold performs comparably to 0.7 sweet spot |
| **S10-K1** | `STRATA_ADAPT_LAG=2` | 3/3 | 1026.1 / 1034.4 | 28.2 / **30.8** | 123.98 / 123.01 | PASS | **Agent B crossed 30.0 tok/s in all 3 batches (30.9, 30.8, 30.8)!** |
| **S10-K2** | `STRATA_ADAPT_LAG=2` + `NOWAIT=1` | 3/3 | 1029.7 / 1033.8 | **29.2 / 30.0** | 123.55 / 123.07 | PASS | **Slower agent decode reached record 29.2 tok/s; Agent B hit 30.0 tok/s** |
| **S10-K3** | `STRATA_SIDE_MIXER=2` | 3/3 | 1026.8 / 1035.7 | 28.3 / 28.2 | 123.87 / 122.85 | PASS | Side stream graph branching adds latency on sm_70 when CPU bottlenecked |
| **S10-P1** | `STRATA_PF_HC_REGION=1` | 3/3 | **1036.5 / 1044.0** | 28.2 / 28.4 | **122.74 / 121.88** | PASS | **Prefill record high (+10-11 tok/s, TTFT -1.3s), zero decode penalty** |
| **S10-P2** | `STRATA_EMB_REUSE_ACCOUNT=1` | 3/3 | 1029.2 / 1034.1 | 27.8 / 28.3 | 123.61 / 123.01 | PASS | Modest prefill gain (+2~3 tok/s), inferior to P1 |
| **S10-P3** | `--prefill auto:16384` | 0/3 | — / — | — / — | — / — | **FAIL_POWER_TRIP** | Sustained 16384 chunk tensor burst trips host PSU; permanently rejected |
| **S10-D4** | `--spec 8` (conf 0.7, prefill auto) | 3/3 | 1025.1 / 1027.8 | **30.4 / 30.3** | 124.08 / 123.79 | **PASS** | **MAJOR BREAKTHROUGH: Both agents simultaneously crossed 30.0 tok/s!** |
| **S10-C1** | `--spec 8` + `ADAPT_LAG=2` + `NOWAIT=1` | 3/3 | 1025.7 / 1029.1 | 27.5 / 28.9 | 124.03 / 123.64 | PASS | Regressed due to 16-token expert cache staleness; D4 alone remains superior |

### Verified Breakthroughs in Stage 10
1. **Decode Breakthrough (S10-D4)**:
   - Expanding the speculative proposal window to 8 tokens (`--spec 8`, conf 0.7) pushed **both Agent A and Agent B past the 30.0 tok/s decode threshold simultaneously** (Medians: Agent A **30.4 tok/s**, Agent B **30.3 tok/s**).
   - In warm-cache conditions, every single batch exceeded 30.3 tok/s (peaking at 30.6 / 30.5 tok/s).
2. **Scheduler Composition Finding (S10-C1)**:
   - While `STRATA_ADAPT_LAG=2` + `STRATA_ADAPT_NOWAIT=1` is optimal for 6-token speculative windows (S10-K2: 29.2 / 30.0 tok/s), combining it with `--spec 8` causes a 16-token lag in expert cache swaps. This stale cache penalty reduces decode throughput to 27.5 / 28.9 tok/s.
   - S10-D4 with default synchronous adaptive scheduler is therefore the undisputed decode champion.
3. **Prefill Breakthrough (S10-P1)**:
   - `STRATA_PF_HC_REGION=1` aliased hyper-connection scratch memory into the shared region, increasing prompt throughput from 1026.5 / 1032.6 tok/s to **1036.5 / 1044.0 tok/s** and cutting TTFT to **122.74 / 121.88 s**.
4. **Hardware Safety Discovery (S10-P3)**:
   - Doubling auto prefill chunk size to 16384 causes extreme transient PSU saturation triggering OCP power cuts. Flag permanently rejected for dual-V100 SXM2 stability.

### Evidence & Backups
- All 10 completed arms (P0, D2, D3, K1, K2, K3, P1, P2, D4, C1) have raw evidence backed up locally to `results/raw/<id>/` with SHA256 manifests.
- P520 is clean and idle, with zero running containers, 0 MiB GPU usage, active `v100-clock-lock.service` (135-1245 MHz), and 150 W power caps.
- ThinkPad `strata-tunnel.service` remains running.
