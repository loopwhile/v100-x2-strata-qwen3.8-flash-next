# S9-F1 — f1-20261110T180620

**3/3 C2 PASS**

Source `8b4c09bd3d9213b2d47880826c6e818c3140664d`; image `sha256:b390db7e6e2fc974c15c7683d7490477beff6955ffdf227c3f5cecced9a7e59d`; binary `83f73ab0c7a9fc44af46e7ee5d5c505cc3bc1634ae452b185f2b62d29ce9eea9`.

| Phase | Scored | Verdict | Prefill A/B | Decode A/B | TTFT A/B s | Output A/B | Overlap s |
|---|---|---|---:|---:|---:|---:|---:|
| startup | False | STARTUP_PASS_NOT_C2 | — | — | — | — | — |
| batch-1 | True | PASS | 960.0 / 906.5 | 26.3 / 26.0 | 132.51 / 140.32 | 2204 / 1662 | 64.01 |
| batch-2 | True | PASS | 980.8 / 909.8 | 25.3 / 26.0 | 129.70 / 139.81 | 1423 / 1644 | 46.08 |
| batch-3 | True | PASS | 936.3 / 1011.0 | 27.0 / 25.7 | 135.86 / 125.84 | 1568 / 2322 | 58.11 |

| Median | A | B |
|---|---:|---:|
| prefill_tok_s | 960.00 | 909.80 |
| decode_tok_s | 26.30 | 26.00 |
| ttft_s | 132.51 | 139.81 |

All three scored batches are retained; startup is unscored. Original IQ3_XXS/native pack, independent single GPUs, CPU affinities, 131072 context and INT8 KV are preserved.

GPU/host lifetime statistics include loading and shutdown; they are not decode-only measurements. RAM unavailable is MemTotal minus MemAvailable. Raw GPU/host/vmstat/iostat series remain backed up. Draft/verify component timings unavailable without profiling are explicitly marked in receipts.

Historical S7/S8 comparisons are descriptive because clock, temperature, cache, swap and output conditions vary. Mechanical C2 PASS is not semantic-quality validation or production promotion.
