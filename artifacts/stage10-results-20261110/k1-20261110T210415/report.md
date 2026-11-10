# Stage 10 S10-K1 Receipt: `k1-20261110T210415`

- **Verdict**: `PASS`
- **Host**: `p520-llm` (boot `eeb2038e-cfb0-4a5c-9afc-9a465596863f`)
- **Engine**: `sha256:dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d` (`ccca488231f12da4...`)
- **Overrides**: `{"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1", "STRATA_ADAPT_LAG": "2"}`
- **DFlash2 Config**: `spec 6`, `conf 0.7`, `prefill auto`

## Scored C2 Batches

| Batch | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Overlap | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| k1-20261110T210415-batch-1 | 1027.7 | 1035.2 | 27.4 | 30.9 | 123.80 | 122.89 | Yes | PASS |
| k1-20261110T210415-batch-2 | 1022.6 | 1028.5 | 29.2 | 30.8 | 124.42 | 123.71 | Yes | PASS |
| k1-20261110T210415-batch-3 | 1026.1 | 1034.4 | 28.2 | 30.8 | 123.98 | 123.01 | Yes | PASS |
| **Median** | **1026.1** | **1034.4** | **28.2** | **30.8** | **123.98** | **123.01** | - | **PASS** |

## Summary Metrics

- **Prefill A / B Median**: 1026.1 / 1034.4 tok/s
- **Decode A / B Median**: 28.2 / 30.8 tok/s
- **TTFT A / B Median**: 123.98 / 123.01 s
- **Target Met (Prefill >= 1100 & Decode >= 30.0)**: NO
