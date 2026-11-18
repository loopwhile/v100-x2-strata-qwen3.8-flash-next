# Stage 11 S11-D4 Receipt: `d4-20261119T025044` (IQ3_S)

- **Verdict**: `PASS`
- **Quantization**: `IQ3_S`
- **Host**: `p520-llm` (boot `e80b19de-4242-4e94-b756-6f500d43a07b`)
- **Engine**: `sha256:dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d` (`ccca488231f12da4...`)
- **Overrides**: `{"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1"}`
- **DFlash2 Config**: `spec 8`, `conf 0.7`, `prefill auto`

## Scored C2 Batches

| Batch | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Overlap | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| d4-20261119T025044-batch-1 | 462.1 | 463.0 | 23.8 | 23.4 | 275.01 | 274.47 | Yes | PASS |
| d4-20261119T025044-batch-2 | 893.8 | 898.0 | 23.3 | 23.2 | 142.30 | 141.69 | Yes | PASS |
| d4-20261119T025044-batch-3 | 906.4 | 910.5 | 22.8 | 23.6 | 140.32 | 139.71 | Yes | PASS |
| **Median** | **893.8** | **898.0** | **23.3** | **23.4** | **142.30** | **141.69** | - | **PASS** |

## Summary Metrics

- **Prefill A / B Median**: 893.8 / 898.0 tok/s
- **Decode A / B Median**: 23.3 / 23.4 tok/s
- **TTFT A / B Median**: 142.30 / 141.69 s
- **vs S6-0 IQ3_S Baseline (22.3 / 21.2 decode)**: +1.0 / +2.2 tok/s
- **vs S10-D4 IQ3_XXS (30.4 / 30.3 decode)**: -7.1 / -6.9 tok/s
