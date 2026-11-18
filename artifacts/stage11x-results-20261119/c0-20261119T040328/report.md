# Stage 11X S11X-C0 Receipt: `c0-20261119T040328`

- **Verdict**: `PASS`
- **Host**: `p520-llm` (boot `e80b19de-4242-4e94-b756-6f500d43a07b`)
- **Engine**: `sha256:dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d` (`ccca488231f12da4...`)
- **Overrides**: `{"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1", "STRATA_PF_HC_REGION": "1"}`
- **DFlash2 Config**: `spec 8`, `conf 0.7`, `prefill auto`

## Scored C2 Batches

| Batch | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Overlap | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| c0-20261119T040328-batch-1 | 1038.8 | 1037.6 | 29.7 | 28.3 | 122.47 | 122.60 | Yes | PASS |
| c0-20261119T040328-batch-2 | 1013.7 | 1029.2 | 30.4 | 30.3 | 125.50 | 123.62 | Yes | PASS |
| c0-20261119T040328-batch-3 | 1033.7 | 1039.5 | 29.7 | 28.4 | 123.07 | 122.39 | Yes | PASS |
| **Median** | **1033.7** | **1037.6** | **29.7** | **28.4** | **123.07** | **122.60** | - | **PASS** |

## Summary Metrics vs `S10-D4` (`1025.1 / 1027.8` Prefill, `30.4 / 30.3` Decode, `124.08 / 123.79 s` TTFT)

- **Prefill A / B Median**: 1033.7 / 1037.6 tok/s (vs S10-D4: +8.6 / +9.8 tok/s)
- **Decode A / B Median**: 29.7 / 28.4 tok/s (vs S10-D4: -0.7 / -1.9 tok/s)
- **TTFT A / B Median**: 123.07 / 122.60 s (vs S10-D4: -1.01 / -1.19 s)
- **Stage 11X Final Target Met (Prefill >= 1200 & Decode >= 40.0)**: NO
