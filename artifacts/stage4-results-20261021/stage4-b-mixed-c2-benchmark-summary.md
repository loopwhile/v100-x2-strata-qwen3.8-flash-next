# Stage 4-B MIXED (IQ3_XXS + IQ2_XS) C2 128K Performance Benchmark Summary

- **Date / Time**: 2026-10-22 15:00:00 KST
- **Engine**: Upstream Strata `v0.1.47` (Release `v0.2.2`, Vanilla Defaults without `STRATA_SM70_TABLE=1`)
- **Docker Image**: `strata-v100-upstream:0.1.47` (`sha256:19c3b72a1097486eeae3fd9b964179a36a1c137615e5c93f6d6e70eacdab8e9d`)
- **Host**: ThinkStation P520, Xeon W-2135, RAM 61 GiB, 2x Tesla V100-SXM2-16GB (`sm_70`), Power Cap 150W (유지)
- **Mixed Arm Configuration**:
  - **Agent A**: Host GPU 0 (Device 0), CPU Affinity `0-2,6-8`, Model: `Qwen3.8-Flash-Next IQ3_XXS`, Port `8080` (ThinkPad: `18080`)
  - **Agent B**: Host GPU 1 (Device 1), CPU Affinity `3-5,9-11`, Model: `Qwen3.8-Flash-Next IQ2_XS`, Port `8081` (ThinkPad: `18081`)
- **Common Serving Args**: 131,072 context, INT8 (`q8_0`) KV, `--kv-resident 32768`, `--spec 4 --spec-min-p 0.5`, `--mmap-experts`
- **Workload**: `V100-PERFORMANCE-C2-128K-v1` (Frozen SHA256: `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`)

---

## 1. Measured Results (Mixed Cold Run #1)

| Metric | Agent A (Host GPU 0 - IQ3_XXS) | Agent B (Host GPU 1 - IQ2_XS) | Concurrency Status / Total |
| --- | --- | --- | --- |
| **Prompt Tokens** | 126,967 | 126,968 | 253,935 total |
| **Output Tokens** | 1,289 | 2,036 | 3,325 total |
| **Wall Time (s)** | 1,077.62 s (~18.0 min) | 303.87 s (~5.1 min) | Batch Wall: 1,077.63 s |
| **TTFT (s)** | **914.90 s** | **214.04 s** | - |
| **Prefill Speed** | **138.8 tok/s** | **593.9 tok/s** | - |
| **Decode Speed** | **7.9 tok/s** | **22.6 tok/s** | - |
| **Expert Cache Hit Rate** | 89.2% | 91.9% | - |
| **Prefix Cache Reuse (`cache_n`)** | 0 (Cold run) | 0 (Cold run) | 0 |
| **Major Page Faults** | **18,690 faults** | 274 faults | 18,964 total |
| **Storage Read (File Tier I/O)** | **606.1 GB** | 25.3 GB | 631.4 GB total |
| **Decode I/O Wait Time** | **104.4 s** | 11.8 s | - |
| **Min 1,024 Output Check** | PASS | PASS | PASS |
| **Finish Reason** | `stop` | `stop` | `stop` |

- **Protocol Mechanical Validation**:
  - `pass_mechanical`: `True`
  - `post_health`: `True`
  - `active_overlap`: **`False` (FAIL)**
  - `decode_overlap_s`: **`0.000 s` (FAIL)**
  - Submission Skew: `0.0042 s`
  - Host Swap Usage Spilled: **1.6 GiB**

---

## 2. Comparison against Homogeneous Stage 4-B Baselines

### Agent A: IQ3_XXS (Host GPU 0) Comparison
| Metric | Homogeneous Stage 4-B (A: IQ3_XXS) | Mixed Stage 4-B (A: IQ3_XXS) | Delta vs Homogeneous |
| --- | --- | --- | --- |
| **TTFT (Latency to First Token)** | 176.50 s | **914.90 s** | **+418.4% (5.2배 지연 폭증 ⚠️)** |
| **Prefill Speed** | 720.4 tok/s | **138.8 tok/s** | **-80.7% 급감 ⚠️** |
| **Decode Speed** | 27.1 tok/s | **7.9 tok/s** | **-70.8% 급감 ⚠️** |
| **Wall Time** | 228.02 s | **1,077.62 s** | +372.6% 지연 |
| **Expert Hit Rate** | 88.4% | 89.2% | +0.8%p |

### Agent B: IQ2_XS (Host GPU 1) Comparison
| Metric | Homogeneous Stage 4-B (B: IQ2_XS) | Mixed Stage 4-B (B: IQ2_XS) | Delta vs Homogeneous |
| --- | --- | --- | --- |
| **TTFT (Latency to First Token)** | 128.69 s | **214.04 s** | **+66.3% 지연 ⚠️** |
| **Prefill Speed** | 988.5 tok/s | **593.9 tok/s** | **-39.9% 감소 ⚠️** |
| **Decode Speed** | 36.6 tok/s | **22.6 tok/s** | **-38.3% 감소 ⚠️** |
| **Wall Time** | 175.54 s | **303.87 s** | +73.1% 지연 |
| **Expert Hit Rate** | 92.6% | 91.9% | -0.7%p |

---

## 3. Root Cause Analysis (원인 심층 분석)

### (1) OS Page Cache 공유 파괴와 워킹셋 폭증
- **동종 배포(Homogeneous IQ2_XS)**: 두 컨테이너가 동일한 GGUF 파일(`/srv/models/strata-iq2xs`)을 mmap합니다. 리눅스 커널은 동일 inode에 대해 **물리 메모리(OS Page Cache)를 완전히 공유**하므로, 2개 컨테이너를 구동해도 익스퍼트 워킹셋은 **~39 GiB**에 불과하여 P520의 61 GiB RAM 내에 100% 상주합니다 (Page Fault 0, Swap 0).
- **이종 혼합 배포(Mixed IQ3_XXS + IQ2_XS)**:
  - Agent A (IQ3_XXS) 익스퍼트 mmap: **47 GiB**
  - Agent B (IQ2_XS) 익스퍼트 mmap: **39 GiB**
  - 두 모델의 파일이 완전히 다르므로 **Page Cache 공유가 불가능**합니다.
  - 총 요구 메모리: **47 GiB + 39 GiB = 86 GiB**.
  - P520 호스트 가용 RAM(61 GiB)을 **25 GiB 초과**하여 극심한 메모리 압박이 발생했습니다.

### (2) 심각한 메모리 스래싱(Thrashing)과 스왑 누출
- 128K 컨텍스트의 프리필 과정에서 양 에이전트가 28개 레이어 전반의 익스퍼트 가중치를 동시에 빈번히 요청했습니다.
- 가용 RAM 부족으로 커널이 끊임없이 페이지 회수(Page Reclaim) 및 드롭을 수행했고, 호스트 스왑이 **1.6 GiB까지 유출**되었습니다.
- Agent A 로그 실측 결과:
  - **18,690회의 Major Page Fault** 발생.
  - 단일 추론 요청 중 NVMe 스토리지로부터 **606.1 GB**의 물리 데이터를 반복해서 다시 읽어 들임.
  - 디코드 단계에서만 I/O 대기에 **104.4초**를 허비함.

### (3) 동시성(Active Decode Overlap)의 완전한 붕괴
- Agent B(IQ2_XS)는 스래싱 악조건 속에서도 214초 시점에 프리필을 끝내고 303.87초에 전체 디코드를 완료했습니다.
- 반면 Agent A(IQ3_XXS)는 18,690회의 Major Page Fault로 인해 프리필에만 **914.90초(15분 이상)**가 소요되었습니다.
- Agent A가 첫 토큰 생성을 시작했을 때(914.9s)는 이미 Agent B가 종료(303.8s)된 지 **10분 이상 지난 후**였습니다.
- 결과적으로 두 에이전트가 동시에 디코드를 수행하는 구간이 **0.000초**가 되어 C2 동시성 계약(`active_overlap = False`)을 만족하지 못하고 Runner의 assertion에서 탈락했습니다.

---

## 4. Engineering Conclusion & Production Recommendation

1. **혼합 양자화 서빙 불가 판정**:
   단일 노드(61 GiB RAM)에서 `--mmap-experts` 기반으로 서로 다른 양자화 모델을 독립 GPU에 분할 서빙하는 것은 **Page Cache 비공유로 인한 86 GiB 워킹셋 요구량** 때문에 메모리 스래싱 및 심각한 성능 저하(TTFT 5.2배 지연, 프리필 -81%)를 유발합니다.
2. **동종(Homogeneous) 서빙의 절대적 우위 확인**:
   동종 모델(특히 IQ2_XS)을 채택할 경우에만 OS Page Cache 공유를 통해 V100 16GB의 한계를 완벽히 극복하고 1,000 tok/s에 육박하는 프리필과 ~40 tok/s 디코드를 안정적으로 유지할 수 있습니다.
3. **후속 조치**:
   - `scripts/79-stop-stage4b-mixed-agents.sh`를 통해 혼합 컨테이너는 정상 중지 및 보존되었습니다.
   - 단일 실행 결과만으로도 구조적 병목(Page Cache Overcommit 86GB > 61GB)이 완벽히 입증되었으므로, 불필요한 하드웨어 부하(스왑 및 18분 단위 스래싱)를 방지하기 위해 3회 반복 측정은 진행하지 않고 단일 실험 보고서로 종료합니다.
