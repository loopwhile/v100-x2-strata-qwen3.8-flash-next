# Stage 11 Summary — `S11-D4` (`IQ3_S` + `S10-D4` DFlash2 Recipe)

**Verdict: `PASS` (3/3 valid concurrent 128K C2 batches + 1 startup smoke PASS; dual-agent 30 tok/s NOT MET on `IQ3_S`).**

- **Run ID**: `d4-20261119T025044` (closed; earlier startup-only attempt `d4-20261119T024740` exited before scoring because `qwen3.8-flash-next-dflash2.q4_0.pack` was not yet linked for `drafting.pack_ready()`)
- **Engine**: Upstream Strata `0.1.59` (`sha256:dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d`, binary `ccca4882...`)
- **Quantization & Assets**: `Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S` (`/srv/models/strata-iq3s`) + stock DFlash2 selector pack (`qwen3.8-flash-next-dflash2.q4_0-selq4.pack`), `--draft-fallback none` (no MTP)
- **Settings**: `--spec 8 --draft-conf 0.7 --prefill auto --max-context 131072 --kv int8 --kv-resident 32768 --expert-cache auto --mmap-experts`, `STRATA_SELECT_SIMT=1`, `STRATA_SM70_TABLE=1`, `STRATA_PF_WMMA=1`
- **Hardware Policy**: Dual Tesla V100 SXM2 16GB, 150 W configured limits, `135–1245 MHz` clock lock, cpusets `0-2,6-8` (GPU0/A) and `3-5,9-11` (GPU1/B)

## Per-Batch Results (`d4-20261119T025044`)

| Batch | Prefill A / B (tok/s) | TTFT A / B (s) | Decode A / B (tok/s) | Output A / B (tok) | Wall (s) | GPU0 Temp / Pwr (Avg / Peak) | GPU1 Temp / Pwr (Avg / Peak) | DFlash2 Acc A / B |
| --- | :---: | :---: | :---: | :---: | ---: | :---: | :---: | :---: |
| `batch-1` | 462.1 / 463.0 | 275.01 / 274.47 | 23.8 / 23.4 | 3210 / 2618 | 409.82 | 49.1/61.0 °C · 68.3/199.8 W | 51.4/62.0 °C · 70.6/207.7 W | 80.58% / 75.77% |
| `batch-2` | 893.8 / 898.0 | 142.30 / 141.69 | 23.3 / 23.2 | 2647 / 2675 | 256.67 | 55.2/64.0 °C · 83.2/195.5 W | 56.1/63.0 °C · 88.1/217.2 W | 81.69% / 76.54% |
| `batch-3` | 906.4 / 910.5 | 140.32 / 139.71 | 22.8 / 23.6 | 3114 / 2483 | 276.70 | 55.6/64.0 °C · 84.1/200.9 W | 56.1/64.0 °C · 79.7/215.8 W | 79.45% / 77.42% |
| **Median** | **893.8 / 898.0** | **142.30 / 141.69** | **23.3 / 23.4** | **3114 / 2618** | **276.70** | **53.3/64.0 °C · 78.5/200.9 W** | **54.5/64.0 °C · 79.5/217.2 W** | — |

## Key Observations

1. **vs Historical `IQ3_S` (`S6-0`: 908.2 / 923.1 prefill, 22.3 / 21.2 decode)**: `S11-D4` increased `IQ3_S` decode medians by **+1.0 / +2.2 tok/s** (`23.3 / 23.4` tok/s) under DFlash2 `spec 8 / conf 0.7`, with `4607` VRAM expert cache slots (`8.78 GiB`). Warm-cache prefill (`893.8–906.4` / `898.0–910.5` tok/s) remained slightly below `S6-0` (1.1%–1.6% difference, non-causal across different engine/clock/cache regimes).
2. **vs `S10-D4` (`IQ3_XXS`: 1025.1 / 1027.8 prefill, 30.4 / 30.3 decode)**: `IQ3_S` decode is **-7.1 / -6.9 tok/s** slower and prefill **-131.3 / -129.8 tok/s** slower. Two capacity factors explain this:
   - **VRAM expert hit rate**: `IQ3_S` achieved `0.751–0.770` (A) / `0.788–0.794` (B) expert hit rates vs `0.822 / 0.855` on `IQ3_XXS`, with larger missed expert payloads on AVX-2 CPU.
   - **64 GB host page-cache spillover**: `IQ3_S` Shard 1 (`51.05 GiB`) topped out at `47.52–47.83 GiB` resident in OS page cache after warmup, leaving ~`2.4–3.9 GB` of physical OS reads per request in batches 2–3 (`batch-1` cold load read `63.1 / 69.9 GB`). Swap remained inactive (`pswpin=0`).
3. **Backup & Host State**: All 164 raw files backed up and SHA-256 verified to [results/raw/d4-20261119T025044-sha256.json](../../results/raw/d4-20261119T025044-sha256.json). P520 GPUs are idle (`0 MiB`, `135 MHz`), all Stage 11 containers stopped, and `p520-llm-a/b` remain stopped.
