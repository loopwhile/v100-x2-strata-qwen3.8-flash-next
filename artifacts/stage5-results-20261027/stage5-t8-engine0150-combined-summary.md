# Stage 5 T8 — Upstream 0.1.50 + Combined SIMT + WMMA Benchmark Summary

- **Date**: 2026-10-27
- **Target**: Lenovo ThinkStation P520, Xeon W-2135 (6C/12T), 64 GB DDR4 ECC, 2 × Tesla V100 16 GB (150 W caps)
- **Model**: Qwen3.8-Flash-Next GSQ-RCO IQ3_S (Mounted from NVMe1 `/srv/models/strata-iq3s`)
- **Engine**: Upstream Strata `v0.2.6` (`0.1.50` / `0.1.51`, commit `4b9e05a2a806a3fe24f7b2560d98626c37dade35`) + `STRATA_SELECT_SIMT=1` + `STRATA_PF_WMMA=1` + `STRATA_STAGER_SSD=0`
- **Workload**: `V100-PERFORMANCE-C2-128K-v1` (SHA256: `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`)
- **Execution Protocol**: 3 Independent Fresh-Process C2 Batches (`cache_n=0`, `cached_tokens=0`, `requests_kept=0`), with full telemetry (`vmstat`, `iostat`, `pidstat`, `nvidia-smi`).
- **Result Status**: ✅ **PASS**

---

## 1. 3-Batch Empirical Results & Cross-Engine Comparison

| Metric | T8 Run 1 | T8 Run 2 | T8 Run 3 | **T8 3-Run Mean** | **T8 3-Run Median** | T1 Baseline Mean (0.1.47) | T6-Fixed Mean (0.1.50 Vanilla) | T4 Mean (0.1.47 SIMT+WMMA) | **T8 vs T6-Fixed** |
|---|---|---|---|---|---|---|---|---|---|
| **Agent A Prefill (tok/s)** | 872.1 | 870.8 | 871.5 | **871.47** | 871.50 | 738.07 | 747.30 | 881.90 | **+16.6%** |
| **Agent B Prefill (tok/s)** | 881.8 | 879.6 | 880.2 | **880.53** | 880.20 | 751.03 | 756.23 | 892.83 | **+16.4%** |
| **Symmetric Mean Prefill** | **876.95** | **875.20** | **875.85** | **876.00 tok/s** | **875.85 tok/s** | 744.55 tok/s | 751.77 tok/s | 887.37 tok/s | **+16.5% 향상 (T1 대비 +17.7%) 🚀** |
| **Agent A TTFT (s)** | 145.88 | 146.08 | 145.97 | **145.98** | 145.97 | 172.54 | 170.42 | 144.24 | **-24.4s 단축** |
| **Agent B TTFT (s)** | 144.26 | 144.62 | 144.53 | **144.47** | 144.53 | 169.66 | 168.46 | 142.48 | **-24.0s 단축** |
| **Symmetric Mean TTFT (s)** | **145.07** | **145.35** | **145.25** | **145.22 s** | **145.25 s** | 171.10 s | 169.44 s | 143.36 s | **-24.2s 단축 (T1 대비 -25.9s) ⚡** |
| **Agent A Decode (tok/s)** | 20.1 | 20.2 | 20.6 | **20.30** | 20.20 | 21.07 | 21.00 | 21.17 | -0.7 tok/s |
| **Agent B Decode (tok/s)** | 21.3 | 21.2 | 21.2 | **21.23** | 21.20 | 21.83 | 21.40 | 21.23 | 동등 유지 |
| **Symmetric Mean Decode** | **20.70** | **20.70** | **20.90** | **20.77 tok/s** | **20.70 tok/s** | 21.45 tok/s | 21.20 tok/s | 21.20 tok/s | **안정적 유지 (~20.8 tok/s)** |
| **Batch Wall Time (s)** | 236.84 | 233.61 | 232.76 | **234.40 s** | **233.61 s** | 254.48 s | 253.91 s | 228.92 s | **-19.5s 단축 ⚡** |
| **Decode Overlap (s)** | 71.85 | 63.22 | 63.15 | **66.07 s** | **63.22 s** | 74.82 s | 77.27 s | 62.70 s | **대칭 동시 디코드** |
| **Swap Usage After Run** | 72 MiB | 73 MiB | 73 MiB | **72.7 MiB** | **73 MiB** | 62 MiB | 69 MiB | 56 MiB | **쓰래싱 0 (ΔSwap = 0~2 MiB)** |
| **Mechanical Contract** | PASS | PASS | PASS | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **All PASS** |

---

## 2. Text Determinism & Cross-Engine Parity Analysis

| Agent | T4 (0.1.47 SIMT+WMMA) SHA256 | T8 Run 1 SHA256 | T8 Run 2 SHA256 | T8 Run 3 SHA256 | Parity Assessment |
|---|---|---|---|---|---|
| **Agent A** | `4ceeb38...` | `c873cf4...` | `51f78f7...` | `a2df696...` | Valid stop, 1,768–1,831 generated tokens across runs. |
| **Agent B** | `f4f7731...` | `ad74532...` | `f4f7731...` | `f4f7731...` | Run 2 & Run 3 matched **0.1.47 T4 (`f4f7731...`) 100% bit-for-bit**. |

---

## 3. Key Findings & Takeaways

1. **초고밀도 재현성 (Ultra-Tight Variance)**:
   - 3회 반복 측정에서 Symmetric 프리필 처리량이 **876.95 / 875.20 / 875.85 tok/s** (최대-최소 편차 **1.75 tok/s, 0.2% 이내**), TTFT가 **145.07 / 145.35 / 145.25 s** (편차 **0.28초**)로 극도로 일관된 성능을 기록했습니다.
2. **스왑 변동 0 (Zero Swap Thrashing)**:
   - `STRATA_STAGER_SSD=0` 및 GGUF 샤드 페이지 캐시 고정 하에서 3회 연속 실행 내내 호스트 스왑 사용량이 `70 MiB -> 72 MiB -> 73 MiB -> 73 MiB`로 사실상 변동 0을 유지했습니다.
3. **0.1.47 (T4) vs 0.1.50 (T8) 비교**:
   - 동일 플래그(`SIMT+WMMA`) 기준 **0.1.47 (T4: 평균 887.37 tok/s, 디코드 21.20 tok/s, Wall 228.92s)** 이 **0.1.50 (T8: 평균 876.00 tok/s, 디코드 20.77 tok/s, Wall 234.40s)** 보다 프리필에서 약 +1.3%(+11.4 tok/s), 디코드에서 +0.43 tok/s 소폭 우세합니다.
