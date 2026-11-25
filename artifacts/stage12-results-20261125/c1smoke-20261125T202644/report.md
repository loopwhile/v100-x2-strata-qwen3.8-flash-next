# S12-C1 (`c1smoke-20261125T202644`) — Stage 12 Receipt Report

- **Generated:** 2026-11-25T20:27:21.112139+09:00
- **Verdict:** `PASS` (mode `smoke1`)
- **Image:** `sha256:33b61b0432e81c44a6d212ca38be46b4191a989a65c4a0141e2cbc9b116f10ec`
- **Engine SHA256:** `c01770d00bd49985f008e39d722b996f0ad476545c8bd50bb96ad8a66ed52dda`
- **Source SHA:** `d46f5f268f8ed797e83a5c63a69bffbd7a581cf6`
- **Overrides:** `{"STRATA_OOMD_ROOM": "0", "STRATA_AVX512BW_IQ": "22", "STRATA_IQ_MT_MIN": "1", "STRATA_IQ_GATHER": "1", "STRATA_IQ256_GATHER": "1", "STRATA_Q2_BITPLANE": "1", "STRATA_MMAP_ADAPT_ASYNC": "1", "STRATA_COLD_OVERLAP": "5", "STRATA_HC_V100": "1", "STRATA_SELECT_SIMT": "1", "STRATA_ATTN_DAILY": "1", "STRATA_GR_UP75": "1", "STRATA_FUSE_WAIT": "2"}`
- **Backup Verified:** 24 files (`all_match=True`)

## Phases

### `c1smoke-20261125T202644-smoke1` — `SMOKE_PASS_NOT_C2`
- Agent A: VRAM peak `15367` MiB | Power avg/peak `40.6` / `52.2` W | Temp max `40` C | Offered/Accepted `97`/`96` | OS read `5184.6` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 1141 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 12.8 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 36.0 ms`
- Agent B: VRAM peak `0` MiB | Power avg/peak `25.5` / `25.6` W | Temp max `38` C | Offered/Accepted `None`/`None` | OS read `None` MB | Exp hit `None`%
