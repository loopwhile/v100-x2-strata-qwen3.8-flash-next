# S9-U1 — u1-20261110T173748

**3/3 C2 PASS**

Source `712fec6b4297c9cfd32ab43daaa2979a9aa01edf`; image `sha256:dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d`; binary `ccca488231f12da422be4a80b5c7f165b7593f6388907cac92d3c3f0d4229031`.

| Phase | Scored | Verdict | Prefill A/B | Decode A/B | TTFT A/B s | Output A/B | Overlap s |
|---|---|---|---:|---:|---:|---:|---:|
| startup | False | STARTUP_PASS_NOT_C2 | — | — | — | — | — |
| batch-1 | True | PASS | 637.8 / 647.1 | 26.1 / 28.8 | 199.43 / 196.46 | 1778 / 1944 | 64.53 |
| batch-2 | True | PASS | 966.0 / 973.6 | 26.2 / 28.6 | 131.67 / 130.67 | 1838 / 1951 | 67.09 |
| batch-3 | True | PASS | 985.7 / 987.5 | 25.4 / 29.0 | 129.04 / 128.83 | 1914 / 1907 | 65.49 |

| Median | A | B |
|---|---:|---:|
| prefill_tok_s | 966.00 | 973.60 |
| decode_tok_s | 26.10 | 28.80 |
| ttft_s | 131.67 | 130.67 |

All three scored batches are retained; startup is unscored. Original IQ3_XXS/native pack, independent single GPUs, CPU affinities, 131072 context and INT8 KV are preserved.

GPU/host lifetime statistics include loading, built-in post-response idle-prefill and shutdown; they are not decode-only measurements. Decode-free GEN 0 records are separated from the sole scored generated request for physical I/O and KV reporting. They are not a second HTTP/C2 request; fresh processes prevent their prefix from being reused by the next scored batch. RAM unavailable is MemTotal minus MemAvailable. Raw GPU/host/vmstat/iostat series remain backed up. Draft/verify component timings unavailable without profiling are explicitly marked in receipts.

Historical S7/S8 comparisons are descriptive because clock, temperature, cache, swap and output conditions vary. Mechanical C2 PASS is not semantic-quality validation or production promotion.
