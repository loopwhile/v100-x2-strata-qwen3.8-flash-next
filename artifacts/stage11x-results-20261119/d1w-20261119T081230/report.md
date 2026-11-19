# Stage 11X S11X-D1W Receipt: `d1w-20261119T081230`

- **Verdict**: `PASS`
- **Host**: `p520-llm` (boot `e80b19de-4242-4e94-b756-6f500d43a07b`)
- **Engine**: `strata-v100:stage11x-d1` (`97e8f19921ec7a0e...`)
- **Overrides**: `{"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1", "STRATA_AVX512BW_IQ": "22", "STRATA_IQ_MT_MIN": "1", "STRATA_IQ_GATHER": "1", "STRATA_IQ256_GATHER": "1", "STRATA_Q2_BITPLANE": "1"}`
- **DFlash2 Config**: `spec 8`, `conf 0.7`, `prefill auto`

## Scored C2 Batches

| Batch | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Overlap | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| d1w-20261119T081230-batch-1 | 985.2 | 991.2 | 33.3 | 32.2 | 129.12 | 128.34 | Yes | PASS |
| d1w-20261119T081230-batch-2 | 1010.8 | 1016.6 | 33.8 | 32.5 | 125.86 | 125.14 | Yes | PASS |
| d1w-20261119T081230-batch-3 | 1023.2 | 1028.8 | 34.6 | 32.2 | 124.32 | 123.64 | Yes | PASS |
| **Median** | **1010.8** | **1016.6** | **33.8** | **32.2** | **125.86** | **125.14** | - | **PASS** |

## Summary Metrics vs `S10-D4` (`1025.1 / 1027.8` Prefill, `30.4 / 30.3` Decode, `124.08 / 123.79 s` TTFT)

- **Prefill A / B Median**: 1010.8 / 1016.6 tok/s (vs S10-D4: -14.3 / -11.2 tok/s)
- **Decode A / B Median**: 33.8 / 32.2 tok/s (vs S10-D4: +3.4 / +1.9 tok/s)
- **TTFT A / B Median**: 125.86 / 125.14 s (vs S10-D4: +1.78 / +1.35 s)
- **Stage 11X Final Target Met (Prefill >= 1200 & Decode >= 40.0)**: NO
