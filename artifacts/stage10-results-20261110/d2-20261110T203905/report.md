# Stage 10 S10-D2 Receipt: `d2-20261110T203905`

- **Verdict**: `PASS`
- **Host**: `p520-llm` (boot `eeb2038e-cfb0-4a5c-9afc-9a465596863f`)
- **Engine**: `sha256:dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d` (`ccca488231f12da4...`)
- **Overrides**: `{"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1"}`
- **DFlash2 Config**: `spec 6`, `conf 0.5`, `prefill auto`

## Scored C2 Batches

| Batch | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Overlap | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| d2-20261110T203905-batch-1 | 1028.2 | 1033.3 | 28.1 | 26.9 | 123.74 | 123.11 | Yes | PASS |
| d2-20261110T203905-batch-2 | 1026.2 | 1033.4 | 27.4 | 27.9 | 123.98 | 123.12 | Yes | PASS |
| d2-20261110T203905-batch-3 | 1027.0 | 1034.5 | 27.6 | 27.5 | 123.87 | 122.99 | Yes | PASS |
| **Median** | **1027.0** | **1033.4** | **27.6** | **27.5** | **123.87** | **123.11** | - | **PASS** |

## Summary Metrics

- **Prefill A / B Median**: 1027.0 / 1033.4 tok/s
- **Decode A / B Median**: 27.6 / 27.5 tok/s
- **TTFT A / B Median**: 123.87 / 123.11 s
- **Target Met (Prefill >= 1100 & Decode >= 30.0)**: NO
