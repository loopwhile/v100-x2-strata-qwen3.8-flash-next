# S12-D1 (`d1smoke-20261125T174823`) — Stage 12 Receipt Report

- **Generated:** 2026-11-25T18:03:23.283584+09:00
- **Verdict:** `PASS` (mode `smoke1`)
- **Image:** `sha256:9d5f636459eecd28a846d88fbed7870e9d281194de4d55794623185d203b7a05`
- **Engine SHA256:** `d1010753103c9f895bb5797c5c2d2ab519c5de10077ea0ccd7116f5d0e26c078`
- **Source SHA:** `d46f5f268f8ed797e83a5c63a69bffbd7a581cf6`
- **Overrides:** `{"STRATA_OOMD_ROOM": "0", "STRATA_AVX512BW_IQ": "22", "STRATA_IQ_MT_MIN": "1", "STRATA_IQ_GATHER": "1", "STRATA_IQ256_GATHER": "1", "STRATA_Q2_BITPLANE": "1"}`
- **Backup Verified:** 24 files (`all_match=True`)

## Phases

### `d1smoke-20261125T174823-smoke1` — `SMOKE_PASS_NOT_C2`
- Agent A: VRAM peak `15379` MiB | Power avg/peak `41.4` / `67.7` W | Temp max `39` C | Offered/Accepted `98`/`96` | OS read `8752.9` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 1163 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 15.2 ms`
  - `strata verify: capturing the 2-token window (897 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 37.1 ms`
- Agent B: VRAM peak `0` MiB | Power avg/peak `25.1` / `25.5` W | Temp max `38` C | Offered/Accepted `None`/`None` | OS read `None` MB | Exp hit `None`%
