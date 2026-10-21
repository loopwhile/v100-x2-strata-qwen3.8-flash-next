# Stage 4-B IQ3_S C2 128K Performance Benchmark Summary

- **Date / Time**: 2026-10-21 23:56:49 KST
- **Engine**: Upstream Strata `v0.1.47` (Release `v0.2.2`, Vanilla Defaults without `STRATA_SM70_TABLE=1`)
- **Docker Image**: `strata-v100-upstream:0.1.47` (`sha256:19c3b72a1097...`)
- **Host**: ThinkStation P520, 2x Tesla V100-SXM2-16GB, 전력 상한 150W (유지)
- **Model**: Qwen3.8-Flash-Next IQ3_S (GSQ-RCO), INT8 (`q8_0`) KV, 131,072 context
- **Workload**: `V100-PERFORMANCE-C2-128K-v1` (Frozen SHA256: `e413acced27c...`)

---

## 1. Measured Results (Single Cold Run)

| Metric | Agent A (Host GPU 0) | Agent B (Host GPU 1) | Symmetrical Mean |
| --- | --- | --- | --- |
| **Prompt Tokens** | 126,967 | 126,968 | 126,967.5 |
| **Output Tokens** | 1,648 | 1,657 | 1,652.5 |
| **Wall Time (s)** | 315.88 s | 314.22 s | 315.05 s |
| **TTFT (s)** | 238.12 s | 237.08 s | **237.60 s** |
| **Prefill Speed** | 533.8 tok/s | 536.2 tok/s | **535.00 tok/s** |
| **Decode Speed** | 21.2 tok/s | 21.5 tok/s | **21.35 tok/s** |
| **Expert Cache Hit Rate** | 80.1% | 82.9% | **81.50%** |
| **Prefix Cache Reuse (`cache_n`)** | 0 (No reuse) | 0 (No reuse) | 0 |
| **Min 1,024 Output Check** | PASS | PASS | PASS |
| **Finish Reason** | `stop` | `stop` | `stop` |

- **Batch Wall Time**: 315.90 s
- **Decode Overlap**: 76.09 s
- **Pass Mechanical**: `True`, **Active Overlap**: `True`, **Post Health**: `True`

---

## 2. IQ3_S Engine Comparison (Stage 2 ~ Stage 4-C)

| Engine / Release | Prefill (tok/s) | TTFT (s) | Decode (tok/s) | Expert Hit | vs Stage 3-A Decode |
|---|---|---|---|---|---|
| **Stage 2** (Strata 0.1.31) | 602.40 | 211.36 | 10.75 | 76.10% | - |
| **Stage 3-A** (Strata 0.1.36) | 721.30 | 176.62 | 10.65 | 75.45% | Baseline |
| **Stage 3-B** (0.1.36 tuned) | 731.15 | 174.25 | 10.70 | 73.50% | +0.5% |
| **Stage 4-B** (0.1.47 vanilla) | **535.00** | **237.60** | **21.35** | **81.50%** | **+100.47% 🚀 (2배 향상)** |
| **Stage 4-C** (0.1.47 + SM70_TABLE) | 468.05 | 271.60 | 20.55 | 81.50% | +92.96% 🚀 |

---

## 3. Analysis

- **디코드 2배 도약 검증**: Stage 4-B(순정 0.1.47)에서도 IQ3_S 디코드 속도가 **21.35 tok/s**로 측정되어 Stage 3-A 대비 **+100.5% (정확히 2배)** 향상되었습니다.
- **Stage 4-B vs Stage 4-C 비교 (SM70_TABLE의 영향)**:
  - **디코드**: Stage 4-B(21.35 tok/s)가 Stage 4-C(20.55 tok/s)보다 약간 높거나 유사.
  - **Prefill / TTFT**: Stage 4-B(535.0 tok/s, 237.6s)가 Stage 4-C(468.1 tok/s, 271.6s) 대비 **Prefill +14.3% 빠르고 TTFT를 34초 단축**.
- **결론**: IQ3 양자화(IQ3_XXS, IQ3_S)에서는 `STRATA_SM70_TABLE=1` 옵션이 디코드 이점 없이 Prefill/TTFT에 오버헤드를 유발하므로, **IQ3 모델 서빙 시에는 순정 Upstream 0.1.47 (Stage 4-B) 설정이 최선**입니다.
