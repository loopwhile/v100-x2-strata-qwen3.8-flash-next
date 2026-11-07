# S8-C2 — c2-20261107T142619

**3/3 C2 PASS**

Primary arguments: `{"--resident-budget-gib": "2"}`; extra flags `[]`.

Reference: `u1-20261107T124518`. C3 inherits the validated C2 resident budget and adds only adapt-async; other scored arms change one primary policy from U1. D1 instead has instrumentation and is never a scored comparison. Context 131072, original IQ3_XXS/native pack/MTP, fixed workload, CPU/GPU isolation, 150 W/1110 MHz and serving/tunnel preservation apply.

| Phase | Scored | Verdict | Prefill A/B | Decode A/B | TTFT A/B s | Output A/B | Overlap s | Wall s |
|---|---|---|---:|---:|---:|---:|---:|---:|
| startup | False | STARTUP_PASS_NOT_C2 | — | — | — | — | — | — |
| batch-1 | True | PASS | 902.7 / 908.2 | 27.4 / 29.1 | 140.91 / 140.02 | 1361 / 1993 | 49.69 | 208.45 |
| batch-2 | True | PASS | 823.4 / 827.2 | 26.6 / 26.8 | 154.44 / 153.75 | 1264 / 2330 | 47.43 | 240.74 |
| batch-3 | True | PASS | 808.8 / 813.6 | 26.5 / 27.9 | 157.21 / 156.31 | 1527 / 2144 | 57.63 | 232.96 |

| Median | A | B | Reference u1-20261107T124518 A/B |
|---|---:|---:|---:|
| Prefill tok/s | 823.40 | 827.20 | 871.00 / 877.20 |
| Decode tok/s | 26.60 | 27.90 | 25.20 / 27.70 |
| TTFT s | 154.44 | 153.75 | 146.02 / 145.01 |

## Conditions and interpretation

All phases and failures remain in the raw tree; startup is not C2. There are no scored retries or baseline reruns. Differences from U1/S7 are descriptive across changing cache/swap/output/temperature conditions, not controlled causal gains. A mechanical PASS does not validate semantic coding/tool-call quality or authorize promotion.

GPU statistics in receipts cover each full process lifetime, including loading/shutdown; they are not decode-only power. Physical I/O, page-cache and swap evidence, effective child args/env and profiler lines are retained in the sanitized receipts. Raw prompts/responses remain outside Git.

Raw P520: `results/stage8/S8-C2/c2-20261107T142619/`. Source/image/binary/harness pins and process identity are in [receipts](receipts.json).
