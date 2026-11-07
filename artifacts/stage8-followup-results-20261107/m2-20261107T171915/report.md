# S8-M2 — m2-20261107T171915

**3/3 C2 PASS**

Primary arguments: `{}`; extra flags `["--expert-cache-per-layer"]`.

Reference: `u1-20261107T124518`. C3 inherits the validated C2 resident budget and adds only adapt-async; other scored arms change one primary policy from U1. D1 instead has instrumentation and is never a scored comparison. Context 131072, original IQ3_XXS/native pack/MTP, fixed workload, CPU/GPU isolation, 150 W/1110 MHz and serving/tunnel preservation apply.

| Phase | Scored | Verdict | Prefill A/B | Decode A/B | TTFT A/B s | Output A/B | Overlap s | Wall s |
|---|---|---|---:|---:|---:|---:|---:|---:|
| startup | False | STARTUP_PASS_NOT_C2 | — | — | — | — | — | — |
| batch-1 | True | PASS | 993.3 / 1000.9 | 25.5 / 28.0 | 128.08 / 127.12 | 1149 / 2140 | 44.93 | 203.55 |
| batch-2 | True | PASS | 994.6 / 1000.1 | 25.8 / 25.6 | 127.89 / 127.21 | 1179 / 2369 | 45.61 | 219.71 |
| batch-3 | True | PASS | 994.8 / 1002.2 | 25.8 / 26.2 | 127.88 / 126.95 | 1179 / 1459 | 45.60 | 182.64 |

| Median | A | B | Reference u1-20261107T124518 A/B |
|---|---:|---:|---:|
| Prefill tok/s | 994.60 | 1000.90 | 871.00 / 877.20 |
| Decode tok/s | 25.80 | 26.20 | 25.20 / 27.70 |
| TTFT s | 127.89 | 127.12 | 146.02 / 145.01 |

## Conditions and interpretation

All phases and failures remain in the raw tree; startup is not C2. There are no scored retries or baseline reruns. Differences from U1/S7 are descriptive across changing cache/swap/output/temperature conditions, not controlled causal gains. A mechanical PASS does not validate semantic coding/tool-call quality or authorize promotion.

GPU statistics in receipts cover each full process lifetime, including loading/shutdown; they are not decode-only power. Physical I/O, page-cache and swap evidence, effective child args/env and profiler lines are retained in the sanitized receipts. Raw prompts/responses remain outside Git.

Raw P520: `results/stage8/S8-M2/m2-20261107T171915/`. Source/image/binary/harness pins and process identity are in [receipts](receipts.json).
