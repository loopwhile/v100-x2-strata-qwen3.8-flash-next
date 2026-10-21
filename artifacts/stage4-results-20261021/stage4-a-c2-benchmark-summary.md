# Stage 4-A C2 128K Performance Benchmark Summary

- **Date / Time**: 2026-10-21 22:00:57 KST
- **Engine**: Upstream Strata `v0.1.44.1` (commit `296b59d2f73c8f04a805df29c2fa97655adace78`)
- **Docker Image**: `strata-v100-upstream:0.1.44.1` (`sha256:56fd71f0ddfe...`)
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
| **Output Tokens** | 1,747 | 1,273 | 1,510.0 |
| **Wall Time (s)** | 195.05 s | 172.18 s | 183.61 s |
| **TTFT (s)** | 136.72 s | 134.11 s | **135.41 s** |
| **Prefill Speed** | 930.3 tok/s | 948.5 tok/s | **939.40 tok/s** |
| **Decode Speed** | 29.9 tok/s | 33.4 tok/s | **31.65 tok/s** |
| **Expert Cache Hit Rate** | 90.5% | 92.7% | **91.60%** |
| **Prefix Cache Reuse (`cache_n`)** | 0 (No reuse) | 0 (No reuse) | 0 |
| **Min 1,024 Output Check** | PASS | PASS | PASS |
| **Finish Reason** | `stop` | `stop` | `stop` |

- **Batch Wall Time**: 195.06 s
- **Decode Overlap**: 35.45 s (both agents actively decoding concurrently)
- **Submission Skew**: 0.00427 s (near-simultaneous release through barrier)
- **Pass Mechanical**: `True`
- **Active Overlap**: `True`
- **Post Health**: `True`

---

## 2. Comparison against Stage 3-A Baseline

| Metric | Stage 3-A (jmnargi/Strata-V100 0.1.36) | Stage 4-A (Upstream Strata 0.1.44.1) | Delta (%) |
| --- | --- | --- | --- |
| **Prefill Speed** | 909.90 tok/s | **939.40 tok/s** | **+3.24%** |
| **TTFT (Latency to First Token)** | 140.09 s | **135.41 s** | **-3.34% (4.68s faster)** |
| **Decode Speed** | 22.20 tok/s | **31.65 tok/s** | **+42.57%** |
| **Expert Hit Rate** | ~90.0% | **91.60%** | +1.6%p |
| **C2 Protocol Compliance** | PASS | **PASS** | Identical |

---

## 3. Analysis & Key Findings

1. **대폭 향상된 디코드 성능 (+42.57%)**:
   - 디코드 속도가 기존 22.20 tok/s에서 **31.65 tok/s**(Agent B의 경우 33.4 tok/s)로 약 **42.6% 급증**했습니다.
   - 이는 Upstream Strata v0.1.44.1에 통합된 개선 사항(Volta 호환 최적화, QSA 디코드 커널, MTP M-spec 커밋 배치 처리 등)이 실제 V100 128K 부하에서 탁월한 효율을 내고 있음을 실증합니다.
2. **프리필 및 TTFT 개선 (+3.24% / -4.68초)**:
   - 127K 토큰에 달하는 극한의 콜드 프롬프트 프리필 속도가 909.9 -> 939.4 tok/s로 향상되었으며, TTFT가 약 4.7초 단축되었습니다.
3. **완벽한 C2 계약 준수**:
   - 프롬프트 독립성(`sha256`), 무예열(`cache_n=0`, `warmup=0`), 최소 출력 토큰(>1024), 동시 디코드 오버랩(35.45s) 모두 통과했습니다.
   - 호스트 전력 설정(`150W`) 및 하드웨어 환경은 일체 변경되지 않았습니다.
