# S12-C1 (`c1-20261125T202739`) — Stage 12 Receipt Report

- **Generated:** 2026-11-25T20:39:45.493214+09:00
- **Verdict:** `PASS` (mode `scored`)
- **Image:** `sha256:33b61b0432e81c44a6d212ca38be46b4191a989a65c4a0141e2cbc9b116f10ec`
- **Engine SHA256:** `c01770d00bd49985f008e39d722b996f0ad476545c8bd50bb96ad8a66ed52dda`
- **Source SHA:** `d46f5f268f8ed797e83a5c63a69bffbd7a581cf6`
- **Overrides:** `{"STRATA_OOMD_ROOM": "0", "STRATA_AVX512BW_IQ": "22", "STRATA_IQ_MT_MIN": "1", "STRATA_IQ_GATHER": "1", "STRATA_IQ256_GATHER": "1", "STRATA_Q2_BITPLANE": "1", "STRATA_MMAP_ADAPT_ASYNC": "1", "STRATA_COLD_OVERLAP": "5", "STRATA_HC_V100": "1", "STRATA_SELECT_SIMT": "1", "STRATA_ATTN_DAILY": "1", "STRATA_GR_UP75": "1", "STRATA_FUSE_WAIT": "2"}`
- **Backup Verified:** 148 files (`all_match=True`)

## Scored C2 Medians vs S11X-D2 Reference

| Metric | This Run (A / B) | S11X-D2 Reference (A / B) | Delta (A / B) |
|---|---:|---:|---:|
| Prefill (tok/s) | 965.9 / 970.6 | 1032.6 / 1037.0 | -66.7 / -66.4 |
| Decode (tok/s) | 30.8 / 34.7 | 37.1 / 41.0 | -6.3 / -6.3 |
| TTFT (s) | 131.73 / 131.09 | 123.21 / 122.69 | +8.52 / +8.40 |

## Phases

### `c1-20261125T202739-startup` — `SMOKE_PASS_NOT_C2`
- Agent A: VRAM peak `15367` MiB | Power avg/peak `41.3` / `57.8` W | Temp max `40` C | Offered/Accepted `97`/`96` | OS read `2087.5` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 904 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 13.2 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 18.3 ms`
- Agent B: VRAM peak `15367` MiB | Power avg/peak `42.2` / `59.7` W | Temp max `42` C | Offered/Accepted `97`/`96` | OS read `606.3` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 898 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 12.8 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 18.2 ms`

### `c1-20261125T202739-batch-1` — `PASS`
- Prefill: `965.9` / `970.6` tok/s | Decode: `29.9` / `32.5` tok/s | TTFT: `131.73` / `131.09` s | Overlap: `44.84s`
- Agent A: VRAM peak `15611` MiB | Power avg/peak `93.9` / `199.2` W | Temp max `64` C | Offered/Accepted `1388`/`1145` | OS read `10806.0` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 853 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 13.8 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 22.3 ms`
- Agent B: VRAM peak `15611` MiB | Power avg/peak `94.6` / `216.6` W | Temp max `64` C | Offered/Accepted `1006`/`838` | OS read `10217.6` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 847 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 13.7 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 21.1 ms`

### `c1-20261125T202739-batch-2` — `PASS`
- Prefill: `962.7` / `965.6` tok/s | Decode: `30.8` / `35.0` tok/s | TTFT: `132.15` / `131.83` s | Overlap: `46.42s`
- Agent A: VRAM peak `15611` MiB | Power avg/peak `96.5` / `204.0` W | Temp max `66` C | Offered/Accepted `1440`/`1187` | OS read `9301.9` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 1011 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 23.3 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 33.6 ms`
- Agent B: VRAM peak `15611` MiB | Power avg/peak `94.5` / `211.5` W | Temp max `65` C | Offered/Accepted `1123`/`930` | OS read `8151.9` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 1018 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 22.6 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 36.3 ms`

### `c1-20261125T202739-batch-3` — `PASS`
- Prefill: `1021.1` / `1029.3` tok/s | Decode: `31.7` / `34.7` tok/s | TTFT: `124.61` / `123.62` s | Overlap: `47.24s`
- Agent A: VRAM peak `15611` MiB | Power avg/peak `95.0` / `205.4` W | Temp max `67` C | Offered/Accepted `1321`/`1083` | OS read `6144.6` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 976 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 14.3 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 40.1 ms`
- Agent B: VRAM peak `15611` MiB | Power avg/peak `96.1` / `223.3` W | Temp max `65` C | Offered/Accepted `1186`/`960` | OS read `4814.3` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 963 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 14.6 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 21.5 ms`
