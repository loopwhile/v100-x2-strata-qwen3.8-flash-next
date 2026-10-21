# Stage 4-C IQ3_S C2 128K Performance Benchmark Summary

- **Date / Time**: 2026-10-21 23:15:02 KST
- **Engine**: Upstream Strata `v0.1.47` (Release `v0.2.2`) with `STRATA_SM70_TABLE=1`
- **Docker Image**: `strata-v100-upstream:0.1.47` (`sha256:19c3b72a1097...`)
- **Host**: ThinkStation P520, 2x Tesla V100-SXM2-16GB, 전력 상한 150W (유지)
- **Model**: Qwen3.8-Flash-Next IQ3_S (GSQ-RCO), INT8 (`q8_0`) KV, 131,072 context
- **Workload**: `V100-PERFORMANCE-C2-128K-v1` (Frozen SHA256: `e413acced27c...`)

---

## 1. Measured Results (Single Cold Run)

| Metric | Agent A (Host GPU 0) | Agent B (Host GPU 1) | Symmetrical Mean |
| --- | --- | --- | --- |
| **Prompt Tokens** | 126,967 | 126,968 | 126,967.5 |
| **Output Tokens** | 1,783 | 1,657 | 1,720.0 |
| **Wall Time (s)** | 359.12 s | 351.33 s | 355.22 s |
| **TTFT (s)** | 270.61 s | 272.59 s | **271.60 s** |
| **Prefill Speed** | 469.7 tok/s | 466.4 tok/s | **468.05 tok/s** |
| **Decode Speed** | 20.1 tok/s | 21.0 tok/s | **20.55 tok/s** |
| **Expert Cache Hit Rate** | 80.1% | 82.9% | **81.50%** |
| **Prefix Cache Reuse (`cache_n`)** | 0 (No reuse) | 0 (No reuse) | 0 |
| **Min 1,024 Output Check** | PASS | PASS | PASS |
| **Finish Reason** | `stop` | `stop` | `stop` |

- **Batch Wall Time**: 359.13 s
- **Decode Overlap**: 78.73 s
- **Pass Mechanical**: `True`, **Active Overlap**: `True`, **Post Health**: `True`

---

## 2. IQ3_S Historical Engine Comparison

| Engine / Release | Prefill (tok/s) | TTFT (s) | Decode (tok/s) | Expert Hit | vs Stage 3-A Decode |
|---|---|---|---|---|---|
| **Stage 2** (Strata 0.1.31) | 602.40 | 211.36 | 10.75 | 76.10% | - |
| **Stage 3-A** (Strata 0.1.36) | 721.30 | 176.62 | 10.65 | 75.45% | Baseline |
| **Stage 3-B** (0.1.36 tuned) | 731.15 | 174.25 | 10.70 | 73.50% | +0.5% |
| **Stage 4-C** (0.1.47 + SM70_TABLE) | 468.05 | 271.60 | **20.55** | **81.50%** | **+92.96% 🚀 (약 2배 향상!)** |

---

## 3. Analysis

- **IQ3_S 디코드 병목 돌파**: Stage 2 및 Stage 3 전반에 걸쳐 10.6~10.7 tok/s에 고착되어 있던 IQ3_S 디코드 속도가 0.1.47 및 `STRATA_SM70_TABLE=1` 최적화 하에서 **20.55 tok/s로 93% 급증**했습니다.
- **IQ 계열 전반의 공통 현상**:
  - IQ2_XS: 22.20 -> 39.60 tok/s (+78.4%)
  - IQ3_XXS: 12.70 -> 26.05 tok/s (+105.1%)
  - IQ3_S: 10.65 -> 20.55 tok/s (+93.0%)
- **Prefill 및 TTFT 트레이드오프**: IQ3_S는 파일 크기가 커짐에 따라 호스트 메모리 매핑 및 스왑 페이징 부하가 발생(테스트 중 swap 사용량 약 3.0 GiB)하여 Prefill은 낮아졌으나, 디코드 단계에서는 20 tok/s를 안정적으로 유지하였습니다.
