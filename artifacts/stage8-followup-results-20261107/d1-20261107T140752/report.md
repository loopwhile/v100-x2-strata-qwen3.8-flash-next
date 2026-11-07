# S8-D1 — d1-20261107T140752

**PROFILE_PASS_NOT_SCORED**

Primary arguments: `{}`; extra flags `[]`.

This arm changes one primary policy relative to U1. D1 instead has instrumentation and is never a scored comparison. Context 131072, original IQ3_XXS/native pack/MTP, fixed workload, CPU/GPU isolation, 150 W/1110 MHz and serving/tunnel preservation apply.

| Phase | Scored | Verdict | Prefill A/B | Decode A/B | TTFT A/B s | Output A/B | Overlap s | Wall s |
|---|---|---|---:|---:|---:|---:|---:|---:|
| startup | False | STARTUP_PASS_NOT_C2 | — | — | — | — | — | — |
| diagnostic-1 | False | PROFILE_PASS_NOT_SCORED | 976.9 / 989.8 | 25.2 / 27.3 | 130.23 / 128.54 | 1806 / 1997 | 71.40 | 201.77 |

## Conditions and interpretation

All phases and failures remain in the raw tree; startup is not C2. There are no scored retries or baseline reruns. Differences from U1/S7 are descriptive across changing cache/swap/output/temperature conditions, not controlled causal gains. A mechanical PASS does not validate semantic coding/tool-call quality or authorize promotion.

GPU statistics in receipts cover each full process lifetime, including loading/shutdown; they are not decode-only power. Physical I/O, page-cache and swap evidence, effective child args/env and profiler lines are retained in the sanitized receipts. Raw prompts/responses remain outside Git.

Raw P520: `results/stage8/S8-D1/d1-20261107T140752/`. Source/image/binary/harness pins and process identity are in [receipts](receipts.json).
