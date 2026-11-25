# S12-U1 (`u1-20261125T164355`) — Stage 12 Receipt Report

- **Generated:** 2026-11-25T16:59:40.242166+09:00
- **Verdict:** `PASS` (mode `scored`)
- **Image:** `sha256:83a48e7dc321a72e0a13642668a887d179d630d2ff4dd204fd49cb7f674c3b6e`
- **Engine SHA256:** `acfe6d530bc970514d0f57c3f5a87fd5b0b77a2666f8bf4095f1ebd33bb0b447`
- **Source SHA:** `d46f5f268f8ed797e83a5c63a69bffbd7a581cf6`
- **Overrides:** `{}`
- **Backup Verified:** 148 files (`all_match=True`)

## Scored C2 Medians vs S11X-D2 Reference

| Metric | This Run (A / B) | S11X-D2 Reference (A / B) | Delta (A / B) |
|---|---:|---:|---:|
| Prefill (tok/s) | 877.1 / 880.5 | 1032.6 / 1037.0 | -155.5 / -156.5 |
| Decode (tok/s) | 21.9 / 22.2 | 37.1 / 41.0 | -15.2 / -18.8 |
| TTFT (s) | 145.04 / 144.48 | 123.21 / 122.69 | +21.83 / +21.79 |

## Phases

### `u1-20261125T164355-startup` — `SMOKE_PASS_NOT_C2`
- Agent A: VRAM peak `15379` MiB | Power avg/peak `41.0` / `51.7` W | Temp max `42` C | Offered/Accepted `97`/`96` | OS read `20405.9` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 839 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 16.6 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 38.0 ms`
- Agent B: VRAM peak `15379` MiB | Power avg/peak `41.8` / `59.8` W | Temp max `44` C | Offered/Accepted `97`/`96` | OS read `8400.9` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 838 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 16.5 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 37.6 ms`

### `u1-20261125T164355-batch-1` — `PASS`
- Prefill: `877.1` / `880.5` tok/s | Decode: `22.0` / `22.2` tok/s | TTFT: `145.04` / `144.48` s | Overlap: `60.45s`
- Agent A: VRAM peak `15637` MiB | Power avg/peak `83.2` / `203.9` W | Temp max `65` C | Offered/Accepted `1020`/`821` | OS read `23426.2` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 840 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 16.3 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 37.0 ms`
- Agent B: VRAM peak `15637` MiB | Power avg/peak `84.8` / `223.0` W | Temp max `65` C | Offered/Accepted `1411`/`1168` | OS read `24676.1` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 835 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 16.0 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 36.4 ms`

### `u1-20261125T164355-batch-2` — `PASS`
- Prefill: `878.2` / `880.1` tok/s | Decode: `21.6` / `22.2` tok/s | TTFT: `144.84` / `144.55` s | Overlap: `69.82s`
- Agent A: VRAM peak `15637` MiB | Power avg/peak `81.7` / `203.4` W | Temp max `67` C | Offered/Accepted `1212`/`977` | OS read `23922.8` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 836 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 16.7 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 40.4 ms`
- Agent B: VRAM peak `15637` MiB | Power avg/peak `82.7` / `210.1` W | Temp max `65` C | Offered/Accepted `1411`/`1168` | OS read `24179.5` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 840 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 16.6 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 38.0 ms`

### `u1-20261125T164355-batch-3` — `PASS`
- Prefill: `876.8` / `881.1` tok/s | Decode: `21.9` / `22.4` tok/s | TTFT: `145.08` / `144.38` s | Overlap: `60.59s`
- Agent A: VRAM peak `15637` MiB | Power avg/peak `84.8` / `201.7` W | Temp max `67` C | Offered/Accepted `1020`/`821` | OS read `23123.2` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 838 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 15.0 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 36.9 ms`
- Agent B: VRAM peak `15637` MiB | Power avg/peak `87.2` / `215.2` W | Temp max `65` C | Offered/Accepted `1375`/`1151` | OS read `24987.3` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 840 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 15.6 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 36.4 ms`
