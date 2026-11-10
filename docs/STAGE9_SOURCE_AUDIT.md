# Stage 9 — preliminary source review and pending P0 gates (2026-11-10)

**Preliminary public GitHub evidence only. P520 has NOT been inspected, no engines built or benchmarked.** See [Stage 9 plan](STAGE9_PLAN.md) for immutable protocol and candidate definitions.

| Repository / release | Source | Status |
| --- | --- | --- |
| Archived S7-XXS-14 | upstream 0.1.54 source **870aedd9e1ebe1c91f94da93b59af17729f6c5c0** | CLOSED, reference only |
| Niko1221/Strata **v0.2.13**, released 2026-11-09 | annotated release tag **fb57f7472c2ab4d176c216b30ed1d6b5e6132ef0** → app commit **d2f096475817d4666c364c820b0ca830f751cfc5** | engine is **0.1.59**; release tag says engine built from **712fec6b4** (abbreviated). Full engine source SHA and executable hash **not yet verified** |
| jmnargi/Strata-V100 latest main checked 2026-11-10 | **8b4c09bd3d9213b2d47880826c6e818c3140664d** (PR #96 merge, 2026-11-09) | fork engine documented **0.1.45.7**; use pinned commit, NOT moving main |
| Stage 8 upstream 0.1.57 | U1/C0/C1/C2/C3/M1/M2 completed | no verified all-metric upgrade or operation promotion |

Source links: [v0.2.13 release](https://github.com/Niko1221/Strata/releases/tag/v0.2.13), [V100 fork](https://github.com/jmnargi/Strata-V100), [fork V100 performance port PR #92](https://github.com/jmnargi/Strata-V100/commit/3819deaa606850f311f0dffc7be7bc68e8df4ea5), [fork split PR #94](https://github.com/jmnargi/Strata-V100/commit/862a6b6cc8225935e6cc294f106f6e2fe5cc5e59).

### Relevant confirmed code/release facts

- v0.2.13 ships **DFlash2 new auto-defaults for Strix Halo and high-memory Blackwell**, measured there, NOT on this IQ3_XXS dual-V100 configuration. It nevertheless has an explicit DFlash2 mode; verify manual V100 compatibility and run DFlash2 as the **mandatory S9-D1 candidate**.
- v0.2.13 drafting source says **one drafter per run**, MTP **or** DFlash2. For DFlash2, it documents **--draft dflash2, --draft-model PACK, --draft-fallback none**, an independent draft vocab/head, and typical non-Strix/Blackwell defaults **--spec 6 --draft-conf 0.35**. Effective runtime flags and pack hash, no MTP load, and nonzero DFlash2 activity are required. Never let Auto or a fallback invalidate D1.
- v0.2.13 fixes Linux expert arena **file-cache fallback** (PR #5531). This is primarily a load/fallback correction. It may not affect the existing **--mmap-experts** code path: P0 must trace it, and results cannot attribute a speedup to it without evidence.
- v0.2.13 changes source build layout to **cmake/backends** with **third_party/strata-ggml** (no llama.cpp download needed). Stage 8's old build helper is not prevalidated for 0.1.59. Confirm CUDA **12.x** / **sm_70**, actual source hash, cmake options, engine BUILD.json.
- V100 fork docs and CUDA source contain **STRATA_SM70_TABLE**, **STRATA_SELECT_SIMT**, **STRATA_PF_WMMA** paths; fork docs say **STRATA_PF_WMMA2 on by default on sm_70**, with explicit 0 disabling second tile. Original S7-XXS-14 had none of that port. P0 must check actual dispatch, not only shell env. Fork #94 targets GPU **layer split**, not the independent one-card-per-agent setup. Fork #96 is Unsloth Dynamic v3.1/Q5_0-specific; original GSQ-RCO IQ3_XXS remains unchanged.
- Stage 8 proved plain mmap had **zero useful pinned PCIe expert share**; adding resident budget caused high physical reads and degraded Prefill/TTFT, while async C3 lifted Decode but harmed balance. Do not copy S8 resident-budget/async tuning into Stage 9 arms without a separately authorized hypothesis.

### Unresolved before any C2

Full upstream 0.1.59 **engine** SHA; pinned build artifacts and effective flags on real P520; source/build parity and prompt path dispatch on V100; fork WMMA2 default correction and any additional default changes; DFlash2 official pack selection/hash, GPU VRAM headroom, startup and native draft metrics; actual live system/port/clock/cache/swap state. If a candidate cannot meet these gates, it is **SKIPPED with evidence**, not scored or substituted.

**Status of P0: NOT EXECUTED. Stage 9 scored runs: 0.**
