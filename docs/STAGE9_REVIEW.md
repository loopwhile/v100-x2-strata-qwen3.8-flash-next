# Stage 9 — final review (2026-11-10 KST)

**CLOSED: U1, D1 and F1 each completed 3/3 concurrent fresh-process 128K C2, 9/9 total PASS. Dual-agent 30 tok/s goal NOT MET. No all-metric upgrade, semantic-quality validation or production promotion.**

[Full metric summary](../artifacts/stage9-results-20261110/summary.md) · [CSV](../artifacts/stage9-results-20261110/summary.csv) · [Per-batch CSV](../artifacts/stage9-results-20261110/batches.csv) · [Source/build audit](STAGE9_SOURCE_AUDIT.md) · [Final host check](../artifacts/stage9-results-20261110/final-host-check.json).

The [consolidated Markdown database](CONSOLIDATED_BENCHMARKS.md) and [master CSV](consolidated-benchmarks.csv) include the nine scored Stage 9 batches and three arm medians, bringing the total to 147 records with the prior 135 rows unchanged. The consolidated GPU averages use the established **power >60 W sample filter**; the standalone full-lifetime GPU means below remain unfiltered, so these averages must not be interchanged.

## Measured results

All values are separate per-agent medians of all three valid batches. No cold batch was discarded.

| Arm | Drafter | Prefill A/B tok/s | Decode A/B tok/s | TTFT A/B s |
|---|---|---:|---:|---:|
| [S9-U1](../artifacts/stage9-results-20261110/u1-20261110T173748/report.md) | MTP spec4/min-p0.5 | 966.0 / 973.6 | 26.1 / 28.8 | 131.67 / 130.67 |
| [S9-D1](../artifacts/stage9-results-20261110/d1-20261110T175220/report.md) | DFlash2 spec6/conf0.7 | 1026.5 / 1032.6 | 28.2 / 29.4 | 123.92 / 123.21 |
| [S9-F1](../artifacts/stage9-results-20261110/f1-20261110T180620/report.md) | MTP spec4/min-p0.5 | 960.0 / 909.8 | 26.3 / 26.0 | 132.51 / 139.81 |

| Arm | Mean power A/B W | Peak power A/B W | Mean temp A/B °C | Peak temp A/B °C | CPU user % | RAM unavailable peak GiB |
|---|---:|---:|---:|---:|---:|---:|
| S9-U1 | 85.52 / 88.72 | 201.81 / 219.88 | 54.8 / 56.3 | 65 / 65 | 23.6 | 11.99 |
| S9-D1 | 91.74 / 92.26 | 221.58 / 226.24 | 57.4 / 57.4 | 66 / 65 | 26.3 | 11.90 |
| S9-F1 | 86.36 / 90.41 | 218.63 / 242.06 | 56.0 / 56.8 | 65 / 65 | 28.4 | 12.03 |

GPU/CPU figures cover the full process lifetime, including loading, shutdown and any built-in idle-prefill after the response. GPU means average the three batch means; peaks are maxima. Configured power limits stayed 150 W; observed sensor peaks above 150 W are retained as measurements, not changed caps. RAM unavailable means MemTotal minus MemAvailable. Raw vmstat/iostat/GPU/host series, swap/page faults, Expert/KV cache, acceptance and per-batch ranges are retained.

## Assessment and comparison limits

- D1 had the strongest descriptive speed of the three new arms on both agents. Its full-lifetime mean power and temperatures were higher than U1; against archived S7-XXS-14, mean power was 91.74/92.26 W versus 81.84/85.38 W and peak temperature 66/65°C versus 65/64°C. This is not an all-metric improvement. Archived mean temperature was unavailable and is not invented.
- No batch in any arm achieved >=30 tok/s on both agents. F1 did not establish a balanced speed upgrade. S7-XXS-14 remains the CLOSED, unrerun operational reference; S8-C1/C0 remain historical alternatives. No reference engine or closed S7/S8 experiment was relaunched.
- U1 first-batch Prefill 637.8/647.1 and TTFT 199.43/196.46s are retained. Its main requests recorded 42.75/47.63 GB physical reads; the next two batches also had material reads. D1 and F1 encountered different cache/read conditions. Clock, temperature, Linux page-cache, swap, output lengths and non-interleaved execution prevent causal version or drafter-speedup claims.
- The host clock service changed after initial inspection, at 17:14:21 to 1245–1245 and17:15:59 to 135–1245 MHz. No clock/power command was issued by this agent. The user explicitly directed continuing at 1245 before the scored runs. Every scored run was later and telemetry peaks stayed<=1245. Historical 1110 MHz references are a different clock condition; the initial setting must not be described as unchanged.
- Semantic coding/tool-call quality was not evaluated. The mechanical contract validates context, counts, overlap, health and repeatability, not answer quality.

## Source, drafter and protocol evidence

- U1/D1 share upstream 0.1.59 SHA `712fec6b4297c9cfd32ab43daaa2979a9aa01edf`, image `dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d`, binary `ccca488231f12da422be4a80b5c7f165b7593f6388907cac92d3c3f0d4229031`. F1 uses fork SHA `8b4c09bd3d9213b2d47880826c6e818c3140664d`, engine 0.1.45.7, separate image/binary. Both builds use CUDA 12.9.1/sm70. Full pins are in the preparation and per-arm receipts.
- Original IQ3_XXS/native pack/tokenizer/MTP and 15 asset SHA256s verified; same independent GPU0/A and GPU1/B with original cpusets, 131072 context, INT8 KV/resident 32768, mmap, auto cache/prefill and three S7 environment flags. Original C2 manifest/harness and both prompt hashes/counts matched. All 18 scored HTTP requests had >=1024 output, finish_reason=stop, zero prefix reuse, simultaneous decode and post-health. Each batch used new containers and engine processes; process identity before/after remained unchanged.
- D1 stock Q4_0-selector pack is 339694592 bytes, SHA `4a42b98220ea7880664002c8edda1563aecbae754b762a2e2f31b2b91ee93ecd`. Source default rule estimates 4139 slots at 16 GiB, yielding spec6/conf0.7. Effective child args, loaded head, no MTP layer and fallback none were verified. DFlash2-specific proposals were positive in all six scored requests; counts exclude separately logged suffix drafts. No tuned-pack or confidence sweep.
- F1 sets WMMA2=0, proven to bypass the second tile in source. Its 13 remaining Volta defaults are recorded in receipts: DEQUANT_WIDE, ADAPT_OVERLAP, SIDE_MIXER, GR_UP75, B6_MMVQ_ROWS, GU_SWIGLU, QSA_ROWS, ATTN_DAILY, GR_NORM_FAST, ARGMAX_ROWS_SM70, QIL, EXPDEC and GR_DOWN_TG. This is the pinned fork recipe, not a pure engine-version isolation.
- F1 emitted one internal decode-free `GEN0` idle-prefill after each scored response (six total). This is the server next-turn worker, not another HTTP/C2 request. The next scored batch used new processes and could not reuse that prefix. Main-request physical I/O/KV records are separated from this later work; full-lifetime resource metrics include it. Initial intermediate exports are retained under `preliminary-exports/` for audit of this aggregation correction. No measurement was repeated.
- Separate draft/verify timing requires profiling flags in these sources. Those flags were not injected into scored arms; unavailable component timings are explicitly labelled. Normal Decode/Prefill/TTFT, draft acceptance and full-lifetime resource data are available.

## Evidence, failures and final state

- Closed scored IDs: `u1-20261110T173748`, `d1-20261110T175220`, `f1-20261110T180620`. Raw P520 paths are `results/stage9/S9-ARM/ID/`; ThinkPad backups are `results/raw/ID/`. Each arm 185 files, 555 scored-arm files total, all SHA256 matched.
- Closed original U1 `u1-20261110T173436` has 45 backed-up files, zero scored batches. Short startup passed, then the old 1110 telemetry predicate automatically failed at 17:35:39. The user clock amendment authorized a new ID, never a scored retry. Preparation failures (Ninja path, wrong helper API name, read-only nested mount) remain separately preserved; no source engine patch or scored retry was used.
- P0 preparations `p0-20261110T171309` and `p0-20261110T171658` have 10+65 SHA-matched evidence files, excluding draft weights. Total verified backup count is 675 files; [hash manifest](../artifacts/stage9-results-20261110/raw-backup-sha256.json). No model weights were transported to ThinkPad.
- Actual measurement runner snapshot SHA `687894426c1e119ba4d6345b1fc97672852671226b9ca8b57fb96a1f40e11f6a` is retained on P520 and in the P0 backup. Delivered code adds a post-run-discovered preflight fix: compare the latest clock-application entry per GPU, so an earlier 1110 line cannot hide a later 1245 range. Regression coverage and syntax checks pass; no extra GPU test was launched for this read-only guard fix.
- Final live audit `2026-11-10T18:26:22.997534+09:00`: no running containers/GPU compute, 0 MiB VRAM, 150 W configured caps, active 135–1245 service, all 278 initial containers and original images retained, all 15 original asset size/mtime pairs unchanged after full P0 hash verification. Ports 8080/8081/18086/18087 are free. ThinkPad tunnel remains active since 16:33:58. No production service was started; initial serving state was empty and remains empty.
- Scripts 113–119, immutable image builds, safety tests and receipts remain for audit only. All IDs are closed; the candidate manifest disables further execution. New experiments or promotion require a new scope. The user subsequently authorized committing/pushing this closure and synchronizing ThinkPad E14, P520 and origin/main; that Git-only scope authorizes no new experiment or production operation.
