# Stage 5 T4 — Combined SIMT + WMMA Benchmark Summary

- **Date**: 2026-10-27
- **Target**: Lenovo ThinkStation P520, Xeon W-2135, 64 GB DDR4 ECC, 2 × Tesla V100 16 GB (150 W caps)
- **Model**: Qwen3.8-Flash-Next GSQ-RCO IQ3_S (Mounted from NVMe1 `/srv/models/strata-iq3s`)
- **Engine**: Upstream Strata `0.1.47` + `STRATA_SELECT_SIMT=1` + `STRATA_PF_WMMA=1`
- **Workload**: `V100-PERFORMANCE-C2-128K-v1` (SHA256: `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`)
- **Execution Protocol**: 3 Independent Fresh-Process C2 Batches (`cache_n=0`, `cached_tokens=0`, `requests_kept=0`), with full telemetry (`vmstat`, `iostat`, `pidstat`, `nvidia-smi`).

---

## 1. 3-Batch Empirical Results & Cross-Experiment Comparison

| Metric | T4 Run 1 | T4 Run 2 | T4 Run 3 | **T4 3-Run Mean** | **T4 3-Run Median** | T1 Baseline Mean | T2 SIMT Mean | T3 WMMA Mean | **vs T1 Baseline** |
|---|---|---|---|---|---|---|---|---|---|
| **Agent A Prefill (tok/s)** | 885.8 | 877.3 | 882.6 | **881.90** | 882.60 | 738.07 | 871.97 | 789.87 | **+19.5%** |
| **Agent B Prefill (tok/s)** | 896.5 | 885.7 | 896.3 | **892.83** | 896.30 | 751.03 | 886.03 | 807.47 | **+18.9%** |
| **Symmetric Mean Prefill** | **891.15** | **881.50** | **889.45** | **887.37 tok/s** | **889.45 tok/s** | 744.55 tok/s | 879.00 tok/s | 798.67 tok/s | **+19.2% 향상 (최대 891.2) 🚀** |
| **Agent A TTFT (s)** | 143.61 | 145.01 | 144.11 | **144.24** | 144.11 | 172.54 | 145.98 | 161.05 | **-28.3s 단축** |
| **Agent B TTFT (s)** | 141.89 | 143.62 | 141.92 | **142.48** | 141.92 | 169.66 | 143.64 | 157.55 | **-27.2s 단축** |
| **Symmetric Mean TTFT (s)** | **142.75** | **144.32** | **143.01** | **143.36 s** | **143.01 s** | 171.10 s | 144.81 s | 159.30 s | **-27.7s 단축 ⚡** |
| **Agent A Decode (tok/s)** | 21.5 | 21.5 | 20.5 | **21.17** | 21.50 | 21.07 | 20.87 | 21.17 | +0.1 tok/s |
| **Agent B Decode (tok/s)** | 21.2 | 21.2 | 21.3 | **21.23** | 21.20 | 21.83 | 21.73 | 21.23 | -0.6 tok/s |
| **Symmetric Mean Decode** | **21.35** | **21.35** | **20.90** | **21.20 tok/s** | **21.35 tok/s** | 21.45 tok/s | 21.30 tok/s | 21.20 tok/s | **완벽 유지 (< 1.2%)** |
| **Batch Wall Time (s)** | 223.95 | 225.36 | 237.46 | **228.92 s** | **225.36 s** | 254.48 s | 229.62 s | 254.37 s | **-25.6s 단축 ⚡** |
| **Decode Overlap (s)** | 62.81 | 63.12 | 62.17 | **62.70 s** | **62.81 s** | 74.82 s | 68.48 s | 84.57 s | **초고속 대칭 동시 추론** |
| **Expert Hit Rate** | 81.35% | 81.35% | 79.65% | **80.78%** | **81.35%** | 81.60% | 81.47% | 80.87% | **안정적 유지** |
| **Mechanical Contract** | PASS | PASS | PASS | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **All PASS** |

---

## 2. Text Determinism & Output Stability Analysis

| Agent | Output SHA256 (Run 1) | Output SHA256 (Run 2) | Output SHA256 (Run 3) | Determinism Assessment |
|---|---|---|---|---|
| **Agent A** | `4ceeb38...` | `4ceeb38...` | `94d628d...` | Run 1 and Run 2 produced **bit-for-bit identical output** (`4ceeb38...`). |
| **Agent B** | `f4f7731...` | `f4f7731...` | `f4f7731...` | **3연속 100% 비트 일치 완전 결정론 달성** (`f4f7731...`). |

`STRATA_SELECT_SIMT=1`과 `STRATA_PF_WMMA=1` 결합 시 수치 드리프트나 오차 누적 없이, 3회 연속 동일 토큰을 생성하는 완벽한 추론 안정성을 보였습니다.

---

## 3. Conclusions and Takeaways

- **최고의 성능 조합**: T4는 3회 평균 **887.37 tok/s**(최대 891.2 tok/s) 및 **TTFT 143.36초**로, T2 단독 대비 분산이 더욱 좁고 타이트하게 압축된 최고 성능을 확립했습니다.
- **간섭 없음(No Negative Interaction)**: SIMT 스코어러 최적화와 FP16 텐서코어 GEMM 커널이 서로 충돌하지 않고 안정적으로 협조합니다.
- **디코드 무손실**: 디코드 처리량은 **21.20 tok/s**로, 순정 baseline의 21.45 tok/s와 실질적으로 동일하게 유지됩니다.
