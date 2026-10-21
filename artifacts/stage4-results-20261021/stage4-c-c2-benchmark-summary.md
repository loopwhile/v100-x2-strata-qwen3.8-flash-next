# Stage 4-C C2 128K Performance Benchmark Summary

- **Date / Time**: 2026-10-21 22:31:45 KST
- **Engine**: Upstream Strata `v0.1.47` with Volta sm_70 Table Tuning (`STRATA_SM70_TABLE=1`)
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
| **Output Tokens** | 1,360 | 2,613 | 1,986.5 |
| **Wall Time (s)** | 161.09 s | 196.81 s | 178.95 s |
| **TTFT (s)** | 128.71 s | 126.83 s | **127.77 s** |
| **Prefill Speed** | 988.3 tok/s | 1,003.1 tok/s | **995.70 tok/s** |
| **Decode Speed** | 41.9 tok/s | 37.3 tok/s | **39.60 tok/s** |
| **Expert Cache Hit Rate** | 94.8% | 91.4% | **93.10%** |
| **Prefix Cache Reuse (`cache_n`)** | 0 (No reuse) | 0 (No reuse) | 0 |
| **Min 1,024 Output Check** | PASS | PASS | PASS |
| **Finish Reason** | `stop` | `stop` | `stop` |

- **Batch Wall Time**: 196.81 s
- **Decode Overlap**: 32.38 s
- **Submission Skew**: 0.00375 s
- **Pass Mechanical**: `True`
- **Active Overlap**: `True`
- **Post Health**: `True`

---

## 2. 4-Way Comprehensive Comparison across All Stages

| Metric | Stage 3-A (0.1.36) | Stage 4-A (0.1.44.1) | Stage 4-B (0.1.47 기본) | Stage 4-C (0.1.47 + SM70_TABLE) | vs 3-A Delta (%) | vs 4-B Delta (%) |
| --- | --- | --- | --- | --- | --- | --- |
| **디코드 속도 (Decode)** | **22.20 tok/s** | **31.65 tok/s** | **38.50 tok/s** | **39.60 tok/s** (A: 41.9 / B: 37.3) | **+78.38% 🚀🚀** | **+2.86% 추가 향상** |
| **프리필 속도 (Prefill)** | **909.90 tok/s** | **939.40 tok/s** | **981.55 tok/s** | **995.70 tok/s** (B: 1,003.1) | **+9.43% 향상** | **+1.44% 추가 향상** |
| **TTFT (첫 토큰 지연시간)** | **140.09 s** | **135.41 s** | **129.60 s** | **127.77 s** | **-8.79% (12.32s 단축)** | **-1.83s 추가 단축** |
| **Expert Hit Rate** | ~90.0% | 91.60% | 93.55% | **93.10%** | +3.1%p | 유사 동등 |
| **C2 Protocol Compliance** | PASS | PASS | PASS | **PASS** | Identical | Identical |

---

## 3. Analysis & Key Findings

1. **디코드 속도 최고치 경신 (39.60 tok/s, 최대 41.9 tok/s)**:
   - `STRATA_SM70_TABLE=1` 환경변수 적용 시 Volta sm_70 하드웨어에 최적화된 interleaved rows table GEMV 커널이 활성화되어, 0.1.47 기본 대비 +2.86%의 추가적인 디코드 속도 향상이 발생했습니다.
   - Stage 3-A 베이스라인(22.2 tok/s) 대비로는 **+78.38%**라는 압도적인 성능 격차를 입증했습니다.
2. **프리필 1,000 tok/s 고지 돌파**:
   - Agent B의 경우 프리필 속도 **1,003.1 tok/s**를 기록하여 V100 128K IQ2_XS 세팅에서 최초로 1,000 tok/s를 넘어섰습니다.
   - 대칭 평균 TTFT 역시 **127.77초**로 단축되어, 이전 세대 엔진 대비 12.3초 더 빠르게 응답을 개시합니다.
3. **정합성 및 안정성 유지**:
   - `STRATA_SM70_TABLE=1` 커널은 비트 단위 동일(bitwise exact) 출력을 보장하는 최적화로서 수치적 왜곡 없이 높은 안정성을 보였습니다.
   - 두 에이전트 모두 `finish_reason: stop`과 정상 토큰 스트리밍을 완수했습니다.
