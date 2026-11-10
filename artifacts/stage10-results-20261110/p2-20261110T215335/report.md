# Stage 10 S10-P2 Receipt: `p2-20261110T215335`

- **Verdict**: `PASS`
- **Host**: `p520-llm` (boot `eeb2038e-cfb0-4a5c-9afc-9a465596863f`)
- **Engine**: `sha256:dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d` (`ccca488231f12da4...`)
- **Overrides**: `{"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1", "STRATA_EMB_REUSE_ACCOUNT": "1"}`
- **DFlash2 Config**: `spec 6`, `conf 0.7`, `prefill auto`

## Scored C2 Batches

| Batch | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Overlap | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| p2-20261110T215335-batch-1 | 1029.2 | 1029.0 | 28.4 | 28.3 | 123.61 | 123.63 | Yes | PASS |
| p2-20261110T215335-batch-2 | 1028.7 | 1034.1 | 27.4 | 28.3 | 123.68 | 123.01 | Yes | PASS |
| p2-20261110T215335-batch-3 | 1030.1 | 1035.9 | 27.8 | 28.3 | 123.50 | 122.80 | Yes | PASS |
| **Median** | **1029.2** | **1034.1** | **27.8** | **28.3** | **123.61** | **123.01** | - | **PASS** |

## Summary Metrics

- **Prefill A / B Median**: 1029.2 / 1034.1 tok/s
- **Decode A / B Median**: 27.8 / 28.3 tok/s
- **TTFT A / B Median**: 123.61 / 123.01 s
- **Target Met (Prefill >= 1100 & Decode >= 30.0)**: NO
