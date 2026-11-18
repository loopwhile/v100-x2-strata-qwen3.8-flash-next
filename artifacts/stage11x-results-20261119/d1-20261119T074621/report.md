# Stage 11X S11X-D1 Receipt: `d1-20261119T074621`

- **Verdict**: `PASS`
- **Host**: `p520-llm` (boot `e80b19de-4242-4e94-b756-6f500d43a07b`)
- **Engine**: `strata-v100:stage11x-d1` (`97e8f19921ec7a0e...`)
- **Overrides**: `{"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1", "STRATA_AVX512BW_IQ": "22", "STRATA_IQ_MT_MIN": "1", "STRATA_IQ_GATHER": "1", "STRATA_IQ256_GATHER": "1", "STRATA_Q2_BITPLANE": "1"}`
- **DFlash2 Config**: `spec 8`, `conf 0.7`, `prefill auto`

## Scored C2 Batches

| Batch | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Overlap | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| d1-20261119T074621-batch-1 | 940.0 | 943.4 | 33.9 | 32.0 | 135.33 | 134.84 | Yes | PASS |
| d1-20261119T074621-batch-2 | 943.0 | 944.4 | 31.4 | 30.8 | 134.88 | 134.69 | Yes | PASS |
| d1-20261119T074621-batch-3 | 970.9 | 973.8 | 32.6 | 31.9 | 131.03 | 130.63 | Yes | PASS |
| **Median** | **943.0** | **944.4** | **32.6** | **31.9** | **134.88** | **134.69** | - | **PASS** |

## Summary Metrics vs `S10-D4` (`1025.1 / 1027.8` Prefill, `30.4 / 30.3` Decode, `124.08 / 123.79 s` TTFT)

- **Prefill A / B Median**: 943.0 / 944.4 tok/s (vs S10-D4: -82.1 / -83.4 tok/s)
- **Decode A / B Median**: 32.6 / 31.9 tok/s (vs S10-D4: +2.2 / +1.6 tok/s)
- **TTFT A / B Median**: 134.88 / 134.69 s (vs S10-D4: +10.80 / +10.90 s)
- **Stage 11X Final Target Met (Prefill >= 1200 & Decode >= 40.0)**: NO
