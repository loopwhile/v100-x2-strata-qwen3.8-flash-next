# S12-U0 (`u0smoke-20261125T162323`) — Stage 12 Receipt Report

- **Generated:** 2026-11-25T16:25:00.743502+09:00
- **Verdict:** `PASS` (mode `smoke1`)
- **Image:** `sha256:5ee459198a4b9c695183bf5901c17ff6b68019381c6b70c72a138fb76d27e93d`
- **Engine SHA256:** `79076b85b0450c86edb5c7bbee54a4c60cd00f564e9adb7058d9e00bc3b50c49`
- **Source SHA:** `a34979fc94f3d126b9bb8210f4ad311345688b52`
- **Overrides:** `{}`
- **Backup Verified:** 24 files (`all_match=True`)

## Phases

### `u0smoke-20261125T162323-smoke1` — `SMOKE_PASS_NOT_C2`
- Agent A: VRAM peak `15379` MiB | Power avg/peak `40.8` / `56.4` W | Temp max `40` C | Offered/Accepted `98`/`96` | OS read `28785.9` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 929 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 17.7 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 39.0 ms`
- Agent B: VRAM peak `0` MiB | Power avg/peak `25.5` / `25.6` W | Temp max `38` C | Offered/Accepted `None`/`None` | OS read `None` MB | Exp hit `None`%
