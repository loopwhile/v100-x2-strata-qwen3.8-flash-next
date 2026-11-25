# S12-D2 (`d2smoke-20261125T182822`) — Stage 12 Receipt Report

- **Generated:** 2026-11-25T18:29:34.530755+09:00
- **Verdict:** `PASS` (mode `smoke1`)
- **Image:** `sha256:922ba4eb58eebcd10a5e586de4c030cdc093ed4f1df429bc1d34b56e97cc520c`
- **Engine SHA256:** `6082be376bfd05701a740a1f408858714380c8806c8b3fba0a834ada03049dc9`
- **Source SHA:** `d46f5f268f8ed797e83a5c63a69bffbd7a581cf6`
- **Overrides:** `{"STRATA_OOMD_ROOM": "0", "STRATA_MMAP_ADAPT_ASYNC": "1", "STRATA_COLD_OVERLAP": "5"}`
- **Backup Verified:** 24 files (`all_match=True`)

## Phases

### `d2smoke-20261125T182822-smoke1` — `SMOKE_PASS_NOT_C2`
- Agent A: VRAM peak `15379` MiB | Power avg/peak `40.4` / `54.1` W | Temp max `39` C | Offered/Accepted `97`/`96` | OS read `4057.5` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 852 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 15.0 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 31.8 ms`
- Agent B: VRAM peak `0` MiB | Power avg/peak `25.1` / `25.1` W | Temp max `38` C | Offered/Accepted `None`/`None` | OS read `None` MB | Exp hit `None`%
