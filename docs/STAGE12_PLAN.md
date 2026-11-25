# Stage 12 — 최신 Strata 기반 Dual V100 IQ3_XXS 성능 최적화 계획

> **상태: PLAN ONLY (2026-11-25 KST)** — 이 문서의 커밋은 실행 승인이 아니다.
> **운영 기준:** S11X-D2 / Strata 0.1.59 + 검증된 자체 패치.
> **신규 엔진:** 공식 v0.2.20 (0.1.66) 및 v0.2.21 (0.1.67).
> **목표:** 기존 IQ3_XXS 품질, 독립적인 두 에이전트, 동시 128K C2, 전력·안정성을 유지하며 Prefill과 Decode의 실제 최대 성능을 찾는다. 1200/50/60은 목표이지 성능 보장이나 상한이 아니다.
> **저장소 기준:** `7f500b32bf935a19707dc0ce64de22738b138543` (S11X-D2 운영 승격).

## 1. 확정된 기준선과 목표

기존 실측은 [Stage 11X summary](../artifacts/stage11x-results-20261119/summary.md), [S11X-D2 정식 receipt](../artifacts/stage11x-results-20261119/d2-20261119T003753/report.md), [운영 계약](P520_SERVING.md)을 참조한다. 완료된 실험 ID를 다시 사용하지 않는다.

| 레시피 | Prefill A/B (tok/s) | Decode A/B (tok/s) | TTFT A/B (s) | 비고 |
|---|---:|---:|---:|---|
| S10-D4 | 1025.1 / 1027.8 | 30.4 / 30.3 | 124.08 / 123.79 | 과거 운영, rollback 보존 |
| S11X-P1 | 1043.9 / 1047.7 | 28.5 / 28.4 | 121.88 / 121.43 | Volta prefill |
| S11X-D1W | 1010.8 / 1016.6 | 33.8 / 32.2 | 125.86 / 125.14 | CPU PathC7, warm 재검증 |
| S11X-C1 | 1037.6 / 1044.8 | 33.0 / 32.3 | 122.60 / 121.77 | P1+D1 |
| **S11X-D2** | **1032.6 / 1037.0** | **37.1 / 41.0** | **123.21 / 122.69** | **현재 운영, 3/3 C2 PASS** |

| 목표 등급 | 각 Agent Prefill | 각 Agent Decode | 판정 |
|---|---:|---:|---|
| 첫 단계 | >=1100 | >=40 | 개선 후보 |
| 적극적 목표 | >=1200 | >=50 | 동시 개선 |
| 도전 목표 | >=1300 | >=60 | 실측으로만 판정 |
| 최종 | 검증된 최대 성능 | 검증된 최대 성능 | 품질·안정성·전력 조건 충족 |

S11X-D2의 느린 Agent A 기준 Prefill 1200은 약 +16.2%, Decode 50/60은 약 +34.8%/+61.7% 필요하다. 50 또는 60에 도달해도 새로운 병목과 개선 근거가 있으면 추가 신규 후보를 검토한다. 목표 미달도 유효한 결과이며 다른 양자화, 단독 GPU 속도, layer split 또는 다른 GPU의 결과로 대체하지 않는다.

## 2. 0.1.59 이후 업데이트와 적용 가능성

11월 25일 GitHub 재확인 결과, 최신 정식 앱은 v0.2.21 (2026-11-24 19:10 KST 공개), Qwen 엔진은 **0.1.67**이다. 11월 24일 main의 Control 0.1.68 / Terminal 0.2.21.1 버전 증가는 엔진 0.1.68 출시가 아니다. 최초 0.1.66 계획을 폐기하지 않고 0.1.67을 추가한다.

| 릴리스 | Qwen 엔진 | 확인된 변경 | Stage 12 판정 |
|---|---|---|---|
| [v0.2.14](https://github.com/Niko1221/Strata/releases/tag/v0.2.14) | 0.1.60 | NVIDIA/AMD 자체 prompt kernels | sm_70 dispatch, prefill auto 크기와 CPU ISA 재검토 |
| [v0.2.15](https://github.com/Niko1221/Strata/releases/tag/v0.2.15) | 0.1.60 유지 | App/Terminal 안정성 수정 | 신규 엔진 후보 아님 |
| [v0.2.16](https://github.com/Niko1221/Strata/releases/tag/v0.2.16) | 0.1.62 | 자체 커널 전환, engine/ 등 디렉터리 재구성, 공식 V100 26K prompt 17.464s → 15.068s | 중요. 0.1.58 대비 시간 13.7% 감소 사례이며 우리 127K C2 또는 D2 대비 개선 보장은 아님 |
| [v0.2.17](https://github.com/Niko1221/Strata/releases/tag/v0.2.17) | 0.1.63 | ROUTE_TAIL_SKIP 기본 OFF(품질 우려), CPU pool dependency, Linux cgroup/RAM 관리, 일부 신형 GPU 가속 | route 정확도·기본값·CPU 경합 확인; Blackwell 전용 제외 |
| [v0.2.18](https://github.com/Niko1221/Strata/releases/tag/v0.2.18) | 0.1.64 | Hy4-Flash 전용 엔진 도입 | 타 모델 전용 성능은 제외 |
| [v0.2.19](https://github.com/Niko1221/Strata/releases/tag/v0.2.19) | 0.1.65 | Inkling 전용 엔진; Blackwell/Ada/Ampere 최적화 | sm_70에서 활성화되는 경로만 선별 |
| [v0.2.20](https://github.com/Niko1221/Strata/releases/tag/v0.2.20) | 0.1.66 | CUDA expert pair 확장, CPU quant SIMD, 4-tier planning, 장문 NaN 수정 | 고우선 소스 감사 및 독립 비교 |
| [v0.2.21](https://github.com/Niko1221/Strata/releases/tag/v0.2.21) | 0.1.67 | Qwen prompt 정확도 수정 #6776(합산 순서 변경), RTX 30+ 오류 수정 #6713, 주로 Inkling/서빙 개선 | 최신 기준 후보; Qwen 공식 속도 동일 설명. 정확도/dispatch/기본값 차이 분리 |
| [main Control 변경](https://github.com/Niko1221/Strata/commit/2af30ccaa0729177c4725ee2073f72bf550e2f86) | 0.1.67 패키지 유지 | Control 0.1.68 / Terminal 0.2.21.1 | 엔진 버전으로 혼동하지 않음 |

### 2.1 소스 고정 (태그가 가리키는 SHA 재확인 완료)

- 기존 0.1.59: `712fec6b4297c9cfd32ab43daaa2979a9aa01edf` + [stage11x-d2.patch](../docker/patches/stage11x-d2.patch).
- 0.1.66, v0.2.20: `a34979fc94f3d126b9bb8210f4ad311345688b52`.
- 0.1.67, v0.2.21: `d46f5f268f8ed797e83a5c63a69bffbd7a581cf6`.
- 두 공식 태그의 engine/CMakeLists.txt에서 각각 0.1.66/0.1.67 확인. release bump 커밋 자체와 실제 태그 SHA를 혼동하지 않는다. mutable main으로 빌드하지 않는다.
- [0.1.66→0.1.67 비교](https://github.com/Niko1221/Strata/compare/v0.2.20...v0.2.21): GitHub API 파일 목록은 300개 제한에 도달했다. 전체 diff와 커밋, 하위 모듈/의존성/패키징은 S12-A0에서 pinned checkout으로 완전 조사한다.
- 추가 릴리스 또는 수정 커밋 발견 시 변경 내용·출처·정확도·호환성을 검토하고 별도 ID/SHA로 등록. 실행 중 버전 변경 금지.
- [jmnargi/Strata-V100](https://github.com/jmnargi/Strata-V100) 포크도 이전 S11X-A0 기준 이후 변경을 읽기 전용으로 확인한다. 신규 포트는 실제 sm_70 적용, 라이선스, 원본 SHA 및 parity가 확인된 경우에만 후보화한다.

### 2.2 실제 하드웨어 적용 여부

| 변경 경로 | 판단 및 필수 검증 |
|---|---|
| [CUDA Unsloth/MoE 변경](https://github.com/Niko1221/Strata/commit/3d69a1d3b249439bad15632f7acc7ccf9936e336) | EXP_MODE=8의 실제 sm_70 dispatch, 정확한 gate/up·down type 조합 및 window shape를 확인. 발표된 MoE kernel 1.04~1.67배, down 최대 2.58배는 전체 C2 속도도 V100 실측도 아니다. |
| [dense_i8_tc.cu](https://github.com/Niko1221/Strata/blob/v0.2.20/engine/src/kernels/cuda/dense_i8_tc.cu) | dense_i8_tc_supported()가 cc>=75를 요구한다. V100에는 INT8 Tensor Core가 없어 발표된 1.78~3.26배 verify/prefill 수치를 직접 적용하지 않는다. sm_75/80/120 전용 가드 우회 금지. |
| [Volta prefill](https://github.com/Niko1221/Strata/blob/v0.2.20/engine/src/prefill/prefill.cpp) | FP16 WMMA / DP4A / fallback, 기존 P1의 WMMA2·Skinny·Lean·pointer table과 새 소스 구조에서 비교. fused INT8 prefill의 sm_75+ 경로와 분리. |
| [CPU SIMD 최적화](https://github.com/Niko1221/Strata/commit/4414c298877ac5381318d5c6b6e87c4245ce420b) | 공식 quantize_q8_K 5.59~5.95배, dot kernel +16.5~54.8%는 커널·포맷별 수치. 실제 IQ3_XXS native expert 호출, AVX2/BW/VNNI 요구, Q8_K 또는 실제 activation quant 호출량 확인. |
| [CPU build](https://github.com/Niko1221/Strata/blob/v0.2.20/engine/cmake/backends/cpu.cmake) | expert.cpp의 AVX512VNNI/VBMI 컴파일 옵션 확인됨. W-2135에서는 CPUID/OSXSAVE 및 ISA guard를 검증하고 필요한 비-VNNI PathC7 포트를 보존. 새 quant layer의 최적화가 native expert 경로로 연결되는지 확인. |
| 메모리 planner, adaptive cache, CPU pool 및 cgroup | 기존 mmap GGUF, native pack, 64GB RAM, 독립 프로세스 각각에서 실효 설정·캐시 슬롯·miss/staging·OS fault 검증. SSD tier, host KV 또는 resident budget을 임의 활성화하지 않는다. |
| DFlash2 | 새 엔진의 실제 selector pack, verify 경로, spec/conf/window 제한 및 fallback none 검증. DSpark/DFly2는 타 모델 전용이며 대체 대상 아님. |
| ROUTE_TAIL_SKIP 및 정확도 변경 | baseline의 유효값을 소스/로그에서 확인. 정확도 우선 OFF 기준을 별도 명시하고 필요시 동일 route 설정 비교만 추가. 기존 출력과 달라질 수 있으므로 quality gate 없이 lossy 경로를 켜지 않는다. |

## 3. 하드웨어·운영·안전 고정 계약

- P520 Xeon W-2135 6C/12T, RAM 64GB, Tesla V100 SXM2 16GB ×2. GPU0/A cpuset `0-2,6-8`, GPU1/B `3-5,9-11`. 독립 1 GPU / 1 agent, GPU pooling/layer split 없음.
- 기존 GPU 각 150W configured cap, 135~1245 MHz clock lock 및 호스트 전력/냉각 설정 유지. GPU 센서 순간 피크는 설정 cap과 별개다. RAM 증설·클럭·전력 조정·PSU 실험 제외.
- **전원 안전 필수:** [Stage 10](STAGE10_PROGRESS.md)의 16384 chunk는 실제 PSU power trip을 유발했다. [S11X source audit](STAGE11X_SOURCE_AUDIT.md)에서 0.1.60 bare auto가 sm_70 단일 GPU 32768로 증가한 것을 확인했다. 신규 엔진은 **`--prefill auto:8192`**를 명시하고 소스와 실제 로그에서 최대 chunk <=8192를 확인하기 전 부하를 시작하지 않는다. 해당 구문이 달라졌다면 동등한 안전한 옵션을 검증, 없으면 BLOCKED. 16384/32768 등 더 큰 청크 금지. 8192에서도 새로운 커널의 전력 특성은 별도 검증해야 한다.
- CUDA 12.x (기존 검증된 toolkit/driver를 우선 재사용), `-DCMAKE_CUDA_ARCHITECTURES=70 -DSTRATA_EXPERIMENTAL_SM60=ON`, Qwen CUDA target, native sm_70 cubin 및 실제 dispatch를 확인한다. [CUDA CMake](https://github.com/Niko1221/Strata/blob/v0.2.20/engine/cmake/backends/cuda.cmake)에서 cc<75는 opt-in임을 확인. CUDA 13 금지. build switch가 바뀌면 source-audit 결과에 정확히 기록.
- W-2135는 AVX512F/BW/DQ/VL/CD 지원, AVX512VNNI/VBMI/VPOPCNTDQ 미지원. AVX-512라는 명칭만으로 dispatch를 판정하지 않는다. ISA 검증 없는 전역 -march=native / -mavx512vnni 등 금지.
- 동일 Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS GGUF shard, native pack, tokenizer, expert profile 및 stock DFlash2 selector pack 사용. DFlash2 SHA256 `4a42b98220ea7880664002c8edda1563aecbae754b762a2e2f31b2b91ee93ecd`. 원본은 read-only, 변환이 필요하면 사본 및 동등성 검증.
- 각 `131072` context, INT8 KV, `--kv-resident 32768 --mmap-experts --expert-cache auto`, `--spec 8 --draft-conf 0.7 --draft-fallback none` 초기 고정. 새로운 엔진 옵션은 동일 실효 동작을 확인한 뒤에만 사용.
- 현행 운영 이미지 `strata-v100:stage11x-d2` SHA256 `26d2bbfe67bc7cb4e489e6f9283e22bb4cd59c6e9659abf3396caa4f1a4f7f38`, engine SHA256 `7f6fc8f7858739d18b177911d32d0d832393274b4ba7797dfd3cf29e634e76a9`.
- 운영 `p520-llm-a/b`, P520 loopback 8080/8081, ThinkPad tunnel 18080/18081, OpenCode IDs, 기존 containers/images/release/config/model/로그 모두 보호. S10-D4 rollback도 그대로 보존. 저장소의 마지막 운영 기록은 11월 19일의 확인 상태일 뿐 현재 host 상태는 별도 확인.

## 4. 기존 병목과 이식 범위

[S11X-P0 및 D2 보고서](../artifacts/stage11x-results-20261119/summary.md)의 실제 결과:

- P0의 Agent A prefill 구간: dequant 39.2%, gate/up GEMM 16.2%, down GEMM 8.3%, QSA attention 6.4%, copy wait 4.0%. GPU event 구간에 host staging/wait가 섞일 수 있다. cold-cache P0 비율을 현재 D2의 순수 GPU 연산 비율로 가정하지 않는다.
- P0(spec8): CPU expert 36.87/32.35 ms/win, GPU waitCPU 35.43/31.35 ms/win, adapt join 9.43/9.02 ms/win. GPU wait와 CPU time은 겹치므로 합산 금지.
- D2 Tier2에서 adapt join 0.00/0.00 ms/win, jobs 0.11/0.08 ms/win(진단). 이미 얻은 이득을 0.1.66/67의 신규 가속률에 중복 합산하지 않는다.
- 실측 D2 peak VRAM 15577 MiB. 여유 공간이 제한적이므로 scratch, ring, pinned RAM, cache slots 증가를 먼저 정량화한다.
- [실제 48-layer expert map](STAGE11X_SOURCE_AUDIT.md): Gate/Up IQ2_XXS 9, IQ2_XS 10, IQ3_XXS 6, IQ3_S 13, IQ2_S 10; Down IQ4_NL 18, Q2_0 30. ty=18 단독 개선은 gate/up의 6/48 layer만 직접 커버한다. 커널별 실제 시간과 형식별 hit/miss, 지원 조합을 기록한다.

### S11X-D2 19개 override 감사 목록

| 그룹 | 기존 환경변수 | 검증 및 처리 |
|---|---|---|
| 기본 D4 (3) | STRATA_SELECT_SIMT=1, STRATA_SM70_TABLE=1, STRATA_PF_WMMA=1 | 활성화 여부 및 새 default 비교 |
| Volta P1 (3) | STRATA_PF_WMMA2=1, STRATA_PF_WMMA_LEAN=1, STRATA_PF_WMMA_SKINNY=1 | 8192 chunk/shape/type/2-byte alignment/indirect weights/scratch parity |
| CPU PathC7 (5) | STRATA_AVX512BW_IQ=22, STRATA_IQ_MT_MIN=1, STRATA_IQ_GATHER=1, STRATA_IQ256_GATHER=1, STRATA_Q2_BITPLANE=1 | 비-VNNI CPU path의 runtime CPUID, arithmetic 및 multi-token parity |
| GPU defaults (6) | STRATA_SIDE_MIXER=2, STRATA_ATTN_DAILY=1, STRATA_GR_UP75=1, STRATA_GU_SWIGLU=1, STRATA_QSA_ROWS=1, STRATA_FUSE_WAIT=2 | 현재 nv_defaults와 비교, no-op 및 중복 삭제 가능 여부 |
| Cache/scheduling (2) | STRATA_MMAP_ADAPT_ASYNC=1, STRATA_COLD_OVERLAP=5 | mmap 2-slot pinned bounce ring, adapt lifetime, stream/event sync, zero-mincore guard 및 cold page fault 확인 |

A2 결과에서 19개 각각과 D2 patch hunk를 **KEEP / UPSTREAM-EQUIVALENT / REBASE / REPLACE / DROP / BLOCKED**로 분류하고 source file:line, 실제 실행 증거, parity, 위험도 및 이유를 남긴다. 환경변수가 존재한다는 사실만으로 활성화되었다고 판정하지 않는다.

기존 실패 사례: 16384 chunk 영구 금지. ADAPT_LAG+NOWAIT spec8, AUX_CPUS=auto, resident-budget-gib 2, pool-workers 3, PF_HC_REGION, expert-cache-per-layer, kv-resident 40960 및 이전 실패 spec/conf 조합은 원인 변경과 새 병목 근거 없이 반복하지 않는다.

## 5. Gate별 실험 레지스터 및 실행 순서

모든 후보는 새 S12-* ID와 별도 image/config/receipt를 가진다. 임의 변수 조합을 금지하며, 정합성을 통과한 단일 변경을 먼저 확인한다.

| Gate / ID | 후보·작업 | 핵심 결과/진행 조건 |
|---|---|---|
| A / S12-A0 | 0.1.59→0.1.66→0.1.67 + 최신 V100 fork 읽기 전용 source audit | full diff, per-type sm_70/ISA dispatch, Qwen #6776, cache/planner/defaults, pack/server API, chunk safety, 새 소스 레이아웃 및 이식 가능성 |
| A / S12-A1 | 공식 두 태그의 독립 CUDA12/sm_70 build | exact SHA, image/binary hash, cubin/ISA, CPU/GPU parity, effective chunk <=8192. GPU 사용/host build는 별도 승인 |
| A / S12-A2 | D2 patch 및 19개 override의 기능별 대응표 | upstream과 기존 변경 중복·충돌 확인, port plan. 새 엔진에서 사라진 환경변수 강제 복원 금지 |
| B / S12-U0 | 0.1.66 순정 엔진, 고정 workload와 필수 안전/모델 설정만 | 엔진 자체 효과, 기존 S11X-D2와 비교. 순정에 D2 override를 몰래 포함하지 않음 |
| B / S12-U1 | 0.1.67 순정 엔진, U0와 동일 계약 | 정확도 수정 포함 최신 후보. U0 대비 성능/품질 차이 |
| B / S12-R0 | 필요 시 보존된 S11X-D2 image의 새로운 비교 실행 | 역사적 reference는 변경하지 않음. 동등한 cache 조건에서 paired/interleaved 비교가 필요한 경우만 승인받아 새 ID로 시행 |
| B / S12-P0 | 선별된 엔진의 비채점 프로파일 | prefill 및 decode residual bottleneck. 필요 시 U0/U1 또는 D2의 비교용 하위 진단 ID를 별도 정의 |
| C / S12-P1 | Volta WMMA2/Skinny/Lean 및 새 FP16 grouped/dequant 경로 | prefill phase 시간, TTFT, exact effective dispatch, VRAM, 전력, parity |
| C / S12-D1 | 비-VNNI AVX512BW PathC7 + 신규 native CPU quant 후보 | CPU expert/activation/dot/scheduling 시간, waitCPU, AVX frequency, per-type correctness |
| C / S12-D2 | mmap async Adapt와 zero-mincore port/equivalent | join/wait/jobs, cache hit/miss, residency/fault, stale mapping 및 async race 검증 |
| C / S12-D3 | 실제 sm_70 지원 GPU resident expert/MoE decode | EXP_MODE=8 등 dispatch 가능 조합만 시험; verify ms/win 및 GPU kernel 비용 |
| C / S12-P2 | host staging, dequant/transfer overlap, prefill ring/cache | P0에서 남은 병목 확인 시. 8192 유지, peak VRAM/RAM 및 page-cache 보호 |
| C / S12-D4 | DFlash2 verify/window 개선 | 유효 tokens/window, acceptance, verify time, 품질. 먼저 stock 동일 spec/conf; 추가 파라미터는 source-supported 안전 범위와 새 근거를 갖춘 별도 ID |
| C / S12-BP* | 조건부 기존 0.1.59 D2 기반 backport | 신규 엔진 전반이 퇴보하고 단일 개선을 이식할 근거가 있을 때. 정확도 수정의 필요성을 별도 평가 |
| D / S12-C1 | 검증된 P/D 최적화 결합 | 단일 후보의 향상이 조합에서도 유지되는지, kernel/cache/CPU/VRAM 충돌 점검 |
| D / S12-F1 | 최종 후보 공식 재검증 | 최소 3 fresh-process C2, 품질·장문·API·전력/안정성 gate. 운영 승격은 별도 승인 |

### Gate A — GPU 사용 전 감사 / build gate

1. 공식 태그 SHA와 CMake engine version, toolchain/driver, native pack geometry/quant map, CLI/ENV semantics, release defaults, build targets 및 source tree 이동을 확인한다.
2. 전체 0.1.59→0.1.66→0.1.67 diff와 V100 fork를 source-level로 조사한다. 결과에 실제 적용 경로와 제외 이유를 기록한다.
3. CMake/compile_commands, cuobjdump(sm_70), objdump/ISA guard, CPUID/OSXSAVE 확인. 가능한 upstream CPU/GPU tests 및 기존 native_arithmetic_parity, native_multi_parity, iq_avx2_parity, q2_bitplane_parity, pf_wmma_parity, file_expert_source_test에 해당하는 테스트를 실행 계획에 포함. 신규 엔진에서 이름이 바뀐 경우 정확한 대체 테스트를 매핑한다. unavailable/skip은 PASS가 아니다.
4. GPU 부하 승인 후 1 GPU씩 짧은 smoke로 실행·pack·DFlash2·chunk 상한 검증, 그 다음 제한된 동시 smoke. 큰 부하로 바로 진입하지 않는다.
5. build/ISA/pack/route/chunk/정합성 gate 미충족 시 해당 후보 BLOCKED. force dispatch, guard 삭제 또는 품질을 희생해 통과시키지 않는다.

### Gate B — 엔진 선별

- U0/U1은 필수 비교 대상으로 각각 1회 짧은 안전 검증 후 1회 동시 C2 선별(승인 범위 내). 공식 점수는 선정된 후보별 최소 3개 유효 fresh-process batch로만 확정.
- U1을 최신 우선 기반으로 고려하되, U0가 더 나으면 차이를 분석. 특히 #6776 정확도 수정은 단순 성능을 위해 되돌리지 않는다. 기존 패치를 포함하지 않은 두 순정 엔진과 현행 D2의 차이를 기록한다.
- 순정이 더 느려도 곧바로 폐기하지 않는다. D2 기능 부재·default/route 차이·cache 상태에 의한 손실을 분리하고 새 엔진 기반 후보와 기존 D2 백포트 후보의 실효 성능을 비교한다.
- P0는 비채점. timing flags/profiler를 정식 속도 측정에서 제거. P0 결과로 C 단계의 우선순위를 재정렬한다.
- R0는 새 승인된 비교로만 수행하며 종료된 S11X-D2 ID를 재사용하거나 역사적 기준값을 대체하지 않는다.

### Gate C/D — 증거 기반 최적화와 종료

- 후보는 하나의 검증 가능한 기능 변경으로 1회 선별. 이득이 없거나 부작용이 크면 제외한다. 기존 P1, D1, D2는 각각 이미 검증된 기능이므로 upstream-equivalent면 재이식할 이유가 없다.
- 진행 기준(계획상 제안): 비교 가능한 warm 상태에서 핵심 지표 약 3% 이상 개선 또는 계측된 병목의 의미 있는 감소가 보일 때 후속 정식 검증. 3% 이내는 분산과 cache/output 차이를 우선 평가하고, 작은 개선도 결합 가치가 뚜렷하면 기록한다. 고정된 통계적 보증이나 절대적인 합격 기준이 아니다.
- 효과 있는 독립 후보만 C1에 결합. 서로 같은 scratch/stream/pool/cache를 사용하는지 확인. 3회 이상 정식 평가에서 개선이 재현된 후보만 F1.
- 추가 시도는 병목 가설·단일 변경·정합성 테스트·새 ID를 명시. 무제한 sweep, 무의미한 동일 조건 반복 금지. 최초 GPU 승인 범위와 추가 후보 예산은 분리한다.

## 6. 측정 계약과 품질 기준

- Frozen C2 [manifest](../bench/workloads/v100-performance-v1.json) SHA256 `e413acced27c1991d76ce2b4f45853b9676e5b9000ef8503ca`; [runner](../bench/c2_v100_contract.py). 실제 materialized request/post-template token IDs, prompt hash, tokenizer/template SHA, runtime context slack 및 token counting semantics를 확인. 기존 manifest/runner는 보존하고 API 변경이 필요하면 새 adapter와 동등성 증빙을 추가.
- A/B 독립 prompt 약 126,967 토큰, 131072 context, 출력 reserve 4096, min output 1024, temperature 0, top_p 1, seed 520, finish_reason 명시적 stop, prefix reuse 0, fresh process. 출력/usage/finish가 누락된 응답을 기본값으로 성공 처리하지 않는다.
- 실제 동시 decode overlap, overlap seconds/ratio, per-agent whole decode와 가능하면 overlap-only throughput 및 aggregate rate를 각각 보고한다. 단순 A+B 중앙값은 실제 overlap 처리율과 다르므로 별도 표기한다.
- 정식 후보 3회 유효 동시 C2 이상. 초기 cold/warm OS page-cache를 별도로 기록하고, 비교 시 같은 cache 상태 및 실제 NVMe read를 통제한다. 가능하면 interleaved 비교; 통제되지 않은 역사적 비교는 관측값으로만 표기. 운영 호스트 전역 drop_caches 또는 swap 조작 금지.
- 새 엔진 prompt prefix reuse는 실제 운영 multi-turn에는 유용할 수 있으나 C2 비교에서는 OFF/0으로 확인한다.
- stdout/stderr, timestamps, exact source/image/binary/assets/config/argv/env, driver/toolkit, cpuset, clocks, configured cap, GPU utilization/VRAM/temperature/power avg+peak, CPU freq/ISA/instructions, per-window CPU/GPU timing/overlap, adaptive join/wait/jobs, expert hit/miss/slots, DFlash2 offered/accepted/effective tokens/window, page residency/fault/Swap/NVMe I/O, request/output hash 및 실제 health를 보존.
- 동일한 output trajectory/forced-token 비교가 소스에서 지원될 경우 별도 진단으로 실행. 동일 토큰에서 layer/kernel/verify 비교, logit/top-token 및 허용 오차를 평가한다. 지원되지 않으면 이유를 문서화하고 output 길이/route/acceptance 차이를 명시. 정식 C2는 변경하지 않는다.
- 별도 품질 suite: 긴 문맥 검색/anchor recall, 코딩 태스크의 테스트 통과, JSON/schema/tool-call parse 및 실행, 정확한 sampling/stop, NaN/반복/garbled 검사. C2 PASS는 의미적 품질 PASS가 아니다. baseline vs candidate 동일 프롬프트, 정답 기준 및 허용 오차 사전 명시. ROUTE_TAIL_SKIP 등 정확도 절충 변경은 별도 승인 없이는 운영 후보에 포함하지 않는다.
- F1 최종 검증에는 반복 128K C2, 독립 API smoke, 장시간 요청/재시작/health, DFlash2 활성 및 no fallback 확인을 포함. 품질·안전성 실패는 처리량이 높아도 승격 불가.

### 최종 판정

1. **Scored PASS**: 유효 C2 및 모든 필수 증빙을 충족. 목표 달성 여부는 별도.
2. **Performance candidate**: 동등 조건에서 Prefill/Decode/TTFT의 실질적 개선 및 다른 핵심 지표의 의미 있는 악화 없음. Pareto trade-off는 별도 보고.
3. **Promotion candidate**: 양쪽 각각 기존 D2보다 빠르거나 동등하며, 최소 하나 이상의 실질적 이득이 재현되고 품질·안전성·API/재시작 검증 통과. 목표의 A/B 개별 중앙값, 모든 배치 달성 여부, worst agent, 변동폭을 보고. 승격은 사용자 결정.
4. **STOP/FAIL**: 전원 차단/불안정, Xid, OOM, CUDA memory fault, SIGILL, NaN/garbled, context corruption, unexpected fallback 또는 운영 손상 징후. 즉시 실험 중단 및 증빙 보존, 자동 재시도 금지. 전원 차단 후 고부하 재개는 별도 원인 조사와 승인.

## 7. 운영 보호 및 rollback

- 먼저 [AGENTS.md](../AGENTS.md), [Stage 4 plan](STAGE4_PLAN.md), [Antigravity handoff](STAGE4_ANTIGRAVITY_HANDOFF.md), [P520 serving guide](P520_SERVING.md)를 확인.
- ThinkPad E14 checkout에서 작업, 필요한 읽기 전용 P520 점검은 ssh p520으로 수행하는 기존 계약을 따른다. 현행 서비스/GPU 점유·disk/RAM 여유·clock lock·power cap·컨테이너 상태를 실제로 확인하고 실행 승인과 유지보수 범위를 별도 확보한다.
- 별도 versioned Dockerfile/image, 전용 후보 컨테이너/실험용 포트/결과 경로 사용. 원본 GGUF/pack/config/release는 immutable. 기존 운영 컨테이너 내부 파일 수정, 자동 업데이트, docker prune, 기존 historical image/container 삭제 금지.
- GPU 두 장이 운영 중이면 실험을 시작하지 않는다. 사용자 승인 후 소유한 운영 pair만 안전하게 중지하고 기존 상태·정확한 rollback command를 보존. 임시 후보 종료 후 기존 승인된 상태로 복구하며 자동 promotion 금지.
- 운영 승격은 F1 결과와 품질 근거를 제출한 뒤 별도 승인. 안정적인 API alias, canonical Qwen 모델 이름, ports/tunnel을 유지하고 기존 S11X-D2 및 S10-D4 rollback release를 보존한다. 기존 helper는 현재 D2를 고정하므로 승격 승인 전 수정하지 않는다.

## 8. 산출물 및 권한

추후 별도 승인된 범위에서 다음 파일을 추가한다.

- docs/STAGE12_SOURCE_AUDIT.md — 전체 diff/형식별 kernel 및 ISA 지원/19개 override/patch 대응표.
- docs/STAGE12_BUILD_AUDIT.md — 버전별 build, hashes, parity/dispatch/안전 gate.
- bench/stage12-candidates.json — pinned engine/patch/config, exact argv/env, candidate dependencies, 금지 조건.
- 신규 Stage12 전용 Dockerfile, docker/patches/stage12-*.patch, scripts의 새로운 번호/파일.
- artifacts/stage12-results-YYYYMMDD/summary.md 및 신규 run ID별 report/raw/log/manifests; 기존 저장소의 결과 저장·해시 정책 준수.
- docs/STAGE12_FINAL_REVIEW.md — 모든 후보/무효 실행/실패/비채점 진단/판정/품질·전력 비교.
- docs/CONSOLIDATED_BENCHMARKS.md 및 CSV에 검증된 결과를 추가만 하고 과거 Stage 7~11X 원본을 덮어쓰지 않는다.

**현재 상태는 계획만 커밋.** 이 문서에서 정의한 후보는 실행 완료 또는 실행 허가를 뜻하지 않는다. 최초 작업은 S12-A0 읽기 전용 감사로 한정하고 A1 빌드/테스트, A2 포트 구현 및 이후 GPU 부하/서비스 정지/승격은 명시적으로 승인된 범위에서만 진행한다. 기존 AGENTS.md/운영 설정/벤치마크/소스/컨테이너는 이 문서 추가로 변경하지 않는다.

### 참고

- [S11X source audit](STAGE11X_SOURCE_AUDIT.md)
- [S11X follow-up plan](STAGE11_OPTIMIZATION_FOLLOWUP_PLAN.md)
- [S11X results](../artifacts/stage11x-results-20261119/summary.md)
- [D2 deployment receipt](../artifacts/p520-serving-20261119/summary.md)
- [Consolidated benchmarks](CONSOLIDATED_BENCHMARKS.md)
- [Stage10 RAM report](STAGE10_T1_RAM_REPORT.md)
- [Upstream 0.2.20 release](https://github.com/Niko1221/Strata/releases/tag/v0.2.20)
- [Upstream 0.2.21 release](https://github.com/Niko1221/Strata/releases/tag/v0.2.21)

공개 성능 발표는 외부 관측값으로만 인용한다. 이 계획은 실제 0.1.66/0.1.67 빌드, P520 벤치마크, 전체 upstream source audit를 완료했다고 주장하지 않는다.
