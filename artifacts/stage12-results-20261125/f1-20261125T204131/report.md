# S12-F1 (`f1-20261125T204131`) — Stage 12 Receipt Report

- **Generated:** 2026-11-25T20:53:16.807644+09:00
- **Verdict:** `PASS` (mode `scored`)
- **Image:** `sha256:33b61b0432e81c44a6d212ca38be46b4191a989a65c4a0141e2cbc9b116f10ec`
- **Engine SHA256:** `c01770d00bd49985f008e39d722b996f0ad476545c8bd50bb96ad8a66ed52dda`
- **Source SHA:** `d46f5f268f8ed797e83a5c63a69bffbd7a581cf6`
- **Overrides:** `{"STRATA_OOMD_ROOM": "0", "STRATA_AVX512BW_IQ": "22", "STRATA_IQ_MT_MIN": "1", "STRATA_IQ_GATHER": "1", "STRATA_IQ256_GATHER": "1", "STRATA_Q2_BITPLANE": "1", "STRATA_MMAP_ADAPT_ASYNC": "1", "STRATA_COLD_OVERLAP": "5", "STRATA_HC_V100": "1", "STRATA_SELECT_SIMT": "1", "STRATA_ATTN_DAILY": "1", "STRATA_GR_UP75": "1", "STRATA_FUSE_WAIT": "2"}`
- **Backup Verified:** 148 files (`all_match=True`)

## Scored C2 Medians vs S11X-D2 Reference

| Metric | This Run (A / B) | S11X-D2 Reference (A / B) | Delta (A / B) |
|---|---:|---:|---:|
| Prefill (tok/s) | 1032.7 / 1043.2 | 1032.6 / 1037.0 | +0.1 / +6.2 |
| Decode (tok/s) | 31.6 / 35.9 | 37.1 / 41.0 | -5.5 / -5.1 |
| TTFT (s) | 123.21 / 121.97 | 123.21 / 122.69 | +0.00 / -0.72 |

## Phases

### `f1-20261125T204131-startup` — `SMOKE_PASS_NOT_C2`
- Agent A: VRAM peak `15367` MiB | Power avg/peak `41.9` / `62.5` W | Temp max `43` C | Offered/Accepted `97`/`96` | OS read `555.1` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 877 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 13.6 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 18.5 ms`
- Agent B: VRAM peak `15367` MiB | Power avg/peak `44.2` / `81.0` W | Temp max `45` C | Offered/Accepted `97`/`96` | OS read `204.1` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 860 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 14.2 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 18.3 ms`

### `f1-20261125T204131-batch-1` — `PASS`
- Prefill: `1041.0` / `1051.9` tok/s | Decode: `31.0` / `35.9` tok/s | TTFT: `122.24` / `120.97` s | Overlap: `47.49s`
- Agent A: VRAM peak `15611` MiB | Power avg/peak `97.5` / `211.2` W | Temp max `66` C | Offered/Accepted `1492`/`1193` | OS read `1106.7` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 869 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 12.3 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 18.0 ms`
- Agent B: VRAM peak `15611` MiB | Power avg/peak `97.8` / `211.0` W | Temp max `65` C | Offered/Accepted `1214`/`989` | OS read `607.7` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 857 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 12.9 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 18.0 ms`

### `f1-20261125T204131-batch-2` — `PASS`
- Prefill: `1022.1` / `1029.9` tok/s | Decode: `32.0` / `35.9` tok/s | TTFT: `124.48` / `123.54` s | Overlap: `43.43s`
- Agent A: VRAM peak `15611` MiB | Power avg/peak `96.5` / `204.7` W | Temp max `67` C | Offered/Accepted `1388`/`1083` | OS read `1151.4` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 996 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 13.8 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 18.4 ms`
- Agent B: VRAM peak `15611` MiB | Power avg/peak `102.3` / `217.8` W | Temp max `65` C | Offered/Accepted `1087`/`893` | OS read `559.9` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 1006 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 13.6 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 18.1 ms`

### `f1-20261125T204131-batch-3` — `PASS`
- Prefill: `1032.7` / `1043.2` tok/s | Decode: `31.6` / `35.3` tok/s | TTFT: `123.21` / `121.97` s | Overlap: `46.56s`
- Agent A: VRAM peak `15611` MiB | Power avg/peak `99.9` / `200.6` W | Temp max `68` C | Offered/Accepted `1458`/`1154` | OS read `795.2` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 846 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 13.1 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 18.4 ms`
- Agent B: VRAM peak `15611` MiB | Power avg/peak `99.0` / `214.2` W | Temp max `66` C | Offered/Accepted `1182`/`976` | OS read `439.5` MB | Exp hit `None`%
  - `strata prefill: warmed the BF16 and FP16 GEMM libraries on GPU 0 in 860 ms (STRATA_PREFILL_WARM=0 skips)`
  - `strata verify: window up to 8 tokens, 81.8 MiB of device buffers`
  - `strata verify: capturing the 1-token window (915 MiB of VRAM free)`
  - `strata verify: captured the 1-token window (upload no error, sync no error) in 12.7 ms`
  - `strata verify: capturing the 2-token window (899 MiB of VRAM free)`
  - `strata verify: captured the 2-token window (upload no error, sync no error) in 17.7 ms`
