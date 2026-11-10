# Stage 10 S10-P1 Receipt: `p1-20261110T214105`

- **Verdict**: `PASS`
- **Host**: `p520-llm` (boot `eeb2038e-cfb0-4a5c-9afc-9a465596863f`)
- **Engine**: `sha256:dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d` (`ccca488231f12da4...`)
- **Overrides**: `{"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1", "STRATA_PF_HC_REGION": "1"}`
- **DFlash2 Config**: `spec 6`, `conf 0.7`, `prefill auto`

## Scored C2 Batches

| Batch | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Overlap | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| p1-20261110T214105-batch-1 | 1039.8 | 1044.0 | 28.2 | 29.5 | 122.37 | 121.88 | Yes | PASS |
| p1-20261110T214105-batch-2 | 1036.5 | 1045.0 | 27.5 | 28.1 | 122.74 | 121.75 | Yes | PASS |
| p1-20261110T214105-batch-3 | 1034.0 | 1042.7 | 28.2 | 28.4 | 123.03 | 122.03 | Yes | PASS |
| **Median** | **1036.5** | **1044.0** | **28.2** | **28.4** | **122.74** | **121.88** | - | **PASS** |

## Summary Metrics

- **Prefill A / B Median**: 1036.5 / 1044.0 tok/s
- **Decode A / B Median**: 28.2 / 28.4 tok/s
- **TTFT A / B Median**: 122.74 / 121.88 s
- **Target Met (Prefill >= 1100 & Decode >= 30.0)**: NO
