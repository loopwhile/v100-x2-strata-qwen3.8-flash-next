# Stage 7 IQ3_XXS S7-XXS-14·15·16 실행 결과 — 2026-11-01

**각 arm C2 3회, 총 9/9 fresh-process dual-agent 128K C2 기계적 PASS.** 재시도나 채점 ID 재사용 없음. 15·16은 upstream 0.1.54 기반의 별도 소스 포트 이미지이며, 프로덕션 승격은 하지 않았다.

## 중위값

| Arm | 구성 | Prefill A / B (tok/s) | Decode A / B (tok/s) | TTFT A / B (s) | Batch wall (s) | PASS |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| S7-XXS-14 | SIMT + SM70_TABLE + WMMA (기존 upstream 이미지) | 997.6 / 1006.6 | 26.4 / 26.2 | 127.53 / 126.48 | 211.54 | 3/3 |
| S7-XXS-15 | 14 + IQ3_XXS WMMA2 선택 포트 | 961.2 / 969.6 | 26.3 / 26.1 | 132.34 / 131.21 | 218.13 | 3/3 |
| S7-XXS-16 | 15 + LEAN 할당·gather 축소 | 990.8 / 998.7 | 26.4 / 27.0 | 128.41 / 127.39 | 219.51 | 3/3 |

## 배치별 실측

| ID | Prefill A / B | Decode A / B | TTFT A / B (s) | 생성 A / B | Wall (s) | Decode overlap (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| xxs-14-1 | 997.6 / 1006.6 | 26.4 / 26.2 | 127.53 / 126.64 | 1674 / 2224 | 211.54 | 63.26 |
| xxs-14-2 | 996.4 / 1006.0 | 25.9 / 26.7 | 127.67 / 126.48 | 1737 / 2577 | 222.95 | 67.00 |
| xxs-14-3 | 999.9 / 1008.1 | 26.5 / 25.8 | 127.21 / 126.20 | 1762 / 2101 | 207.70 | 66.45 |
| xxs-15-1 | 886.6 / 884.3 | 26.0 / 26.1 | 143.46 / 143.89 | 1665 / 2300 | 231.80 | 63.43 |
| xxs-15-2 | 961.2 / 969.6 | 26.3 / 26.1 | 132.34 / 131.21 | 1844 / 2274 | 218.13 | 70.14 |
| xxs-15-3 | 990.0 / 996.1 | 26.5 / 26.7 | 128.48 / 127.72 | 1652 / 2198 | 210.05 | 62.35 |
| xxs-16-1 | 904.1 / 893.6 | 26.1 / 25.9 | 140.71 / 142.37 | 1266 / 2453 | 237.11 | 46.76 |
| xxs-16-2 | 990.8 / 998.7 | 26.4 / 27.2 | 128.41 / 127.39 | 1297 / 2509 | 219.51 | 49.00 |
| xxs-16-3 | 1012.9 / 1018.7 | 26.4 / 27.0 | 125.59 / 124.89 | 1268 / 2251 | 208.07 | 47.99 |

모든 배치: prompt A/B 126967/126968, 생성 >=1024, cache_n=cached_tokens=0, finish_reason=stop, warmup 0, 실제 동시 decode 및 post-health PASS. A/B CPU affinity와 GPU mapping, 131072 context, INT8 KV resident 32768, MTP spec 4/min-p 0.5 및 native model pack을 유지했다. Agent 컨테이너 ID 18개는 전부 서로 다르다. Manifest와 C2 harness는 원본 그대로다.

## 캐시·swap·일관성

| ID | Expert page cache A / B | Loan slots A / B | Major faults (host) | Swap in / out (host pages) |
| --- | ---: | ---: | ---: | ---: |
| xxs-14-1 | 100% / 100% | 2489 / 2489 | 1483 | 20011 / 0 |
| xxs-14-2 | 100% / 100% | 2489 / 2489 | 54 | 1 / 1 |
| xxs-14-3 | 100% / 100% | 2489 / 2489 | 7 | 0 / 0 |
| xxs-15-1 | 95% / 95% | 2489 / 2489 | 63314 | 164995 / 307145 |
| xxs-15-2 | 99% / 99% | 2489 / 2489 | 4473 | 177 / 22 |
| xxs-15-3 | 100% / 100% | 2489 / 2489 | 2655 | 136 / 1 |
| xxs-16-1 | 95% / 95% | 2173 / 2173 | 38833 | 147984 / 250783 |
| xxs-16-2 | 98% / 98% | 2173 / 2173 | 1492 | 165 / 2 |
| xxs-16-3 | 100% / 100% | 2173 / 2173 | 438 | 251 / 0 |

15번 첫 배치에는 expert cache 95%, major-fault/swap 증가가 있었고 2·3회차로 갈수록 프리필이 빨라졌다. 16번도 첫 배치와 후속 배치의 편차를 모두 포함했다. 이 값들은 host 전체 카운터이며 원인을 특정하는 per-process 프로파일은 아니다. 순차 실행이고 캐시 상태가 달라 **WMMA2 또는 LEAN의 인과적 속도 우위를 확정하지 않는다.** 첫 배치를 제외하거나 추가 재측정하지 않았다. `page cache %`는 엔진의 expert-region 추정값이며 전체 GGUF 파일 fincore 비율과는 구분한다.

LEAN은 chunk 8192 / ring 96을 유지하면서 loan slots를 2489→2173개로 줄였다. 이것은 검증된 할당 효과다. Decode tok/s와 wall은 출력 길이·MTP 채택률에도 영향을 받으므로 wall 감소만으로 최적화를 판정하지 않는다. Per-run MTP 채택/제안 수, GPU/VM 통계와 범위는 [정제 receipts](stage7-iq3xxs-14-16-receipts.json)에 포함했다.

## 빌드와 검증

- 기반 upstream SHA `870aedd9e1ebe1c91f94da93b59af17729f6c5c0`, fork 참조 SHA `2c9b1dd7bda3102c4a8e65fbe56c45f5c6882926`. 14는 기존 image를 그대로 사용했고 15·16은 고유 태그·image ID로 분리했다. CUDA 12.9.86 / sm_70 / engine 0.1.54 확인.
- 15: WMMA2 off/on, 양 GPU 합계 44개 matrix parity 검사 PASS. IQ3_XXS 및 input-index 테스트 포함. 16은 동일 kernel library/parity binary 해시를 검증해 이 증거를 재사용했고, 변경한 LEAN allocation/index 경로는 fresh 128K 호환성으로 검증했다.
- 15·16의 128K 호환성 검사는 각 출력 32토큰의 비채점 검사다. 실제 type-18 WMMA2 CUDA kernel launch, 16의 LEAN/ids=1, zero cache 및 post-health를 확인한 후에만 러너를 허용했다. 두 arm의 A/B 첫 32토큰 출력 해시가 각각 같았지만, 별도 품질 평가는 아니다.
- 15번 빌드의 초기 import/CMake PATH 실패와 컴파일 산출물 재사용 기록을 모두 보존했다. 정확한 이미지·engine·patch SHA, 부분 포트 범위, 타입별 dispatch 및 allocation guard는 [source/build audit](stage7-iq3xxs-port-source-audit.md)를 참조한다.

## 실행 범위와 보존

14번 C2 3회 후 에이전트가 추가한 비채점 추적 검사는 사용자가 지적한 범위 확장이었다. 종료 확인 전에 이미 끝났으며, 채점 결과와 섞지 않았다. 경위와 실패한 port preflight까지 [14번 개별 보고서](stage7-iq3xxs-14-report.md)에 보존했다. 이후 사용자가 15·16 진행을 명시 지시했고, 해당 arm에 필요한 검증과 각 C2 3회만 수행했다. 최종 C2 이후 추가 GPU 실험은 하지 않는다.

GPU 설정·전력/클록·호스트 설정·기존 이미지/컨테이너/모델/MTP·8080/8081·ThinkPad tunnel을 변경하지 않았다. 모든 샘플의 configured power limit은 150 W였다. 실제 active SM 중앙값/최댓값·최대 온도·전력·VRAM은 receipts에 기록했다. 순간 sampled power는 configured limit을 초과할 수 있으며, power limit 변경을 뜻하지 않는다. 모든 arm의 chunk/ring, peak VRAM/thermal/clock 값은 원시 로그와 정제 JSON에 남았다.

원본은 P520 `results/stage7-iq3xxs-v100-port/`에 보존하고 ThinkPad에도 별도 백업했다. 빌드·parity·호환성 원본은 ThinkPad `results/stage7-v100-port-build-records/`에도 보존했다. 공개 artifact에는 프롬프트/생성 본문을 포함하지 않는다. 별도 coding/tool-call 품질 suite와 프로덕션 승격은 수행하지 않았다. **14·15·16 ID는 완료·폐쇄되었으며 재실행하지 않는다.** Stage 7의 IQ2_XS/IQ3_S 등 다른 트랙은 완료된 것으로 표시하지 않는다.
