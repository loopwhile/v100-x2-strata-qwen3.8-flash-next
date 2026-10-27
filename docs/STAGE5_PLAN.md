# Stage 5 — IQ3_S software-only optimization test plan

Status: **PLAN ONLY — no tests run, no containers deployed, no engine promoted**  
Created: 2026-10-27 (Asia/Seoul)  
Target: Lenovo ThinkStation P520, Xeon W-2135 (6C/12T), 64 GB DDR4-2400 ECC (~61 GiB usable), 2 × Tesla V100 16 GB (sm_70; 150 W caps).  
Scope: **Qwen3.8-Flash-Next GSQ-RCO IQ3_S**, two **independent** 131,072-context coding agents, one physical V100 per agent.

> The seven entries below are **experiment types, not seven individual C2 runs**. T4 (combined flags) is conditional; repeated runs and the T5 single-agent controls require additional individual batches. No speed or quality gain is claimed by this plan. The production-oriented IQ2_XS recommendation and preserved service remain unchanged.

## 1. Objective and evidence

**Objective:** Determine whether IQ3_S can improve its 128K prompt ingestion while keeping the Stage 4-B decode gain on the existing hardware, without a RAM/GPU/power upgrade or changes to the operational network tunnel.

| Archived IQ3_S result | Engine | Mean prefill | Mean decode | Mean TTFT | Expert hit |
| --- | --- | ---: | ---: | ---: | ---: |
| Stage 3-A | V100 fork 0.1.36 | 721.30 tok/s | 10.65 tok/s | 176.62 s | 75.45% |
| **Stage 4-B — reference** | Upstream 0.1.47, vanilla | **535.00 tok/s** | **21.35 tok/s** | **237.60 s** | **81.50%** |
| Stage 4-C | Upstream 0.1.47 + `STRATA_SM70_TABLE=1` | 468.05 tok/s | 20.55 tok/s | 271.60 s | 81.50% |

These numbers are arithmetic means of Agent A/B observations in **one dual-agent batch per configuration**, not independent replications. A different output length changes end-to-end wall time. An archived point is a historical reference, not proof of present throughput.

- [Stage 4-B IQ3_S report](../artifacts/stage4-results-20261021/stage4-b-iq3s-c2-benchmark-summary.md) and [raw summary](../artifacts/stage4-results-20261021/c2-stage4b-iq3s-run1-summary.json)
- [Stage 4-C IQ3_S report](../artifacts/stage4-results-20261021/stage4-c-iq3s-c2-benchmark-summary.md)
- [Stage 4 IQ3_S original configs](../artifacts/stage4-configs-20261021/iq3s/) and [C2 runner](../scripts/77-bench-stage4b-iq3s-c2.sh)

**Upstream evidence (not measured on this P520):**

- [Official V100 guide](https://github.com/Niko1221/Strata/blob/main/docs/NVIDIA_V100.md) describes `STRATA_PF_WMMA=1`, `STRATA_PF_WMMA2=1`, and other opt-in Volta kernels.
- [V100 fork PR #74](https://github.com/jmnargi/Strata-V100/pull/74) extends grouped WMMA2 to IQ3_S and measures a different single/split-GPU setup with shorter prompts.
- [V100 fork PR #80](https://github.com/jmnargi/Strata-V100/pull/80) reports a **12.2%** prefill-throughput gain from `STRATA_SELECT_SIMT=1` at 131,072 tokens **on a two-GPU layer-split V100 setup**, not dual independent 16 GB agents. This is evidence to test, not a P520 speed projection.
- [Strata 0.2.6 release](https://github.com/Niko1221/Strata/releases/tag/v0.2.6) ships **Qwen engine 0.1.50** (unchanged from app release 0.2.5); do not confuse it with the separate DeepSeek 0.1.51 engine.
- [Stager regression issue #1353](https://github.com/Niko1221/Strata/issues/1353) documents a past RAM-versus-SSD profile regression and a subsequent 0.1.41 fix. It does **not** establish that 0.1.47 has the same bug.

**Important distinction:** the previous IQ3_XXS + IQ2_XS *mixed-quantization* failure (major faults, swap and no decode overlap) cannot be assigned automatically to homogeneous IQ3_S ×2, whose containers may share file-backed GGUF pages. Measure page residency and actual physical reads before calling RAM shortage the cause. Strata `file_mb` is a logical tier counter and is **not** equivalent to NVMe bytes read.

## 2. Frozen contract and non-negotiable constraints

Keep the following fixed in primary T1–T4/T6/T7 arms unless an explicitly named diagnostic varies one field:

| Item | Frozen configuration |
| --- | --- |
| Quantization/assets | Original IQ3_S GSQ-RCO GGUF shards, existing native pack, tokenizer, expert profile and read-only shared MTP |
| Topology | Independent Agent A on host GPU 0, Agent B on host GPU 1; **no layer split between GPUs** |
| CPU affinity | A: `0-2,6-8`; B: `3-5,9-11` |
| Context / KV | `--max-context 131072 --kv int8 --kv-resident 32768` |
| Expert / prompt | `--expert-cache auto --prefill auto --mmap-experts` |
| Speculation | `--spec 4 --spec-min-p 0.5`, existing MTP |
| Baseline kernel policy | Upstream 0.1.47 defaults; **do not** enable `STRATA_SM70_TABLE=1` in the primary arms |
| Frozen workload | `V100-PERFORMANCE-C2-128K-v1` |
| Manifest path | `bench/workloads/v100-performance-v1.json` |
| Manifest SHA-256 | `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca` |
| Request constraints | A: 126,967 input tokens; B: 126,968; output reserve 4,096, minimum 1,024 generated per agent |
| Concurrency | Shared launch barrier; fresh processes; zero prefix reuse; meaningful *simultaneous decode*; post-run health |
| Hardware policy | 150 W existing GPU power caps; no clock, power, driver, RAM, GPU, PSU or thermal-policy changes |

**Preservation rules:**

1. Do not stop a live IQ2_XS serving agent, occupy its GPU, or claim ports 8080/8081 without a separately approved test window. First inspect `docker ps`, `docker inspect`, port listeners, mounted configs and GPU usage. The repo cannot prove what is running now.
2. Never remove/recreate/overwrite `strata-jmn-iq2xs-agent-a/b`, Stage 3/4 historical containers, original engine images, GGUF/model packs, existing configs, logs, saved results or ThinkPad `strata-tunnel.service`. Do not retarget 18080/18081 or P520 8080/8081.
3. New builds, configs, scripts and result directories must have dedicated Stage 5 names. Pin every source commit and record engine binary SHA, Docker image ID, effective env/args and model asset hashes. Build with CUDA 12.x, `sm_70`, `STRATA_EXPERIMENTAL_SM60=ON`; **do not compile Volta with CUDA 13**.
4. Do not run `docker rm -f` against preserved containers, destructive `git reset`, `docker system prune`, `drop_caches` or swap-reset commands as a shortcut for clean measurements.
5. Plan/documentation work does not authorize test execution, downtime, production promotion or changing GPU power settings. Promotion requires a separate decision.

## 3. Seven planned experiment types

| ID | Test | Exact experimental contrast | Primary decision |
| --- | --- | --- | --- |
| **T1** | Stage 4-B IQ3_S baseline repeat | 0.1.47 vanilla unchanged, dual 128K C2; **three fresh-process batches** | Establish current baseline variability and resource bottlenecks |
| **T2** | QSA scorer | T1 + **`STRATA_SELECT_SIMT=1` only** | Measure 128K prefill/TTFT effect and numeric/quality drift |
| **T3** | Volta FP16 prompt experts | T1 + **`STRATA_PF_WMMA=1` only** | Determine whether V100 tensor-core expert GEMMs help IQ3_S |
| **T4 (conditional)** | Combined scorer + WMMA | T1 + **both T2 and T3 flags only**, if isolated arms justify | Test interaction; improvements are not additive by assumption |
| **T5** | One agent versus simultaneous two | Same 0.1.47 recipe, run A alone and B alone, then both together | Separate host CPU/RAM/page-cache/SSD/PCIe contention from engine effects |
| **T6** | Official newer Qwen engine | Isolated upstream **Qwen 0.1.50** versus T1 using frozen assets/configs | Measure version-level improvement/regression; confirm release and exact commit at build time |
| **T7** | Updated Volta fork | Isolated latest selected **jmnargi/Strata-V100** commit versus T1 | Measure IQ3_S-capable WMMA2 and fork improvements with identical topology/workload |

T2/T3 flags must be injected into **newly created** test containers, e.g. Docker `-e STRATA_SELECT_SIMT=1`. `docker start` of an existing container will not change its environment. Verify the flags actually reached the Strata process; a configured flag with an inapplicable kernel is not a valid optimization test.

**T4 go/no-go:** run only if at least one isolated option has a repeatable practical improvement and neither produces unacceptable errors or quality regressions. Otherwise document T4 as **SKIPPED (gate not met)**. Keep the seven-type register intact.

**T5 controls:** compare each agent on its **same GPU and cpuset** with and without concurrent peer; do not double the single agent's CPU set or migrate it to another GPU. Record A-only/B-only independently and an A+B concurrent control. A change in shared Linux page-cache warmth must be logged, not mislabeled as a pure CPU effect. This diagnostic may need multiple additional batches beyond the seven numbered experiment types.

**T6/T7 source gates:** verify the version actually reported by the executable, source commit, pinned dependencies, model loading, CUDA 12.9.x and Volta kernel availability. In T7 inspect which WMMA2 switches are already default-on so T7 is not mislabeled as a clean single-flag ablation. The fork PR #74/#80 experiments use different topology and should not be copied as expected P520 gains.

## 4. Measurement method and diagnostics

1. **Preflight:** archive sanitized `git` status and branch SHAs; inspect live containers, port and GPU occupancy, disk free space, host RAM/swap, driver, power caps, effective A/B CPU affinities, engine version/flags and native-model paths. Confirm frozen workload hash before any run.
2. **Baseline first:** T1 runs three independent **fresh-process** C2 batches, not three requests against the same warmed conversation. Keep `cache_n=0` and `cached_tokens=0`. Do **not** assume zero prefix reuse implies a cold Linux filesystem page cache.
3. **Per experiment:** use a paired or interleaved A/B schedule where feasible (e.g., control–candidate–candidate–control), preserve request hashes/sampling settings, and repeat candidate batches **at least two to three times**. Compare per-agent rates, per-batch wall time and medians/spreads; Agent A and B within one batch are **not independent repetitions**.
4. **Capture:** prompt counts, generated counts, TTFT, prefill/decode tokens/s, request/batch wall time, true decode overlap, start skew, expert hit rate, cache slots, prefix reuse, MTP accept/offer counts if reported, GPUs' VRAM/compute/power/thermals, per-process CPU and I/O, host free/available RAM, swap deltas and **major faults**.
5. **Distinguish telemetry:** gather `vmstat 1`, `iostat -xz 1` when installed, `pidstat`/process fault counters, `free -h`, `/proc/vmstat`, container cgroup memory stats and GPU utilization. Correlate process faults and physical block I/O with engine file-tier counters. Treat physical I/O claims cautiously.
6. **Diagnosis separate from timed runs:** `STRATA_PREFILL_TIMING=1` can identify attention/expert/GDN/host-sync costs but adds profiling overhead. Time profiling **off** for formal comparisons. Source-verified `STRATA_STAGER_SSD=0`, `STRATA_STAGER_THREADS=4` are **secondary diagnostics only if T1/T5 indicate a stager/memory problem**, not default Stage 5 settings.
7. **Correctness:** all original C2 mechanical checks must pass (two loaded 128K services, valid counts, ≥1,024 outputs per agent, no prefix reuse, overlap, post-health). Add a fixed suite of real coding tasks/tool-call/JSON checks and record answer differences. FP16 WMMA and tiled scorer can change floating-point behavior: identical text is **not** required, but functional quality cannot be assumed.
8. **Stop/gate:** on major fault storms, swap thrashing, anomalous host instability, failing health/overlap, OOM or unexpectedly severe slowdowns, stop **only Stage 5 candidate services**, preserve the diagnostic logs, and review before retrying. Never automatically restart the preserved production pair or modify their resources.

Avoid using a single synthetic 128K cold request as the only representation of OpenCode's day-to-day latency: after the strict C2 comparison, report a **separately labeled** warm multi-turn agentic workload (prefix reuse, incremental 0–3K reads and long-output code generation). Do not blend warm-cache numbers with C2 scores.

## 5. Success criteria, results and optional second-pass tuning

**Engineering goal (not a forecast):** improve repeatable dual-agent IQ3_S prefill from the archived 535 tok/s toward an initial **600 tok/s** milestone, while preserving approximately **21.35 tok/s** decode (within measured run noise), lowering TTFT/end-to-end time, maintaining 128K context and passing stability/correctness gates. The 721 tok/s Stage 3-A prefill is a historical reference, **not** a guaranteed attainable 0.1.47/0.1.50 target.

- Judge improvements against **new T1 repeated data**, not merely the archived single-run mean. Report both A and B, batch wall, median, range, configuration differences and uncertainty; do not promote a 1–3% swing as established without reproducibility.
- A newer engine/fork should count as an improvement only if **overall task utility** (long 128K prompt plus meaningful generated output and agentic follow-up) is better, not because one metric improved while another collapsed.
- Record source/build receipt, frozen inputs and hash, test status (`PLANNED`, `RUNNING`, `PASS`, `FAIL`, `SKIPPED`), full logs and a sanitized summary per arm under a new `artifacts/stage5-results-<date>/` when testing actually occurs. Keep raw bulky records in gitignored `results/` unless intentionally curated.
- Do **not** promote any IQ3_S candidate to the existing IQ2_XS ports/service or change the ThinkPad tunnel in Stage 5.
- Only after T1–T7 diagnosis warrants it, start a **separate optional Phase 2** for one-variable-at-a-time `--kv-resident`, `--prefill`/ring, `--expert-cache`, stager/CPU worker settings, and `--spec`/`--spec-min-p`. Their values, safety, expected impact and experiment count are **not pre-approved or predetermined**.

## 6. Execution checklist (initial state)

- [x] T1 — 0.1.47 dual IQ3_S baseline (3 batches: Cold 703.3 tok/s, Warm 759-771 tok/s, Decode 21.45 tok/s, detailed telemetry captured)
- [x] T2 — `STRATA_SELECT_SIMT=1` alone (3 batches: Mean 879.0 tok/s, +18.1% prefill speedup, TTFT -26.3s, Decode 21.3 tok/s, PASS)
- [x] T3 — `STRATA_PF_WMMA=1` alone (3 batches: Mean 798.7 tok/s, +7.3% prefill speedup, TTFT -11.8s, 84.6s overlap, PASS)
- [x] T4 — combination: `STRATA_SELECT_SIMT=1` + `STRATA_PF_WMMA=1` (3 batches: Mean 887.4 tok/s, TTFT 143.4s, Decode 21.2 tok/s, PASS)
- [ ] T5 — A-only, B-only, A+B resource contention controls
- [x] T6 — upstream Qwen 0.1.50 isolated source-pinned build and C2 (FAIL / SEVERE REGRESSION: 247.1 tok/s prefill, 514s TTFT, 34.6K major faults, 2.27GB swap thrashing; Gate stop triggered, containers cleanly stopped)
- [ ] T7 — latest selected jmnargi V100 fork isolated source-pinned build and C2
- [ ] Compare repeated results, record quality limitations and choose **no promotion** or propose a separately approved next step

**Plan status at creation:** No Stage 5 benchmarks have been run; no conclusions on Stage 5 performance, no Docker runtime settings changed.
