# Stage 11X S11X-D2 Receipt: `d2-20261119T003753`

- **Verdict**: `PASS`
- **Host**: `p520-llm` (boot `e80b19de-4242-4e94-b756-6f500d43a07b`)
- **Engine**: `strata-v100:stage11x-d2` (`7f6fc8f7858739d1...`)
- **Overrides**: `{"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1", "STRATA_PF_WMMA2": "1", "STRATA_PF_WMMA_LEAN": "1", "STRATA_PF_WMMA_SKINNY": "1", "STRATA_AVX512BW_IQ": "22", "STRATA_IQ_MT_MIN": "1", "STRATA_IQ_GATHER": "1", "STRATA_IQ256_GATHER": "1", "STRATA_Q2_BITPLANE": "1", "STRATA_SIDE_MIXER": "2", "STRATA_ATTN_DAILY": "1", "STRATA_GR_UP75": "1", "STRATA_GU_SWIGLU": "1", "STRATA_QSA_ROWS": "1", "STRATA_FUSE_WAIT": "2", "STRATA_MMAP_ADAPT_ASYNC": "1", "STRATA_COLD_OVERLAP": "5"}`
- **DFlash2 Config**: `spec 8`, `conf 0.7`, `prefill auto`

## Scored C2 Batches

| Batch | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Overlap | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| d2-20261119T003753-batch-1 | 1027.0 | 1029.7 | 37.1 | 39.7 | 123.87 | 123.54 | Yes | PASS |
| d2-20261119T003753-batch-2 | 1032.6 | 1037.0 | 37.5 | 41.0 | 123.21 | 122.69 | Yes | PASS |
| d2-20261119T003753-batch-3 | 1037.4 | 1045.2 | 37.1 | 41.0 | 122.62 | 121.73 | Yes | PASS |
| **Median** | **1032.6** | **1037.0** | **37.1** | **41.0** | **123.21** | **122.69** | - | **PASS** |

## Summary Metrics vs `S10-D4` (`1025.1 / 1027.8` Prefill, `30.4 / 30.3` Decode, `124.08 / 123.79 s` TTFT)

- **Prefill A / B Median**: 1032.6 / 1037.0 tok/s (vs S10-D4: +7.5 / +9.2 tok/s)
- **Decode A / B Median**: 37.1 / 41.0 tok/s (vs S10-D4: +6.7 / +10.7 tok/s)
- **TTFT A / B Median**: 123.21 / 122.69 s (vs S10-D4: -0.87 / -1.10 s)
- **Stage 11X Final Target Met (Prefill >= 1200 & Decode >= 40.0)**: NO
