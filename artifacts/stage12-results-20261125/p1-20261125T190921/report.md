# S12-P1 (`p1-20261125T190921`) — Stage 12 Receipt Report

- **Generated:** 2026-11-25T19:22:33.851283+09:00
- **Verdict:** `PASS` (mode `scored`)
- **Image:** `sha256:0cbf5d14914b0dc2ca7b62686f976937395cc56ee5ffb17eb35a8bcb13927b51`
- **Engine SHA256:** `ec05dafc29e93dffaaa97ffdb97ae21c7be6477793492b5db504af26a2b45221`
- **Source SHA:** `d46f5f268f8ed797e83a5c63a69bffbd7a581cf6`
- **Overrides:** `{"STRATA_OOMD_ROOM": "0", "STRATA_PF_WMMA": "1", "STRATA_PF_WMMA2": "1", "STRATA_PF_WMMA_LEAN": "1", "STRATA_PF_WMMA_SKINNY": "1"}`
- **Backup Verified:** 148 files (`all_match=True`)

## Scored C2 Medians vs S11X-D2 Reference

| Metric | This Run (A / B) | S11X-D2 Reference (A / B) | Delta (A / B) |
|---|---:|---:|---:|
| Prefill (tok/s) | 1014.3 / 1021.7 | 1032.6 / 1037.0 | -18.3 / -15.3 |
| Decode (tok/s) | 23.1 / 24.2 | 37.1 / 41.0 | -14.0 / -16.8 |
| TTFT (s) | 125.44 / 124.54 | 123.21 / 122.69 | +2.23 / +1.85 |

## Phases

### `p1-20261125T190921-startup` — `SMOKE_PASS_NOT_C2`
- Agent A: VRAM peak `15379` MiB | Power avg/peak `40.4` / `48.4` W | Temp max `40` C | Offered/Accepted `97`/`96` | OS read `3366.5` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 887 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 14.9 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 34.7 ms`
- Agent B: VRAM peak `15379` MiB | Power avg/peak `41.8` / `55.5` W | Temp max `42` C | Offered/Accepted `97`/`96` | OS read `596.2` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 852 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 15.5 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 20.1 ms`

### `p1-20261125T190921-batch-1` — `PASS`
- Prefill: `925.0` / `928.3` tok/s | Decode: `22.5` / `24.2` tok/s | TTFT: `137.56` / `137.06` s | Overlap: `76.12s`
- Agent A: VRAM peak `15615` MiB | Power avg/peak `86.4` / `197.2` W | Temp max `61` C | Offered/Accepted `1254`/`1064` | OS read `14900.7` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 891 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 21.9 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 21.8 ms`
- Agent B: VRAM peak `15615` MiB | Power avg/peak `84.7` / `207.1` W | Temp max `63` C | Offered/Accepted `1270`/`1026` | OS read `13817.2` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 880 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 19.6 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 21.7 ms`

### `p1-20261125T190921-batch-2` — `PASS`
- Prefill: `1014.3` / `1021.7` tok/s | Decode: `23.1` / `24.8` tok/s | TTFT: `125.44` / `124.54` s | Overlap: `80.02s`
- Agent A: VRAM peak `15615` MiB | Power avg/peak `85.5` / `199.5` W | Temp max `64` C | Offered/Accepted `1336`/`1100` | OS read `5367.5` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 986 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 15.9 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 31.5 ms`
- Agent B: VRAM peak `15615` MiB | Power avg/peak `92.1` / `216.0` W | Temp max `63` C | Offered/Accepted `1481`/`1166` | OS read `3759.2` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 982 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 15.5 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 32.1 ms`

### `p1-20261125T190921-batch-3` — `PASS`
- Prefill: `1031.4` / `1037.1` tok/s | Decode: `23.2` / `23.7` tok/s | TTFT: `123.37` / `122.71` s | Overlap: `79.01s`
- Agent A: VRAM peak `15615` MiB | Power avg/peak `86.4` / `203.3` W | Temp max `64` C | Offered/Accepted `1320`/`1089` | OS read `2137.8` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 856 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 15.2 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 23.6 ms`
- Agent B: VRAM peak `15615` MiB | Power avg/peak `90.4` / `213.5` W | Temp max `64` C | Offered/Accepted `1609`/`1262` | OS read `1108.8` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 867 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 16.1 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 20.5 ms`
