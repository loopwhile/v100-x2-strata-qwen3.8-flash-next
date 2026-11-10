# Stage 10 S10-D3 Receipt: `d3-20261110T205215`

- **Verdict**: `PASS`
- **Host**: `p520-llm` (boot `eeb2038e-cfb0-4a5c-9afc-9a465596863f`)
- **Engine**: `sha256:dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d` (`ccca488231f12da4...`)
- **Overrides**: `{"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1"}`
- **DFlash2 Config**: `spec 6`, `conf 0.6`, `prefill auto`

## Scored C2 Batches

| Batch | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Overlap | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| d3-20261110T205215-batch-1 | 1029.3 | 1034.4 | 28.0 | 29.7 | 123.60 | 122.99 | Yes | PASS |
| d3-20261110T205215-batch-2 | 1020.3 | 1020.3 | 28.3 | 28.9 | 124.68 | 124.69 | Yes | PASS |
| d3-20261110T205215-batch-3 | 1027.8 | 1032.2 | 28.4 | 29.3 | 123.77 | 123.25 | Yes | PASS |
| **Median** | **1027.8** | **1032.2** | **28.3** | **29.3** | **123.77** | **123.25** | - | **PASS** |

## Summary Metrics

- **Prefill A / B Median**: 1027.8 / 1032.2 tok/s
- **Decode A / B Median**: 28.3 / 29.3 tok/s
- **TTFT A / B Median**: 123.77 / 123.25 s
- **Target Met (Prefill >= 1100 & Decode >= 30.0)**: NO
