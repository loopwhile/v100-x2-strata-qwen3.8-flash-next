# Stage 10 Progress & Empirical Results (2026-11-10 KST)

**Status: Paused by user request ("여기서 일시 중단하고 커밋 푸시해줘."). 21 scored batches and 1 diagnostic batch completed 100% PASS with 0 retries.**

## Baseline and Candidate Comparison

All benchmarks were executed on Lenovo ThinkStation P520 (dual Tesla V100 SXM2 16GB, 150 W configured limits, 135-1245 MHz clock lock, 131072 context, INT8 KV, GSQ-RCO IQ3_XXS + DFlash2 stock selector pack, frozen C2 128K prompt workload).

| Arm | Exact Change | Valid C2 | Prefill A/B tok/s | Decode A/B tok/s | TTFT A/B s | Verdict | Notes |
|---|---|:---:|---:|---:|---:|:---:|---|
| S7-XXS-14 (archived) | 0.1.54 + MTP | 3/3 | 997.6 / 1006.6 | 26.4 / 26.2 | 127.53 / 126.48 | PASS | Historical reference |
| S8-C0 (archived) | 0.1.57 + MTP | 3/3 | 997.2 / 1006.3 | 25.6 / 27.9 | 127.57 / 126.42 | PASS | Historical reference |
| S8-C1 (archived) | 0.1.57 + MTP | 3/3 | 998.1 / 1007.2 | 26.2 / 28.3 | 127.45 / 126.32 | PASS | Historical reference |
| **S9-D1 (Baseline)** | 0.1.59 + stock DFlash2 | 3/3 | **1026.5 / 1032.6** | **28.2 / 29.4** | **123.92 / 123.21** | PASS | Stage 10 starting baseline |
| **S10-P0** | `STRATA_DECODE_TIMING=1`, `STRATA_VERIFY_PROFILE=1` | 1 diag | 954.1 / 959.7 | 27.4 / 27.7 | 133.35 / 132.57 | DIAG PASS | Profiling shows `waitCPU`: 50.64 ms, `adapt join`: 9.66 ms, `draft`: 2.85 ms |
| **S10-D2** | `--draft-conf 0.5` | 3/3 | 1027.0 / 1033.4 | 27.6 / 27.5 | 123.87 / 123.11 | PASS | Lower draft threshold causes rejection/verification overhead |
| **S10-D3** | `--draft-conf 0.6` | 3/3 | 1027.8 / 1032.2 | 28.3 / 29.3 | 123.77 / 123.25 | PASS | Intermediate threshold comparable to 0.7 sweet spot |
| **S10-K1** | `STRATA_ADAPT_LAG=2` | 3/3 | 1026.1 / 1034.4 | 28.2 / **30.8** | 123.98 / 123.01 | PASS | **Agent B crossed 30.0 tok/s in all 3 batches (30.9, 30.8, 30.8)!** |
| **S10-K2** | `STRATA_ADAPT_LAG=2` + `NOWAIT=1` | 3/3 | 1029.7 / 1033.8 | **29.2 / 30.0** | 123.55 / 123.07 | PASS | **Slower agent decode reached record 29.2 tok/s; Agent B hit 30.0 tok/s** |
| **S10-K3** | `STRATA_SIDE_MIXER=2` | 3/3 | 1026.8 / 1035.7 | 28.3 / 28.2 | 123.87 / 122.85 | PASS | Side stream graph branching adds overhead on sm_70 when CPU bottlenecked |
| **S10-P1** | `STRATA_PF_HC_REGION=1` | 3/3 | **1036.5 / 1044.0** | 28.2 / 28.4 | **122.74 / 121.88** | PASS | **Prefill record high (+10-11 tok/s, TTFT -1.3s), zero decode penalty** |
| **S10-P2** | `STRATA_EMB_REUSE_ACCOUNT=1` | 3/3 | 1029.2 / 1034.1 | 27.8 / 28.3 | 123.61 / 123.01 | PASS | Modest prefill gain (+2~3 tok/s), inferior to P1 |
| **S10-P3** | `--prefill auto:16384` | 0/3 | — / — | — / — | — / — | **FAIL_POWER_TRIP** | Sustained 16384 chunk tensor burst trips host PSU; permanently rejected |

## Detailed Breakdown of Key Findings

### 1. DFlash2 Draft Speed vs Verification Bottleneck (S10-P0)
From the high-resolution instrumentation log in `S10-P0`:
```
strata decode timing: 936 windows, avg T 2.81, 2.48 tokens/window, 90.48 ms/window =
  adapt wait 0.02 +
  verify 77.85 (GPU-reach wait 21.35 + per-layer host 53.43 [plan 0.30 actq 0.24 jobs 1.94 CPU 50.64] + stage 0.02) +
  commit/emit 0.08 +
  draft 2.85 +
  adapt join 9.66 +
  other 0.02
```
- DFlash2 drafting took only **2.85 ms** per window, generating an average of 2.48 accepted tokens per verify window.
- The dominant bottleneck was CPU expert misses and computation (**50.64 ms** out of 90.48 ms).
- The secondary bottleneck was adaptive swap join synchronization (**9.66 ms**).

### 2. Adaptive Scheduler Optimization (S10-K1 and S10-K2)
- Applying `STRATA_ADAPT_LAG=2` decouples the current verify window from pending adaptive swaps, hiding the 9.66 ms join stall.
- In **S10-K1**, Agent B achieved **30.9, 30.8, and 30.8 tok/s** across all three scored batches, marking the first time any agent has exceeded 30 tok/s in dual-agent concurrent 128K C2 serving.
- Adding `STRATA_ADAPT_NOWAIT=1` in **S10-K2** improved Agent A from 28.2 tok/s to **29.2 tok/s** (peaking at 29.8 tok/s), resulting in the highest slower-agent decode throughput ever recorded on this platform.

### 3. Hyper-Connection Memory Region Aliasing (S10-P1)
- Setting `STRATA_PF_HC_REGION=1` aliases the hyper-connection scratch memory in the prefill stage into the shared region.
- This boosted prompt throughput by **+10.0 / +11.4 tok/s** (Agent A 1036.5, Agent B 1044.0 tok/s) and shaved 1.2 to 1.3 seconds off TTFT (**122.74 / 121.88 s**), with zero impact on decode throughput or stability.

### 4. Hardware Safety Limit on Prefill Chunk Size (S10-P3)
- Lifting the auto prefill chunk size to 16384 (`--prefill auto:16384`) resulted in sustained tensor core saturation on both GPUs simultaneously, triggering PSU over-current/over-voltage protection (OCP/OVP) and immediate system power reboot.
- This candidate was classified as `REJECTED (FAIL_HARDWARE_POWER_TRIP)`. Default 8192 chunking remains the mandatory safe envelope for dual-V100 SXM2.

## Next Prospective Work (When Resumed)
When Stage 10 testing is resumed by the user, the clear winning candidates to evaluate are:
1. **S10-D4**: `--spec 8` (longer speculative window with baseline conf 0.7 or 0.6).
2. **S10-C1**: Sequenced combination of verified winners:
   `STRATA_ADAPT_LAG=2`, `STRATA_ADAPT_NOWAIT=1`, and `STRATA_PF_HC_REGION=1`.
   This combination is expected to deliver **Prefill ~1044 tok/s and Decode ~29.5 - 30.5 tok/s simultaneously**.
