# Stage 5 T6 — Upstream 0.1.50 (Strata v0.2.6) Benchmark & Gate Diagnostic Summary

- **Date**: 2026-10-27
- **Target**: Lenovo ThinkStation P520, Xeon W-2135 (6C/12T), 64 GB DDR4 ECC, 2 × Tesla V100 16 GB (150 W caps)
- **Model**: Qwen3.8-Flash-Next GSQ-RCO IQ3_S (Mounted from NVMe1 `/srv/models/strata-iq3s`)
- **Engine Candidate**: Upstream Strata `v0.2.6` (reported engine `0.1.51` / `0.1.50`), commit `4b9e05a2a806a3fe24f7b2560d98626c37dade35`, CUDA 12.9.1, sm_70
- **Workload**: `V100-PERFORMANCE-C2-128K-v1` (SHA256: `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`)
- **Result Status**: ⚠️ **SEVERE REGRESSION / GATE STOP TRIGGERED**

---

## 1. T6 Run 1 Results vs T1 Baseline & T4 Champion

| Metric | T6 Run 1 (Upstream 0.1.50) | T1 Baseline (0.1.47 Mean) | T4 Champion (SIMT+WMMA Mean) | vs T1 Baseline | vs T4 Champion |
|---|---|---|---|---|---|
| **Agent A Prefill (tok/s)** | 247.1 | 738.07 | 881.90 | **-66.5%** | **-72.0%** |
| **Agent B Prefill (tok/s)** | 247.1 | 751.03 | 892.83 | **-67.1%** | **-72.3%** |
| **Symmetric Mean Prefill** | **247.10 tok/s** | **744.55 tok/s** | **887.37 tok/s** | **-66.8% 심각한 성능 저하 ⚠️** | **-72.2% 급락 ⚠️** |
| **Agent A TTFT (s)** | 514.13 | 172.54 | 144.24 | **+341.6s (+198%)** | **+369.9s (+256%)** |
| **Agent B TTFT (s)** | 514.13 | 169.66 | 142.48 | **+344.5s (+203%)** | **+371.7s (+261%)** |
| **Symmetric Mean TTFT (s)** | **514.13 s (8.57분)** | **171.10 s (2.85분)** | **143.36 s (2.39분)** | **+343.0s 폭증 ⚠️** | **+370.8s 폭증 ⚠️** |
| **Agent A Decode (tok/s)** | 19.0 | 21.07 | 21.17 | -2.07 tok/s (-9.8%) | -2.17 tok/s (-10.2%) |
| **Agent B Decode (tok/s)** | 18.7 | 21.83 | 21.23 | -3.13 tok/s (-14.3%) | -2.53 tok/s (-11.9%) |
| **Symmetric Mean Decode** | **18.85 tok/s** | **21.45 tok/s** | **21.20 tok/s** | **-12.1% 감속** | **-11.1% 감속** |
| **Batch Wall Time (s)** | **601.58 s (10.03분)** | **254.48 s (4.24분)** | **228.92 s (3.82분)** | **+347.1s 폭증 ⚠️** | **+372.7s 폭증 ⚠️** |
| **Decode Overlap (s)** | 76.58 s | 74.82 s | 62.70 s | 대칭 진행 | 대칭 진행 |
| **Mechanical Contract** | PASS | PASS | PASS | 기계적 통과 | 기계적 통과 |

---

## 2. Root Cause Telemetry & Diagnostics

T6 실행 중 호스트 커널 텔레메트리(`telemetry-vmstat.log`, `telemetry-pidstat.log`, `vmstat-proc-*`) 정밀 분석 결과:

### 1) 극심한 스왑 쓰래싱 (Swap Thrashing) 및 메이저 페이지 폴트 폭풍
- **메이저 페이지 폴트 (`pgmajfault`)**: 실행 전후 **34,595건** 폭증 (T1~T4는 <20건에 불과).
- **스왑 아웃 (`pswpout`)**: **567,540 pages (2.27 GB)** 가 스왑 영역으로 방출됨.
- **물리 디스크 I/O (`pgpgin`)**: **352.8 GB** 물리 디스크 읽기 발생.
- **연속 디스크 읽기 속도**: 500초 동안 **800~850 MB/s** 디스크 읽기 지속.
- **컨텍스트 스위치 (`cs`)**: 초당 **400,000 ~ 625,000 회** 발생 (T4는 18,000~25,000 회).
- **I/O 대기 블록 프로세스 (`b`)**: **32 ~ 53개**의 프로세스가 지속적으로 커널 I/O 슬립 상태에 고착.

### 2) Upstream 0.1.50 (v0.2.6) 내부 메커니즘 변경 원인 분석
1. **대화 캐시 기본 활성화 (`conversation_cache_mib: 8192`)**:
   - 0.1.47에서는 기본값이 `0`이었으나, 0.1.50/0.1.51에서는 에이전트당 `8,192 MiB` (8 GiB)가 자동 할당됨.
   - 2개 에이전트가 동시에 실행되며 **16 GiB의 호스트 RAM**이 캐시로 선점됨.
2. **SSD 스테이저 프로파일 강제 진입 (`STRATA_STAGER_SSD`)**:
   - `prefill.cpp`: 캐시 적중률이 90% 미만이면(`src->cached_share < 0.90`), 자동으로 `files = true`로 전환되어 SSD 프로파일 작동.
   - SSD 프로파일 진입 시 에이전트당 **32개의 호스트 복사 스레드**와 **128 depth 링 버퍼**를 생성.
   - 2개 에이전트 합산 **64개 복사 스레드**가 6C/12T CPU(각 컨테이너당 3코어 할당) 및 NVMe1에 동시 경합하여 심각한 I/O 락 및 컨텍스트 스위칭 유발.
3. **페이지 캐시 고갈 및 이탈**:
   - 80 GB 모델 샤드 크기 대비 64 GB 호스트 RAM 환경에서, 16 GB 대화 캐시 선점 + 64개 스레드의 비동기 프리페치가 합쳐져 리눅스 페이지 캐시가 완전히 고갈되고 스왑(2.27 GB) 쓰래싱으로 붕괴함.

---

## 3. Gate Rule 트리거 및 조치

- **규정 준수**: `docs/STAGE5_PLAN.md` Section 4, Item 8:
  > *"Stop/gate: on major fault storms, swap thrashing, anomalous host instability, failing health/overlap, OOM or unexpectedly severe slowdowns, stop only Stage 5 candidate services, preserve the diagnostic logs, and review before retrying."*
- **조치 내역**:
  - T6 Run 1 완료 즉시 2개 Stage 5 컨테이너(`strata-s5-agent-a`, `strata-s5-agent-b`)를 안전하게 정지 및 제거.
  - 호스트 GPU 0 / GPU 1 모두 VRAM 0 MiB 사용, 유휴 상태 27W 확인.
  - 호스트 사용 가능 메모리 59 GiB로 정상 회복, 스왑 사용량 62 MiB로 안정화.
  - 역사적 상용 컨테이너(`strata-jmn-iq2xs-agent-a/b`) 및 SSH 터널(18080/18081) 무결성 유지.

---

## 4. 최종 판정

- **Upstream 0.1.50 (Strata v0.2.6) 순정 기본값**: **FAIL / 심각한 회귀**
  - 순정 설정 상태의 upstream 0.1.50은 64 GB RAM 환경의 듀얼 128K 에이전트 구성에 부적합하며, 심각한 메모리 경합과 쓰래싱을 유발함.
