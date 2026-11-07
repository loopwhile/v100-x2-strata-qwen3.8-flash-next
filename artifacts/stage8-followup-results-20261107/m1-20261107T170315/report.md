# S8-M1 — m1-20261107T170315

**3/3 C2 PASS**

Primary arguments: `{"--spec": "6"}`; extra flags `[]`.

Reference: `u1-20261107T124518`. C3 inherits the validated C2 resident budget and adds only adapt-async; other scored arms change one primary policy from U1. D1 instead has instrumentation and is never a scored comparison. Context 131072, original IQ3_XXS/native pack/MTP, fixed workload, CPU/GPU isolation, 150 W/1110 MHz and serving/tunnel preservation apply.

| Phase | Scored | Verdict | Prefill A/B | Decode A/B | TTFT A/B s | Output A/B | Overlap s | Wall s |
|---|---|---|---:|---:|---:|---:|---:|---:|
| startup | False | STARTUP_PASS_NOT_C2 | — | — | — | — | — | — |
| batch-1 | True | PASS | 998.2 / 1008.2 | 25.2 / 26.2 | 127.45 / 126.17 | 1189 / 1638 | 47.08 | 188.71 |
| batch-2 | True | PASS | 996.1 / 1003.7 | 25.4 / 26.1 | 127.71 / 126.77 | 1189 / 1683 | 46.78 | 191.07 |
| batch-3 | True | PASS | 996.7 / 1002.0 | 25.3 / 26.0 | 127.64 / 126.97 | 1189 / 1809 | 46.85 | 196.40 |

| Median | A | B | Reference u1-20261107T124518 A/B |
|---|---:|---:|---:|
| Prefill tok/s | 996.70 | 1003.70 | 871.00 / 877.20 |
| Decode tok/s | 25.30 | 26.10 | 25.20 / 27.70 |
| TTFT s | 127.64 | 126.77 | 146.02 / 145.01 |

## Conditions and interpretation

All phases and failures remain in the raw tree; startup is not C2. There are no scored retries or baseline reruns. Differences from U1/S7 are descriptive across changing cache/swap/output/temperature conditions, not controlled causal gains. A mechanical PASS does not validate semantic coding/tool-call quality or authorize promotion.

GPU statistics in receipts cover each full process lifetime, including loading/shutdown; they are not decode-only power. Physical I/O, page-cache and swap evidence, effective child args/env and profiler lines are retained in the sanitized receipts. Raw prompts/responses remain outside Git.

Raw P520: `results/stage8/S8-M1/m1-20261107T170315/`. Source/image/binary/harness pins and process identity are in [receipts](receipts.json).
