# Stage 10 S10-K3 Receipt: `k3-20261110T212830`

- **Verdict**: `PASS`
- **Host**: `p520-llm` (boot `eeb2038e-cfb0-4a5c-9afc-9a465596863f`)
- **Engine**: `sha256:dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d` (`ccca488231f12da4...`)
- **Overrides**: `{"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1", "STRATA_SIDE_MIXER": "2"}`
- **DFlash2 Config**: `spec 6`, `conf 0.7`, `prefill auto`

## Scored C2 Batches

| Batch | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Overlap | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| k3-20261110T212830-batch-1 | 1030.4 | 1037.1 | 27.9 | 28.4 | 123.47 | 122.68 | Yes | PASS |
| k3-20261110T212830-batch-2 | 1025.3 | 1033.0 | 28.3 | 28.2 | 124.07 | 123.17 | Yes | PASS |
| k3-20261110T212830-batch-3 | 1026.8 | 1035.7 | 29.0 | 28.1 | 123.87 | 122.85 | Yes | PASS |
| **Median** | **1026.8** | **1035.7** | **28.3** | **28.2** | **123.87** | **122.85** | - | **PASS** |

## Summary Metrics

- **Prefill A / B Median**: 1026.8 / 1035.7 tok/s
- **Decode A / B Median**: 28.3 / 28.2 tok/s
- **TTFT A / B Median**: 123.87 / 122.85 s
- **Target Met (Prefill >= 1100 & Decode >= 30.0)**: NO
