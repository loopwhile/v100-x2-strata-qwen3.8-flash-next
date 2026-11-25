# S12-D3 (`d3-20261125T194836`) — Stage 12 Receipt Report

- **Generated:** 2026-11-25T20:03:29.158481+09:00
- **Verdict:** `PASS` (mode `scored`)
- **Image:** `sha256:5693cd7d5fb460a2d164a8f22f4a0a5b9fd2c2063cdd028e88a1439bd3e3a2ea`
- **Engine SHA256:** `b29f813299b91a179716f15e73b71c5b1e4cfd1fa9060014b2aa09596795dba0`
- **Source SHA:** `d46f5f268f8ed797e83a5c63a69bffbd7a581cf6`
- **Overrides:** `{"STRATA_OOMD_ROOM": "0", "STRATA_HC_V100": "1"}`
- **Backup Verified:** 148 files (`all_match=True`)

## Scored C2 Medians vs S11X-D2 Reference

| Metric | This Run (A / B) | S11X-D2 Reference (A / B) | Delta (A / B) |
|---|---:|---:|---:|
| Prefill (tok/s) | 894.9 / 898.9 | 1032.6 / 1037.0 | -137.7 / -138.1 |
| Decode (tok/s) | 21.8 / 21.1 | 37.1 / 41.0 | -15.3 / -19.9 |
| TTFT (s) | 142.19 / 141.52 | 123.21 / 122.69 | +18.98 / +18.83 |

## Phases

### `d3-20261125T194836-startup` — `SMOKE_PASS_NOT_C2`
- Agent A: VRAM peak `15371` MiB | Power avg/peak `41.0` / `53.0` W | Temp max `40` C | Offered/Accepted `98`/`96` | OS read `2210.1` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 858 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 17.5 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 31.1 ms`
- Agent B: VRAM peak `15371` MiB | Power avg/peak `42.3` / `80.5` W | Temp max `42` C | Offered/Accepted `98`/`96` | OS read `820.5` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 861 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 16.6 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 41.0 ms`

### `d3-20261125T194836-batch-1` — `PASS`
- Prefill: `894.9` / `898.9` tok/s | Decode: `21.0` / `20.1` tok/s | TTFT: `142.19` / `141.52` s | Overlap: `73.03s`
- Agent A: VRAM peak `15619` MiB | Power avg/peak `81.6` / `206.4` W | Temp max `64` C | Offered/Accepted `1100`/`887` | OS read `14814.5` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 870 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 20.9 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 35.7 ms`
- Agent B: VRAM peak `15619` MiB | Power avg/peak `85.1` / `213.7` W | Temp max `64` C | Offered/Accepted `1412`/`1124` | OS read `16970.9` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 850 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 14.8 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 35.3 ms`

### `d3-20261125T194836-batch-2` — `PASS`
- Prefill: `806.6` / `807.7` tok/s | Decode: `21.8` / `21.1` tok/s | TTFT: `157.71` / `157.48` s | Overlap: `66.47s`
- Agent A: VRAM peak `15619` MiB | Power avg/peak `79.3` / `207.1` W | Temp max `65` C | Offered/Accepted `1044`/`865` | OS read `26496.8` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 1021 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 14.6 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 33.7 ms`
- Agent B: VRAM peak `15619` MiB | Power avg/peak `86.9` / `217.6` W | Temp max `65` C | Offered/Accepted `1561`/`1247` | OS read `25170.8` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 956 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 14.6 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 37.4 ms`

### `d3-20261125T194836-batch-3` — `PASS`
- Prefill: `994.3` / `1001.3` tok/s | Decode: `22.6` / `22.6` tok/s | TTFT: `127.97` / `127.08` s | Overlap: `62.76s`
- Agent A: VRAM peak `15619` MiB | Power avg/peak `85.8` / `206.1` W | Temp max `66` C | Offered/Accepted `1015`/`851` | OS read `6708.6` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 855 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 16.8 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 34.8 ms`
- Agent B: VRAM peak `15619` MiB | Power avg/peak `92.0` / `213.5` W | Temp max `66` C | Offered/Accepted `1583`/`1250` | OS read `4801.4` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 851 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 28.8 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 32.7 ms`
