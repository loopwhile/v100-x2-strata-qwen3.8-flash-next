# S6-3 kernel screening — 2026-10-28

One unprofiled frozen dual C2 screen per isolated flag, with all other settings at S6-0. Baseline decode medians A/B: 22.3/21.2 tok/s; screening results alone do not establish a win. Effective flag activation in the target kernel is not directly logged and must be established before attribution.

| Flag | A decode | B decode | Output A/B | C2 | Result |
| --- | ---: | ---: | ---: | --- | --- |
| SIDE_MIXER=2 | 22.8 | 21.4 | 1332 / 1261 | PASS | Small difference within baseline variability; unconfirmed |
| GU_SWIGLU=1 | 22.3 | 21.4 | 1332 / 1495 | PASS | No clear dual improvement |
| GR_UP75=1 | 22.7 | 21.4 | 1332 / 1503 | PASS | Small difference within baseline variability; unconfirmed |
| ATTN_DAILY=1 | 22.1 | 21.3 | 1485 / 1489 | PASS | No clear dual improvement |
| GR_NORM_FAST=1 | 21.7 | 21.0 | 1315 / 1646 | PASS | No clear dual improvement |
| ARGMAX_ROWS_SM70=1 | 21.8 | 21.3 | 1315 / 1706 | PASS | No clear dual improvement |

Pinned source contains all three switches; GU_SWIGLU and GR_UP75 are off by default on V100 with the SM70 bundle disabled. Raw results and preserved engine and Docker logs are on P520 under `results/c2-stage6-s6-3-*`.
