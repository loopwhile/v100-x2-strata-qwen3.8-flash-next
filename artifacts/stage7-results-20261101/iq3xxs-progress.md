# Stage 7 IQ3_XXS — preliminary execution receipt

Status: in progress; no promotion. P520 source `870aedd9e1ebe1c91f94da93b59af17729f6c5c0`, Qwen engine 0.1.54, CUDA 12.9 / sm_70, image `sha256:2095eed79b0038ef23d602a0490bf0d89c63ad8e84ace8654c5016b2a51d2246`, binary SHA-256 `e98d7c6316500dfce9c05784557b3f20f6a340bdc853aaa49d479697f6247b4e`. Frozen C2 manifest SHA-256 `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`. Both model shard hashes matched their Stage 5 receipt. The model hash verification warmed filesystem cache.

Short health/API smoke passed; separately labeled `compat-3` 128K compatibility passed, not included below. `compat-1` and `compat-2` failed before inference due to a mistyped hash constant in a new runner; corrected; logs preserved on P520.

| S7-XXS-1 vanilla | A/B prefill tok/s | A/B decode tok/s | A/B TTFT s | Batch wall s | Verdict |
| --- | --- | --- | --- | ---: | --- |
| 1 | 847.9 / 853.6 | 23.9 / 24.8 | 150.02 / 149.02 | 255.46 | PASS |
| 2 | 880.9 / 884.0 | 24.1 / 24.4 | 144.40 / 143.89 | 250.70 | PASS |
| 3 | 883.6 / 891.5 | 24.0 / 24.1 | 143.97 / 142.68 | 251.61 | PASS |
| Median | 880.9 / 884.0 | 24.0 / 24.4 | 144.40 / 143.89 | 251.61 | 3/3 |

All three passed exact A/B prompt counts, output >=1024, zero cache reuse, concurrent decode, stop and post-health checks. Inputs and outputs are per-agent. Results are not quality evaluations. Linux cache residency, GPU clocks, swap and I/O were captured per batch; historical comparisons are non-interleaved and cannot establish causal version improvements. P520 raw evidence: `~/v100-x2-strata-qwen3.8-flash-next/results/stage7-iq3xxs/xxs-1-{1,2,3}`. `file_mb` is logical expert reads, not physical storage I/O.

At startup, Agent A logs reported the expert GGUF as 99%, 100% and 100% page-cached across vanilla runs 1–3 and selected the RAM stager profile. `STRATA_ROUTE_TAIL_SKIP=7` was reported as an engine default. File-level `fincore` and the engine's expert-region cache estimate measure different scopes. No claim of quality or isolated version effect follows from these observations.

| S7-XXS-2 SIMT only | A/B prefill tok/s | A/B decode tok/s | A/B TTFT s | Batch wall s | Verdict |
| --- | --- | --- | --- | ---: | --- |
| 1 | 992.6 / 996.9 | 24.9 / 24.6 | 128.18 / 127.63 | 212.01 | PASS |
| 2 | 994.3 / 1001.2 | 25.0 / 24.7 | 127.97 / 127.10 | 211.65 | PASS |
| 3 | 992.6 / 1000.5 | 25.6 / 24.6 | 128.17 / 127.20 | 212.26 | PASS |
| Median | 992.6 / 1000.5 | 25.0 / 24.6 | 128.17 / 127.20 | 212.01 | 3/3 |

SIMT override only: `STRATA_SELECT_SIMT=1`; `STRATA_STAGER_SSD=0` was not forced. Three batches passed the same mechanical checks. Raw evidence: `~/v100-x2-strata-qwen3.8-flash-next/results/stage7-iq3xxs/xxs-2-{1,2,3}`. This sequential, non-interleaved comparison does not control all cache and clock variation.

| S7-XXS-3 WMMA only | A/B prefill tok/s | A/B decode tok/s | A/B TTFT s | Batch wall s | Verdict |
| --- | --- | --- | --- | ---: | --- |
| 1 | 882.4 / 888.7 | 24.2 / 24.8 | 144.16 / 143.15 | 229.69 | PASS |
| 2 | 885.5 / 891.5 | 23.7 / 25.5 | 143.65 / 142.69 | 221.03 | PASS |
| 3 | 885.6 / 890.0 | 24.1 / 25.0 | 143.61 / 142.93 | 233.69 | PASS |
| Median | 885.5 / 890.0 | 24.1 / 25.0 | 143.65 / 142.93 | 229.69 | 3/3 |

Only `STRATA_PF_WMMA=1` was forced. The source has a conditional WMMA path and the pack contains potentially eligible formats; actual WMMA kernel execution has not been verified. Raw evidence: `~/v100-x2-strata-qwen3.8-flash-next/results/stage7-iq3xxs/xxs-3-{1,2,3}`. Output lengths vary, affecting batch wall time.

ThinkPad and P520 `bench/c2_v100_contract.py` SHA-256 both matched `a8e42cc5a71421a7287618fd5be0332ae40f312426e4d243ce1c7619fdfc5246` when checked during S7-XXS-4.

| S7-XXS-4 SIMT + WMMA | A/B prefill tok/s | A/B decode tok/s | A/B TTFT s | Batch wall s | Verdict |
| --- | --- | --- | --- | ---: | --- |
| 1 | 988.1 / 994.4 | 24.5 / 24.1 | 128.76 / 127.93 | 216.50 | PASS |
| 2 | 992.0 / 996.3 | 24.8 / 24.4 | 128.25 / 127.70 | 209.30 | PASS |
| 3 | 987.7 / 993.5 | 24.6 / 24.6 | 128.78 / 128.09 | 215.46 | PASS |
| Median | 988.1 / 994.4 | 24.6 / 24.4 | 128.76 / 127.93 | 215.46 | 3/3 |

Overrides: `STRATA_SELECT_SIMT=1`, `STRATA_PF_WMMA=1`; stager not forced. All batches passed the same mechanical checks. Actual WMMA kernel execution remains unverified. Raw evidence: `~/v100-x2-strata-qwen3.8-flash-next/results/stage7-iq3xxs/xxs-4-{1,2,3}`.

| S7-XXS-5 SSD stager disabled | A/B prefill tok/s | A/B decode tok/s | A/B TTFT s | Batch wall s | Verdict |
| --- | --- | --- | --- | ---: | --- |
| 1 | 885.4 / 892.0 | 24.2 / 25.0 | 143.66 / 142.63 | 242.83 | PASS |
| 2 | 885.2 / 891.4 | 23.8 / 23.9 | 143.67 / 142.70 | 238.47 | PASS |
| 3 | 886.7 / 892.0 | 24.1 / 24.6 | 143.44 / 142.59 | 236.19 | PASS |
| Median | 885.4 / 892.0 | 24.1 / 24.6 | 143.66 / 142.63 | 238.47 | 3/3 |

Only `STRATA_STAGER_SSD=0` was forced. Raw evidence: `~/v100-x2-strata-qwen3.8-flash-next/results/stage7-iq3xxs/xxs-5-{1,2,3}`. The engine had already selected RAM stager profile under the observed warm-cache vanilla conditions; avoid treating this comparison as evidence of a cold-SSD stager effect.

| S7-XXS-6 SIMT + WMMA + SSD stager disabled | A/B prefill tok/s | A/B decode tok/s | A/B TTFT s | Batch wall s | Verdict |
| --- | --- | --- | --- | ---: | --- |
| 1 | 986.9 / 994.3 | 24.9 / 24.5 | 128.90 / 127.98 | 208.45 | PASS |
| 2 | 989.7 / 998.0 | 24.3 / 24.2 | 128.56 / 127.49 | 218.88 | PASS |
| 3 | 990.6 / 995.6 | 24.8 / 24.6 | 128.43 / 127.79 | 213.57 | PASS |
| Median | 989.7 / 995.6 | 24.8 / 24.5 | 128.56 / 127.79 | 213.57 | 3/3 |

All six selected arms now have three runner-PASS batches each. This receipt is preliminary: independently audit raw data, telemetry, stager behavior and contract checks before final reporting. Exact WMMA kernel execution remains unverified. No quality suite or deployment promotion was performed.
