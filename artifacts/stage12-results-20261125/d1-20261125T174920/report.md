# S12-D1 (`d1-20261125T174920`) — Stage 12 Receipt Report

- **Generated:** 2026-11-25T18:03:25.004098+09:00
- **Verdict:** `PASS` (mode `scored`)
- **Image:** `sha256:9d5f636459eecd28a846d88fbed7870e9d281194de4d55794623185d203b7a05`
- **Engine SHA256:** `d1010753103c9f895bb5797c5c2d2ab519c5de10077ea0ccd7116f5d0e26c078`
- **Source SHA:** `d46f5f268f8ed797e83a5c63a69bffbd7a581cf6`
- **Overrides:** `{"STRATA_OOMD_ROOM": "0", "STRATA_AVX512BW_IQ": "22", "STRATA_IQ_MT_MIN": "1", "STRATA_IQ_GATHER": "1", "STRATA_IQ256_GATHER": "1", "STRATA_Q2_BITPLANE": "1"}`
- **Backup Verified:** 148 files (`all_match=True`)

## Scored C2 Medians vs S11X-D2 Reference

| Metric | This Run (A / B) | S11X-D2 Reference (A / B) | Delta (A / B) |
|---|---:|---:|---:|
| Prefill (tok/s) | 865.0 / 879.7 | 1032.6 / 1037.0 | -167.6 / -157.3 |
| Decode (tok/s) | 23.0 / 27.0 | 37.1 / 41.0 | -14.1 / -14.0 |
| TTFT (s) | 147.16 / 144.66 | 123.21 / 122.69 | +23.95 / +21.97 |

## Phases

### `d1-20261125T174920-startup` — `SMOKE_PASS_NOT_C2`
- Agent A: VRAM peak `15379` MiB | Power avg/peak `40.6` / `53.1` W | Temp max `39` C | Offered/Accepted `98`/`96` | OS read `5420.0` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 850 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 32.0 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 20.4 ms`
- Agent B: VRAM peak `15379` MiB | Power avg/peak `42.0` / `61.2` W | Temp max `42` C | Offered/Accepted `98`/`96` | OS read `2383.2` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 912 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 17.6 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 39.2 ms`

### `d1-20261125T174920-batch-1` — `PASS`
- Prefill: `865.0` / `879.7` tok/s | Decode: `23.0` / `27.0` tok/s | TTFT: `147.16` / `144.66` s | Overlap: `70.89s`
- Agent A: VRAM peak `15637` MiB | Power avg/peak `85.9` / `203.5` W | Temp max `63` C | Offered/Accepted `1215`/`984` | OS read `16212.4` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 1004 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 15.6 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 20.2 ms`
- Agent B: VRAM peak `15637` MiB | Power avg/peak `89.7` / `208.7` W | Temp max `64` C | Offered/Accepted `1611`/`1312` | OS read `16350.2` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 1007 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 15.3 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 20.0 ms`

### `d1-20261125T174920-batch-2` — `PASS`
- Prefill: `720.2` / `720.2` tok/s | Decode: `21.4` / `24.2` tok/s | TTFT: `176.57` / `176.56` s | Overlap: `73.51s`
- Agent A: VRAM peak `15637` MiB | Power avg/peak `81.5` / `193.5` W | Temp max `61` C | Offered/Accepted `1233`/`1034` | OS read `47345.1` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 875 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 20.6 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 32.8 ms`
- Agent B: VRAM peak `15637` MiB | Power avg/peak `83.2` / `217.6` W | Temp max `61` C | Offered/Accepted `1169`/`923` | OS read `49863.8` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 922 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 19.3 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 31.2 ms`

### `d1-20261125T174920-batch-3` — `PASS`
- Prefill: `953.4` / `952.8` tok/s | Decode: `24.6` / `28.3` tok/s | TTFT: `133.48` / `133.55` s | Overlap: `65.69s`
- Agent A: VRAM peak `15637` MiB | Power avg/peak `90.2` / `207.0` W | Temp max `66` C | Offered/Accepted `1213`/`981` | OS read `8163.8` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 991 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 15.1 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 25.0 ms`
- Agent B: VRAM peak `15637` MiB | Power avg/peak `97.1` / `212.9` W | Temp max `65` C | Offered/Accepted `1301`/`1053` | OS read `7263.5` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 963 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 15.6 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 22.9 ms`
