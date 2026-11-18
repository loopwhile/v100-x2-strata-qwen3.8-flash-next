# Stage 11X S11X-P1 Receipt: `p1-20261119T070809`

- **Verdict**: `PASS`
- **Host**: `p520-llm` (boot `e80b19de-4242-4e94-b756-6f500d43a07b`)
- **Engine**: `strata-v100:stage11x-p1` (`062f6e3bcf41288e...`)
- **Overrides**: `{"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1", "STRATA_PF_WMMA2": "1", "STRATA_PF_WMMA_LEAN": "1", "STRATA_PF_WMMA_SKINNY": "1"}`
- **DFlash2 Config**: `spec 8`, `conf 0.7`, `prefill auto`

## Scored C2 Batches

| Batch | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Overlap | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| p1-20261119T070809-batch-1 | 1046.2 | 1048.4 | 28.5 | 30.4 | 121.61 | 121.34 | Yes | PASS |
| p1-20261119T070809-batch-2 | 1043.9 | 1047.7 | 28.4 | 28.3 | 121.88 | 121.43 | Yes | PASS |
| p1-20261119T070809-batch-3 | 1038.0 | 1043.6 | 28.8 | 28.4 | 122.57 | 121.90 | Yes | PASS |
| **Median** | **1043.9** | **1047.7** | **28.5** | **28.4** | **121.88** | **121.43** | - | **PASS** |

## Summary Metrics vs `S10-D4` (`1025.1 / 1027.8` Prefill, `30.4 / 30.3` Decode, `124.08 / 123.79 s` TTFT)

- **Prefill A / B Median**: 1043.9 / 1047.7 tok/s (vs S10-D4: +18.8 / +19.9 tok/s)
- **Decode A / B Median**: 28.5 / 28.4 tok/s (vs S10-D4: -1.9 / -1.9 tok/s)
- **TTFT A / B Median**: 121.88 / 121.43 s (vs S10-D4: -2.20 / -2.36 s)
- **Stage 11X Final Target Met (Prefill >= 1200 & Decode >= 40.0)**: NO
