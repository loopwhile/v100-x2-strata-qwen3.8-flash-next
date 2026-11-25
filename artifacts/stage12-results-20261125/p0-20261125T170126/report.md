# S12-P0 (`p0-20261125T170126`) — Stage 12 Receipt Report

- **Generated:** 2026-11-25T17:06:24.392552+09:00
- **Verdict:** `PASS` (mode `diag`)
- **Image:** `sha256:83a48e7dc321a72e0a13642668a887d179d630d2ff4dd204fd49cb7f674c3b6e`
- **Engine SHA256:** `acfe6d530bc970514d0f57c3f5a87fd5b0b77a2666f8bf4095f1ebd33bb0b447`
- **Source SHA:** `d46f5f268f8ed797e83a5c63a69bffbd7a581cf6`
- **Overrides:** `{"STRATA_PREFILL_TIMING": "1", "STRATA_DECODE_TIMING": "1", "STRATA_VERIFY_PROFILE": "1"}`
- **Backup Verified:** 41 files (`all_match=True`)

## Phases

### `p0-20261125T170126-diagnostic-1` — `DIAGNOSTIC_PASS_NOT_SCORED`
- Prefill: `877.3` / `879.7` tok/s | Decode: `21.6` / `22.2` tok/s | TTFT: `145.00` / `144.62` s | Overlap: `61.60s`
- Agent A: VRAM peak `15737` MiB | Power avg/peak `82.4` / `207.9` W | Temp max `65` C | Offered/Accepted `1020`/`821` | OS read `23769.3` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 878 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 25.8 ms`
  - `strata verify: capturing the 2-token window (889 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 45.1 ms`
- Agent B: VRAM peak `15737` MiB | Power avg/peak `87.4` / `208.2` W | Temp max `65` C | Offered/Accepted `1388`/`1171` | OS read `24337.8` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 858 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 25.6 ms`
  - `strata verify: capturing the 2-token window (889 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 48.0 ms`
