# Stage 7 — IQ3_XXS additional 0.1.54 optimization tests

**Status: EXECUTED (2026-11-01 19:09–20:13 KST).** S7-XXS-8..11 3 batches each, S7-XXS-12 2 batches (stopped early by operator), DIAG-1 1 non-scored batch — **15/15 C2 mechanical PASS**. See the [S7-XXS-8..12 result report](../artifacts/stage7-results-20261101/stage7-iq3xxs-opt-report.md). Stage 7 validates **Strata engine 0.1.54 across quantizations**; IQ3_XXS is only one model. S7-XXS-1..6 already completed 18/18 C2 PASS. No production promotion.

> **Result summary (empirical, same-session):** SIMT2 prefill −0.3% vs same-session SIMT=1 control; GDN_REC_WARP=2 +0.1–0.25% (within noise, numerics changed, quality not checked); Q8_GATHER_WIDE=0 no measurable effect; **SM70_TABLE=1 was the only consistent signal: −1.4 to −2.0% decode time on identical-output pairs** versus the other tested configurations; `--prefill 4096` regressed prefill by −36.7% (TTFT ~126 → ~200 s). Comparisons to archived S7-XXS-2 show a common-mode ~+1.2% prefill shift across all arms and are not causal evidence. Nothing was promoted.

## Baseline and test matrix

Reference **S7-XXS-2 (SIMT=1)**, 3-run per-agent medians: Prefill **992.6 / 1000.5 tok/s**, Decode **25.0 / 24.6 tok/s**, TTFT **128.17 / 127.20 s**, Batch Wall **212.01 s**. Compare against these archived 0.1.54 values. Do not rerun Stage 5 or S7-XXS-1..6 as a new baseline.

| Stage 7 arm | Only change relative to S7-XXS-2 | Target | C2 | Status |
| --- | --- | --- | ---: | --- |
| **S7-XXS-8** | Set `STRATA_SELECT_SIMT=2` instead of SIMT=1 | Prefill QSA scorer | 3 | **3/3 PASS** — prefill 1002.1 / 1008.0, no gain |
| **S7-XXS-9** | SIMT=1 plus `STRATA_GDN_REC_WARP=2` | Prefill GDN recurrence | 3 | **3/3 PASS** — prefill 1005.9 / 1014.3, within noise |
| **S7-XXS-10** | SIMT=1 plus `STRATA_Q8_GATHER_WIDE=0` | Decode INT8-KV gather | 3 | **3/3 PASS** — no measurable decode effect |
| **S7-XXS-11** | SIMT=1 plus `STRATA_SM70_TABLE=1` | Decode V100 expert/GEMV/HC kernels | 3 | **3/3 PASS** — decode time −1.4 to −2.0% on identical outputs |
| **S7-XXS-12** | SIMT=1 plus config `--prefill 4096` (replaces `auto` = chunk 8192) | Prefill chunk size | 3 | **2/2 PASS, stopped early** — prefill 635.2 / 640.2 (−36.7%) |
| **S7-XXS-DIAG-1 (optional)** | SIMT=1 plus `STRATA_PREFILL_TIMING=1 STRATA_DECODE_TIMING=1 STRATA_VERIFY_PROFILE=1` | **Profiling only (non-scored)** | 1 | **PROFILE_PASS_NOT_SCORED** |
| **S7-XXS-13 (conditional)** | Combine **only individually confirmed improvements**, requires separate recipe | Combined | 3 if chosen | Not prepared |

**Planned: 15 new scored C2 batches + optional 1 diagnostic. Executed: 14 scored + 1 diagnostic** (`xxs-12-3` intentionally not run). Existing optional S7-XXS-7 (WMMA2) remains separate and not approved for execution. These tests do not complete the entire multi-model Stage 7; IQ2_XS and IQ3_S are still pending.

## Interpretation of earlier speedups

- SIMT2 in upstream `src/kernels/cuda/qsa_select.cu` uses larger tiles and was designed bitwise-identical to SIMT1. Its whole-C2 V100 gain has not been measured.
- Upstream V100 documented +6 ~ 9% for the **GDN recurrence kernel**, not total Prefill. `GDN_REC_WARP=2` changes FP32 summation order, so check output and agent quality separately.
- Upstream V100 documented ~11% on the **Q8 gather kernel**, not entire Decode. `Q8_GATHER_WIDE=0` preserves the kernel arithmetic.
- Upstream V100 SM70_TABLE benchmark reduced GPU verify-window work from 22.80 to 21.24 ms on **IQ2_XS**; Stage 6 IQ3_S one-run test did not establish dual-agent benefit. Do not assume this boosts IQ3_XXS.
- A different V100 workload showed one smaller-prefill-chunk win; `--prefill 4096` is exploratory, not a predicted improvement.
- Stage 6 CPU Expert / GPU waitCPU dominated **IQ3_S**; do not assume identical bottlenecks for 0.1.54 IQ3_XXS without an instrumented diagnostic.

## Frozen environment and safety

Use **new runner** [`scripts/99-stage7-iq3xxs-opt-c2.sh`](../scripts/99-stage7-iq3xxs-opt-c2.sh). Original `scripts/97-stage7-iq3xxs-c2.sh` and its 18/18 results are unchanged. New IDs `xxs-{8,9,10,11,12}-{1,2,3}` or optional `xxs-diag-1` write only to `results/stage7-iq3xxs-opt/<id>/` and refuse any overwrite/retry.

Keep pinned upstream **v0.2.8 / engine 0.1.54**, source `870aedd9e1ebe1c91f94da93b59af17729f6c5c0`, image ID `sha256:2095eed79b0038ef23d602a0490bf0d89c63ad8e84ace8654c5016b2a51d2246`. Keep 2 independent Tesla V100 16GB, A GPU0 cpuset `0-2,6-8`, B GPU1 cpuset `3-5,9-11`, 1110MHz ceiling, 150W cap, 131072 context, INT8 KV resident 32768, MTP spec 4 / min-p 0.5, matching IQ3_XXS native pack and model.

Frozen C2 manifest SHA-256 `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`; prompt A/B 126967/126968, each >=1024 output tokens, zero prompt cache reuse, decode overlap, stop, post-health, fresh-process per batch. Collect independent A/B prefill, decode, TTFT, batch wall, outputs and hardware/cache/I/O telemetry. The optional profile is **not** a scored benchmark. Environment-variable presence alone does not prove actual CUDA kernel execution.

Runner reuses local **read-only source configs** `results/stage5-iq3xxs/agent-a.json` and `agent-b.json` and checks pinned arguments. New image/build, power/clock changes, model restoration, production port 18080/18081 or ThinkPad tunnel modifications are **not** part of this change. Runner refuses running Docker/GPU jobs, occupied test ports 18084/18085 and overlapping Stage 7 runs. Never stop a live agent without separate approval.

## Operator command (P520, only after explicit approval and live-host preflight)

```bash
cd ~/v100-x2-strata-qwen3.8-flash-next
bash -n scripts/99-stage7-iq3xxs-opt-c2.sh
timeout 1800 bash scripts/99-stage7-iq3xxs-opt-c2.sh xxs-8-1
```

Run each remaining ID **manually**; no automatic sweep or retry is included. New candidate S7-XXS-13 is intentionally not executable until selected. Preserve failed receipts and raw data; C2 PASS does not establish coding/Tool Call quality.

## Evidence

- [S7-XXS-8..12 result report (2026-11-01)](../artifacts/stage7-results-20261101/stage7-iq3xxs-opt-report.md)
- [Existing Stage 7 IQ3_XXS report](../artifacts/stage7-results-20261101/stage7-iq3xxs-final-report.md)
- [Stage 5 IQ3_XXS matrix](../artifacts/stage5-results-20261029/stage5-iq3xxs-matrix-summary.md)
- [Stage 6 profiling](STAGE6_FINAL_REPORT.md)
- [Upstream pinned V100 documentation](https://github.com/Niko1221/Strata/blob/v0.2.8/docs/NVIDIA_V100.md)
- [SIMT2 source](https://github.com/Niko1221/Strata/blob/v0.2.8/src/kernels/cuda/qsa_select.cu)
- [GDN source](https://github.com/Niko1221/Strata/blob/v0.2.8/src/prefill/kernels.cu)
- [KV gather source](https://github.com/Niko1221/Strata/blob/v0.2.8/src/kernels/cuda/kv_q8.cu)
