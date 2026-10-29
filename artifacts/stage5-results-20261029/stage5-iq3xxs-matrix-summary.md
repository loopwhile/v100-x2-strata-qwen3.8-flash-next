# Stage 5 IQ3_XXS — experiment matrix (2026-10-29)

Two independent 128K agents on P520, A GPU0/cpuset `0-2,6-8`, B GPU1/cpuset `3-5,9-11`, INT8 KV, existing MTP and frozen C2 manifest `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`. Rates below are **per-agent medians across three batches**, not combined throughput. Every listed dual-agent batch passed the mechanical, active-decode-overlap and post-health checks, generated at least 1024 tokens per agent, had `cache_n=0`, `cached_tokens=0`, and finished with `stop`.

| Arm | Recipe | A/B prefill tok/s | A/B decode tok/s | A/B TTFT s | Median batch wall s |
| --- | --- | --- | --- | --- | ---: |
| T1 | upstream 0.1.47 | 889.6 / 902.7 | 27.1 / 25.7 | 142.99 / 140.93 | 235.02 |
| T2 | T1 + SELECT_SIMT | 1010.4 / 1019.2 | 25.9 / 26.7 | 125.91 / 124.86 | 203.41 |
| T3 | T1 + PF_WMMA | 890.3 / 894.1 | 25.3 / 25.8 | 142.86 / 142.27 | 228.36 |
| T4 | T1 + SELECT_SIMT + PF_WMMA | 992.8 / 1000.6 | 26.5 / 26.2 | 128.12 / 127.16 | 198.33 |
| T6-Fixed | upstream 0.1.50 + STAGER_SSD=0 | 887.3 / 896.7 | 26.4 / 25.6 | 143.36 / 141.86 | 216.46 |
| T7 default | fork `2c9b1dd` + SIMT + WMMA + STAGER_SSD=0; default SM70 bundle | 1034.9 / 1040.8 | 23.5 / 24.2 | 122.95 / 122.25 | 209.17 |
| T7-Fixed | fork `2c9b1dd`, SM70_PERF=0 + SIMT + WMMA + WMMA2 + STAGER_SSD=0 | 1030.7 / 1044.9 | 26.6 / 26.7 | 123.46 / 121.78 | 214.49 |
| T8 | upstream 0.1.50 + SIMT + WMMA + STAGER_SSD=0 | 990.5 / 996.8 | 26.7 / 26.0 | 128.45 / 127.64 | 199.44 |

T5 resource contention diagnostic used upstream 0.1.47 and the current post-change clock condition. A alone: prefill 921.2, decode 27.2 tok/s, TTFT 138.07 s; B alone: 928.8, 25.7 tok/s, 136.95 s. Simultaneous control: A 890.9/26.6 and B 896.8/24.6 tok/s (prefill/decode), TTFT 142.83/141.86 s, 236.62 s batch wall; all three runs passed their applicable checks. These are **one measurement per mode**, with possible OS page-cache differences, and do not establish a repeatable contention effect. The isolated single-agent runner initially failed twice before inference (tokenizer API and manifest path); those attempts remain preserved. Its fallback expert-hit and file counters are not reliable and are not reported.

## Comparability and limitations

- The machine rebooted unexpectedly during T1's original third run. It has no final summary or post-health and is **inconclusive**, not a pass or a new run to combine with a retry. T1's first two successful runs preceded the reboot; the third was a new successful retry after thermal paste replacement and reboot. OS page-cache warmth differed substantially.
- The user changed GPU clock settings after T2 and before T3. Observed SM clock samples during T3, T4, T5, T6, T7 default and T8 were at most 1110 MHz; previous T1/T2/T7-Fixed measurements were taken before this change. No clock or power settings were changed by this experiment. Comparisons across that boundary mix hardware conditions and cannot isolate effects of the software flags. Measurements are not interleaved, and varying generated lengths affect batch wall times.
- T7-Fixed was tested earlier, not re-run after the clock change. Its full receipt is [here](stage5-iq3xxs-t7fixed-summary.md). T7 default enables the fork's SM70 default bundle and is not a single-flag ablation. Whether each configured kernel actually ran for IQ3_XXS has not been established. No comprehensive coding-quality evaluation was performed; C2 mechanical success is not semantic quality validation. A small JSON smoke previously passed for T7-Fixed only.
- T2 and T7-Fixed show the largest recorded prefill medians, but no production winner or causally attributed improvement is established. The T7 default's lower decode values versus the historical fixed recipe are observations under different clock conditions. No promotion is authorized by these tests.

## Receipts and current state

The 0.1.47 image ID is `sha256:19c3b72a1097486eeae3fd9b964179a36a1c137615e5c93f6d6e70eacdab8e9d`; 0.1.50 is `sha256:91fe3614de84290c458aa9a50992d35af252507bef9b3a59de6f33737849c393` (engine SHA-256 `01343af269c05318e347bcb60d7e0d6cd3a4e0b20014c4bd0d753e5ac7b5a0da`); fork ID is `sha256:5b62fa861bbdb346f81b0b3edf88ee21396fb4e59795a14b2b092dfa2e4aa156`.

P520 raw evidence, configs, scripts, failures and continuous sampled GPU telemetry are in `~/v100-x2-strata-qwen3.8-flash-next/results/stage5-iq3xxs-matrix/` and `results/c2-stage5-*-iq3xxs-*`. An ignored local backup is `results/p520-stage5-iq3xxs-full-20261029/`. Files may contain request contents; review before sharing. All trial containers were stopped after their batches and left intact; the final check found no running Docker containers, 0 MiB used on both GPUs, and 150 W power limits. Earlier unexpected reboot remains unexplained. IQ3_S was archived as documented in the prior receipt and must be restored before future IQ3_S work.
