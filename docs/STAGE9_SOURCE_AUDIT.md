# Stage 9 — preliminary source review and pending P0 gates (2026-11-10)

**CLOSED — 2026-11-10. Source/build/assets/runtime gates passed; U1/D1/F1 each completed 3/3 concurrent 128K C2 (9/9). No promotion. [Final review](STAGE9_REVIEW.md).** See [Stage 9 plan](STAGE9_PLAN.md) for immutable protocol and candidate definitions.

| Repository / release | Source | Status |
| --- | --- | --- |
| Archived S7-XXS-14 | upstream 0.1.54 source **870aedd9e1ebe1c91f94da93b59af17729f6c5c0** | CLOSED, reference only |
| Niko1221/Strata **v0.2.13**, released 2026-11-09 | annotated release tag **fb57f7472c2ab4d176c216b30ed1d6b5e6132ef0** → app commit **d2f096475817d4666c364c820b0ca830f751cfc5** | engine is **0.1.59**; release tag says engine built from **712fec6b4** (abbreviated). Full engine source SHA **712fec6b4297c9cfd32ab43daaa2979a9aa01edf** resolved and checked out; binary SHA `ccca488231f12da422be4a80b5c7f165b7593f6388907cac92d3c3f0d4229031`, image `dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d`, actual `strata 0.1.59` |
| jmnargi/Strata-V100 latest main checked 2026-11-10 | **8b4c09bd3d9213b2d47880826c6e818c3140664d** (PR #96 merge, 2026-11-09) | fork engine documented **0.1.45.7**; use pinned commit, NOT moving main |
| Stage 8 upstream 0.1.57 | U1/C0/C1/C2/C3/M1/M2 completed | no verified all-metric upgrade or operation promotion |

Source links: [v0.2.13 release](https://github.com/Niko1221/Strata/releases/tag/v0.2.13), [V100 fork](https://github.com/jmnargi/Strata-V100), [fork V100 performance port PR #92](https://github.com/jmnargi/Strata-V100/commit/3819deaa606850f311f0dffc7be7bc68e8df4ea5), [fork split PR #94](https://github.com/jmnargi/Strata-V100/commit/862a6b6cc8225935e6cc294f106f6e2fe5cc5e59).

### Current P0 evidence (2026-11-10)

- ThinkPad `619ad2077e81cddcdb73b19f1dbcbdceca2c998f`; P520 `dbc9620be571835e793333d8d2349efd517a6a43` clean at entry. No remote Git reset/pull. Stage 9 files are transported into a separate ignored preparation tree.
- P520 live at 17:10 KST: zero running containers/GPU compute, 0 MiB VRAM each, 150 W; boot receipt confirms the 135–1110 MHz range. Historical serving pairs remain stopped; ThinkPad tunnel active.
- Upstream full engine SHA `712fec6b4297c9cfd32ab43daaa2979a9aa01edf`, CMake version 0.1.59, vendored `third_party/strata-ggml`; no old get_llama_cpp call in the upstream build. Fork CMake version 0.1.45.7.
- Pinned upstream `slots_of` with frozen 128K/int8/auto args and 16384 MiB estimates **4139 expert slots**, so `conf_for(cuda,4139)` returns **0.7**, spec **6**. This is the user-selected upstream default rule, not a confidence sweep; estimated slots are not measured engine allocation.
- D1 uses stock Q4_0-selector pack `qwen3.8-flash-next-dflash2.q4_0-selq4.pack`, 339694592 bytes, SHA256 `4a42b98220ea7880664002c8edda1563aecbae754b762a2e2f31b2b91ee93ecd`, prepared from pinned incoai revision `a22a1744e85c17364dcc54a6a420af7135d4c7f6`. Download/pack/hash gate passed; [preparation receipt](../artifacts/stage9-results-20261110/p0-build-preparation.json).
- Fork `nv_defaults.cpp` supplies WMMA2 and additional Volta switches. `w2_on()` requires value `1`, so explicit `STRATA_PF_WMMA2=0` bypasses the second tile dispatch and retains the first tile; other built-in fork defaults remain source behavior and will be recorded. These are not an engine-only causal isolation.
- Upstream `generate.cpp` enters FileExpertSource for explicit `--mmap-experts`; the arena fallback/load repair is not evidence of a decode improvement in this path.
- First preparation-only build `p0-20261110T171309` failed at CMake configuration because venv Ninja was not passed explicitly. No engine/inference/C2 ran. Corrected preparation `p0-20261110T171658` passed `CMAKE_MAKE_PROGRAM`, both builds and the offline/model/DFlash2 gates. Both attempts remain retained.
- [Pinned source excerpts and file hashes](../artifacts/stage9-results-20261110/source-evidence.json).

### Relevant confirmed code/release facts

- v0.2.13 ships **DFlash2 new auto-defaults for Strix Halo and high-memory Blackwell**, measured there, NOT on this IQ3_XXS dual-V100 configuration. It nevertheless has an explicit DFlash2 mode; verify manual V100 compatibility and run DFlash2 as the **mandatory S9-D1 candidate**.
- v0.2.13 drafting source says **one drafter per run**, MTP **or** DFlash2. For DFlash2, it documents **--draft dflash2, --draft-model PACK, --draft-fallback none**, an independent draft vocab/head, and typical non-Strix/Blackwell defaults **--spec 6 --draft-conf 0.35**. Effective runtime flags and pack hash, no MTP load, and nonzero DFlash2 activity are required. Never let Auto or a fallback invalidate D1.
- v0.2.13 fixes Linux expert arena **file-cache fallback** (PR #5531). This is primarily a load/fallback correction. It may not affect the existing **--mmap-experts** code path: P0 must trace it, and results cannot attribute a speedup to it without evidence.
- v0.2.13 changes source build layout to **cmake/backends** with **third_party/strata-ggml** (no llama.cpp download needed). Stage 8's old build helper is not prevalidated for 0.1.59. Confirm CUDA **12.x** / **sm_70**, actual source hash, cmake options, engine BUILD.json.
- V100 fork docs and CUDA source contain **STRATA_SM70_TABLE**, **STRATA_SELECT_SIMT**, **STRATA_PF_WMMA** paths; fork docs say **STRATA_PF_WMMA2 on by default on sm_70**, with explicit 0 disabling second tile. Original S7-XXS-14 had none of that port. P0 must check actual dispatch, not only shell env. Fork #94 targets GPU **layer split**, not the independent one-card-per-agent setup. Fork #96 is Unsloth Dynamic v3.1/Q5_0-specific; original GSQ-RCO IQ3_XXS remains unchanged.
- Stage 8 proved plain mmap had **zero useful pinned PCIe expert share**; adding resident budget caused high physical reads and degraded Prefill/TTFT, while async C3 lifted Decode but harmed balance. Do not copy S8 resident-budget/async tuning into Stage 9 arms without a separately authorized hypothesis.

### Original pre-execution checklist (resolved source/build receipts and execution notes below)

Full upstream 0.1.59 **engine** SHA; pinned build artifacts and effective flags on real P520; source/build parity and prompt path dispatch on V100; fork WMMA2 default correction and any additional default changes; DFlash2 official pack selection/hash, GPU VRAM headroom, startup and native draft metrics; actual live system/port/clock/cache/swap state. If a candidate cannot meet these gates, it is **SKIPPED with evidence**, not scored or substituted.

**P0 source/build/assets/offline gates PASS. Actual startup/dispatch/VRAM gates are checked separately before each arm scores.**

### Completed preparation and clock amendment

Both upstream and fork built under CUDA 12.9.1/sm70. Fork actual version `strata 0.1.45.7`, image `b390db7e6e2fc974c15c7683d7490477beff6955ffdf227c3f5cecced9a7e59d`, binary SHA `83f73ab0c7a9fc44af46e7ee5d5c505cc3bc1634ae452b185f2b62d29ce9eea9`. Both immutable images reproduced the original C2 calibration/hashes. All 15 original model/pack/tokenizer/MTP checksums passed.

DFlash2 preparation initially called the wrong helper name (`fetch` instead of source's `ensure`); the failed non-GPU preparation and corrected v2 remain retained. A nested drafter mount under the original read-only model tree failed safely before any process could start. D1 now aliases the same physical native pack at `/stage9-data/packs/iq3_xxs-native` and mounts only its new drafter at `/stage9-data/dflash2`; all original model/MTP mounts stay read-only. The actual pinned drafting transformer passed a no-GPU U1/D1 argument test: D1 selects the verified stock selector pack, vocab, spec6/conf0.7, no MTP option and fallback none.

First U1 `u1-20261110T173436` completed short startup requests, then the old telemetry predicate rejected observed 1245 MHz. The runner automatically stopped at 17:35:39 with zero scored C2. It is CLOSED and raw evidence is SHA-backed up (45 files), with a [preparation-only report](../artifacts/stage9-results-20261110/preparation-attempts/u1-20261110T173436/report.md). No manual stop/power/clock command was issued. The user explicitly instructed continuing at 1245 MHz; the new runner accepts observed clocks up to 1245 without altering hardware settings. New U1 ID `u1-20261110T173748` uses that scoped amendment. Historical clocks are a separate comparison caveat.


### Verified scored progress

- U1 `u1-20261110T173748`: 3/3 C2 PASS, [report](../artifacts/stage9-results-20261110/u1-20261110T173748/report.md), 185 raw backup files SHA-matched. Prefill medians 966.0/973.6, Decode 26.1/28.8, TTFT 131.67/130.67s. First cold/cache-sensitive batch retained (637.8/647.1 Prefill, ~42.8/47.6 GB engine-reported physical reads).
- D1 `d1-20261110T175220`: 3/3 C2 PASS, [report](../artifacts/stage9-results-20261110/d1-20261110T175220/report.md), 185 raw backup files SHA-matched. Exact same upstream image/binary as U1. Prefill 1026.5/1032.6, Decode 28.2/29.4, TTFT 123.92/123.21s. All actual child args have no --mtp, fallback none, pinned selector pack/vocab, spec6/conf0.7; loaded-head/no-MTP log and nonzero draft counters passed before and during scoring.
- DFlash2-specific activity is derived from engine DONE totals minus separately logged suffix drafts (no MTP/lookup-chain). Nonzero DFlash2 proposals exist in every scored A/B request. Exact totals and calculation method are in D1 receipts; acceptance is not semantic quality.
- F1 `f1-20261110T180620`: 3/3 C2 PASS, [report](../artifacts/stage9-results-20261110/f1-20261110T180620/report.md), 185 files SHA-matched. Prefill 960.0/909.8, Decode 26.3/26.0, TTFT 132.51/139.81s. WMMA2=0, exact immutable fork image/binary, 13 recorded built-in Volta defaults. No agent-added tuning stack.
- GPU means include load/shutdown; the user-approved observed clock envelope is up to 1245 MHz. The agent issued no clock/power/host/tunnel change. Final journal inspection found a separate host clock-policy change after initial inspection, as detailed below. Older 1110 MHz historical measurements and cold/warm cache differences prevent causal attribution to source or drafter alone. No promotion or semantic-quality suite.

### Final closure and host-clock receipt

The final service journal is **different from the initial journal**: at 17:14:21 both GPUs were set to 1245–1245; at 17:15:59 both were set to 135–1245. The source of these host operations is not identified by this audit; the agent issued no such command. The user later explicitly instructed continuing at 1245. All scored runs started after 17:38 and observed peaks <=1245. The final service definition and full journal are preserved in [final-host-check.json](../artifacts/stage9-results-20261110/final-host-check.json). Do not claim hardware state was globally unchanged from initial inspection or revert the current user-approved range.

The delivered preflight now checks the latest per-GPU application receipt, with a regression test rejecting an old 1110 match when a later 1245 receipt exists. Measurement snapshot hashes remain immutable in per-arm receipts; post-phase 1245 telemetry checks passed for all scored batches. No measurement was repeated for this guard correction.

F1's API server schedules a canonical next-turn prefix through its native decode-free idle-prefill worker (`serve/server.py` prefill/schedule_warm); all six scored main requests have one later GEN0 event. This is not another generated HTTP request. There is exactly one positive-generation engine request per scored phase, whose prompt had zero reuse. Physical I/O/KV extraction now selects that request; idle work remains in separate records and full-process resource means. Initial exports are retained in `preliminary-exports/`. Source excerpts and file hashes were added to the source-evidence receipt; no kernel/server source patch was applied.

Final scope: 9/9 PASS, no dual-agent 30 result, no quality validation or promotion. All 675 raw/preparation files SHA-matched; all 278 original containers and initial images preserved/stopped; original 15 assets unchanged after P0 hash verification. GPUs idle and tunnel active. All IDs closed; no future execution is authorized by the retained runners.
