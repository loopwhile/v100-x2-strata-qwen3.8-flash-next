# S12-P1 (`p1smoke-20261125T190817`) — Stage 12 Receipt Report

- **Generated:** 2026-11-25T19:09:13.809475+09:00
- **Verdict:** `PASS` (mode `smoke1`)
- **Image:** `sha256:0cbf5d14914b0dc2ca7b62686f976937395cc56ee5ffb17eb35a8bcb13927b51`
- **Engine SHA256:** `ec05dafc29e93dffaaa97ffdb97ae21c7be6477793492b5db504af26a2b45221`
- **Source SHA:** `d46f5f268f8ed797e83a5c63a69bffbd7a581cf6`
- **Overrides:** `{"STRATA_OOMD_ROOM": "0", "STRATA_PF_WMMA": "1", "STRATA_PF_WMMA2": "1", "STRATA_PF_WMMA_LEAN": "1", "STRATA_PF_WMMA_SKINNY": "1"}`
- **Backup Verified:** 24 files (`all_match=True`)

## Phases

### `p1smoke-20261125T190817-smoke1` — `SMOKE_PASS_NOT_C2`
- Agent A: VRAM peak `15379` MiB | Power avg/peak `40.5` / `49.8` W | Temp max `39` C | Offered/Accepted `97`/`96` | OS read `5454.7` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 890 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 15.3 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 30.3 ms`
- Agent B: VRAM peak `0` MiB | Power avg/peak `25.5` / `25.6` W | Temp max `38` C | Offered/Accepted `None`/`None` | OS read `None` MB | Exp hit `None`%
