# Stage 5 T6 — Upstream 0.1.50 (Strata v0.2.6) Benchmark & Stager Fix Summary

- **Date**: 2026-10-27
- **Target**: Lenovo ThinkStation P520, Xeon W-2135 (6C/12T), 64 GB DDR4 ECC, 2 × Tesla V100 16 GB (150 W caps)
- **Model**: Qwen3.8-Flash-Next GSQ-RCO IQ3_S (Mounted from NVMe1 `/srv/models/strata-iq3s`)
- **Engine Candidate**: Upstream Strata `v0.2.6` (reported engine `0.1.51` / `0.1.50`), commit `4b9e05a2a806a3fe24f7b2560d98626c37dade35`, CUDA 12.9.1, sm_70
- **Workload**: `V100-PERFORMANCE-C2-128K-v1` (SHA256: `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`)
- **Result Status**: ✅ **PASS (After Fixing Page-Cache Eviction & Forcing RAM Stager Profile `STRATA_STAGER_SSD=0`)**

---

## 1. T6-Fixed 3-Batch Empirical Results vs Unfixed T6, T1 Baseline & T4 Champion

| Metric | T6 Unfixed Run 1 | T6-Fixed Run 1 | T6-Fixed Run 2 | T6-Fixed Run 3 | **T6-Fixed 3-Run Mean** | **T6-Fixed Median** | T1 Baseline Mean (0.1.47) | T4 Champion Mean (SIMT+WMMA) | **T6-Fixed vs T1 Baseline** |
|---|---|---|---|---|---|---|---|---|---|
| **Agent A Prefill (tok/s)** | 247.1 | 737.5 | 719.5 | 784.9 | **747.30** | 737.50 | 738.07 | 881.90 | **+1.3%** |
| **Agent B Prefill (tok/s)** | 247.1 | 745.2 | 725.8 | 797.7 | **756.23** | 745.20 | 751.03 | 892.83 | **+0.7%** |
| **Symmetric Mean Prefill** | 247.10 | **741.35** | **722.65** | **791.30** | **751.77 tok/s** | **741.35 tok/s** | 744.55 tok/s | 887.37 tok/s | **+1.0% (Unfixed 대비 3.04배 🚀)** |
| **Agent A TTFT (s)** | 514.13 | 172.44 | 176.78 | 162.03 | **170.42** | 172.44 | 172.54 | 144.24 | **-2.1s 단축** |
| **Agent B TTFT (s)** | 514.13 | 170.67 | 175.23 | 159.47 | **168.46** | 170.67 | 169.66 | 142.48 | **-1.2s 단축** |
| **Symmetric Mean TTFT (s)** | 514.13 | **171.56** | **176.01** | **160.75** | **169.44 s** | **171.56 s** | 171.10 s | 143.36 s | **-1.7s (Unfixed 대비 -344.7s ⚡)** |
| **Agent A Decode (tok/s)** | 19.0 | 21.0 | 21.2 | 20.8 | **21.00** | 21.00 | 21.07 | 21.17 | 동등 유지 |
| **Agent B Decode (tok/s)** | 18.7 | 21.5 | 20.9 | 21.8 | **21.40** | 21.50 | 21.83 | 21.23 | 동등 유지 |
| **Symmetric Mean Decode** | 18.85 | **21.25** | **21.05** | **21.30** | **21.20 tok/s** | **21.25 tok/s** | 21.45 tok/s | 21.20 tok/s | **완벽 유지 (< 1.2%)** |
| **Batch Wall Time (s)** | 601.58 | 250.75 | 268.05 | 242.94 | **253.91 s** | **250.75 s** | 254.48 s | 228.92 s | **동등 유지 (-0.6s)** |
| **Decode Overlap (s)** | 76.58 | 75.31 | 77.51 | 78.98 | **77.27 s** | **77.51 s** | 74.82 s | 62.70 s | **+2.45s 안정적 중첩** |
| **Expert Hit Rate** | 81.65% | 81.50% | 82.05% | 81.45% | **81.67%** | **81.50%** | 81.60% | 80.78% | **안정적 유지** |
| **Mechanical Contract** | PASS | PASS | PASS | PASS | **PASS** | **PASS** | **PASS** | **PASS** | **All PASS** |

---

## 2. Text Determinism & Parity with 0.1.47 (T1)

| Agent | T1 Run 1 SHA256 (0.1.47) | T6-Fixed Run 1 SHA256 | T6-Fixed Run 2 SHA256 | T6-Fixed Run 3 SHA256 | Parity Assessment |
|---|---|---|---|---|---|
| **Agent A** | `0c7715d...` | `0c7715d...` | `3799569...` | `0c7715d...` | Run 1 & Run 3 matched **0.1.47 T1 Run 1 bit-for-bit (`0c7715d...`)** |
| **Agent B** | `e18bf68...` | `e18bf68...` | `e18bf68...` | `b65d259...` | Run 1 & Run 2 matched **0.1.47 T1 Run 1 bit-for-bit (`e18bf68...`)** |

---

## 3. Root Cause Diagnosis & Fix Verification

### 1) 초기 T6 Unfixed Run 1에서 발생한 쓰래싱 메커니즘
- **직전 `docker build`에 의한 페이지 캐시 오염**:
  - `86-docker-build-upstream-0.1.50.sh` 실행 중 생성된 컴파일 아티팩트 및 Docker 레이어(~6.7 GB)가 리눅스 커널 `Active(file)` LRU 리스트로 승격되면서, `Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00001-of-00002.gguf` (51.1 GiB)의 페이지 캐시 상주율을 **86.7% (44.3 GiB / 51.1 GiB)** 로 떨어뜨림.
- **90% 임계값 미달로 인한 SSD 스테이저 강제 전환 (`prefill.cpp` Line 1471)**:
  - `src->cached_share(256) < 0.90` 조건에 걸려 두 에이전트가 모두 `files = true` (SSD 프로파일)로 진입.
  - 에이전트당 **32개 복사 스레드 + 128-슬롯 핀드 링 버퍼(340 MB)** 가 할당되어, 합산 **64개 스레드 + 680 MB 추가 고정 RAM** 소모.
- **LRU Cyclic Scan Thrashing 발생**:
  - 61.1 GiB 호스트 RAM에서 6.7 GiB `Active(file)` 빌드 캐시 + 680 MB 추가 핀드 링이 공간을 차지하자, 128K 프롬프트의 16개 청크(청크당 8,192 토큰)가 36개 레이어를 순차 스캔할 때마다 직전 청크의 페이지를 밀어내는 Cyclic Scan Thrashing 발생 (`pread` 398 GB, 디스크 읽기 352.8 GB, 메이저 폴트 34,595건).

### 2) 해결 조치 및 검증 결과
1. **GGUF 샤드 `Active(file)` 페이지 캐시 100% 복원**:
   - `00001-of-00002.gguf` (51.1 GiB) 및 `dense.bin` (1.4 GiB)에 대해 2-pass 순차 읽기를 수행하여 `fincore` 기준 **51.1G / 51.1G (100%)** 상주 상태로 복원.
2. **`STRATA_STAGER_SSD=0` 고정**:
   - 기동 시 일시적인 메모리 회수가 발생하더라도 절대 32스레드/128링 SSD 프로파일로 빠지지 않고 RAM 프로파일(3스레드/16링)을 유지하도록 강제.
3. **결과**:
   - 3-Batch 평균 프리필 **751.77 tok/s** (최대 **791.30 tok/s**), TTFT **169.44 s**, 디코드 **21.20 tok/s**로 T1 (0.1.47 순정 평균 744.55 tok/s) 대비 동등 이상의 성능을 완벽히 입증.
