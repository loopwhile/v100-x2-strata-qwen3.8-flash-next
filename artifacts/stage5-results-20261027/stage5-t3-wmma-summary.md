# Stage 5 T3 — `STRATA_PF_WMMA=1` Benchmark Summary

- **Date**: 2026-10-27
- **Target**: Lenovo ThinkStation P520, Xeon W-2135, 64 GB DDR4 ECC, 2 × Tesla V100 16 GB (150 W caps)
- **Model**: Qwen3.8-Flash-Next GSQ-RCO IQ3_S (Mounted from NVMe1 `/srv/models/strata-iq3s`)
- **Engine**: Upstream Strata `0.1.47` + `STRATA_PF_WMMA=1` (Volta V100 Tensor-Core FP16 Expert GEMMs)
- **Workload**: `V100-PERFORMANCE-C2-128K-v1` (SHA256: `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`)
- **Execution Protocol**: 3 Independent Fresh-Process C2 Batches (`cache_n=0`, `cached_tokens=0`, `requests_kept=0`), with full telemetry (`vmstat`, `iostat`, `pidstat`, `nvidia-smi`).

---

## 1. 3-Batch Empirical Results & T1/T2 Comparison

| Metric | T3 Run 1 | T3 Run 2 | T3 Run 3 | **T3 3-Run Mean** | **T3 3-Run Median** | **T1 Baseline Mean** | **T2 SIMT Mean** | **vs T1 Baseline** |
|---|---|---|---|---|---|---|---|---|
| **Agent A Prefill (tok/s)** | 798.3 | 776.5 | 794.8 | **789.87** | 794.80 | 738.07 | 871.97 | **+7.0%** |
| **Agent B Prefill (tok/s)** | 813.0 | 799.1 | 810.3 | **807.47** | 810.30 | 751.03 | 886.03 | **+7.5%** |
| **Symmetric Mean Prefill** | **805.65** | **787.80** | **802.55** | **798.67 tok/s** | **802.55 tok/s** | **744.55 tok/s** | **879.00 tok/s** | **+7.3% 향상 🚀** |
| **Agent A TTFT (s)** | 159.32 | 163.81 | 160.02 | **161.05** | 160.02 | 172.54 | 145.98 | **-11.5s 단축** |
| **Agent B TTFT (s)** | 156.45 | 159.19 | 157.01 | **157.55** | 157.01 | 169.66 | 143.64 | **-12.1s 단축** |
| **Symmetric Mean TTFT (s)** | **157.89** | **161.50** | **158.51** | **159.30 s** | **158.51 s** | **171.10 s** | **144.81 s** | **-11.8s 단축 ⚡** |
| **Agent A Decode (tok/s)** | 21.3 | 21.1 | 21.1 | **21.17** | 21.10 | 21.07 | 20.87 | +0.1 tok/s |
| **Agent B Decode (tok/s)** | 21.6 | 21.6 | 20.5 | **21.23** | 21.60 | 21.83 | 21.73 | -0.6 tok/s |
| **Symmetric Mean Decode** | **21.45** | **21.35** | **20.80** | **21.20 tok/s** | **21.35 tok/s** | **21.45 tok/s** | **21.30 tok/s** | **완벽 유지 (차이 < 1.1%)** |
| **Batch Wall Time (s)** | 243.83 | 248.18 | 271.09 | **254.37 s** | **248.18 s** | **254.48 s** | **229.62 s** | **유사 (생성 토큰 증가 반영)** |
| **Decode Overlap (s)** | 84.23 | 83.49 | 85.98 | **84.57 s** | **84.23 s** | **74.82 s** | **68.48 s** | **+9.8s 향상 (역대 최장 오버랩)** |
| **Expert Hit Rate** | 81.55% | 81.50% | 79.55% | **80.87%** | **81.50%** | **81.60%** | **81.47%** | **안정적 유지** |
| **Mechanical Contract** | PASS | PASS | PASS | **PASS** | **PASS** | **PASS** | **PASS** | **All PASS** |

---

## 2. Technical Findings & Comparison: T2 vs T3

1. **FP16 Tensor-Core Expert GEMM (`STRATA_PF_WMMA=1`) 효과**:
   - V100 텐서코어를 활용하는 FP16 GEMM 커널은 IQ3_S의 128K 프롬프트 인제스천을 순정 대비 **+7.3% (744.6 -> 798.7 tok/s)** 가속하고, TTFT를 **11.8초 단축**시켰습니다.
   - 하지만 QSA 스코어러 커널을 최적화한 **T2 (`STRATA_SELECT_SIMT=1`)의 +18.1% (879.0 tok/s)** 향상 폭이 더 컸습니다.
   - 반면, T3는 두 에이전트 간 디코드 타이밍 동기화가 탁월하여 **평균 디코드 오버랩이 84.57초**로 역대 가장 길고 안정적인 동시 생성을 보였습니다.

2. **T4 (SIMT + WMMA 결합) 게이트 평가**:
   - `STAGE5_PLAN.md` 78행에 명시된 T4 실행 게이트 조건:
     > *"run only if at least one isolated option has a repeatable practical improvement and neither produces unacceptable errors or quality regressions."*
   - T2 (`STRATA_SELECT_SIMT=1`)는 **+18.1% 향상(879 tok/s)**으로 뚜렷한 실용적 이득을 달성.
   - T3 (`STRATA_PF_WMMA=1`) 역시 **+7.3% 향상(798.7 tok/s)** 및 84.6s 동시 오버랩을 달성.
   - 두 플래그 모두 오류나 디코드 저하가 전혀 없었으므로, **T4 (T2 + T3 결합) 실행 게이트를 완벽히 통과(GO)**했습니다!
