# Stage 9 — dual-V100 IQ3_XXS engine and drafter comparison

**Status: PLANNED ONLY — 2026-11-10 KST. No host tests, new images, C2 results, deployments, or service changes have been made by this commit.**

## Objective and reference selection

Find an operational recipe that improves **both agents'** Prefill, Decode, TTFT, GPU temperature, GPU power and stable 128K behavior over S7-XXS-14, without an important regression in any other criterion. A fast Decode result with significantly worse Prefill or TTFT is not an overall improvement. A minimum 30 tok/s Decode on **both** agents in each of three C2 batches is a stretch goal, not a predicted outcome.

**S7-XXS-14 stays the archived operational reference. NEVER remeasure, rename, resume or overwrite its closed experiments.** It used upstream engine 0.1.54 (commit 870aedd9e1ebe1c91f94da93b59af17729f6c5c0), source image SHA256 2095eed79b0038ef23d602a0490bf0d89c63ad8e84ace8654c5016b2a51d2246. Its three scored C2 batches all passed.

| Archived S7-XXS-14 result | Agent A / GPU0 | Agent B / GPU1 |
| --- | ---: | ---: |
| Prefill tok/s median | 997.6 | 1006.6 |
| Decode tok/s median | 26.4 | 26.2 |
| TTFT seconds median | 127.53 | 126.48 |
| Peak temperature °C (maximum of 3 runs) | 65 | 64 |
| Mean power W (mean of 3 full-lifetime means) | 81.84 | 85.38 |
| Peak power W (maximum of 3 runs) | 172.87 | 177.57 |

Sources: [S7-XXS-14 report](../artifacts/stage7-results-20261101/stage7-iq3xxs-14-16-report.md) and [raw receipt JSON](../artifacts/stage7-results-20261101/stage7-iq3xxs-14-16-receipts.json). Baseline **mean temperature** was not available in this summary; do not invent a value. Full-lifetime GPU means include model loading and shutdown.

Stage 8 already finished. S8-C1 (engine 0.1.57 + three pool workers) is the strongest **speed-oriented Stage 8 alternative**: Prefill 998.1/1007.2, Decode 26.2/28.3, TTFT 127.45/126.32. S8-C0 (without pool-workers 3) is the lower-CPU alternative: Prefill 997.2/1006.3, Decode 25.6/27.9, TTFT 127.57/126.42; whole-host CPU user utilization 27.1% against C1's 32.1%. Neither proves an all-metric advantage against S7-XXS-14. S8-C3 raised Decode to 29.0/28.7 but reduced Prefill to 820.5/825.0 and raised TTFT to 155.00/154.14 seconds: **not** a balanced operational winner. Do not rerun any Stage 8 arm. Source: [Stage 8 review](STAGE8_CONTINUATION_REVIEW.md) and [resource table](../artifacts/stage8-followup-results-20261107/summary.md).

## Frozen run contract

- Two **independent** one-GPU agents on P520 (no layer split, VRAM pool, batch slots, mixed quants): A GPU0/cpuset 0-2,6-8; B GPU1/cpuset 3-5,9-11.
- Original **Qwen3.8-Flash-Next GSQ-RCO IQ3_XXS** GGUF shards, native pack, tokenizer and MTP assets; no Unsloth or re-quantization. Model and binary/file SHA256s must be recorded.
- Each agent context 131072, INT8 KV, KV resident 32768, mmap experts, expert-cache auto, prefill auto; same original prefill/decode workload and CPU mapping.
- Reuse S7-XXS-14 flags **STRATA_SELECT_SIMT=1, STRATA_SM70_TABLE=1, STRATA_PF_WMMA=1**, and its MTP spec 4 / min-p 0.5 for **MTP arms**. Do NOT add Stage 8 C1/C2/C3/M1/M2 options, custom WMMA2/LEAN patches, new cache allocation or an unrequested combination.
- Original frozen 128K C2 manifest **bench/workloads/v100-performance-v1.json** SHA256 e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca; harness **bench/c2_v100_contract.py** SHA256 a8e42cc5a71421a7287618fd5be0332ae40f312426e4d243ce1c7619fdfc5246; prompt counts A 126967, B 126968; no prefix reuse.
- Preserve GPU **150 W** cap and **135–1110 MHz** SM clock range, existing host BIOS/power/swaps, historical Docker images, containers, results, files, ports 8080/8081 and ThinkPad tunnel/18080/18081. Use CUDA **12.x**, explicitly target Volta **sm_70**, unique image names and verified free non-serving ports.
- Valid scored batch: **fresh A/B engine processes**, two active simultaneous Decode streams, cache_n=cached_tokens=0, >=1024 output tokens **each**, finish_reason=stop **each**, full 128K/health, complete telemetry and saved raw artifacts. Exactly **3 scored C2 batches per selected viable arm**; never discard a cold batch or silently retry a failure. Maximum scored Stage 9 batches: **9**, no new S7 baseline runs.

## Candidate sequence

| ID | Exact intent | C2 |
| --- | --- | ---: |
| **S9-P0** | Source and host feasibility audit: resolve full source pins, CUDA12/sm_70 code paths, memory and startup safety; NO scored inference | 0 |
| **S9-U1** | **Upstream 0.1.59 + archived S7-XXS-14 recipe + explicitly MTP** (spec 4, min-p 0.5) | 3 |
| **S9-D1** | **The identical upstream 0.1.59 image as U1**, but select **DFlash2 instead of MTP** with an official SHA256-pinned compatible pack and verified live DFlash2 dispatch | 3 |
| **S9-F1** | **jmnargi/Strata-V100 at pinned commit 8b4c09bd3d9213b2d47880826c6e818c3140664d** + S7-XXS-14 MTP recipe (source engine documented 0.1.45.7) | 3 |
| **S9-R1** | Review results against S7-XXS-14 and U1/D1 internally, without automatic promotion | 0 |

**DFlash2 is mandatory to investigate, not optional.** For D1 choose DFlash2 explicitly rather than Auto; ensure the **MTP drafter is not loaded**; force **no DFlash2-to-MTP fallback**. Inspect startup args and logs for actual DFlash2 loading and nonzero drafter activity. Pin one appropriate official pack and SHA256. Draft settings differ intentionally from MTP: upstream typically uses spec 6 and draft confidence 0.35 for non-Strix/Blackwell GPUs; **verify actual engine defaults at P0**, record explicit effective spec/conf/draft-model/head and draft acceptance. If V100 16 GB cannot safely load/use it, record SKIPPED/FAILED with receipts, **never label MTP fallback as DFlash2 success**. D1 must collect **Prefill, Decode and TTFT**, not just Decode, plus full GPU and host resource metrics.

### Mandatory S9-P0 source gate

1. Resolve complete **0.1.59 engine source SHA** rather than assuming that the v0.2.13 app tag target is the engine commit. v0.2.13's annotated tag targets d2f096475817d4666c364c820b0ca830f751cfc5 (app/control); tag message says engine packages built from abbreviated 712fec6b4. Verify full engine-tree revision and BUILD.json before a build or scored run.
2. Upstream v0.2.13 changed the engine build to cmake/backends and bundled **third_party/strata-ggml**. Stage 8's 0.1.57 setup/get_llama_cpp builder is **not assumed compatible**. Produce a new auditable CUDA12 sm_70 image and startup proof; do not edit historical images.
3. Verify the **same three S7 flags** are accepted and actually route to expected Volta kernels on each engine. Fork documentation indicates **STRATA_PF_WMMA2 is enabled by default on sm_70**; S7-XXS-14 did **not** use that new port. F1 should force **STRATA_PF_WMMA2=0** only if source/dispatch confirmation shows it restores the reference path. Log all remaining unavoidable default/kernel changes, not merely flag names.
4. Inspect Linux Expert Arena load/fallback fix **PR #5531 / issue #5327**. Do not claim a Decode speedup if this exact **mmap-experts** path never executes the fix. No storage-policy change in the primary arms.
5. Confirm original pack/model/workload/harness checksums, independent GPU/CPU pinning, draft choice/pack, VRAM safety, Linux page cache/swap, temperatures, clock lock, port availability and live serving/GPU use. **Last Stage 8 host check was on Nov 7, not a current idle check.**
6. Log upstream/fork git source/binary hashes, Docker image ID, CUDA toolkit, effective engine args, drafter identity and dispatch proof to [source audit](STAGE9_SOURCE_AUDIT.md). If gate fails, mark candidate SKIPPED with a reason rather than fabricating three scored runs.

### Execution and reporting

A future **separately approved** execution must: inspect live host; create only isolated Stage 9 Docker images and owned containers; perform unscored startup/health/short output checks; run exactly three fresh A+B 128K C2 batches for each eligible arm; archive each unique ID at results/stage9/S9-ARM/unique-id with raw logs and SHA256 backups; stop only owned containers; review results before the next arm. Do not pre-run a baseline, conduct one-run speed screens, patch kernels, change stage scope, or auto-promote a winner.

Per **agent** and **batch**: Prefill tok/s, Decode tok/s, TTFT, wall time, output count/hash, overlap and validity, MTP/DFlash2 proposed/accepted and acceptance rate, draft/verify timing, Expert/KV hit rates, GPU temperature **mean+peak**, power **mean+peak**, SM/utilization and VRAM **mean+peak**, CPU utilization, RAM available/used/peak, swap in/out, major page faults, page cache and physical I/O. Separate full-process-lifetime averages from phase-only metrics. Keep the 3 individual batches, medians and ranges. Compare U1 against D1 (same engine), and compare each against archived S7; do not attribute cross-date cache/swap/output differences solely to engine code. Evaluate both agents **and the slower agent**, not averages only. Prefer a verified non-dominated balanced recipe; acceptable gains must not hide serious Prefill/TTFT/power/temperature regression. A mechanical C2 pass does not prove coding-agent/tool-call quality: separate quality validation is required before an eventual promotion.

**Stage 9 current scored results: none. GitHub plan creation alone does not authorize P520 operations.**
