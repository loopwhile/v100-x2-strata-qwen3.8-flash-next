# Stage 11X S11X-C1 Receipt: `c1-20261119T085422`

- **Verdict**: `PASS`
- **Host**: `p520-llm` (boot `e80b19de-4242-4e94-b756-6f500d43a07b`)
- **Engine**: `strata-v100:stage11x-c1` (`6c8f0ca8885284de...`)
- **Overrides**: `{"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1", "STRATA_PF_WMMA2": "1", "STRATA_PF_WMMA_LEAN": "1", "STRATA_PF_WMMA_SKINNY": "1", "STRATA_AVX512BW_IQ": "22", "STRATA_IQ_MT_MIN": "1", "STRATA_IQ_GATHER": "1", "STRATA_IQ256_GATHER": "1", "STRATA_Q2_BITPLANE": "1"}`
- **DFlash2 Config**: `spec 8`, `conf 0.7`, `prefill auto`

## Scored C2 Batches

| Batch | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Overlap | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| c1-20261119T085422-batch-1 | 1036.1 | 1041.2 | 33.0 | 32.3 | 122.78 | 122.19 | Yes | PASS |
| c1-20261119T085422-batch-2 | 1043.2 | 1048.3 | 33.5 | 32.3 | 121.96 | 121.37 | Yes | PASS |
| c1-20261119T085422-batch-3 | 1037.6 | 1044.8 | 32.8 | 32.3 | 122.60 | 121.77 | Yes | PASS |
| **Median** | **1037.6** | **1044.8** | **33.0** | **32.3** | **122.60** | **121.77** | - | **PASS** |

## Summary Metrics vs `S10-D4` (`1025.1 / 1027.8` Prefill, `30.4 / 30.3` Decode, `124.08 / 123.79 s` TTFT)

- **Prefill A / B Median**: 1037.6 / 1044.8 tok/s (vs S10-D4: +12.5 / +17.0 tok/s)
- **Decode A / B Median**: 33.0 / 32.3 tok/s (vs S10-D4: +2.6 / +2.0 tok/s)
- **TTFT A / B Median**: 122.60 / 121.77 s (vs S10-D4: -1.48 / -2.02 s)
- **Stage 11X Final Target Met (Prefill >= 1200 & Decode >= 40.0)**: NO
