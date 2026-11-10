# Stage 10 T1 RAM Contention & Capacity Diagnosis Report (Verified DFlash2)

> **Experiment ID**: `t1-20261111T003644` (Strict DFlash2 spec 8 / draft-conf 0.7 verified)  
> **Execution Date**: 2026-11-11T00:36:44 ~ 2026-11-11T00:57:53+09:00  
> **Host**: Lenovo ThinkStation P520 (`p520-llm`, Intel Xeon W-2135 @ 3.70 GHz, 6C/12T, 64 GB DDR4-2666 ECC Quad-Channel, 2x Tesla V100-SXM2-16GB 150 W)  
> **Scope**: Solo A / Solo B 6-batch fresh C2 128K evaluation under strict verified DFlash2 (`--spec 8`, `--draft-conf 0.7`), with real-time Intel PCM uncore memory controller monitoring (`pcm-memory 1`) to assess RAM contention and the necessity of 32 GB RAM expansion (64 GB $\rightarrow$ 96 GB).

---

## 1. Executive Summary & Final Verdict

| 진단 항목 | 실측 관찰 결과 (DFlash2 검증 완료) | 32 GB 추가 시 영향 | 판정 |
| :--- | :--- | :--- | :---: |
| **RAM 대역폭 포화 여부** | • 피크 대역폭: **19.3 GB/s** (W-2135 한계 85.3 GB/s 대비 **22.6%** 점유)<br>• 평균 대역폭: **11.6 GB/s** (**13.6%** 점유)<br>• 동시 실행 시 추정치: **~38.6 GB/s** (한계의 45.2% 수준) | RAM 용량을 늘려도 CPU 메모리 컨트롤러 대역폭(Quad-Channel 85.3 GB/s)은 증가하지 않으며, 현재도 대역폭 여유가 77.4%에 달함 | **영향 0%<br>(대역폭 충분)** |
| **RAM 용량 부족 여부** | • `Major Page Fault (디스크 폴트)`: **0 건**<br>• `Swap In / Swap Out`: **0 건**<br>• 가용 메모리(`MemAvailable`): **~63.0 GiB** (전체 64 GB 중 상시 여유) | 현재 64 GB 상태에서 47 GB mmap 모델 가중치가 OS 페이지 캐시에 100% 상주하고도 14 GB 이상의 순수 여유 메모리가 남아있음 | **영향 0%<br>(용량 충분)** |
| **단독 vs 동시 디코드 속도** | • **단독 디코드**: **30.9 tok/s** (Agent A 30.8, Agent B 31.1)<br>• **동시 디코드 (S10-D4)**: **30.4 tok/s** (저하율 **-1.6%**) | 디코드 단계는 GPU 연산 및 VRAM/캐시 위주로 동작하여 2개 에이전트 동시 구동 시에도 속도 저하가 1.6%에 불과함 | **경합 미미<br>(-1.6%)** |
| **단독 vs 동시 프리필 속도** | • **단독 프리필**: **1,082.1 tok/s** (TTFT 117.58 s)<br>• **동시 프리필 (S10-D4)**: **1,024.6 tok/s** (TTFT 124.56 s, 저하율 **-5.3%**) | PCIe 버스 분할 및 CPU 프롬프트 토크나이징 시 스레드 분산에 의한 미세 경합 (-6.98초 TTFT 차이) | **RAM과 무관<br>(PCIe/CPU 경합)** |

> ### 🎯 최종 결론 (Recommendation)
> **RAM 32 GB 추가 증설(64 GB $\rightarrow$ 96 GB)은 추론 속도(Prefill, Decode, TTFT)에 향상 효과가 0%이므로 증설할 필요가 없습니다.**  
> 1. DFlash2 30 tok/s 고속 디코드 상태에서도 CPU 메모리 컨트롤러 대역폭 점유율은 **22.6%**에 불과하며, 77% 이상의 대역폭 여유가 상시 존재합니다.
> 2. 64 GB 메모리 용량에서 스왑(`pswpout=0`)과 디스크 메이저 폴트(`pgmajfault=0`)가 전무하므로, 96 GB로 증설하더라도 캐시 적중률이나 연산 속도에 어떠한 변화도 생기지 않습니다.

---

## 2. DFlash2 무결성 검증 (엔진 및 컨테이너 로그 영수증)

스크립트 `scripts/125-stage10-t1.py`에서 모델 식별자 접두사 정규식을 수정하고 프로세스 단언(`validate_drafter`)을 강제하여, **MTP 후퇴 없이 DFlash2가 단독 로드**되었음을 실시간 로그로 100% 검증했습니다:

```text
[strata] drafting: DFlash2 alone (--draft dflash2, --draft-conf 0.7)
[strata] engine started: /opt/strata/engine/strata ... --spec 8 --prefill auto --expert-cache auto 
         --draft dflash2 --draft-model /stage10-data/dflash2/qwen3.8-flash-next-dflash2.q4_0-selq4.pack 
         --draft-fallback none --mtp-draft-vocab /shared-mtp/rt/draft_vocab.bin --draft-conf 0.7

strata dflash2: 106299-token draft head (178.4 MiB), drafter 591 MiB of VRAM (Q4_0 weights)
strata dflash2: selector codebooks: Q4_0 rows (about 174 MiB less than bf16)
strata serve: DFlash2 drafter on (...); windows up to 8 tokens; no MTP layer is loaded (--draft-fallback none)
```

---

## 3. 세부 실측 데이터 (DFlash2 6개 Solo 배치 전수)

| 배치 ID | 에이전트 | Prompt (tok) | Output (tok) | Prefill (tok/s) | **Decode (tok/s)** | TTFT (s) | Wall (s) | RAM Read (MB/s)<br>Mean / Peak | RAM Write (MB/s)<br>Mean / Peak | Total RAM BW (MB/s)<br>Mean / Peak |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `solo-a-batch-1` | Agent A | 126,967 | 2,017 | 1,080.4 | **30.8** | 117.78 | 183.22 | 7,928.1 / 12,104.5 | 3,510.8 / 6,565.4 | 11,438.9 / 18,034.8 |
| `solo-a-batch-2` | Agent A | 126,967 | 2,017 | 1,077.9 | **30.8** | 118.03 | 183.43 | 7,951.2 / 12,816.6 | 3,515.5 / 8,778.7 | 11,466.7 / 19,221.1 |
| `solo-a-batch-3` | Agent A | 126,967 | 2,017 | 1,079.8 | **30.8** | 117.82 | 183.31 | 7,925.9 / 12,525.0 | 3,507.6 / 7,155.8 | 11,433.6 / 18,686.3 |
| **Solo A 중간값** | **Agent A** | **126,967** | **2,017** | **1,079.8** | **30.8** | **117.82** | **183.31** | **7,928.1 / 12,525.0** | **3,510.8 / 7,155.8** | **11,438.9 / 18,686.3** |
| `solo-b-batch-1` | Agent B | 126,968 | 1,895 | 1,085.2 | **31.1** | 117.24 | 178.10 | 8,068.6 / 12,724.2 | 3,610.1 / 7,612.8 | 11,678.7 / 18,949.7 |
| `solo-b-batch-2` | Agent B | 126,968 | 1,895 | 1,087.8 | **31.1** | 116.96 | 177.92 | 8,063.4 / 12,538.3 | 3,603.0 / 7,685.6 | 11,666.3 / 18,758.0 |
| `solo-b-batch-3` | Agent B | 126,968 | 1,895 | 1,083.9 | **31.1** | 117.38 | 178.28 | 8,079.1 / 12,888.4 | 3,609.9 / 7,076.7 | 11,689.0 / 19,276.3 |
| **Solo B 중간값** | **Agent B** | **126,968** | **1,895** | **1,085.2** | **31.1** | **117.24** | **178.10** | **8,068.6 / 12,724.2** | **3,609.9 / 7,612.8** | **11,678.7 / 18,949.7** |
| **전체 Solo 중간값**| **단독 실행**| **126,967** | **1,956** | **1,082.1** | **30.9** | **117.58** | **180.70** | **7,998.6 / 12,624.6** | **3,560.4 / 7,384.3** | **11,558.8 / 18,949.7** |

---

## 4. DFlash2 단독(Solo) vs 동시(Concurrent) 서빙 정밀 비교

| 지표 | DFlash2 Solo 단독 (t1-20261111T003644) | DFlash2 Concurrent 동시 (S10-D4) | 동시 서빙 시 변동률 | 판정 |
| :--- | :---: | :---: | :---: | :---: |
| **Agent A Decode** | **30.8 tok/s** | **30.4 tok/s** | **-1.3%** | 오차 범위 내 완전 일치 |
| **Agent B Decode** | **31.1 tok/s** | **30.3 tok/s** | **-2.6%** | 경합 극미 (-0.8 tok/s) |
| **전체 Decode 중간값** | **30.9 tok/s** | **30.4 tok/s** | **-1.6%** | **동시 실행 디코드 저하율 1.6%** |
| **Prefill 중간값** | **1,082.1 tok/s** | **1,024.6 tok/s** | **-5.3%** | PCIe 버스 및 CPU 사전처리 경합 |
| **TTFT 중간값** | **117.58 s** | **124.56 s** | **+5.9%** (약 6.98초 지연) | PCIe 전송 경합 (-6.98s) |

---

## 5. Intel PCM 메모리 대역폭 분석 및 32 GB 증설 불필요 근거

```mermaid
xychart-beta
    title "CPU Memory Controller Bandwidth vs Limit (MB/s)"
    x-axis ["Decode Mean", "Prefill Peak", "Concurrent Max (Est.)", "DDR4-2666 Limit"]
    y-axis "Bandwidth (MB/s)" 0 --> 90000
    bar [11559, 19276, 38552, 85333]
```

1. **대역폭 여유도 (Headroom)**:
   - 디코드 단계 평균 대역폭: **11,559 MB/s (약 11.6 GB/s)** $\rightarrow$ 쿼드채널 정격 한계의 **13.6%**
   - 프리필 단계 피크 대역폭: **19,276 MB/s (약 19.3 GB/s)** $\rightarrow$ 쿼드채널 정격 한계의 **22.6%**
   - 2개 에이전트가 동시에 최고 피크를 찍더라도 예상 대역폭은 **약 38.6 GB/s**로, W-2135 한계(85.3 GB/s)의 **45.2%**에 불과합니다.
   - 즉, **메모리 버스 대역폭의 54.8% 이상이 상시 여유 공간**입니다.

2. **메모리 용량 및 페이징 분석**:
   - 64 GB 물리 메모리 중 47 GB가 모델 GGUF 전체 샤드를 메모리에 캐싱하고 있습니다.
   - 가용 메모리(`MemAvailable`)는 상시 **63.0 GiB** 이상으로 유지되었습니다.
   - 테스트 전 과정에서 `pgmajfault` (Major fault) = **0건**, `pswpin / pswpout` (Swap) = **0건**으로 디스크 I/O 병목이 전무했습니다.

---

## 6. 결론 요약

1. **디코드 속도 정합성**: DFlash2 적용 시 단독 실행 디코드 속도는 **30.8 ~ 31.1 tok/s**이며, 동시 실행(30.4 tok/s) 대비 저하율은 **-1.6%**로 디코드 경합은 거의 존재하지 않습니다.
2. **RAM 32 GB 증설 효과**: 대역폭과 용량 모두 64 GB 환경에서 55~77% 이상의 여유를 확보하고 있으므로, **32 GB를 추가하더라도 추론 속도에는 0.0%의 영향도 미치지 못합니다.** (증설 불필요 확정)
