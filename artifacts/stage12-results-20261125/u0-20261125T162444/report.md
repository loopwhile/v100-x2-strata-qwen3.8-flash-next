# S12-U0 (`u0-20261125T162444`) — Stage 12 Receipt Report

- **Generated:** 2026-11-25T16:40:53.576982+09:00
- **Verdict:** `PASS` (mode `scored`)
- **Image:** `sha256:5ee459198a4b9c695183bf5901c17ff6b68019381c6b70c72a138fb76d27e93d`
- **Engine SHA256:** `79076b85b0450c86edb5c7bbee54a4c60cd00f564e9adb7058d9e00bc3b50c49`
- **Source SHA:** `a34979fc94f3d126b9bb8210f4ad311345688b52`
- **Overrides:** `{}`
- **Backup Verified:** 148 files (`all_match=True`)

## Scored C2 Medians vs S11X-D2 Reference

| Metric | This Run (A / B) | S11X-D2 Reference (A / B) | Delta (A / B) |
|---|---:|---:|---:|
| Prefill (tok/s) | 876.5 / 881.7 | 1032.6 / 1037.0 | -156.1 / -155.3 |
| Decode (tok/s) | 21.3 / 24.2 | 37.1 / 41.0 | -15.8 / -16.8 |
| TTFT (s) | 145.12 / 144.28 | 123.21 / 122.69 | +21.91 / +21.59 |

## Phases

### `u0-20261125T162444-startup` — `SMOKE_PASS_NOT_C2`
- Agent A: VRAM peak `15379` MiB | Power avg/peak `40.3` / `49.3` W | Temp max `40` C | Offered/Accepted `98`/`96` | OS read `19845.7` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 836 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 15.8 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 37.6 ms`
- Agent B: VRAM peak `15379` MiB | Power avg/peak `41.2` / `50.3` W | Temp max `43` C | Offered/Accepted `98`/`96` | OS read `8950.3` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 841 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 14.8 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 37.5 ms`

### `u0-20261125T162444-batch-1` — `PASS`
- Prefill: `810.1` / `813.8` tok/s | Decode: `21.1` / `24.0` tok/s | TTFT: `157.02` / `156.31` s | Overlap: `68.82s`
- Agent A: VRAM peak `15637` MiB | Power avg/peak `80.3` / `197.3` W | Temp max `64` C | Offered/Accepted `1475`/`1228` | OS read `28810.0` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 841 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 16.6 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 37.5 ms`
- Agent B: VRAM peak `15637` MiB | Power avg/peak `84.0` / `218.2` W | Temp max `64` C | Offered/Accepted `1140`/`922` | OS read `30204.3` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 837 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 16.3 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 37.2 ms`

### `u0-20261125T162444-batch-2` — `PASS`
- Prefill: `876.5` / `881.7` tok/s | Decode: `21.3` / `24.2` tok/s | TTFT: `145.12` / `144.28` s | Overlap: `62.84s`
- Agent A: VRAM peak `15637` MiB | Power avg/peak `82.4` / `203.6` W | Temp max `66` C | Offered/Accepted `1402`/`1185` | OS read `23360.7` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 919 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 16.7 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 36.6 ms`
- Agent B: VRAM peak `15637` MiB | Power avg/peak `83.6` / `213.9` W | Temp max `65` C | Offered/Accepted `1033`/`830` | OS read `24825.8` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 837 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 16.3 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 36.1 ms`

### `u0-20261125T162444-batch-3` — `PASS`
- Prefill: `882.2` / `886.0` tok/s | Decode: `21.9` / `24.5` tok/s | TTFT: `144.19` / `143.58` s | Overlap: `73.34s`
- Agent A: VRAM peak `15637` MiB | Power avg/peak `83.9` / `198.9` W | Temp max `66` C | Offered/Accepted `1478`/`1263` | OS read `23436.2` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 850 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 16.6 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 37.3 ms`
- Agent B: VRAM peak `15637` MiB | Power avg/peak `84.4` / `208.8` W | Temp max `65` C | Offered/Accepted `1233`/`967` | OS read `24732.9` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 858 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 16.7 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 36.9 ms`
