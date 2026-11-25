# S12-D3 (`d3smoke-20261125T194733`) — Stage 12 Receipt Report

- **Generated:** 2026-11-25T19:48:15.372991+09:00
- **Verdict:** `PASS` (mode `smoke1`)
- **Image:** `sha256:5693cd7d5fb460a2d164a8f22f4a0a5b9fd2c2063cdd028e88a1439bd3e3a2ea`
- **Engine SHA256:** `b29f813299b91a179716f15e73b71c5b1e4cfd1fa9060014b2aa09596795dba0`
- **Source SHA:** `d46f5f268f8ed797e83a5c63a69bffbd7a581cf6`
- **Overrides:** `{"STRATA_OOMD_ROOM": "0", "STRATA_HC_V100": "1"}`
- **Backup Verified:** 24 files (`all_match=True`)

## Phases

### `d3smoke-20261125T194733-smoke1` — `SMOKE_PASS_NOT_C2`
- Agent A: VRAM peak `15371` MiB | Power avg/peak `41.3` / `65.4` W | Temp max `40` C | Offered/Accepted `98`/`96` | OS read `5470.3` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 892 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 12.9 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 48.4 ms`
- Agent B: VRAM peak `0` MiB | Power avg/peak `25.1` / `25.1` W | Temp max `38` C | Offered/Accepted `None`/`None` | OS read `None` MB | Exp hit `None`%
