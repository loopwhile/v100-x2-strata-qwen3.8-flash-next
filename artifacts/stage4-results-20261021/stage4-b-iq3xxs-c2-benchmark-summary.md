# Stage 4-B IQ3_XXS C2 128K Performance Benchmark Summary

- **Date / Time**: 2026-10-21 23:40:21 KST
- **Engine**: Upstream Strata `v0.1.47` (Release `v0.2.2`, Vanilla Defaults without `STRATA_SM70_TABLE=1`)
- **Docker Image**: `strata-v100-upstream:0.1.47` (`sha256:19c3b72a1097...`)
- **Host**: ThinkStation P520, 2x Tesla V100-SXM2-16GB, 전력 상한 150W (유지)
- **Model**: Qwen3.8-Flash-Next IQ3_XXS (GSQ-RCO), INT8 (`q8_0`) KV, 131,072 context
- **Workload**: `V100-PERFORMANCE-C2-128K-v1` (Frozen SHA256: `e413acced27c...`)

---

## 1. Measured Results (Single Cold Run)

| Metric | Agent A (Host GPU 0) | Agent B (Host GPU 1) | Symmetrical Mean |
| --- | --- | --- | --- |
| **Prompt Tokens** | 126,967 | 126,968 | 126,967.5 |
| **Output Tokens** | 1,396 | 2,737 | 2,066.5 |
| **Wall Time (s)** | 228.02 s | 282.45 s | 255.23 s |
| **TTFT (s)** | 176.50 s | 174.04 s | **175.27 s** |
| **Prefill Speed** | 720.4 tok/s | 730.6 tok/s | **725.50 tok/s** |
| **Decode Speed** | 27.1 tok/s | 25.2 tok/s | **26.15 tok/s** |
| **Expert Cache Hit Rate** | 88.4% | 84.2% | **86.30%** |
| **Prefix Cache Reuse (`cache_n`)** | 0 (No reuse) | 0 (No reuse) | 0 |
| **Min 1,024 Output Check** | PASS | PASS | PASS |
| **Finish Reason** | `stop` | `stop` | `stop` |

- **Batch Wall Time**: 282.46 s
- **Decode Overlap**: 51.52 s
- **Pass Mechanical**: `True`, **Active Overlap**: `True`, **Post Health**: `True`

---

## 2. IQ3_XXS Engine Comparison (Stage 2 ~ Stage 4-C)

| Engine / Release | Prefill (tok/s) | TTFT (s) | Decode (tok/s) | Expert Hit | vs Stage 3-A Decode |
|---|---|---|---|---|---|
| **Stage 2** (Strata 0.1.31) | 623.05 | 204.39 | 11.45 | 76.15% | - |
| **Stage 3-A** (Strata 0.1.36) | 790.95 | 161.08 | 12.70 | 79.35% | Baseline |
| **Stage 3-B** (0.1.36 tuned) | 815.05 | 156.35 | 12.75 | 77.55% | +0.4% |
| **Stage 4-B** (0.1.47 vanilla) | **725.50** | **175.27** | **26.15** | **86.30%** | **+105.91% 🚀🚀** |
| **Stage 4-C** (0.1.47 + SM70_TABLE) | 630.70 | 201.60 | **26.05** | **86.90%** | **+105.12% 🚀🚀** |

---

## 3. Analysis

- **디코드 향상의 근원 규명**: Stage 4-B(순정 0.1.47)에서도 디코드 속도가 **26.15 tok/s**를 기록하여 Stage 3-A 대비 2배 이상(+105.9%) 향상되었습니다. 즉, IQ3_XXS 디코드 절벽 해결은 `STRATA_SM70_TABLE=1` 튜닝이 아니라 **Upstream Strata 0.1.47 코어 엔진 자체의 개선** 덕분임이 실증되었습니다.
- **Prefill 및 TTFT 차이**: `STRATA_SM70_TABLE=1`을 적용하지 않은 Stage 4-B가 Stage 4-C 대비 **Prefill 속도가 15% 더 빠르고(725.5 tok/s vs 630.7 tok/s), TTFT도 26초 단축(175.27s vs 201.60s)**되었습니다. IQ3_XXS 양자화에서는 순정 0.1.47이 SM70_TABLE 튜닝보다 우수한 전체 레이턴시 균형을 보여줍니다.
