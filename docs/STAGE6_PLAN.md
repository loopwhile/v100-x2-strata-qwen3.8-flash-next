# Stage 6 — IQ3_S dual-agent Decode 30+ optimization: complete execution plan

**Status (2026-10-28): CLOSED — all eight phases recorded; S6-7 candidate combination SKIPPED. Goal NOT MET.**
**Final result:** [Stage 6 final report](STAGE6_FINAL_REPORT.md). This is an **archived plan, not active work instructions**.
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
S6-1/S6-2 source investigation clarified runtime spec=6, mtp_max=4, lookup=3 under configured --spec 4: suffix drafting extends the verification window by two. See the [MTP receipt](../artifacts/stage6-results-20261028/s6-2-mtp.md).

## Eight-stage outcome matrix (retrospective)

| Phase | Status | Recorded evidence |
| --- | --- | --- |
| **S6-0** | COMPLETE: 3 valid C2 batches, A/B median 22.3/21.2 tok/s | [Baseline](../artifacts/stage6-results-20261028/s6-baseline.md) |
| **S6-1** | DIAGNOSTIC COMPLETE: CPU Expert / GPU waitCPU dominant | [Profile](../artifacts/stage6-results-20261028/s6-1-profile.md) |
| **S6-2** | SCREENED: 5 MTP candidate batches; no confirmed winner | [MTP](../artifacts/stage6-results-20261028/s6-2-mtp.md) |
| **S6-3** | SCREENED: 6 decode-kernel candidates; no confirmed winner | [Kernels](../artifacts/stage6-results-20261028/s6-3-kernels.md) |
| **S6-4** | SCREENED: 3 SM70 candidates; no confirmed winner | [SM70](../artifacts/stage6-results-20261028/s6-4-sm70.md) |
| **S6-5** | SCREENED: 2 CPU/PCIe candidates; no confirmed winner | [CPU/PCIe](../artifacts/stage6-results-20261028/s6-5-cpu-pcie.md) |
| **S6-6** | NO VALID WINNER: 1 invalid C2 + 1 startup VRAM-plan failure | [KV/cache](../artifacts/stage6-results-20261028/s6-6-cache.md) |
| **S6-7** | SKIPPED: assessment only; **no combined or 3-batch candidate run** | [Assessment](../artifacts/stage6-results-20261028/s6-7-assessment.md) |

Stage 6 is **closed with the 30 tok/s target unmet**. Only S6-0 has replicated Stage 6 dual-agent C2 evidence. Later measurements are largely one-batch screens, not statistically validated speedups, and do not establish any universal performance ceiling. No production promotion occurred.
## Original test methodology (archived; not active)

1. **Preflight on both hosts:** clean `git status`, `git pull --ff-only` when safe; verify source hashes, both GPU power caps 150W, ports, running processes, Stage 6 container definitions, same inode/model files, host RAM/swap and model file page-cache residency. Do not clear cache, rebuild images, restart preserved production containers or change power caps.
2. **Candidate isolation:** use `scripts/93-stage6-prepare-arm.py` to create candidate A/B JSON configs in gitignored `results/stage6/arms/<arm-id>/`. Both get identical serving args and optional flags; source model is unchanged. Use `STRATA_S6_ARM_DIR="$PWD/results/stage6/arms/<arm-id>" bash scripts/88-start-stage6-agents.sh both` when the Stage 6 names are absent. Prior arm teardown: `89-stop` then **explicit** `92-remove-stage6-only.sh --confirm-stage6-only` (Stage 6 names only). Do not ever use `docker rm -f` on production/preserved containers.
3. **S6-1 diagnostic:** create `s6-1-profile` arm with the two profiling flags; run `bash scripts/91-bench-stage6-c2.sh s6-1-profile 1 --diagnostic`. This records frozen workload data but is **not a scored performance comparison**. Analyze its local logs (no Git commit of raw prompts/tokens/logs). Source-verify what runtime MTP stats count.
4. **Screening:** optional short-prompt A+B tests identify obviously regressing flags, but **do not equate short-context results to 128K C2**. Relevant candidates must pass at least one frozen dual C2 batch, then 3 fresh-process replications. Profile flags must be **absent** from scored runs.
5. **Order/noise control:** interleave control and candidate where practical (A/B/A/B), document cache warmth and clocks, record per-agent statistics and acceptance. A and B from one batch are two agents **not two independent statistical replicates**. Capture engine hash, actual Docker image ID, candidate JSON SHA, effective flags, generated lengths/hashes.
6. **Hard correctness/safety gates:** both /health loaded with context 131072; zero reused prefix in scored runs; minimum 1024 output tokens; both have active decode overlap; post-health; no OOM, massive major faults, swap thrashing or persistent regressions. The official C2 harness verifies mechanical and overlap but is **not a semantic coding-quality test**; run separate task-quality checks on promising candidates.
7. **Win/stop rules:** baseline ~21.45 tok/s A/B mean is a reference. Candidate advances only if improvement exceeds batch variability and both agents remain healthy; do not select on mean alone if one GPU regresses. For S6-7, all **six per-agent observations across >=3 independent valid dual batches** must each be >=30 tok/s. Report prefill degradation separately; aim to retain ~899 tok/s Stage 5 reference, but decode 30+ remains primary objective.
8. **Records:** no invented measurements or optimistic gain percentages. `artifacts/stage6-results-20261028/s6-baseline.md` is immutable historical evidence; append distinct S6-1...S6-7 summaries under `artifacts/stage6-results-20261028/` using [result template](STAGE6_RESULT_TEMPLATE.md). Preserve raw `results/` locally (gitignored).

## Original proposed arms (historical; see result receipts for actual tests)

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

## Stage 6 document chain and closure

Read in order: **[final report](STAGE6_FINAL_REPORT.md)** → [recorded results](../artifacts/stage6-results-20261028/) → **this archived plan** → [historical Codex handoff](STAGE6_CODEX_HANDOFF.md) → [container/port safety prep](STAGE6_PREP.md) → [S6-0 completed receipt](../artifacts/stage6-results-20261028/s6-baseline.md) → [results template](STAGE6_RESULT_TEMPLATE.md).

**CLOSED:** S6-1 was performed, S6-2 through S6-6 results were recorded, and S6-7 combination was skipped due to no verified winner. Future investigations require a new scope; do not resume experiments based on this archived plan.
