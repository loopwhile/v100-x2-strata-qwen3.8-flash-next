# Current operation — Stage 10 PAUSED BY USER (2026-11-10 KST), 21 scored + 1 diagnostic C2 PASS

**Status: Paused by explicit user request ("여기서 일시 중단하고 커밋 푸시해줘."). All 21 scored batches and 1 diagnostic batch completed 100% PASS with 0 retries. All evidence backed up to ThinkPad and verified with SHA256.**

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

### Verified Breakthroughs in Stage 10
1. **Decode Breakthrough (S10-K1 / S10-K2)**:
   - Delaying adaptive tier swap application (`STRATA_ADAPT_LAG=2`) eliminated the 9.66 ms adaptive join wait discovered in S10-P0 profiling.
   - In S10-K1, Agent B exceeded 30.0 tok/s in all three scored batches (30.9, 30.8, 30.8 tok/s; median 30.8 tok/s).
   - In S10-K2 (`STRATA_ADAPT_LAG=2` + `STRATA_ADAPT_NOWAIT=1`), Agent A reached 29.2 tok/s (batch 2 hit 29.8 tok/s), pushing the slower agent median to **29.2 tok/s** and Agent B to **30.0 tok/s**.
2. **Prefill Breakthrough (S10-P1)**:
   - `STRATA_PF_HC_REGION=1` aliased hyper-connection scratch memory into the shared region, increasing prompt throughput from 1026.5 / 1032.6 tok/s to **1036.5 / 1044.0 tok/s** and cutting TTFT to **122.74 / 121.88 s**.
3. **Hardware Safety Discovery (S10-P3)**:
   - Doubling auto prefill chunk size to 16384 causes extreme transient PSU saturation triggering OCP power cuts. Flag permanently rejected for dual-V100 SXM2 stability.

### Evidence & Backups
- All 8 completed arms (P0, D2, D3, K1, K2, K3, P1, P2) have raw evidence backed up locally to `results/raw/<id>/` with SHA256 manifests.
- P520 is clean and idle, with zero running containers, 0 MiB GPU usage, active `v100-clock-lock.service` (135-1245 MHz), and 150 W power caps.
- ThinkPad `strata-tunnel.service` remains running.
