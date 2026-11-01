# S6-3 kernel screening — 2026-10-28

One unprofiled frozen dual C2 screen per isolated flag, with all other settings at S6-0. Baseline decode medians A/B: 22.3/21.2 tok/s; screening results alone do not establish a win. Effective flag activation in the target kernel is not directly logged and must be established before attribution.

| Flag | A / B prefill tok/s | A / B TTFT s | A decode | B decode | Output A/B | C2 | Result |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| SIDE_MIXER=2 | 934.1 / 943.9 | 136.20 / 134.80 | 22.8 | 21.4 | 1332 / 1261 | PASS | Small difference within baseline variability; unconfirmed |
| GU_SWIGLU=1 | 893.7 / 912.7 | 142.37 / 139.40 | 22.3 | 21.4 | 1332 / 1495 | PASS | No clear dual improvement |
| GR_UP75=1 | 933.0 / 942.5 | 136.37 / 134.99 | 22.7 | 21.4 | 1332 / 1503 | PASS | Small difference within baseline variability; unconfirmed |
| ATTN_DAILY=1 | 919.4 / 934.3 | 138.40 / 136.17 | 22.1 | 21.3 | 1485 / 1489 | PASS | No clear dual improvement |
| GR_NORM_FAST=1 | 929.5 / 943.1 | 136.86 / 134.93 | 21.7 | 21.0 | 1315 / 1646 | PASS | No clear dual improvement |
| ARGMAX_ROWS_SM70=1 | 899.2 / 912.3 | 141.54 / 139.48 | 21.8 | 21.3 | 1315 / 1706 | PASS | No clear dual improvement |

Pinned source contains all three switches; GU_SWIGLU and GR_UP75 are off by default on V100 with the SM70 bundle disabled. Raw results and preserved engine and Docker logs are on P520 under `results/c2-stage6-s6-3-*`.
