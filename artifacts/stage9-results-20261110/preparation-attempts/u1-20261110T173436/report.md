# S9-U1 — u1-20261110T173436

**INCOMPLETE 0/3 PASS**

Source `712fec6b4297c9cfd32ab43daaa2979a9aa01edf`; image `sha256:dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d`; binary `ccca488231f12da422be4a80b5c7f165b7593f6388907cac92d3c3f0d4229031`.

| Phase | Scored | Verdict | Prefill A/B | Decode A/B | TTFT A/B s | Output A/B | Overlap s |
|---|---|---|---:|---:|---:|---:|---:|
| startup | False | INCONCLUSIVE | — | — | — | — | — |

All three scored batches are retained; startup is unscored. Original IQ3_XXS/native pack, independent single GPUs, CPU affinities, 131072 context and INT8 KV are preserved.

GPU/host lifetime statistics include loading and shutdown; they are not decode-only measurements. RAM unavailable is MemTotal minus MemAvailable. Raw GPU/host/vmstat/iostat series remain backed up. Draft/verify component timings unavailable without profiling are explicitly marked in receipts.

Historical S7/S8 comparisons are descriptive because clock, temperature, cache, swap and output conditions vary. Mechanical C2 PASS is not semantic-quality validation or production promotion.

Recorded error: `AssertionError('Clock/power cap mismatch')`
