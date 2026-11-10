# S9-D1 — d1-20261110T175220

**3/3 C2 PASS**

Source `712fec6b4297c9cfd32ab43daaa2979a9aa01edf`; image `sha256:dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d`; binary `ccca488231f12da422be4a80b5c7f165b7593f6388907cac92d3c3f0d4229031`.

| Phase | Scored | Verdict | Prefill A/B | Decode A/B | TTFT A/B s | Output A/B | Overlap s |
|---|---|---|---:|---:|---:|---:|---:|
| startup | False | STARTUP_PASS_NOT_C2 | — | — | — | — | — |
| batch-1 | True | PASS | 1026.3 / 1032.0 | 28.9 / 29.4 | 123.96 / 123.29 | 2518 / 1721 | 57.73 |
| batch-2 | True | PASS | 1026.5 / 1033.7 | 28.2 / 28.7 | 123.92 / 123.09 | 2266 / 1862 | 64.02 |
| batch-3 | True | PASS | 1027.0 / 1032.6 | 27.9 / 29.4 | 123.88 / 123.21 | 2191 / 1721 | 57.82 |

| Median | A | B |
|---|---:|---:|
| prefill_tok_s | 1026.50 | 1032.60 |
| decode_tok_s | 28.20 | 29.40 |
| ttft_s | 123.92 | 123.21 |

All three scored batches are retained; startup is unscored. Original IQ3_XXS/native pack, independent single GPUs, CPU affinities, 131072 context and INT8 KV are preserved.

GPU/host lifetime statistics include loading and shutdown; they are not decode-only measurements. RAM unavailable is MemTotal minus MemAvailable. Raw GPU/host/vmstat/iostat series remain backed up. Draft/verify component timings unavailable without profiling are explicitly marked in receipts.

Historical S7/S8 comparisons are descriptive because clock, temperature, cache, swap and output conditions vary. Mechanical C2 PASS is not semantic-quality validation or production promotion.
