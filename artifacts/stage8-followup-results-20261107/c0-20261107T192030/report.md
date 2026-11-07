# S8-C0 — c0-20261107T192030

**3/3 C2 PASS**

Primary arguments: `{}`; extra flags `[]`.

Reference: `c1-20261107T141343`. C3 inherits the validated C2 resident budget and adds only adapt-async; other scored arms change one primary policy from U1. D1 instead has instrumentation and is never a scored comparison. Context 131072, original IQ3_XXS/native pack/MTP, fixed workload, CPU/GPU isolation, 150 W/1110 MHz and serving/tunnel preservation apply.

| Phase | Scored | Verdict | Prefill A/B | Decode A/B | TTFT A/B s | Output A/B | Overlap s | Wall s |
|---|---|---|---:|---:|---:|---:|---:|---:|
| startup | False | STARTUP_PASS_NOT_C2 | — | — | — | — | — | — |
| batch-1 | True | PASS | 995.2 / 1002.7 | 25.3 / 27.7 | 127.84 / 126.89 | 1726 / 1951 | 68.15 | 197.35 |
| batch-2 | True | PASS | 997.5 / 1006.8 | 25.6 / 28.2 | 127.54 / 126.35 | 1682 / 1944 | 65.62 | 195.12 |
| batch-3 | True | PASS | 997.2 / 1006.3 | 26.3 / 27.9 | 127.57 / 126.42 | 1953 / 2314 | 74.11 | 209.27 |

| Median | A | B | Reference c1-20261107T141343 A/B |
|---|---:|---:|---:|
| Prefill tok/s | 997.20 | 1006.30 | 998.10 / 1007.20 |
| Decode tok/s | 25.60 | 27.90 | 26.20 / 28.30 |
| TTFT s | 127.57 | 126.42 | 127.45 / 126.32 |

## Conditions and interpretation

All phases and failures remain in the raw tree; startup is not C2. There are no scored retries or baseline reruns. Differences from U1/S7 are descriptive across changing cache/swap/output/temperature conditions, not controlled causal gains. A mechanical PASS does not validate semantic coding/tool-call quality or authorize promotion.

GPU statistics in receipts cover each full process lifetime, including loading/shutdown; they are not decode-only power. Physical I/O, page-cache and swap evidence, effective child args/env and profiler lines are retained in the sanitized receipts. Raw prompts/responses remain outside Git.

Raw P520: `results/stage8/S8-C0/c0-20261107T192030/`. Source/image/binary/harness pins and process identity are in [receipts](receipts.json).
