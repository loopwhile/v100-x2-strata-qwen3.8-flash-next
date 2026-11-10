# Stage 10 S10-D4 Receipt: `d4-20261110T225518`

- **Verdict**: `PASS`
- **Host**: `p520-llm` (boot `501871eb-ee71-4ce0-82d5-dc9cd5bb8486`)
- **Engine**: `sha256:dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d` (`ccca488231f12da4...`)
- **Overrides**: `{"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1"}`
- **DFlash2 Config**: `spec 8`, `conf 0.7`, `prefill auto`

## Scored C2 Batches

| Batch | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Overlap | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| d4-20261110T225518-batch-1 | 957.2 | 959.8 | 30.4 | 28.2 | 132.89 | 132.54 | Yes | PASS |
| d4-20261110T225518-batch-2 | 1028.7 | 1032.4 | 30.4 | 30.3 | 123.68 | 123.21 | Yes | PASS |
| d4-20261110T225518-batch-3 | 1025.1 | 1027.8 | 30.6 | 30.5 | 124.08 | 123.79 | Yes | PASS |
| **Median** | **1025.1** | **1027.8** | **30.4** | **30.3** | **124.08** | **123.79** | - | **PASS** |

## Summary Metrics

- **Prefill A / B Median**: 1025.1 / 1027.8 tok/s
- **Decode A / B Median**: 30.4 / 30.3 tok/s
- **TTFT A / B Median**: 124.08 / 123.79 s
- **Target Met (Prefill >= 1100 & Decode >= 30.0)**: NO
