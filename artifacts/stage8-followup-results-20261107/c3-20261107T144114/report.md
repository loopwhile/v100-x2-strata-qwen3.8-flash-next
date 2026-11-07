# S8-C3 — c3-20261107T144114

**3/3 C2 PASS**

Primary arguments: `{"--resident-budget-gib": "2", "--adapt-async": "1"}`; extra flags `[]`.

Reference: `c2-20261107T142619`. C3 inherits the validated C2 resident budget and adds only adapt-async; other scored arms change one primary policy from U1. D1 instead has instrumentation and is never a scored comparison. Context 131072, original IQ3_XXS/native pack/MTP, fixed workload, CPU/GPU isolation, 150 W/1110 MHz and serving/tunnel preservation apply.

| Phase | Scored | Verdict | Prefill A/B | Decode A/B | TTFT A/B s | Output A/B | Overlap s | Wall s |
|---|---|---|---:|---:|---:|---:|---:|---:|
| startup | False | STARTUP_PASS_NOT_C2 | — | — | — | — | — | — |
| batch-1 | True | PASS | 889.2 / 895.7 | 30.0 / 28.3 | 143.04 / 141.99 | 1929 / 2382 | 64.30 | 226.24 |
| batch-2 | True | PASS | 820.5 / 825.0 | 29.0 / 30.4 | 155.00 / 154.14 | 2076 / 1830 | 59.18 | 226.64 |
| batch-3 | True | PASS | 811.1 / 817.8 | 29.0 / 28.7 | 156.77 / 155.54 | 2074 / 2401 | 71.56 | 239.18 |

| Median | A | B | Reference c2-20261107T142619 A/B |
|---|---:|---:|---:|
| Prefill tok/s | 820.50 | 825.00 | 823.40 / 827.20 |
| Decode tok/s | 29.00 | 28.70 | 26.60 / 27.90 |
| TTFT s | 155.00 | 154.14 | 154.44 / 153.75 |

## Conditions and interpretation

All phases and failures remain in the raw tree; startup is not C2. There are no scored retries or baseline reruns. Differences from U1/S7 are descriptive across changing cache/swap/output/temperature conditions, not controlled causal gains. A mechanical PASS does not validate semantic coding/tool-call quality or authorize promotion.

GPU statistics in receipts cover each full process lifetime, including loading/shutdown; they are not decode-only power. Physical I/O, page-cache and swap evidence, effective child args/env and profiler lines are retained in the sanitized receipts. Raw prompts/responses remain outside Git.

Raw P520: `results/stage8/S8-C3/c3-20261107T144114/`. Source/image/binary/harness pins and process identity are in [receipts](receipts.json).
