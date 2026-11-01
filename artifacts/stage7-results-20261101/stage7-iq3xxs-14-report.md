# S7-XXS-14 execution report — 2026-11-01

**S7-XXS-14: 3/3 fresh dual-agent 128K C2 PASS.** This report covers arm 14 only. No promotion or production change.

| Batch | Prefill A / B (tok/s) | Decode A / B (tok/s) | TTFT A / B (s) | Output A / B | Wall (s) | Decode overlap (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| xxs-14-1 | 997.6 / 1006.6 | 26.4 / 26.2 | 127.53 / 126.64 | 1674 / 2224 | 211.54 | 63.26 |
| xxs-14-2 | 996.4 / 1006.0 | 25.9 / 26.7 | 127.67 / 126.48 | 1737 / 2577 | 222.95 | 67.00 |
| xxs-14-3 | 999.9 / 1008.1 | 26.5 / 25.8 | 127.21 / 126.20 | 1762 / 2101 | 207.70 | 66.45 |

Per-agent medians: **Prefill 997.6 / 1006.6 tok/s; Decode 26.4 / 26.2 tok/s; TTFT 127.53 / 126.48 s.** Median batch wall 211.54 s. Prefill ranges A 996.4–999.9, B 1006.0–1008.1; decode ranges A 25.9–26.5, B 25.8–26.7.

All three batches: A/B prompts 126967 / 126968; outputs >=1024; cache_n=cached_tokens=0; finish_reason=stop; no warmup; overlapping decode; passing post-health; distinct container IDs and fresh processes. Original manifest, configs, CPU/GPU mapping and upstream image were preserved. Runner SHA-256: `287146daaaf31b449219203373ecb5bc3d8202beae87cb03d14a45f2768f6797`. Original records are on P520 and backed up on ThinkPad under `results/stage7-iq3xxs-v100-port/`.

Compared descriptively with archived S7-XXS-13 medians (1004.2 / 1010.6 prefill; 26.5 / 26.1 decode), these runs show **no established improvement**. The arms were sequential and not interleaved; page-cache/time/output/MTP differences prevent a causal attribution. WMMA changes numerical behavior; no quality suite was run.

GPU telemetry: configured caps remained 150 W throughout; active SM median and observed maximum 1110 MHz on both GPUs. Maximum temperatures A/B 65/64 °C, VRAM 15585 MiB each. One-second sampled power maxima A/B 172.87/177.57 W; these are measured samples, not configured-cap changes.

## Additional diagnostic and scope correction

After the three scored batches, the agent added a separate non-scored dual-agent 128K diagnostic to observe actual WMMA launches via CUPTI. The user objected to this extra work and clarified the scope as three C2 batches per requested arm. This diagnostic was an agent-added scope expansion; it must not become a default or prerequisite for repeating arm 14.

`smoke14-trace-1` failed its port preflight before creating containers/results because TIME_WAIT was mistaken for an occupied listener. The port check was corrected and a new ID used. `smoke14-trace-2` completed at **22:15:41 KST**, before the termination/status check, with `SMOKE_PASS_NOT_SCORED`. Both agents recorded successful driver launches of the original generic WMMA kernels. This is **not a fourth C2 score** and is excluded from all metrics above. One CPU-only temporary container compiled the tracing library; no 15/16 engine image was built.

At the final live check both GPUs had **0 MiB, 0% utilization**, no running containers, and 150 W limits. The user subsequently explicitly requested proceeding with 15/16; those operations belong to the separate port execution record. No further arm-14 run is planned. Historical containers/images/models, 8080/8081 and the ThinkPad tunnel remained unchanged. Initial service state was empty; no production container was automatically started.

## Separate 15/16 execution track

Pinned upstream WMMA2 dispatch covers IQ2_S/IQ4_NL, not IQ3_XXS. Arms 15/16 require separate source-port images and the pre-existing gates in [the port plan](../../docs/STAGE7_IQ3XXS_FORK_PORT_PLAN.md). The user explicitly requested continuing those arms after the scope correction; source/build decisions and progress are recorded in [the source audit](stage7-iq3xxs-port-source-audit.md). Arm-14 results alone do not complete the nine-batch request.
