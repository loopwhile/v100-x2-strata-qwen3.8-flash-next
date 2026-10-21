# Stage 4-B C2 128K Performance Benchmark Summary

- **Date / Time**: 2026-10-21 22:23:11 KST
- **Engine**: Upstream Strata `v0.1.47` (Release `v0.2.2`, commit `011c9e600a93bbc9fd451c563501b5831c32bbca`)
- **Docker Image**: `strata-v100-upstream:0.1.47` (`sha256:19c3b72a1097...`)
- **Host**: ThinkStation P520, Xeon W-2135, RAM 61 GiB, 2x Tesla V100-SXM2-16GB (`sm_70`)
- **Power Cap**: 150W (Default, Unchanged)
- **Model**: Qwen3.8-Flash-Next IQ2_XS (GSQ-RCO), INT8 (`q8_0`) KV, 131,072 context
- **KV Cache**: `--kv int8 --kv-resident 32768 --max-context 131072`
- **Workload**: `V100-PERFORMANCE-C2-128K-v1` (`bench/workloads/v100-performance-v1.json`)
- **Workload Manifest SHA-256**: `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca` (MATCH)

---

## 1. Measured Results (Single Cold Run)

| Metric | Agent A (Host GPU 0) | Agent B (Host GPU 1) | Symmetrical Mean |
| --- | --- | --- | --- |
| **Prompt Tokens** | 126,967 | 126,968 | 126,967.5 |
| **Output Tokens** | 1,490 | 1,717 | 1,603.5 |
| **Wall Time (s)** | 167.33 s | 175.54 s | 171.44 s |
| **TTFT (s)** | 130.52 s | 128.69 s | **129.60 s** |
| **Prefill Speed** | 974.6 tok/s | 988.5 tok/s | **981.55 tok/s** |
| **Decode Speed** | 40.4 tok/s | 36.6 tok/s | **38.50 tok/s** |
| **Expert Cache Hit Rate** | 94.5% | 92.6% | **93.55%** |
| **Prefix Cache Reuse (`cache_n`)** | 0 (No reuse) | 0 (No reuse) | 0 |
| **Min 1,024 Output Check** | PASS | PASS | PASS |
| **Finish Reason** | `stop` | `stop` | `stop` |

- **Batch Wall Time**: 175.55 s
- **Decode Overlap**: 36.81 s
- **Submission Skew**: 0.00409 s
- **Pass Mechanical**: `True`
- **Active Overlap**: `True`
- **Post Health**: `True`

---

## 2. 3-Way Comprehensive Comparison

| Metric | Stage 3-A (0.1.36) | Stage 4-A (0.1.44.1) | Stage 4-B (0.1.47) | vs 3-A Delta (%) |
| --- | --- | --- | --- | --- |
| **Decode Speed** | **22.20 tok/s** | **31.65 tok/s** | **38.50 tok/s** | **+73.42% 🚀🚀** |
| **Prefill Speed** | **909.90 tok/s** | **939.40 tok/s** | **981.55 tok/s** | **+7.87% (+71.7 tok/s)** |
| **TTFT (Latency to First Token)** | **140.09 s** | **135.41 s** | **129.60 s** | **-7.49% (10.49s faster)** |
| **Batch Wall Time** | ~200 s | 195.06 s | **175.55 s** | **-12.2% 단축** |
| **Expert Hit Rate** | ~90.0% | 91.60% | **93.55%** | **+3.55%p 향상** |
| **C2 Protocol Compliance** | PASS | PASS | **PASS** | Identical |

---

## 3. Analysis & Key Findings

1. **디코드 속도의 극적인 혁신 (+73.4%)**:
   - Stage 3-A(22.20 tok/s) 대비 Stage 4-B(38.50 tok/s)는 **+73.4%**의 경이로운 향상을 기록했습니다.
   - 특히 Agent A의 경우 **40.4 tok/s**를 돌파하여 V100 16GB 단일 GPU 환경에서 128K 초장문 컨텍스트 디코드의 새로운 최고 기록을 달성했습니다.
2. **프리필 속도 1,000 tok/s 육박 (981.55 tok/s)**:
   - 127K 토큰 콜드 프롬프트 프리필 속도가 909.90 -> 981.55 tok/s로 향상되어 1,000 토큰/초에 거의 도달했습니다.
   - 첫 토큰 출력 시간(TTFT) 역시 140초대에서 **129.6초**로 단축되어 10초 이상 빨라졌습니다.
3. **캐시 적중률 및 효율 향상 (93.55%)**:
   - Expert Cache Hit Rate가 93.55%로 최고치를 기록하며 VRAM과 호스트 메모리 간의 대역폭 압박을 크게 완화했습니다.
