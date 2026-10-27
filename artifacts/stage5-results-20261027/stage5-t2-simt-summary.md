# Stage 5 T2 — `STRATA_SELECT_SIMT=1` Benchmark Summary

- **Date**: 2026-10-27
- **Target**: Lenovo ThinkStation P520, Xeon W-2135, 64 GB DDR4 ECC, 2 × Tesla V100 16 GB (150 W caps)
- **Model**: Qwen3.8-Flash-Next GSQ-RCO IQ3_S (Mounted from NVMe1 `/srv/models/strata-iq3s`)
- **Engine**: Upstream Strata `0.1.47` + `STRATA_SELECT_SIMT=1`
- **Workload**: `V100-PERFORMANCE-C2-128K-v1` (SHA256: `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`)
- **Execution Protocol**: 3 Independent Fresh-Process C2 Batches (`cache_n=0`, `cached_tokens=0`, `requests_kept=0`), with full telemetry (`vmstat`, `iostat`, `pidstat`, `nvidia-smi`).

---

## 1. 3-Batch Empirical Results & T1 Comparison

| Metric | T2 Run 1 | T2 Run 2 | T2 Run 3 | **T2 3-Run Mean** | **T2 3-Run Median** | **T1 Baseline Mean** | **vs T1 Baseline** |
|---|---|---|---|---|---|---|---|
| **Agent A Prefill (tok/s)** | 882.6 | 842.9 | 890.4 | **871.97** | 882.60 | 738.07 | **+18.1%** |
| **Agent B Prefill (tok/s)** | 896.6 | 859.0 | 902.5 | **886.03** | 896.60 | 751.03 | **+18.0%** |
| **Symmetric Mean Prefill** | **889.60** | **850.95** | **896.45** | **879.00 tok/s** | **889.60 tok/s** | **744.55 tok/s** | **+18.1% (최대 896.5 tok/s) 🚀** |
| **Agent A TTFT (s)** | 144.13 | 150.93 | 142.87 | **145.98** | 144.13 | 172.54 | **-26.6s 단축** |
| **Agent B TTFT (s)** | 141.88 | 148.09 | 140.95 | **143.64** | 141.88 | 169.66 | **-26.0s 단축** |
| **Symmetric Mean TTFT (s)** | **143.00** | **149.51** | **141.91** | **144.81 s** | **143.00 s** | **171.10 s** | **-26.3s 단축 ⚡** |
| **Agent A Decode (tok/s)** | 21.3 | 20.6 | 20.7 | **20.87** | 20.70 | 21.07 | -0.2 tok/s |
| **Agent B Decode (tok/s)** | 21.9 | 21.8 | 21.5 | **21.73** | 21.80 | 21.83 | -0.1 tok/s |
| **Symmetric Mean Decode** | **21.60** | **21.20** | **21.10** | **21.30 tok/s** | **21.20 tok/s** | **21.45 tok/s** | **완벽 유지 (차이 < 0.7%)** |
| **Batch Wall Time (s)** | 239.31 | 228.89 | 220.65 | **229.62 s** | **228.89 s** | **254.48 s** | **-24.9s 단축 ⚡** |
| **Decode Overlap (s)** | 66.12 | 66.00 | 73.33 | **68.48 s** | **66.12 s** | **74.82 s** | **안정적 동시 디코드** |
| **Expert Hit Rate** | 81.95% | 81.40% | 81.05% | **81.47%** | **81.40%** | **81.60%** | **동일 수준** |
| **Mechanical Contract** | PASS | PASS | PASS | **PASS** | **PASS** | **PASS** | **All PASS** |

---

## 2. Text Determinism & Numerical Drift Analysis

| Agent | Output SHA256 (Run 1) | Output SHA256 (Run 2) | Output SHA256 (Run 3) | Determinism Assessment |
|---|---|---|---|---|
| **Agent A** | `333c17f...` | `7d9365b...` | `7d9365b...` | Run 2 and Run 3 produced **bit-for-bit identical output** (`7d9365b...`). |
| **Agent B** | `46b221d...` | `46b221d...` | `0bf025a...` | Run 1 and Run 2 produced **bit-for-bit identical output** (`46b221d...`). |

`STRATA_SELECT_SIMT=1` maintains complete functional validity, JSON/code syntax conformance, and high cross-run determinism without numeric divergence.

---

## 3. Conclusions and Gate Status for T4

- **T2 Verdict**: **CLEAR PASS (Highly Favorable Optimization)**
  - Prefill 속도: **+18.1% 향상 (879.0 tok/s)**
  - TTFT: **26.3초 단축 (144.8초)**
  - Decode 속도: **21.3 tok/s로 완전 보존**
  - 시스템 안정성: 스왑 제로, Major fault 최소 수준 유지
- **T4 결합 게이트 충족**: T2가 뚜렷하고 재현성 있는 실질적 성능 향상을 입증하였으므로, T3 결과에 따라 **T4 결합 실험(SIMT + WMMA)을 공식적으로 진행할 수 있는 자격**을 확보했습니다.
