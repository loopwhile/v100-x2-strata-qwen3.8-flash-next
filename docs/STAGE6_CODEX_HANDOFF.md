# Codex CLI — archived Stage 6 instructions (2026-10-28)

> **ARCHIVED / NOT AN ACTIVE TASK.** The Stage 6 experiment campaign is **CLOSED**. S6-0 was measured 3 times, S6-1 was profiled, S6-2..S6-6 screens are recorded, and **S6-7 combination and final candidate 3-batch validation were SKIPPED**. A/B 30 tok/s goal was **NOT MET**. Read [final report](STAGE6_FINAL_REPORT.md) and [original receipts](../artifacts/stage6-results-20261028/) before considering any new work.

The commands below document the **original S6-0..S6-7 execution plan** for reproducibility, **not authorization** to stop/remove containers, run benchmarks, or resume Stage 6. The [plan](STAGE6_PLAN.md) and [prep/safety](STAGE6_PREP.md) are archived. Future work requires a new approved experiment scope; historical production safety rules still apply.

## Archived preflight procedure (read-only until separately approved)

1. On ThinkPad checkout and `ssh p520` checkout, inspect `git status --short --branch` and `git log -1 --oneline`. Use `git pull --ff-only` only on clean branches and never overwrite uncommitted Codex changes.
2. Validate both candidate configs with `python3 -m json.tool` and scripts with `bash -n`.
3. Inspect existing containers/GPUs without modifying them. If `strata-s6-iq3s-agent-a/b` exist in stopped state from S6-0, **do not attempt `88-start` until Stage 6-only definitions are explicitly cleared**. `scripts/89-stop-stage6-agents.sh` stops Stage 6 only, `scripts/92-remove-stage6-only.sh --confirm-stage6-only` removes **stopped Stage 6-only containers**. Never modify any other name.
4. Keep current GPU0/GPU1, A/B CPU affinity, 64GB RAM, 150W caps, same IQ3_S and SSD. No layer split, power tweaking, original container deletion, Stage 5 result overwrite or changes to existing ThinkPad tunnel.
5. The previous P520 image ID / binary hashes are recorded in [S6-0](../artifacts/stage6-results-20261028/s6-baseline.md) and match the reference. Do not rebuild the pinned image.

## Historical S6-1 preparation (already completed; do not rerun automatically)

On P520 within the repository:

```bash
# Syntax check; no container changes
python3 scripts/93-stage6-prepare-arm.py --help

# HISTORICAL: S6-1 was already executed and recorded
python3 scripts/93-stage6-prepare-arm.py --id s6-1-profile \
  --env STRATA_DECODE_TIMING=1 --env STRATA_VERIFY_PROFILE=1

# After checking that only Stage 6 containers are stopped and clearing only those definitions:
bash scripts/92-remove-stage6-only.sh --confirm-stage6-only
STRATA_S6_ARM_DIR="$PWD/results/stage6/arms/s6-1-profile" bash scripts/88-start-stage6-agents.sh both
bash scripts/90-status-stage6-agents.sh

# Profiled C2: clearly identified as diagnostic, not a scored benchmark
bash scripts/91-bench-stage6-c2.sh s6-1-profile 1 --diagnostic

# Save the diagnostic and inspect logs under local results/stage6/logs/; record
# offered/accepted MTP drafts, tokens/window, ms/window and CPU/GPU/PCIe waits.
bash scripts/89-stop-stage6-agents.sh
```

If 128K profiling proves too expensive/unstable, record exactly why and collect safe shorter diagnostics with the same dual agents, but do not use short-input numbers as the Stage 6 final acceptance result.

## Historical S6-2 MTP arms (screened; no verified winner)

```bash
python3 scripts/93-stage6-prepare-arm.py --id s6-2-spec4-p07 --spec 4 --min-p 0.7
python3 scripts/93-stage6-prepare-arm.py --id s6-2-spec6-p05 --spec 6 --min-p 0.5
python3 scripts/93-stage6-prepare-arm.py --id s6-2-spec6-p07 --spec 6 --min-p 0.7
python3 scripts/93-stage6-prepare-arm.py --id s6-2-spec8-p05 --spec 8 --min-p 0.5
python3 scripts/93-stage6-prepare-arm.py --id s6-2-spec8-p07 --spec 8 --min-p 0.7
```

Baseline `--spec 4 --spec-min-p 0.5` is already measured in S6-0. Do not infer spec depth from raw runtime metrics until source verified. S6-2 winning arm needs >=3 scored C2 batches to advance.

## Historical S6-3/S6-4 kernel/SM70 arms (screened)

```bash
python3 scripts/93-stage6-prepare-arm.py --id s6-3-side-mixer --env STRATA_SIDE_MIXER=2
python3 scripts/93-stage6-prepare-arm.py --id s6-3-gu-swiglu --env STRATA_GU_SWIGLU=1
python3 scripts/93-stage6-prepare-arm.py --id s6-3-gr-up75 --env STRATA_GR_UP75=1
python3 scripts/93-stage6-prepare-arm.py --id s6-3-attn-daily --env STRATA_ATTN_DAILY=1
python3 scripts/93-stage6-prepare-arm.py --id s6-3-gr-norm --env STRATA_GR_NORM_FAST=1
python3 scripts/93-stage6-prepare-arm.py --id s6-3-argmax --env STRATA_ARGMAX_ROWS_SM70=1

python3 scripts/93-stage6-prepare-arm.py --id s6-4-sm70-table --env STRATA_SM70_TABLE=1
python3 scripts/93-stage6-prepare-arm.py --id s6-4-expdec --env STRATA_EXPDEC=1
python3 scripts/93-stage6-prepare-arm.py --id s6-4-adapt-overlap --env STRATA_ADAPT_OVERLAP=1
```

Source-verify individual switch support in pinned `jmnargi/Strata-V100@2c9b1dd` before trusting the results. `STRATA_SM70_PERF=0` remains on in every arm; it means the bundle is off, not that explicit individual flags cannot be enabled. Don't conflate bundle regression with every component's performance.

## Historical S6-5/S6-6 CPU/PCIe and cache tests (screened)

```bash
# Example only; change one dimension per arm, DO NOT change CPU affinity:
python3 scripts/93-stage6-prepare-arm.py --id s6-5-pcie-035 --pcie-frac 0.35
python3 scripts/93-stage6-prepare-arm.py --id s6-5-pool-2 --pool-workers 2
python3 scripts/93-stage6-prepare-arm.py --id s6-6-kv-24576 --kv-resident 24576 # HISTORICAL C2 FAIL: B output 937
```

A manually forced expert-cache count is an **experimental VRAM-capacity choice**, not a guarantee of more throughput. Check the engine's planner and GPU free memory before using one.

## Archived scored-run procedure (NOT an active instruction)

```bash
# <arm-id> is one existing directory under results/stage6/arms/.
# Ensure both GPU slots are available and no Stage 2–5/production GPU processes exist.
bash scripts/89-stop-stage6-agents.sh
bash scripts/92-remove-stage6-only.sh --confirm-stage6-only
STRATA_S6_ARM_DIR="$PWD/results/stage6/arms/<arm-id>" bash scripts/88-start-stage6-agents.sh both
bash scripts/90-status-stage6-agents.sh
bash scripts/91-bench-stage6-c2.sh <arm-id> 1
bash scripts/91-bench-stage6-c2.sh <arm-id> 2
bash scripts/91-bench-stage6-c2.sh <arm-id> 3
```

Only candidates that pass screening and all gates warrant three complete C2 runs; keep raw outputs in ignored `results/` and curated summarized evidence in `artifacts/stage6-results-20261028/`. If the screen fails or degrades, write a documented REJECT and proceed to the next arm.

For a diagnostic profile only, the wrapper requires `--diagnostic`; for formal C2 scores omit it. The wrapper detects the **actual config bind-mounted into Agent A/B** and records its hashes and container inspect; it will not quietly score a candidate with the baseline config path.

## S6-7 original finish-line (assessment only; candidate test SKIPPED)

Combine only winner settings from S6-2...S6-6, with a new arm ID. Use the same GPU/CPU/RAM/SSD topology and frozen 128K C2; >=3 independent valid concurrent batches; **both A and B must each be >=30 tok/s in each batch**. Compare prefill/TTFT, CPU and PCIe behavior, correctness/quality, wall time, and repeatability. Report any sub-30 partial improvement accurately, and do not promote/restart preserved production agents.

**CLOSED:** The Stage 6 result is recorded in the [final report](STAGE6_FINAL_REPORT.md). This archival handoff does not authorize new tests, container resets, production promotions, hardware changes or operations on the P520. Request a new, clearly scoped test approval before any further runtime action.
