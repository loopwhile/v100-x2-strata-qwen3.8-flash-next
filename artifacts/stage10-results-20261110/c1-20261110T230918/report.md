# Stage 10 S10-C1 Receipt: `c1-20261110T230918`

- **Verdict**: `PASS`
- **Host**: `p520-llm` (boot `501871eb-ee71-4ce0-82d5-dc9cd5bb8486`)
- **Engine**: `sha256:dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d` (`ccca488231f12da4...`)
- **Overrides**: `{"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1", "STRATA_ADAPT_LAG": "2", "STRATA_ADAPT_NOWAIT": "1"}`
- **DFlash2 Config**: `spec 8`, `conf 0.7`, `prefill auto`

## Scored C2 Batches

| Batch | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Overlap | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| c1-20261110T230918-batch-1 | 1027.0 | 1029.1 | 27.6 | 29.1 | 123.88 | 123.64 | Yes | PASS |
| c1-20261110T230918-batch-2 | 1025.3 | 1030.4 | 26.9 | 28.9 | 124.09 | 123.48 | Yes | PASS |
| c1-20261110T230918-batch-3 | 1025.7 | 1026.5 | 27.5 | 28.4 | 124.03 | 123.94 | Yes | PASS |
| **Median** | **1025.7** | **1029.1** | **27.5** | **28.9** | **124.03** | **123.64** | - | **PASS** |

## Summary Metrics

- **Prefill A / B Median**: 1025.7 / 1029.1 tok/s
- **Decode A / B Median**: 27.5 / 28.9 tok/s
- **TTFT A / B Median**: 124.03 / 123.64 s
- **Target Met (Prefill >= 1100 & Decode >= 30.0)**: NO
