# S12-C1T (`c1t-20261125T205904`) — Stage 12 Receipt Report

- **Generated:** 2026-11-25T21:09:24.035206+09:00
- **Verdict:** `PASS` (mode `scored`)
- **Image:** `sha256:33b61b0432e81c44a6d212ca38be46b4191a989a65c4a0141e2cbc9b116f10ec`
- **Engine SHA256:** `c01770d00bd49985f008e39d722b996f0ad476545c8bd50bb96ad8a66ed52dda`
- **Source SHA:** `d46f5f268f8ed797e83a5c63a69bffbd7a581cf6`
- **Overrides:** `{"STRATA_OOMD_ROOM": "0", "STRATA_AVX512BW_IQ": "22", "STRATA_IQ_MT_MIN": "1", "STRATA_IQ_GATHER": "1", "STRATA_IQ256_GATHER": "1", "STRATA_Q2_BITPLANE": "1", "STRATA_MMAP_ADAPT_ASYNC": "1", "STRATA_COLD_OVERLAP": "5", "STRATA_HC_V100": "1", "STRATA_SELECT_SIMT": "1", "STRATA_ATTN_DAILY": "1", "STRATA_GR_UP75": "1", "STRATA_FUSE_WAIT": "2", "STRATA_ROUTE_TAIL_SKIP": "7"}`
- **Backup Verified:** 148 files (`all_match=True`)

## Scored C2 Medians vs S11X-D2 Reference

| Metric | This Run (A / B) | S11X-D2 Reference (A / B) | Delta (A / B) |
|---|---:|---:|---:|
| Prefill (tok/s) | 1039.4 / 1046.8 | 1032.6 / 1037.0 | +6.8 / +9.8 |
| Decode (tok/s) | 41.3 / 45.2 | 37.1 / 41.0 | +4.2 / +4.2 |
| TTFT (s) | 122.40 / 121.54 | 123.21 / 122.69 | -0.81 / -1.15 |

## Phases

### `c1t-20261125T205904-startup` — `SMOKE_PASS_NOT_C2`
- Agent A: VRAM peak `15367` MiB | Power avg/peak `41.9` / `87.0` W | Temp max `42` C | Offered/Accepted `98`/`96` | OS read `25.0` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 854 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata serve: STRATA_ROUTE_TAIL_SKIP=7 is ON: a missed expert that every token of a verify window routes at rank 7 or lower is skipped (answers differ slightly); it is off when STRATA_ROUTE_TAIL_SKIP is not set or is 0`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 13.4 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
- Agent B: VRAM peak `15367` MiB | Power avg/peak `42.5` / `74.9` W | Temp max `44` C | Offered/Accepted `98`/`96` | OS read `25.2` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 858 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata serve: STRATA_ROUTE_TAIL_SKIP=7 is ON: a missed expert that every token of a verify window routes at rank 7 or lower is skipped (answers differ slightly); it is off when STRATA_ROUTE_TAIL_SKIP is not set or is 0`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 23.8 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`

### `c1t-20261125T205904-batch-1` — `PASS`
- Prefill: `1024.7` / `1035.6` tok/s | Decode: `40.4` / `45.5` tok/s | TTFT: `124.15` / `122.87` s | Overlap: `38.99s`
- Agent A: VRAM peak `15611` MiB | Power avg/peak `101.0` / `214.5` W | Temp max `63` C | Offered/Accepted `1068`/`837` | OS read `407.7` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 852 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata serve: STRATA_ROUTE_TAIL_SKIP=7 is ON: a missed expert that every token of a verify window routes at rank 7 or lower is skipped (answers differ slightly); it is off when STRATA_ROUTE_TAIL_SKIP is not set or is 0`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 13.1 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
- Agent B: VRAM peak `15611` MiB | Power avg/peak `105.3` / `226.9` W | Temp max `64` C | Offered/Accepted `1314`/`1063` | OS read `454.1` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 861 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata serve: STRATA_ROUTE_TAIL_SKIP=7 is ON: a missed expert that every token of a verify window routes at rank 7 or lower is skipped (answers differ slightly); it is off when STRATA_ROUTE_TAIL_SKIP is not set or is 0`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 13.2 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`

### `c1t-20261125T205904-batch-2` — `PASS`
- Prefill: `1039.4` / `1046.8` tok/s | Decode: `41.3` / `45.2` tok/s | TTFT: `122.40` / `121.54` s | Overlap: `42.55s`
- Agent A: VRAM peak `15611` MiB | Power avg/peak `104.5` / `199.5` W | Temp max `67` C | Offered/Accepted `1251`/`971` | OS read `1019.7` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 852 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata serve: STRATA_ROUTE_TAIL_SKIP=7 is ON: a missed expert that every token of a verify window routes at rank 7 or lower is skipped (answers differ slightly); it is off when STRATA_ROUTE_TAIL_SKIP is not set or is 0`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 13.1 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
- Agent B: VRAM peak `15611` MiB | Power avg/peak `107.4` / `221.0` W | Temp max `65` C | Offered/Accepted `1314`/`1063` | OS read `484.2` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 863 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata serve: STRATA_ROUTE_TAIL_SKIP=7 is ON: a missed expert that every token of a verify window routes at rank 7 or lower is skipped (answers differ slightly); it is off when STRATA_ROUTE_TAIL_SKIP is not set or is 0`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 12.2 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`

### `c1t-20261125T205904-batch-3` — `PASS`
- Prefill: `1040.2` / `1048.5` tok/s | Decode: `42.5` / `44.3` tok/s | TTFT: `122.31` / `121.34` s | Overlap: `42.54s`
- Agent A: VRAM peak `15611` MiB | Power avg/peak `107.2` / `203.7` W | Temp max `68` C | Offered/Accepted `1249`/`992` | OS read `641.1` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 877 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata serve: STRATA_ROUTE_TAIL_SKIP=7 is ON: a missed expert that every token of a verify window routes at rank 7 or lower is skipped (answers differ slightly); it is off when STRATA_ROUTE_TAIL_SKIP is not set or is 0`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 13.8 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
- Agent B: VRAM peak `15611` MiB | Power avg/peak `105.4` / `220.2` W | Temp max `66` C | Offered/Accepted `1313`/`1046` | OS read `436.2` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 863 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata serve: STRATA_ROUTE_TAIL_SKIP=7 is ON: a missed expert that every token of a verify window routes at rank 7 or lower is skipped (answers differ slightly); it is off when STRATA_ROUTE_TAIL_SKIP is not set or is 0`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 13.1 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
