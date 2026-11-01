# Stage 7 — Strata Qwen engine 0.1.54 validation across model quantizations

**Status: IN PROGRESS — 0.1.54 built, IQ3_XXS S7-XXS-1..6 18/18 C2 PASS (2026-11-01); IQ3_XXS S7-XXS-8..13 EXECUTED (17 scored + 1 diagnostic C2 PASS; S7-XXS-12 stopped at 2 batches); IQ3_XXS S7-XXS-14..16 COMPLETED 9/9 C2 PASS, three per arm, IDs closed; additional quantizations pending. No production promotion.**

**Created:** 2026-11-01 (Asia/Seoul)  
**Target engine:** upstream [Niko1221/Strata v0.2.8](https://github.com/Niko1221/Strata/releases/tag/v0.2.8), **Qwen engine 0.1.54** (the application version is 0.2.8, not 0.1.54). Pin an exact upstream source SHA at build time.

## 1. Scope and objective

**Stage 7 evaluates the Strata 0.1.54 ENGINE, not a single quantization.** IQ3_XXS is one candidate and has a well-documented Stage 5 matrix worth reproducing; it is **not** the definition or exclusive target of Stage 7. The model remains Qwen3.8-Flash-Next GSQ-RCO GGUF, with quantization-specific arms.

Goals:
1. Verify that upstream 0.1.54 compiles and runs correctly on Tesla V100 / Volta `sm_70` under CUDA 12.x.
2. Compare 0.1.54's 128K concurrent-C2 prefill, decode, TTFT, batch completion time, memory behavior, and stability with archived results **for each tested quantization**.
3. Identify which **version-compatible runtime switches** still help each quantization. Do not presume a setting that won for IQ3_S or IQ3_XXS also wins for IQ2_XS or Q4.
4. Keep inference-quality/tool-call checks separate from mechanical C2 pass/fail, and record any relevant changes to default behavior.
5. Keep all previous-stage artifacts and live serving endpoints intact. Stage 7 does not authorize production promotion.

### Candidate models (not limited to IQ3_XXS)

| Quantization | Stage 7 role | Existing evidence / qualification |
| --- | --- | --- |
| **IQ2_XS** | Primary high-throughput candidate | Stage 4-B/4-C existing 0.1.47 baselines; assess 0.1.54 vanilla and appropriate Volta decode/prefill options. |
| **IQ3_XXS** | Primary higher-precision / Stage 5 matrix candidate | Stage 5 T1–T8 and T7-Fixed archived. Its detailed 0.1.54 switch matrix is below. |
| **IQ3_S** | Primary higher-precision candidate if archived model can be safely restored | Stage 5 T1–T8 and Stage 6 results archived; check disk space before any restore. |
| **UD-Q4_K_XL** | Optional feasibility/regression candidate | Previously functional but impractically slow at dual-agent 128K. Run only if resources and a separately approved scope justify it. |
| Additional quantizations | Optional later expansion | Add a separate per-model protocol and pinned model assets before testing; do not silently broaden the frozen comparison. |

**Not planned by default:** mixed-quantization co-residency, layer splitting, changing 128K context, hardware upgrades, power/clock experiments or production cutover. Any such work must be a separately named experiment.

## 2. Frozen cross-model C2 contract

For every homogeneous dual-agent arm, unless explicitly labeled otherwise:

| Item | Fixed requirement |
| --- | --- |
| Host | ThinkStation P520, Xeon W-2135, 64 GB DDR4-2400 ECC, 2 × Tesla V100 16 GB |
| Topology | Independent Agent A on physical GPU 0; Agent B on physical GPU 1. No GPU pooling/layer split. |
| CPU affinity | A `0-2,6-8`; B `3-5,9-11` |
| Workload | `V100-PERFORMANCE-C2-128K-v1`; `bench/workloads/v100-performance-v1.json` |
| Frozen manifest SHA-256 | `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca` |
| Actual input | A 126,967 tokens; B 126,968 tokens |
| Context & KV | `--max-context 131072 --kv int8 --kv-resident 32768` |
| Default runtime arguments | `--expert-cache auto --prefill auto --spec 4 --spec-min-p 0.5 --mmap-experts` |
| Model assets | Original pinned GSQ-RCO GGUF for **each quantization**, its matching native pack, tokenizer, and shared read-only MTP; never swap quantizations within the same arm |
| C2 validity | Fresh Strata processes; no prompt-prefix reuse (`cache_n=0`, `cached_tokens=0`); synchronized dual-agent start, meaningful simultaneous decode, at least 1,024 output tokens per agent, stop/health checks |
| Repetitions | **3 valid fresh-process C2 batches per selected arm**; failures retained and labeled, not counted as successful runs |
| Hardware | Keep existing power limits and clocks unchanged during Stage 7; report observed condition and any mismatch versus historical records |

Use archived Stage 4–6 measurements as **historical references**. **Do not rerun 0.1.47/0.1.50/fork solely to create a new baseline**. Different GPU clock and Linux page-cache conditions must be disclosed when interpreting deltas; a cross-date comparison is not a controlled causal effect.

A no-prefix-reuse C2 request can still benefit from the Linux filesystem page cache and GPU expert cache. Capture page-cache residency, swap, major faults, storage I/O and expert hit rates. Treat Strata's logical `file_mb` counter as distinct from physical disk reads.

## 3. Stage 7 experiment registry

Each model gets its **own** arm IDs and results. Do not flatten all model variants into one universal switch recipe or interpret the run count below as the complete Stage 7 quota.

### 3.1 IQ3_XXS: candidate 0.1.54 optimization matrix

All rows use the **same upstream 0.1.54 binary** and the frozen IQ3_XXS assets. Options not listed are inherited from the pinned new-engine baseline; verify effective environment at process startup.

| ID | Upstream engine | Runtime override | Historical reference | C2 batches | Status |
| --- | --- | --- | --- | ---: | --- |
| S7-XXS-1 | 0.1.54 | Vanilla: no experimental switch forced | Stage 5 T1 (0.1.47 vanilla) | 3 | COMPLETED 3/3 (2026-11-01) |
| S7-XXS-2 | 0.1.54 | `STRATA_SELECT_SIMT=1` | Stage 5 T2 | 3 | COMPLETED 3/3 (2026-11-01) |
| S7-XXS-3 | 0.1.54 | `STRATA_PF_WMMA=1` | Stage 5 T3 | 3 | COMPLETED 3/3 (2026-11-01) |
| S7-XXS-4 | 0.1.54 | `STRATA_SELECT_SIMT=1 STRATA_PF_WMMA=1` | Stage 5 T4 | 3 | COMPLETED 3/3 (2026-11-01) |
| S7-XXS-5 | 0.1.54 | `STRATA_STAGER_SSD=0` | Stage 5 T6-Fixed is 0.1.50, not a same-engine match | 3 | COMPLETED 3/3 (2026-11-01) |
| S7-XXS-6 | 0.1.54 | `STRATA_SELECT_SIMT=1 STRATA_PF_WMMA=1 STRATA_STAGER_SSD=0` | Stage 5 T8 (0.1.50) | 3 | COMPLETED 3/3 (2026-11-01) |
| S7-XXS-7 (conditional) | 0.1.54 | `STRATA_SELECT_SIMT=1 STRATA_PF_WMMA=1 STRATA_PF_WMMA2=1 STRATA_STAGER_SSD=0` | Exploratory; **not** a reproduction of the fork's T7-Fixed | 3 | NOT AUTHORIZED / OPTIONAL |

**S7-XXS-1 through S7-XXS-6 completed 18/18 valid C2 batches; S7-XXS-7 remains optional / not run.** This is an **IQ3_XXS submatrix**, not the whole Stage 7.

Notes:
- S7-XXS-2 intentionally preserves T2's single SIMT override; do **not** quietly force `STRATA_STAGER_SSD=0` in that arm. Stager intervention belongs in separate arms. New 0.1.54 default behavior still may differ; record it.
- The old Stage 5 **T7 / T7-Fixed** use `jmnargi/Strata-V100@2c9b1dd`, its own scheduling/kernels and `STRATA_SM70_PERF` semantics. They cannot be recreated just by copying environment variables into upstream 0.1.54.
- `STRATA_PF_WMMA2=1` must be source- and log-verified as actually applicable to IQ3_XXS before treating S7-XXS-7 as an optimization result.
- Stage 5 T2 historical per-agent 3-batch medians: prefill **1010.4 / 1019.2 tok/s**, decode **25.9 / 26.7 tok/s**, TTFT **125.91 / 124.86 s**, median batch wall **203.41 s**. T7-Fixed historical prefill **1030.7 / 1044.9**, decode **26.6 / 26.7 tok/s**. These were not all measured at the same GPU clock/page-cache condition. See [Stage 5 IQ3_XXS matrix](../artifacts/stage5-results-20261029/stage5-iq3xxs-matrix-summary.md) and [T7-Fixed receipt](../artifacts/stage5-results-20261029/stage5-iq3xxs-t7fixed-summary.md).

### 3.1a IQ3_XXS additional optimization arms (EXECUTED 2026-11-01)

See [Stage 7 IQ3_XXS optimization extension](STAGE7_IQ3XXS_OPT_PLAN.md) and the [S7-XXS-8..13 result report](../artifacts/stage7-results-20261101/stage7-iq3xxs-opt-report.md): S7-XXS-8..13 (SIMT2, GDN recurrence, INT8 KV gather, SM70_TABLE, prefill 4096, and confirmed combination S7-XXS-13). **17 scored C2 batches + 1 non-scored diagnostic, all mechanical PASS**; S7-XXS-12 was stopped by the operator after 2 batches. Same-session results: SIMT2 prefill −0.3%; GDN_REC_WARP=2 within noise (numerics changed, quality unchecked); Q8_GATHER_WIDE=0 no measurable effect; SM70_TABLE=1 the only consistent signal (−1.4 to −2.0% decode time on identical-output pairs); prefill 4096 −36.7% prefill. S7-XXS-13 confirmed SIMT=1 + SM70_TABLE=1 across 3 batches with <0.06% prefill variance vs S7-XXS-11. Cross-date comparisons against archived S7-XXS-2 show a common-mode shift and are not causal. The existing 18/18 completed runs and `scripts/97-stage7-iq3xxs-c2.sh` are preserved. No promotion. Stage 7 remains an engine-level multi-quantization evaluation.

### 3.1b IQ3_XXS selective V100 source ports (COMPLETED / CLOSED)

[S7-XXS-14 / 15 / 16 definition](STAGE7_IQ3XXS_FORK_PORT_PLAN.md) completed **9/9 valid C2 batches, three per arm**, on 2026-11-01; [execution report](../artifacts/stage7-results-20261101/stage7-iq3xxs-14-16-report.md), [source/build audit](../artifacts/stage7-results-20261101/stage7-iq3xxs-port-source-audit.md).

- **14:** unchanged pinned upstream 0.1.54, SIMT+SM70+WMMA. Prefill medians 997.6 / 1006.6, decode 26.4 / 26.2 tok/s.
- **15:** separately pinned 0.1.54-derived IQ3_XXS WMMA2 port. Prefill 961.2 / 969.6, decode 26.3 / 26.1.
- **16:** separately pinned 15+LEAN allocation/index adaptation. Prefill 990.8 / 998.7, decode 26.4 / 27.0. Loan slots reduced 2489→2173.

Source, CUDA12/sm_70 compilation, parity and instrumented fresh 128K checks passed before enabling scored IDs in runner 100. Page-cache/swap differences and output/MTP variation prevent a causal throughput-win claim. No quality suite or promotion. **Do not rerun or reuse any 14–16 ID.** This closes only this IQ3_XXS subtrack, not multi-quantization Stage 7.

### 3.2 IQ2_XS: engine-upgrade assessment (model-specific)

Select a compact 0.1.54 matrix based on Stage 4-B vanilla and Stage 4-C `STRATA_SM70_TABLE=1` evidence. Begin with 0.1.54 vanilla and then test only source-compatible, IQ2_XS-relevant switches, e.g. SM70 table or SIMT, each in isolated arms. Use 3 valid C2 batches per selected arm. Do **not** transpose IQ3_XXS's six-arm matrix automatically. Archived Stage 4-C means (**995.70 tok/s prefill; 39.60 tok/s decode**) are one-batch comparisons, not 3-run medians.

### 3.3 IQ3_S: engine-upgrade assessment (model-specific)

If original IQ3_S files can be safely restored from the existing archive, use its Stage 5 T1/T2/T3/T4/T6/T8/T7-Fixed evidence to choose applicable 0.1.54 vanilla, SIMT, WMMA and SSD-stager arms. Use 3 valid C2 batches per selected arm. Stage 6 is **closed**; do not reopen or rename its results as Stage 7. The latest recorded model relocation left roughly 79 GiB free on `/srv/models` while the IQ3_S tree occupied approximately 80 GiB; **recheck actual space, archive hashes and service consumers before copying anything**. Do not delete other model assets to make room without separate approval.

### 3.4 UD-Q4_K_XL and future quantizations

Optional; use a separately documented memory/capacity gate and model-specific 0.1.54 feasibility recipe before a 3-batch C2 commitment. A startup/health-only smoke is **not** an equivalent 128K C2 result. Report failures and resource limits rather than silently omitting the model.

## 4. Build and execution gates

1. **Preflight only** before any build: inspect running Docker containers, GPU occupancy, ports 8080/8081, host RAM/swap, actual GPU clocks/power caps and accessible model assets. Never assume a GitHub snapshot proves current P520 state.
2. Build upstream Qwen **0.1.54** from a **pinned SHA** with the existing CUDA 12.9.1 Volta-compatible approach: `-DSTRATA_ENABLE_CUDA=ON -DSTRATA_EXPERIMENTAL_SM60=ON -DCMAKE_CUDA_ARCHITECTURES=70`. **Never CUDA 13 for V100**. Use a **new image tag**, e.g. `strata-v100-upstream:0.1.54`; the base tag is **built and pinned**, as recorded in the IQ3_XXS receipts; new candidate images still require unique tags. Verify the actual `strata` engine version, commit SHA, build flags, binary SHA and image ID.
3. Run an isolated 128K compatibility/health smoke for each candidate quantization before timed C2; failures do not count as C2 success.
4. Create **new Stage 7-only** configs/containers/logs and test ports; verify CPU affinity, physical GPU mapping, model hashes and effective flags. Do not repoint ThinkPad 18080/18081 or P520 serving 8080/8081.
5. Execute each selected arm as **three valid fresh-process dual-agent C2 batches**. Capture A/B metrics independently, per-run counts, medians/ranges, batch wall, overlap, stop reasons, GPU/CPU telemetry, page cache, swap and I/O, and status.
6. Report **both** within-0.1.54 switch comparisons and labeled cross-version **historical** comparisons. Do not claim a quality gain from C2 mechanical pass alone; run a separately labeled agent/tool-call quality suite if appropriate.
7. Publish sanitized per-model results under a new `artifacts/stage7-results-<YYYYMMDD>/` tree, preserving full raw records locally where required. Proposed configs and scripts must use Stage 7 naming and must not overwrite existing stages.
8. Choose whether to promote a version/quantization only in a **separate explicit decision** after results and rollback checks. This planning document does **not** permit stopping existing agents, running builds/tests, restoring models or changing the live service.

## 5. Selection and reporting

A result is usable only with passing contract checks, 3 valid repetitions per selected arm, no hidden stager/cache collapse, and clean post-health. Score **prefill, decode, TTFT, batch wall, consistency and host stability together**. The engineering targets (e.g. passing IQ3_XXS T2's ~1,015 tok/s prefill without losing ~26 tok/s decode) are **reference thresholds**, not predicted 0.1.54 gains. Keep throughput figures **per agent**, not summed across two servers.

Record one row per model + arm, with engine SHA, quantization, effective runtime overrides, A/B prefill and decode medians, A/B TTFT, batch-wall median, 3-run pass/fail, cache/I/O notes and historical-reference caveat.

**Stage 7 can finish with 'no upgrade'** if upstream 0.1.54 is not better for a candidate; the purpose is a reproducible engine evaluation across models, not automatic promotion.

## 6. Status register

| Work item | Status |
| --- | --- |
| Stage 7 scope defined as upstream Strata 0.1.54 validation across quantizations | DOCUMENTED |
| 0.1.54 source SHA, binary build and dedicated image | BUILT; image/source IDs recorded in IQ3_XXS final report |
| IQ3_XXS S7-XXS-1 to S7-XXS-6 | COMPLETED (18/18 valid C2 PASS) |
| IQ3_XXS S7-XXS-8 to S7-XXS-13 | EXECUTED (8–11 & 13: 3/3 PASS each; 12: 2/2 PASS, stopped early; diagnostic non-scored PASS) — [report](../artifacts/stage7-results-20261101/stage7-iq3xxs-opt-report.md) |
| IQ3_XXS S7-XXS-14 | **COMPLETED 3/3 C2 PASS** — [report](../artifacts/stage7-results-20261101/stage7-iq3xxs-14-report.md); IDs closed |
| IQ3_XXS S7-XXS-15 / S7-XXS-16 | **COMPLETED 3/3 C2 PASS each** — pinned separate source-port images; [report](../artifacts/stage7-results-20261101/stage7-iq3xxs-14-16-report.md); IDs closed |
| IQ2_XS model-specific 0.1.54 matrix | CANDIDATE, NOT RUN |
| IQ3_S model-specific 0.1.54 matrix | CANDIDATE, REQUIRES ASSET CHECK |
| UD-Q4_K_XL additional feasibility | OPTIONAL, NOT RUN |
| Quality tests, deployment selection and final report | NOT STARTED |

**Sources:** [Strata v0.2.8 release](https://github.com/Niko1221/Strata/releases/tag/v0.2.8) · [V100 upstream guide](https://github.com/Niko1221/Strata/blob/v0.2.8/docs/NVIDIA_V100.md) · [Stage 5 IQ3_XXS evidence](../artifacts/stage5-results-20261029/stage5-iq3xxs-matrix-summary.md) · [Stage 6 closure](STAGE6_FINAL_REPORT.md).
