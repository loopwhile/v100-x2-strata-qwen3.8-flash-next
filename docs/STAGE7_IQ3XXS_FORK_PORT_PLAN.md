# Stage 7 — IQ3_XXS V100 Fork selective port: S7-XXS-14 / 15 / 16

**Status: CLOSED — S7-XXS-14/15/16 each completed 3/3 C2 PASS (9/9 total), 2026-11-01.** This extends only the **IQ3_XXS** branch of Stage 7's upstream-engine **0.1.54** evaluation. All historical S7-XXS-1..13 receipts, Stage 5 measurements, output files, Docker images and live services remain untouched. The original planning commit performed no host operations. The later user-authorized execution is recorded in the [14–16 execution report](../artifacts/stage7-results-20261101/stage7-iq3xxs-14-16-report.md); there is no production promotion.

> **Execution closed:** all nine scored IDs are completed and must not be rerun. Source/build/parity/128K/dispatch/allocation gates passed before enabling 15/16; see the [source audit](../artifacts/stage7-results-20261101/stage7-iq3xxs-port-source-audit.md). Each arm uses a literal pinned image ID. No promotion or new experiment is authorized by this closure.

## 1. Motivation and evidence

- **Primary reference: S7-XXS-13**, upstream 0.1.54, `STRATA_SELECT_SIMT=1` + `STRATA_SM70_TABLE=1`; three C2 medians: **Prefill 1004.2 / 1010.6 tok/s**, **Decode 26.5 / 26.1 tok/s**, **TTFT 126.69 / 125.89 s** (A/B). S7-XXS-11 separately reproduced the same flags with another 3/3 C2 PASS. Compare per-agent, not pooled.
- Stage 5 **T7-Fixed** used `jmnargi/Strata-V100@2c9b1dd7bda3102c4a8e65fbe56c45f5c6882926` (engine 0.1.45.3) and reported Prefill **1030.7 / 1044.9**, Decode **26.6 / 26.7**, TTFT **123.46 / 121.78**. **It preceded the current 1110 MHz GPU cap**, so these historical results do **not** establish a source-patch speedup over S7-XXS-13 at fixed hardware conditions.
- Base for *all three tests*: upstream `Niko1221/Strata@870aedd9e1ebe1c91f94da93b59af17729f6c5c0` (v0.2.8 / Qwen engine 0.1.54). Never wholesale downgrade/replace it with Fork 0.1.45.3.
- **Original planning rationale; later source verification is in the source audit:** fork's V100 guide describes an IQ3_XXS-capable second WMMA tile and `STRATA_PF_WMMA_LEAN=1`. In upstream 0.1.54 the `STRATA_PF_WMMA2=1` switch already exists, but the upstream V100 guide lists narrower covered shapes. The **actual compiled dispatch and relevant differences must be established with source diff and CUDA path evidence before declaring a fork port necessary or successful**. The fork's lean buffers were measured for **IQ3_S layer split**, not this independent IQ3_XXS topology.

## 2. Experimental arm definitions

| Arm | Engine/image | Effective overrides | Incremental question | Repeats | Execution state |
| --- | --- | --- | --- | ---: | --- |
| **S7-XXS-13** (existing control; **do not rerun**) | Pinned upstream 0.1.54 | `STRATA_SELECT_SIMT=1`, `STRATA_SM70_TABLE=1` | Archived fixed reference | 3 completed | **3/3 PASS** |
| **S7-XXS-14** | **Unmodified**, pinned `strata-v100-upstream:0.1.54` image | **13 + `STRATA_PF_WMMA=1`** | Does first-stage WMMA provide benefit on top of SIMT+SM70? | **3** | **COMPLETED 3/3 C2 PASS — IDs closed** |
| **S7-XXS-15** | **0.1.54-derived image** after verified IQ3_XXS WMMA2 path or selective fork port | **14 + `STRATA_PF_WMMA2=1`** | Does the *verified* IQ3_XXS WMMA2 kernel add an effect over 14? | **3** | **COMPLETED 3/3 C2 PASS — IDs closed** |
| **S7-XXS-16** | **0.1.54-derived image** with 15's kernel plus validated WMMA_LEAN port | **15 + `STRATA_PF_WMMA_LEAN=1`** | Does reducing unused WMMA buffers and expert-row copies help over 15? | **3** | **COMPLETED 3/3 C2 PASS — IDs closed** |

**Total conditional budget: 9 fresh-process dual-agent C2 batches**. All three arms completed their three batches. Do not rerun or reuse any `xxs-14-*`, `xxs-15-*` or `xxs-16-*` measured ID. S7-XXS-7 remains an unrelated optional arm, not relabeled or silently run. If 14's WMMA never dispatches or regresses, **do not run 15/16 merely to fill IDs**; document the reason and review feasibility.

## 3. Source gates (satisfied for the pinned measured images)

1. Pin and compare **actual source** at the two SHAs above (not latest `main`). In particular inspect `src/prefill/prefill.cpp`, the WMMA expert kernels/dispatch, `src/core/nv_defaults.cpp`, configuration parse, allocation/buffer sizing and relevant parity tests.
2. For **15**, inspect whether upstream 0.1.54 already handles IQ3_XXS under `STRATA_PF_WMMA2=1`. If it does, **do not duplicate the patch**: document effective path, original version and source line/dispatch proof, and use a distinct verified image receipt. Otherwise port **only** the necessary IQ3_XXS WMMA2 tile + dispatch/ABI parts from the pinned fork; retain upstream 0.1.54's other fixes and verify no changed/unsupported quantization types.
3. For **16**, port the fork's lean-buffers implementation (source notes place it in `src/prefill/prefill.cpp`), accounting for 0.1.54's new buffer planner. Require the same predicate for buffer sizing, allocation, gather skips and fallback use; retain a fail-fast guard against reading unallocated buffers. Recheck VRAM headroom and cache/expert placement.
4. Build **separate** uniquely tagged `0.1.54-v100-wmma2` and `0.1.54-v100-wmma2-lean` images. The base 0.1.54 and S7-XXS-14 image are immutable. Record upstream/fork SHA, exact patch SHA/tree, compiler/CUDA 12.x flags, sm_70 device binary, BUILD.json, engine SHA-256, Docker digest, and per-image feature proof. Reuse existing image-building conventions but never retag or overwrite an older image.
5. Run compile, relevant WMMA/WMMA2/Prefill allocation parity, smoke, effective-flag readback, and *instrumented* evidence of IQ3_XXS kernels executing; do not mistake a set environment variable or startup health for kernel dispatch. **Only then** update the new runner to accept 15/16 with **hard-pinned image IDs** and reviewed arm-specific flags. No image ID may be sourced from an unreviewed user environment variable.
6. `WMMA` and `WMMA2` use FP16 operands, which can change logits and output from integer MMQ paths. The lean buffers can alter expert-cache residency. Compare generated text/tool-call quality separately; C2 mechanical PASS only establishes system contract.

The fork's documented `STRATA_SPLIT_MTP_BATCH=1` improvement was for **GPU layer-split** serving; these are **two independent one-GPU agents**, not a layer split. Do not silently add it. Likewise do not import the fork's entire `STRATA_SM70_PERF` default bundle: Stage 5 T7-default did not establish a decode gain, and some Stage 6 screening options lost speed.

## 4. Frozen hardware/C2 contract and telemetry

- Lenovo P520, **2 independent V100 16GB agents**: A GPU0 / cpuset `0-2,6-8`, B GPU1 / `3-5,9-11`; context **131072**, INT8 KV `--kv-resident 32768`, MTP `--spec 4 --spec-min-p 0.5`, expert mmap, native IQ3_XXS pack and shared MTP data. **No layer split**.
- Hold **GPU 1110 MHz SM ceiling and 150 W configured limit** fixed. Record actual clock, average and peak GPU power/temperature per GPU (sampled power peaks may exceed configured limit), VRAM, host RAM/swap, I/O, Linux page cache/major faults, output length, MTP acceptance and concurrent decode overlap.
- Frozen C2 manifest SHA-256: `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`. A/B prompt **126967 / 126968**, each response **>=1024** output tokens, cache_n/cached_tokens 0, `finish_reason=stop`, active simultaneous Decode and post-health PASS.
- **3 valid batches per arm**; one fresh process for each. Never reuse ID or delete failed receipts. Compare **14 vs archived 13**, **15 vs 14**, **16 vs 15**, while labeling cross-session and hardware/cache uncertainty. Assess Prefill, Decode, TTFT, batch wall, peak power and thermals jointly; any failure or quality regression blocks promotion.
- Stage 5/7 earlier receipts and scripts/97 and scripts/99 remain unchanged; existing production agent containers, service ports 8080/8081 and ThinkPad tunnel 18080/18081 are out of scope.

## 5. Runner and pinned execution receipts (CLOSED)

**Isolated runner:** [`scripts/100-stage7-iq3xxs-v100-port-c2.sh`](../scripts/100-stage7-iq3xxs-v100-port-c2.sh). New raw-data namespace: `results/stage7-iq3xxs-v100-port/<id>/`; it shares the existing Stage 7 experiment lock, checks image/manifest, existing containers/GPU users, ports 18084/18085, context/KV/MTP config, and fails if an ID already exists.

The measured images are pinned in the runner:

| Arm | Image ID |
| --- | --- |
| 14 | `sha256:2095eed79b0038ef23d602a0490bf0d89c63ad8e84ace8654c5016b2a51d2246` |
| 15 | `sha256:95b0e4a50a775cd1e5bbfefa711c6e038923867961d1a9e159b9fe1f92ea189e` |
| 16 | `sha256:57b951d4375dd397d6a0f09cd45cc340c80f1f4b7a5260378bd0c88710d66779` |

All nine IDs are closed. The runner retains duplicate-directory/container guards for audit; it is not a new execution order. New experiments require separately approved scope and unique IDs. The final report records cache/swap uncertainty, build failures, diagnostics and preservation status.

## References

- [Stage 7 IQ3_XXS optimization results, including S7-XXS-13](../artifacts/stage7-results-20261101/stage7-iq3xxs-opt-report.md)
- [Stage 5 T7-Fixed result](../artifacts/stage5-results-20261029/stage5-iq3xxs-t7fixed-summary.md)
- [Pinned fork source `2c9b1dd`](https://github.com/jmnargi/Strata-V100/tree/2c9b1dd7bda3102c4a8e65fbe56c45f5c6882926)
- [Fork's V100 WMMA2 + WMMA_LEAN notes](https://github.com/jmnargi/Strata-V100/blob/2c9b1dd/docs/NVIDIA_V100.md)
- [Pinned upstream 0.1.54 source](https://github.com/Niko1221/Strata/tree/870aedd9e1ebe1c91f94da93b59af17729f6c5c0)
- [Upstream 0.1.54 V100 kernel guide](https://github.com/Niko1221/Strata/blob/870aedd9e1ebe1c91f94da93b59af17729f6c5c0/docs/NVIDIA_V100.md)
