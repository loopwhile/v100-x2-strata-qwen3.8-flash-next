# S12-U1 (`u1smoke-20261125T164236`) — Stage 12 Receipt Report

- **Generated:** 2026-11-25T16:59:38.356808+09:00
- **Verdict:** `PASS` (mode `smoke1`)
- **Image:** `sha256:83a48e7dc321a72e0a13642668a887d179d630d2ff4dd204fd49cb7f674c3b6e`
- **Engine SHA256:** `acfe6d530bc970514d0f57c3f5a87fd5b0b77a2666f8bf4095f1ebd33bb0b447`
- **Source SHA:** `d46f5f268f8ed797e83a5c63a69bffbd7a581cf6`
- **Overrides:** `{}`
- **Backup Verified:** 24 files (`all_match=True`)

## Phases

### `u1smoke-20261125T164236-smoke1` — `SMOKE_PASS_NOT_C2`
- Agent A: VRAM peak `15379` MiB | Power avg/peak `39.7` / `45.1` W | Temp max `42` C | Offered/Accepted `97`/`96` | OS read `28795.0` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 882 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 14.9 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 39.4 ms`
- Agent B: VRAM peak `0` MiB | Power avg/peak `25.5` / `25.6` W | Temp max `40` C | Offered/Accepted `None`/`None` | OS read `None` MB | Exp hit `None`%
