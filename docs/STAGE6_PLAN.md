# Stage 6 — IQ3_S dual-agent Decode 30+ optimization: complete execution plan

**Status (2026-10-28): S6-0 COMPLETE; S6-1 through S6-7 PLANNED / NOT YET MEASURED.**
**Primary next action: S6-1 decode profiling**, not another S6-0 run.
**Scope:** two independent IQ3_S agents at once, A on GPU0, B on GPU1. Target **>=30 decode tok/s PER AGENT** in each of at least three valid concurrent C2 batches. Aggregate A+B throughput or single-agent throughput does **not** qualify. This is an engineering target, not a prediction.

## Fixed constraints — never trade away for apparent speed

- Lenovo ThinkStation P520; 2 x Tesla V100 16 GB at unchanged **150W/GPU**.
- Independent Agent A: GPU0, CPU cpuset `0-2,6-8`, host `127.0.0.1:18082`; independent B: GPU1, CPU cpuset `3-5,9-11`, host `127.0.0.1:18083`. Each uses its own CPU portion and its own GPU; both share 64 GB RAM, one NVMe SSD and the exact same physical IQ3_S model files/page cache.
- **No** layer split, GPU pooling, single-agent promotion, CPU repartition, hardware purchase, changes to power/clocks/PCIe, different quant, swap or cache-dropping tricks.
- Qwen3.8-Flash-Next GSQ-RCO **IQ3_S** pinned GGUF/native pack/MTP; context **131072**, INT8 KV, `--mmap-experts`, two simultaneous frozen C2 requests (126967/126968 prompt tokens, >=1024 output tokens per agent).
- Frozen C2 manifest SHA256 `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`.
- Preserved production and Stage 2–5 containers/images/logs, original ThinkPad `strata-tunnel.service`, 18080/18081 tunnel and P520 8080/8081 ports **must not be altered**. Stage 6 container reset is explicitly confined to Stage 6 names.
- Baseline engine image `strata-v100-jmnargi:2c9b1dd`, inspected P520 image ID `sha256:5b62fa861bbdb346f81b0b3edf88ee21396fb4e59795a14b2b092dfa2e4aa156`, engine SHA256 `f0da5abf41115c9c0707751ec940f0f1977d04c690b55713cd19b2b7ba815030`.
- Stage 5 T7-Fixed environment: `STRATA_SM70_PERF=0 STRATA_SELECT_SIMT=1 STRATA_PF_WMMA=1 STRATA_PF_WMMA2=1 STRATA_STAGER_SSD=0`. Baseline native args: `--spec 4 --spec-min-p 0.5 --expert-cache auto --prefill auto --kv-resident 32768` plus pinned common args.

## Existing S6-0 evidence — DO NOT RERUN AS A "PREPARATION" STEP

Codex committed [the three validated S6-0 runs](../artifacts/stage6-results-20261028/s6-baseline.md) at commit `8199e3b`.
All three frozen dual-agent C2 batches passed mechanical/overlap/post-health and no prompt-prefix reuse. The **A/B decode medians** across the three independent batches were **22.3 / 21.2 tok/s**. Warm prefill medians were **908.2 / 923.1 tok/s**; the cold first batch was notably slower, so record page-cache warmth explicitly. Stage 5 T7-Fixed historical **A/B mean** was 21.45 tok/s, but that is not a substitute for each agent's Stage 6 result.
A nuance for S6-1: config is `--spec 4`, while metrics showed `spec=6`, `mtp_max=4`, `lookup=3`. These runtime fields should be identified from pinned source/actual accepted-draft counters; **do not assume `spec=6` means the config silently changed to `--spec 6`**.

## Eight-stage test matrix (each row is a phase, NOT just one benchmark)

| Stage | State | Tests / controlled variable | Required deliverable / progression gate |
| --- | --- | --- | --- |
| **S6-0** | **COMPLETE** | T7-Fixed same 2-GPU/2-agent 128K C2; 3 fresh-process batches | Baseline [archived](../artifacts/stage6-results-20261028/s6-baseline.md). **Advance to S6-1**. |
| **S6-1** | TODO | Both agents, instrumented `STRATA_DECODE_TIMING=1`; optional `STRATA_VERIFY_PROFILE=1`, no scored profiling results | Quantify `tokens/window`, `ms/window`, MTP accepted/offered, GPU compute, waitCPU, waitB/PCIe, waitA/host, expert tier/cache, CPU/GPU contention, file staging, major faults. Baseline bottleneck attribution. |
| **S6-2** | TODO | MTP `--spec` `4,6,8` x `--spec-min-p` `0.5,0.7`; one candidate per arm; preserve MTP and 128K | Show actual acceptance/tokens/window and verify cost; confirm best candidate with 3 scored dual C2 batches; Stage 3-B spec8 produced almost no IQ3_S gain, so no assumed gain. |
| **S6-3** | TODO | Individual kernel flags `SIDE_MIXER=2`, `GU_SWIGLU=1`, `GR_UP75=1`, `ATTN_DAILY=1`, `GR_NORM_FAST=1`, `ARGMAX_ROWS_SM70=1`; optionally `Q8_GATHER_WIDE=0` after profile | Test **one flag at a time** against unchanged baseline; check version support, outputs, acceptance/noise; then interleave winning combinations. |
| **S6-4** | TODO | Separate likely regression-causing SM70 bundle flags `SM70_TABLE=1`, `EXPDEC=1`, `ADAPT_OVERLAP=1` while **keeping `SM70_PERF=0`** | Isolate T7 default bundle's 18.60 tok/s regression; record culprit(s) and avoid harmful combinations; do not re-enable full bundle indiscriminately. |
| **S6-5** | TODO, PROFILE-GATED | CPU pool-worker count / `--pcie-frac` / adaptive scheduling (one variable at a time **within existing 3-physical-core-per-agent cpusets**) | Show measured improvement in waitCPU/waitB versus added overhead; NO CPU-affinity changes. Skip without matching S6-1 bottleneck evidence. |
| **S6-6** | TODO, PROFILE-GATED | `--expert-cache` automatic vs bounded manual slots; `--kv-resident` limited alternatives while **preserving 131072 context and INT8 KV** | Measure real GPU slots, expert hit, VRAM reserve, PCIe/CPU waits, TTFT/decode. Stop on VRAM/OOM/cache-stager regressions. Skip unless justified by S6-1. |
| **S6-7** | TODO | Combine **individually validated** winners, keeping all fixed hardware and C2 rules | Interleaved control/candidate, >=3 independent fresh-process **dual-agent 128K C2** candidate batches, each A>=30 AND B>=30, active overlap, correctness, post-health, output>=1024; report mean/median/range and prefill/TTFT tradeoffs. No silent production promotion. |

Do **not** stop Stage 6 at S6-0. After S6-1, follow the next documented stages; if a phase is unhelpful, mark SKIPPED with evidence and continue to the next. Early stopping applies to **unsafe individual candidate arms**, not automatic abandonment of Stage 6. If 30+ is not achieved, preserve a justified best sub-30 recipe and complete the final engineering assessment.

## Test methodology

1. **Preflight on both hosts:** clean `git status`, `git pull --ff-only` when safe; verify source hashes, both GPU power caps 150W, ports, running processes, Stage 6 container definitions, same inode/model files, host RAM/swap and model file page-cache residency. Do not clear cache, rebuild images, restart preserved production containers or change power caps.
2. **Candidate isolation:** use `scripts/93-stage6-prepare-arm.py` to create candidate A/B JSON configs in gitignored `results/stage6/arms/<arm-id>/`. Both get identical serving args and optional flags; source model is unchanged. Use `STRATA_S6_ARM_DIR="$PWD/results/stage6/arms/<arm-id>" bash scripts/88-start-stage6-agents.sh both` when the Stage 6 names are absent. Prior arm teardown: `89-stop` then **explicit** `92-remove-stage6-only.sh --confirm-stage6-only` (Stage 6 names only). Do not ever use `docker rm -f` on production/preserved containers.
3. **S6-1 diagnostic:** create `s6-1-profile` arm with the two profiling flags; run `bash scripts/91-bench-stage6-c2.sh s6-1-profile 1 --diagnostic`. This records frozen workload data but is **not a scored performance comparison**. Analyze its local logs (no Git commit of raw prompts/tokens/logs). Source-verify what runtime MTP stats count.
4. **Screening:** optional short-prompt A+B tests identify obviously regressing flags, but **do not equate short-context results to 128K C2**. Relevant candidates must pass at least one frozen dual C2 batch, then 3 fresh-process replications. Profile flags must be **absent** from scored runs.
5. **Order/noise control:** interleave control and candidate where practical (A/B/A/B), document cache warmth and clocks, record per-agent statistics and acceptance. A and B from one batch are two agents **not two independent statistical replicates**. Capture engine hash, actual Docker image ID, candidate JSON SHA, effective flags, generated lengths/hashes.
6. **Hard correctness/safety gates:** both /health loaded with context 131072; zero reused prefix in scored runs; minimum 1024 output tokens; both have active decode overlap; post-health; no OOM, massive major faults, swap thrashing or persistent regressions. The official C2 harness verifies mechanical and overlap but is **not a semantic coding-quality test**; run separate task-quality checks on promising candidates.
7. **Win/stop rules:** baseline ~21.45 tok/s A/B mean is a reference. Candidate advances only if improvement exceeds batch variability and both agents remain healthy; do not select on mean alone if one GPU regresses. For S6-7, all **six per-agent observations across >=3 independent valid dual batches** must each be >=30 tok/s. Report prefill degradation separately; aim to retain ~899 tok/s Stage 5 reference, but decode 30+ remains primary objective.
8. **Records:** no invented measurements or optimistic gain percentages. `artifacts/stage6-results-20261028/s6-baseline.md` is immutable historical evidence; append distinct S6-1...S6-7 summaries under `artifacts/stage6-results-20261028/` using [result template](STAGE6_RESULT_TEMPLATE.md). Preserve raw `results/` locally (gitignored).

## Proposed arms (candidate names; NOT yet measured)

```text
S6-1: s6-1-profile                         flags: STRATA_DECODE_TIMING=1, STRATA_VERIFY_PROFILE=1; diagnostic
S6-2: s6-2-spec4-p05 (control), -spec4-p07, -spec6-p05, -spec6-p07, -spec8-p05, -spec8-p07
S6-3: s6-3-side-mixer, -gu-swiglu, -gr-up75, -attn-daily, -gr-norm, -argmax
S6-4: s6-4-sm70-table, -expdec, -adapt-overlap
S6-5: s6-5-pool-<n>, -pcie-<fraction>         ONLY if S6-1 identifies CPU/PCIe waits
S6-6: s6-6-cache-<n>, -kv-resident-<n>       ONLY if S6-1 identifies VRAM/cache misses
S6-7: s6-7-combined-<name>                   only passing winner flags/args
```

The complete recipe for generating these arms is in [Codex continuation handoff](STAGE6_CODEX_HANDOFF.md). Actual binary support and effective environment must be verified before attributing speedups to a flag. A candidate's performance **cannot** be inferred from the referenced fork's layer-split setup.

## Stage 6 document chain and next step

Read in order: **this plan** → [Codex handoff](STAGE6_CODEX_HANDOFF.md) → [container/port safety prep](STAGE6_PREP.md) → [S6-0 completed receipt](../artifacts/stage6-results-20261028/s6-baseline.md) → [results template](STAGE6_RESULT_TEMPLATE.md).

**NEXT: S6-1 diagnostic. Do not pause after S6-0 or ask to reproduce the already completed baseline unless new evidence shows its data invalid.**
