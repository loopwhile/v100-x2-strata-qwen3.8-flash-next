# Stage 4-C IQ3_XXS C2 128K Performance Benchmark Summary

- **Date / Time**: 2026-10-21 22:56:15 KST
- **Engine**: Upstream Strata `v0.1.47` (Release `v0.2.2`) with `STRATA_SM70_TABLE=1`
- **Docker Image**: `strata-v100-upstream:0.1.47` (`sha256:19c3b72a1097...`)
- **Host**: ThinkStation P520, 2x Tesla V100-SXM2-16GB, 전력 상한 150W (유지)
- **Model**: Qwen3.8-Flash-Next IQ3_XXS (GSQ-RCO), INT8 (`q8_0`) KV, 131,072 context
- **Workload**: `V100-PERFORMANCE-C2-128K-v1` (Frozen SHA256: `e413acced27c...`)

---

## 1. Measured Results (Single Cold Run)

| Metric | Agent A (Host GPU 0) | Agent B (Host GPU 1) | Symmetrical Mean |
| --- | --- | --- | --- |
| **Prompt Tokens** | 126,967 | 126,968 | 126,967.5 |
| **Output Tokens** | 1,373 | 1,996 | 1,684.5 |
| **Wall Time (s)** | 253.92 s | 279.12 s | 266.52 s |
| **TTFT (s)** | 202.36 s | 200.83 s | **201.60 s** |
| **Prefill Speed** | 628.3 tok/s | 633.1 tok/s | **630.70 tok/s** |
| **Decode Speed** | 26.6 tok/s | 25.5 tok/s | **26.05 tok/s** |
| **Expert Cache Hit Rate** | 87.9% | 85.9% | **86.90%** |
| **Prefix Cache Reuse (`cache_n`)** | 0 (No reuse) | 0 (No reuse) | 0 |
| **Min 1,024 Output Check** | PASS | PASS | PASS |
| **Finish Reason** | `stop` | `stop` | `stop` |

- **Batch Wall Time**: 279.13 s
- **Decode Overlap**: 51.55 s
- **Pass Mechanical**: `True`, **Active Overlap**: `True`, **Post Health**: `True`

---

## 2. IQ3_XXS Historical Engine Comparison

| Engine / Release | Prefill (tok/s) | TTFT (s) | Decode (tok/s) | Expert Hit | vs Stage 3-A Decode |
|---|---|---|---|---|---|
| **Stage 2** (Strata 0.1.31) | 623.05 | 204.39 | 11.45 | 76.15% | - |
| **Stage 3-A** (Strata 0.1.36) | 790.95 | 161.08 | 12.70 | 79.35% | Baseline |
| **Stage 3-B** (0.1.36 tuned) | 815.05 | 156.35 | 12.75 | 77.55% | +0.4% |
| **Stage 4-C** (0.1.47 + SM70_TABLE) | 630.70 | 201.60 | **26.05** | **86.90%** | **+105.12% 🚀🚀 (2배 이상 향상!)** |

---

## 3. Analysis

- **IQ3 디코드 절벽 완전 극복**: 기존 0.1.31 및 0.1.36 포크에서 11~12.7 tok/s에 정체되어 있던 IQ3_XXS 디코드 속도가 0.1.47 엔진 및 sm_70 table 튜닝에서 **26.05 tok/s로 2배 이상 폭증(+105%)**했습니다.
- **캐시 효율 급증**: Expert hit rate가 79.35% -> 86.90%로 대폭 상승하여 디코드 구간의 메모리 대역폭 병목을 효과적으로 해소했습니다.
