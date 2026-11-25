# S12-C0 (`c0-20261125T170951`) — Stage 12 Receipt Report

- **Generated:** 2026-11-25T17:22:32.268592+09:00
- **Verdict:** `PASS` (mode `scored`)
- **Image:** `sha256:83a48e7dc321a72e0a13642668a887d179d630d2ff4dd204fd49cb7f674c3b6e`
- **Engine SHA256:** `acfe6d530bc970514d0f57c3f5a87fd5b0b77a2666f8bf4095f1ebd33bb0b447`
- **Source SHA:** `d46f5f268f8ed797e83a5c63a69bffbd7a581cf6`
- **Overrides:** `{"STRATA_OOMD_ROOM": "0"}`
- **Backup Verified:** 148 files (`all_match=True`)

## Scored C2 Medians vs S11X-D2 Reference

| Metric | This Run (A / B) | S11X-D2 Reference (A / B) | Delta (A / B) |
|---|---:|---:|---:|
| Prefill (tok/s) | 1034.2 / 1040.5 | 1032.6 / 1037.0 | +1.6 / +3.5 |
| Decode (tok/s) | 21.9 / 22.3 | 37.1 / 41.0 | -15.2 / -18.7 |
| TTFT (s) | 123.04 / 122.30 | 123.21 / 122.69 | -0.17 / -0.39 |

## Phases

### `c0-20261125T170951-startup` — `SMOKE_PASS_NOT_C2`
- Agent A: VRAM peak `15379` MiB | Power avg/peak `41.1` / `50.3` W | Temp max `41` C | Offered/Accepted `97`/`96` | OS read `1830.8` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 838 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 19.9 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 20.6 ms`
- Agent B: VRAM peak `15379` MiB | Power avg/peak `43.3` / `76.2` W | Temp max `43` C | Offered/Accepted `97`/`96` | OS read `142.9` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 839 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 15.9 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 20.5 ms`

### `c0-20261125T170951-batch-1` — `PASS`
- Prefill: `1034.2` / `1040.5` tok/s | Decode: `21.9` / `22.3` tok/s | TTFT: `123.04` / `122.30` s | Overlap: `60.51s`
- Agent A: VRAM peak `15637` MiB | Power avg/peak `90.1` / `199.3` W | Temp max `64` C | Offered/Accepted `1020`/`821` | OS read `953.2` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 837 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 15.1 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 20.0 ms`
- Agent B: VRAM peak `15637` MiB | Power avg/peak `96.3` / `215.4` W | Temp max `65` C | Offered/Accepted `1339`/`1123` | OS read `443.5` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 845 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 17.9 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 20.3 ms`

### `c0-20261125T170951-batch-2` — `PASS`
- Prefill: `1035.1` / `1040.6` tok/s | Decode: `21.9` / `22.4` tok/s | TTFT: `122.93` / `122.29` s | Overlap: `60.51s`
- Agent A: VRAM peak `15637` MiB | Power avg/peak `90.5` / `200.0` W | Temp max `66` C | Offered/Accepted `1020`/`821` | OS read `1031.0` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 836 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 15.6 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 19.8 ms`
- Agent B: VRAM peak `15637` MiB | Power avg/peak `93.8` / `220.0` W | Temp max `65` C | Offered/Accepted `1380`/`1155` | OS read `394.4` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 850 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 15.3 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 19.6 ms`

### `c0-20261125T170951-batch-3` — `PASS`
- Prefill: `1030.9` / `1036.2` tok/s | Decode: `21.7` / `21.7` tok/s | TTFT: `123.43` / `122.82` s | Overlap: `82.93s`
- Agent A: VRAM peak `15637` MiB | Power avg/peak `90.4` / `202.7` W | Temp max `67` C | Offered/Accepted `1387`/`1120` | OS read `1168.8` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 831 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 14.7 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 19.8 ms`
- Agent B: VRAM peak `15637` MiB | Power avg/peak `94.6` / `210.9` W | Temp max `65` C | Offered/Accepted `1420`/`1170` | OS read `473.9` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 844 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 15.1 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 20.9 ms`
