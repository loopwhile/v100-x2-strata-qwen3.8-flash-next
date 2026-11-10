# Stage 9 results — 2026-11-10

| Arm | Valid C2 | Prefill A/B tok/s | Decode A/B tok/s | TTFT A/B s |
|---|---:|---:|---:|---:|
| S7-XXS-14 (archived) | 3/3 historical | 997.6 / 1006.6 | 26.4 / 26.2 | 127.53 / 126.48 |
| S8-C1 (archived) | 3/3 historical | 998.1 / 1007.2 | 26.2 / 28.3 | 127.45 / 126.32 |
| S8-C0 (archived) | 3/3 historical | 997.2 / 1006.3 | 25.6 / 27.9 | 127.57 / 126.42 |
| [S9-U1](u1-20261110T173748/report.md) | 3/3 (3/3 C2 PASS) | 966.0 / 973.6 | 26.1 / 28.8 | 131.67 / 130.67 |
| [S9-D1](d1-20261110T175220/report.md) | 3/3 (3/3 C2 PASS) | 1026.5 / 1032.6 | 28.2 / 29.4 | 123.92 / 123.21 |
| [S9-F1](f1-20261110T180620/report.md) | 3/3 (3/3 C2 PASS) | 960.0 / 909.8 | 26.3 / 26.0 | 132.51 / 139.81 |

| Arm | GPU mean/peak temp °C A/B | GPU mean/peak W A/B | Host CPU user % | RAM unavailable peak GiB |
|---|---:|---:|---:|---:|
| S9-U1 | 54.8 / 56.3 / peak 65.0 / 65.0 | 85.52 / 88.72 / peak 201.81 / 219.88 | 23.6 | 11.99 |
| S9-D1 | 57.4 / 57.4 / peak 66.0 / 65.0 | 91.74 / 92.26 / peak 221.58 / 226.24 | 26.3 | 11.90 |
| S9-F1 | 56.0 / 56.8 / peak 65.0 / 65.0 | 86.36 / 90.41 / peak 218.63 / 242.06 | 28.4 | 12.03 |

GPU means cover each full process lifetime including loading, built-in post-response idle-prefill and shutdown; reported means average the three batch means. The sole generated request supplies physical I/O and KV figures; decode-free GEN 0 events are recorded separately. Scored HTTP requests have no prefix reuse and the next batch starts new processes. RAM unavailable = MemTotal − MemAvailable, sampled each second. Full per-batch data, ranges, draft acceptance, Expert/KV cache, page faults, swap and I/O are in summary.json and linked receipts.

Original IQ3_XXS, independent GPU/CPU mapping, 131072 context, INT8 KV and 150 W configured cap remain fixed. User explicitly approved proceeding at 1245 MHz. The host service journal shows a separate clock-policy change after initial inspection, settling at 135–1245 MHz at 17:15:59 before all scored runs; this agent issued no clock/power command. Historical 1110 MHz runs therefore have a different clock envelope. D1 uses stock DFlash2 selector-Q4 with source-derived spec6/conf0.7; U1/F1 use MTP4/min-p0.5. D1 and U1 share the exact same engine image. Fork defaults are part of that fork candidate, with WMMA2 explicitly disabled.

Historical S7/S8 references were not rerun. Cross-date cache/swap/output/clock/thermal differences prevent causal version-speedup claims. Decode gains alone do not establish a balanced Prefill/TTFT/power/temperature upgrade. Missing profiling-only draft/verify times are marked, never invented. Mechanical PASS is not semantic-quality validation; no production promotion.
