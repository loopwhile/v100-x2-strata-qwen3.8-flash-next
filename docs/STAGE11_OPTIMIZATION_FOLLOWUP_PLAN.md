# Stage 11 후속 성능 최적화 계획 — IQ3_XXS / Dual V100 / 128K C2 / Prefill 1200 · Decode 40

> **상태:** PLAN ONLY — GitHub 문서 커밋 승인, GPU 테스트·서빙 변경·소스 수정 미실행
> **대상:** Qwen3.8-Flash-Next GSQ-RCO **IQ3_XXS**, V100-SXM2 16GB ×2 **독립 에이전트**
> **목표:** Agent A와 B 각각, **동시 128K C2**에서 **Prefill ≥1200 tok/s AND Decode ≥40 tok/s**
> **기준 GitHub 커밋:** `a9b3d6eb4a0933142b6f432c11e55e378fb8a6c2` (2026-11-19 확인)
> **ID 정책:** 기존 `S11-D4`(IQ3_S) 및 Stage 2 ~ 11 완료 기록은 **CLOSED**. 본 문서는 종료된 Stage 11을 재개하는 실행 승인서가 아니다. 신규 후속 연구는 `S11X-*` ID의 **별도 승인된 신규 캠페인**으로만 정의한다. 필요하면 실제 착수 시 공식 Stage 12로 명명하되 기존 ID를 재사용하지 않는다.

## 1. 변경 의사결정: IQ3_S → IQ3_XXS

- 기존 후속 계획의 최적화 대상이었던 **IQ3_S는 제외**한다. 그 실험 기록은 삭제하거나 변경하지 않는다.
- **IQ3_XXS S10-D4**를 현재 성능 기준선 및 운영 레시피로 고정한다. 이미 확정된 3배치 C2 결과를 다시 측정해서 기준값으로 바꾸지 않는다.
- **더 나은 모델 품질보다 기존 IQ3_XXS 품질을 유지하면서 실제 처리속도를 높이는 것이 이번 목표**다. IQ2_XS·IQ3_S 등의 다른 양자화로 목표를 채웠다고 판정하지 않는다.
- 2개의 GPU를 하나의 추론에 묶는 layer/tensor split이나 NVLink 멀티 GPU 결과로 **독립 A/B 2개** 목표를 대체하지 않는다.

## 2. 실측 기준선과 목표 격차

| 항목 | S10-D4 Agent A | S10-D4 Agent B | 목표(각각) | 현재 대비 필요 변화 |
|---|---:|---:|---:|---:|
| Prefill (tok/s) ↑ | 1025.1 | 1027.8 | **1200** | **A +17.1% / B +16.8%** |
| Decode (tok/s) ↑ | 30.4 | 30.3 | **40** | **A +31.6% / B +32.0%** |
| TTFT (s) ↓ | 124.08 | 123.79 | 참고: 110초 내외 | Prefill 1200일 때 126,967/1200 ≈105.8초가 **순수 처리시간**; 실제 TTFT 별도 |
| C2 검증 | 3/3 PASS | 3/3 PASS | ≥3 fresh-process 유효 배치 | cold 포함, overlap·출력 검사 |

**실측으로 확인된 출발점**

1. **S10-D4**: 0.1.59 + stock DFlash2, `--spec 8 --draft-conf 0.7 --prefill auto`; 양쪽 Decode 중앙값 30.4/30.3. B 첫 배치는 28.2이므로 모든 배치에서 30을 넘긴 것은 아님.
2. **S10-P1**: `STRATA_PF_HC_REGION=1` 단독 변화는 Prefill 1036.5/1044.0, TTFT 122.74/121.88을 보였으나 **spec6 기준**이며 B Decode는 28.4. **D4(spec8)+P1 결합은 미측정**이므로 개선이 더해진다고 가정하지 않는다.
3. **S10-P0**: 계측용 `spec6` 진단에서 윈도당 CPU expert `50.64ms`, adaptive join `9.66ms`, drafter `2.85ms`, 전체 `90.48ms`. GPU waitCPU와 CPU 시간은 겹치므로 중복 합산 금지. **spec8 D4에 그대로 귀속 금지**.
4. **S10-T1**: IQ3_XXS 단독 Prefill A/B `1079.8/1085.2`, Decode `30.8/31.1`; 동시 D4와 비교 시 Prefill 약 5% 차이. 단독 성능도 1200에 못 미치므로 **경합 제거만으로 목표 달성 불가**. 메모리 대역폭 단독 피크 약 19.3GB/s, 평균 약 11.6GB/s; 동시 대역폭은 추정치이며 실측 포화 판정으로 사용하지 않음.
5. **S11-D4 (IQ3_S)**: 893.8/898.0 Prefill, 23.3/23.4 Decode. **비교용 아카이브**일 뿐 이번 후보가 아니다.
6. **S10-P3**: `--prefill auto:16384`가 실제 시스템 전원 차단을 유발. **영구 제외**, 전력/클럭/PSU 설정 변경 금지.

**판단:** 1200/40은 공개 문서상 IQ3_XXS 동시 128K로 아직 검증되지 않았다. 실측, 분석적 목표, 외부 GPU 사례를 분리 기록한다. 목표 속도는 성공 판정 기준이지 성능 예측이 아니다.

## 3. 고정된 하드웨어·소프트웨어·측정 계약

- Lenovo P520, Xeon W-2135 (6C/12T), **RAM 64GB 유지**, GPU0/A cpuset `0-2,6-8`, GPU1/B `3-5,9-11`. 두 GPU는 완전히 독립적으로 한 모델씩 서빙한다.
- GPU 각 **150W configured power cap**, 원래 `135–1245MHz` 정책을 유지. GPU 센서 순간 피크가 150W를 넘더라도 cap 자체가 바뀐 것은 아니다. 전원 이상 발생 시 즉시 중단, 자동 재시도 금지.
- **동일한 IQ3_XXS GGUF/Native pack/tokenizer/expert-profile**, stock DFlash2 selector pack SHA `4a42b98220ea7880664002c8edda1563aecbae754b762a2e2f31b2b91ee93ecd`, DFlash2 fallback `none`, 131072 context, INT8 KV, resident 32768, `--mmap-experts`, `--expert-cache auto`, 안전한 `--prefill auto`.
- 출발 엔진 0.1.59 source `712fec6b4297c9cfd32ab43daaa2979a9aa01edf`; 이미지 ID `sha256:dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d` 고정. 새 소스/바이너리는 **후보별 별도 이미지**로 분리.
- 출발 환경변수 `STRATA_SELECT_SIMT=1`, `STRATA_SM70_TABLE=1`, `STRATA_PF_WMMA=1`. 운영 D4에는 `ADAPT_LAG/NOWAIT` 없음. `STRATA_ROUTE_TAIL_SKIP=7` 등의 기본값은 명시·기록하고 별도 품질 게이트 없이 바꾸지 않음.
- frozen C2 workload SHA `e413acced27c1991d76ce2b4f45853b9676e5b9000ef8503ca`; A/B 프롬프트 126,967/126,968토큰, cache-prefix 재사용 0, A/B 각각 출력 ≥1024, finish_reason `stop`, 중복된 decode 시간, post-health, 세션/프로세스의 신선도 확인. OS **파일 페이지 캐시의 cold/warm 여부는 별도 표기**.
- 운영 컨테이너 `p520-llm-a/b`, 포트 8080/8081, ThinkPad 터널 18080/18081, 역사적 이미지/모델/컨테이너/증빙을 보존. 실험 실행 승인 전에 P520 실제 serving/GPU 점유 상태를 재확인.

## 4. 실험 레지스터와 우선순위

각 후보는 한 번에 **하나의 검증 가능한 변경**만 적용한다. 조합은 독립 검증 이후 별도 승인한다.

| ID | 우선 | 실험/질문 | 실험 판단 기준 |
|---|---|---|---|
| **S11X-A0** | **0 필수** | **읽기 전용 소스 감사:** 최신 upstream Strata 및 V100 포크와 pinned 0.1.59 비교. IQ3_XXS에서 실제 적용되는 CPU expert, Cache, Volta prefill, DFlash2 커널, CUDA dispatch 차이만 선별 | 정확한 소스·sm_70 가드·품질/빌드/VRAM 영향 확인. layer-split 전용·sm_80+ 전용 후보 제외 |
| **S11X-P0** | **0 필수** | **비채점 D4(spec8) 계측:** CPU expert miss·time, GPU wait, per-window accepted tokens, verify, draft, adaptive join, QSA/GDN, Prefill kernel/transfer, page-cache/OS I/O를 구분 | 프로파일러 자체로 속도 감소 가능. P0 tok/s는 정식 점수에서 제외 |
| **S11X-C0** | **1 저비용** | D4에 `STRATA_PF_HC_REGION=1`만 추가. Stage10 P1은 spec6이므로 spec8에서 효과 있는지 확인 | D4 대비 Prefill/TTFT 개선 + Decode 손실 여부. 성능 개선 약 1%에 그치면 주력 후보로 승격하지 않음 |
| **S11X-D1** | **1 고효과 후보** | **CPU Expert 경로:** 실제 AVX2 코드·CPU miss·quantized GEMV, thread scheduling, CPU/GPU overlap 분석 후 적용 가능한 커널/스케줄링 수정 중 단일 변경 | per-window CPU expert 지연 및 Decode 동시 개선 재현. W-2135의 AVX-512 지원만으로 가속 가능하다고 가정하지 않음 |
| **S11X-D2** | **1 고효과 후보** | **Expert cache/profile:** 실제 코딩 워크로드와 홀드아웃을 분리하고 GPU hot expert 배치·adaptive eviction·CPU fallback을 최적화 | cache hit↑, CPU stall↓, 품질 유지. 캐시 슬롯 무작정 증대·VRAM OOM 유발 금지 |
| **S11X-P1** | **1 고효과 후보** | **Volta Prefill 커널:** IQ3_XXS에서 기존 WMMA/SIMT와 새로운 WMMA2/W2·QSA/GDN·scratch path의 실제 dispatch, 동기화, 텐서 코어 효율 비교 | 동일 8192 auto chunk에서 128K prompt time과 TTFT가 개선되는지 검증, 정확도/전력 안정성 확인 |
| **S11X-P2** | 2 조건부 | **동시 Prefill 경합:** CPU affinity·메모리 대역폭·PCIe·GPU utilization과 OS 파일 읽기를 단계별로 계측. 기존 T1 solo 대비 누적 손실의 원인 분리 | 단독 성능 자체가 1200 미만이므로 경합 제거만으로 목표를 채운다고 가정 금지. 기존 RAM 증설 가설 반복 금지 |
| **S11X-D3** | 2 조건부 | **DFlash2 확인:** tuned draft pack 유효성/해시/라이선스/토큰·검증 비용 분석, source-validated spec·conf 변형. 기본 D4와 1개 옵션만 비교 | effective tok/window 및 decode 상승, verify penalty·VRAM·출력 품질 저하 없음. 다른 GPU의 속도향상값 전용 금지 |
| **S11X-C1** | 최종 조건부 | **최종 후보 조합:** 독립적인 안정적 개선이 확인된 Decode/Prefill 후보만 결합 | **Agent A와 B 각각 Prefill ≥1200 + Decode ≥40**, 같은 128K 동시 C2 3배치 중앙값, 전력·품질·안정성 통과 |

### 이미 부정적·불필요하다고 확인된 접근

- `--prefill auto:16384`: **전원 차단으로 재시도 금지**.
- `--spec 8 + ADAPT_LAG=2 + NOWAIT=1`: S10-C1에서 Decode 27.5/28.9로 후퇴.
- `--draft-conf 0.5`/`0.6`: S10-D2/D3에서 0.7보다 분명한 이득 없음.
- `STRATA_SIDE_MIXER=2`: S10-K3에서 유의미한 개선 없음.
- `--resident-budget-gib 2`/`--adapt-async 1` 계열: S8에서 Prefill 약 820으로 크게 악화.
- `--pool-workers 3`, `--expert-cache-per-layer`, `--kv-resident 40960` 재시도는 새로운 병목 근거가 없는 한 제외.
- **GPU 2장 layer split**의 70 ~ 125 tok/s 수치는 한 요청 속도이므로 본 목표를 증명하지 못한다.

## 5. 단계별 의사결정과 측정 예산

### Gate A — 소스 및 병목 확인 (GPU 성능평가 전)

- `S11X-A0`: 최신 소스의 구체적인 커밋 SHA를 읽기 전용으로 확정하고, IQ3_XXS + sm_70에서 실행 가능한 경로만 후보로 뽑는다.
- `S11X-P0`: 새 범위 승인 후, D4 기준 비채점 진단 **1회**. spec8 전용 CPU expert/verify 분해와 Prefill 연산·대기·I/O 단계별 수치 확보.
- **중단 조건:** 계측된 병목과 수정 가능한 코드 경로가 전혀 연결되지 않으면 확정되지 않은 플래그의 무차별 A/B 시험을 진행하지 않는다.

### Gate B — 저비용 후보 선별

- `S11X-C0` D4+PF_HC_REGION 먼저 1회 선별. 더 중요한 D1/D2/P1은 **소스 검증 및 별도 유닛·정합성 테스트 통과 후** 1회 선별.
- 성능 지표와 실제 커널 활성화 로그를 모두 확보한다. 매우 작은 이득은 run-to-run 분산과 cold/warm 차이로 해석한다.
- 1회 선별 결과가 유망하면 **3회 유효 동시 128K C2** 확인. 후보별 사용 예산은 평가 후 사용자가 별도로 승인한다.

### Gate C — 구조적 개선 선별

- D1 CPU experts / D2 cache / P1 Prefill 중 **측정으로 가장 큰 시간을 절약할 수 있는** 경로부터 진행한다.
- 성능 향상값이 다른 단계에서 나왔어도 **동일 엔진/동일 자산/동일 GPU 정책과 동등한 캐시 조건**에서 재측정한 것인지 따로 표시한다.
- DFlash2 tuned pack은 CPU expert가 주병목인 상황에서는 우선순위를 낮춘다. verify-time 병목 감소 또는 유효 수락토큰 증가의 실증이 있으면 D3로 진행한다.

### Gate D — 최종 확인

- `S11X-C1`: 한 후보가 좋아도 조합이 상쇄될 수 있으므로 별도 3배치 동시 C2 및 의미적 품질 검증.
- 결과는 **① 모든 배치 통과 여부 ② 3회 중앙값 통과 여부 ③ cold 배치 성능 ④ warm 배치 성능 ⑤ 실제 코딩 업무 품질**을 따로 보고한다.
- 목표 미달이라도 검증된 개선폭과 새 병목을 기록하고 원인 없는 반복 실행을 중단한다.

## 6. 테스트에서 반드시 보존할 증빙

각 배치마다: exact engine version/source/image/binary SHA, DFlash2 head·model SHA 및 fallback none 검증, effective CLI/env, C2 매니페스트, Prompt/Output 수, TTFT, Prefill/Decode, wall time, 실제 decode overlap, tokens/window, acceptance, expert hit 및 GPU cache slots, CPU expert time, GPU wait, Prefill kernel time, GPU 온도/전력 평균 및 피크, 150W configured cap, CPU/RAM/Swap/Major Fault, NVMe 실제 읽기량, OS page-cache 상태, 사전·사후 health.

정합성: fixed long-context retrieval, 코딩 태스크, JSON/tool-call 실행, 출력 의미 비교; 특히 `STRATA_ROUTE_TAIL_SKIP` 등 출력에 영향을 줄 수 있는 로직 변경은 품질 검증 필수. **C2 기계적 PASS ≠ 의미적 품질 PASS**.

## 7. 보고서의 상태와 실행 권한

- GitHub `main`에 있는 `docs/STAGE11_PLAN.md`는 **IQ3_S의 완료된 기존 Stage 11 기록**이므로 변경하거나 덮어쓰지 않는다.
- 이 문서는 **IQ3_XXS의 신규 후속 계획**, 운영 레시피 S10-D4는 그대로 보존.
- **본 계획서의 GitHub 문서 커밋만 승인됨.** P520 GPU 실행·Docker 빌드·컨테이너 재시작·GPU 클럭/전력 변경은 별도 실행 승인 전까지 수행하지 않는다.
- 사용자의 별도 실행 승인 시 최초 범위는 A0(소스 감사)과 P0(비채점 진단)만으로 제한하고, 새 ID/로그 경로/rollback/호스트 preflight를 확정한다.

## 근거 경로 (기존 저장소)

- `docs/STAGE10_PROGRESS.md`; `artifacts/stage10-results-20261110/d4-20261110T225518/report.md`
- `artifacts/stage10-results-20261110/p1-20261110T214105/report.md`; `docs/STAGE10_T1_RAM_REPORT.md`
- `docs/STAGE9_SOURCE_AUDIT.md`; `docs/STAGE8_CONTINUATION_REVIEW.md`
- `docs/STAGE11_PLAN.md`; `artifacts/stage11-results-20261119/summary.md` (IQ3_S 완료 참고)
- `bench/workloads/v100-performance-v1.json`; `bench/c2_v100_contract.py`