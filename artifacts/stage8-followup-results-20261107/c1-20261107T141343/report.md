# S8-C1 — c1-20261107T141343

**3/3 C2 PASS**

Primary arguments: `{"--pool-workers": "3"}`; extra flags `[]`.

Reference: `u1-20261107T124518`. C3 inherits the validated C2 resident budget and adds only adapt-async; other scored arms change one primary policy from U1. D1 instead has instrumentation and is never a scored comparison. Context 131072, original IQ3_XXS/native pack/MTP, fixed workload, CPU/GPU isolation, 150 W/1110 MHz and serving/tunnel preservation apply.

| Phase | Scored | Verdict | Prefill A/B | Decode A/B | TTFT A/B s | Output A/B | Overlap s | Wall s |
|---|---|---|---:|---:|---:|---:|---:|---:|
| startup | False | STARTUP_PASS_NOT_C2 | — | — | — | — | — | — |
| batch-1 | True | PASS | 997.4 / 1004.5 | 26.2 / 28.0 | 127.56 / 126.65 | 1715 / 1951 | 65.40 | 196.15 |
| batch-2 | True | PASS | 998.1 / 1007.2 | 26.6 / 28.3 | 127.45 / 126.32 | 1936 / 2314 | 72.70 | 207.92 |
| batch-3 | True | PASS | 998.3 / 1007.2 | 25.7 / 28.6 | 127.44 / 126.31 | 1775 / 2230 | 68.98 | 204.09 |

| Median | A | B | Reference u1-20261107T124518 A/B |
|---|---:|---:|---:|
| Prefill tok/s | 998.10 | 1007.20 | 871.00 / 877.20 |
| Decode tok/s | 26.20 | 28.30 | 25.20 / 27.70 |
| TTFT s | 127.45 | 126.32 | 146.02 / 145.01 |

## Conditions and interpretation

All phases and failures remain in the raw tree; startup is not C2. There are no scored retries or baseline reruns. Differences from U1/S7 are descriptive across changing cache/swap/output/temperature conditions, not controlled causal gains. A mechanical PASS does not validate semantic coding/tool-call quality or authorize promotion.

GPU statistics in receipts cover each full process lifetime, including loading/shutdown; they are not decode-only power. Physical I/O, page-cache and swap evidence, effective child args/env and profiler lines are retained in the sanitized receipts. Raw prompts/responses remain outside Git.

Raw P520: `results/stage8/S8-C1/c1-20261107T141343/`. Source/image/binary/harness pins and process identity are in [receipts](receipts.json).
