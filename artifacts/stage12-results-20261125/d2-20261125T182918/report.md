# S12-D2 (`d2-20261125T182918`) — Stage 12 Receipt Report

- **Generated:** 2026-11-25T18:40:50.091388+09:00
- **Verdict:** `PASS` (mode `scored`)
- **Image:** `sha256:922ba4eb58eebcd10a5e586de4c030cdc093ed4f1df429bc1d34b56e97cc520c`
- **Engine SHA256:** `6082be376bfd05701a740a1f408858714380c8806c8b3fba0a834ada03049dc9`
- **Source SHA:** `d46f5f268f8ed797e83a5c63a69bffbd7a581cf6`
- **Overrides:** `{"STRATA_OOMD_ROOM": "0", "STRATA_MMAP_ADAPT_ASYNC": "1", "STRATA_COLD_OVERLAP": "5"}`
- **Backup Verified:** 148 files (`all_match=True`)

## Scored C2 Medians vs S11X-D2 Reference

| Metric | This Run (A / B) | S11X-D2 Reference (A / B) | Delta (A / B) |
|---|---:|---:|---:|
| Prefill (tok/s) | 1012.3 / 1017.1 | 1032.6 / 1037.0 | -20.3 / -19.9 |
| Decode (tok/s) | 27.6 / 28.3 | 37.1 / 41.0 | -9.5 / -12.7 |
| TTFT (s) | 125.69 / 125.11 | 123.21 / 122.69 | +2.48 / +2.42 |

## Phases

### `d2-20261125T182918-startup` — `SMOKE_PASS_NOT_C2`
- Agent A: VRAM peak `15379` MiB | Power avg/peak `40.1` / `48.4` W | Temp max `39` C | Offered/Accepted `97`/`96` | OS read `1606.9` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 884 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 20.8 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 24.2 ms`
- Agent B: VRAM peak `15379` MiB | Power avg/peak `41.1` / `50.8` W | Temp max `42` C | Offered/Accepted `97`/`96` | OS read `191.0` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 900 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 20.7 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 24.9 ms`

### `d2-20261125T182918-batch-1` — `PASS`
- Prefill: `936.1` / `963.7` tok/s | Decode: `26.3` / `26.7` tok/s | TTFT: `136.02` / `132.08` s | Overlap: `54.05s`
- Agent A: VRAM peak `15637` MiB | Power avg/peak `90.1` / `200.0` W | Temp max `63` C | Offered/Accepted `991`/`839` | OS read `8705.7` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 851 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 16.6 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 21.6 ms`
- Agent B: VRAM peak `15637` MiB | Power avg/peak `94.1` / `221.0` W | Temp max `64` C | Offered/Accepted `1117`/`869` | OS read `8923.6` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 844 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 16.6 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 21.0 ms`

### `d2-20261125T182918-batch-2` — `PASS`
- Prefill: `1012.3` / `1017.1` tok/s | Decode: `27.7` / `28.3` tok/s | TTFT: `125.69` / `125.11` s | Overlap: `47.22s`
- Agent A: VRAM peak `15637` MiB | Power avg/peak `101.0` / `200.9` W | Temp max `66` C | Offered/Accepted `872`/`736` | OS read `6704.2` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 880 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 16.8 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 39.6 ms`
- Agent B: VRAM peak `15637` MiB | Power avg/peak `98.7` / `210.1` W | Temp max `65` C | Offered/Accepted `1095`/`864` | OS read `5117.2` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 908 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 17.1 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 39.2 ms`

### `d2-20261125T182918-batch-3` — `PASS`
- Prefill: `1013.6` / `1017.3` tok/s | Decode: `27.6` / `29.0` tok/s | TTFT: `125.54` / `125.09` s | Overlap: `47.14s`
- Agent A: VRAM peak `15637` MiB | Power avg/peak `100.4` / `207.6` W | Temp max `67` C | Offered/Accepted `878`/`734` | OS read `4701.0` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 847 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 17.6 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 24.9 ms`
- Agent B: VRAM peak `15637` MiB | Power avg/peak `97.2` / `210.1` W | Temp max `65` C | Offered/Accepted `997`/`787` | OS read `2697.7` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 844 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 16.5 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 23.8 ms`
