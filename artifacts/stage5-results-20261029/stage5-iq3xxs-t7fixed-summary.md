# Stage 5 IQ3_XXS — T7-Fixed dual-agent C2

Measured 2026-10-29 on P520. Three independent fresh-process batches, same T7-Fixed environment and topology as the historical IQ3_S Stage 5 comparison. This is an isolated quantization trial, not a production promotion or an IQ3_S Stage 6 result.

| Batch | A prefill | B prefill | A decode | B decode | A TTFT | B TTFT | A/B outputs | Batch wall | Decode overlap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| 1 | 822.6 | 827.3 | 26.4 | 26.7 | 154.60 s | 153.74 s | 1460 / 2265 | 238.71 s | 55.31 s |
| 2 | 1030.7 | 1044.9 | 26.6 | 25.5 | 123.46 s | 121.78 s | 1458 / 2361 | 214.49 s | 54.91 s |
| 3 | 1041.8 | 1051.9 | 26.6 | 27.1 | 122.11 s | 120.97 s | 1458 / 2336 | 207.22 s | 54.97 s |
| Median | 1030.7 | 1044.9 | 26.6 | 26.7 | 123.46 s | 121.78 s | — | 214.49 s | 54.97 s |

Rates are tokens/s. All runs passed the harness's mechanical, active-overlap and post-health checks; A/B prompts were 126967/126968 tokens, outputs were at least 1024, cache_n and cached_tokens were zero, and there was no request warmup after process restart. Zero prompt-prefix reuse does not imply cold Linux page cache: copy, verification, smoke, and earlier batches warmed or changed the cache. Output lengths differ and affect batch wall time. The short JSON calculation smoke passed on both agents; this is not a comprehensive coding-quality evaluation.

Historical IQ3_S T7-Fixed three-batch medians: A/B prefill 891.4/919.4 tok/s and decode 21.4/21.4 tok/s ([source](../stage5-results-20261027/stage5-t7-jmnargi-summary.md)). These are historical, non-interleaved runs, with different cache conditions and output lengths; they are not a controlled causal comparison. Whether the configured WMMA2 kernel actually executed on IQ3_XXS is not established by the available logs.

## Configuration and observations

- Image `strata-v100-jmnargi:2c9b1dd`, inspected ID `sha256:5b62fa861bbdb346f81b0b3edf88ee21396fb4e59795a14b2b092dfa2e4aa156`; native engine SHA-256 `f0da5abf41115c9c0707751ec940f0f1977d04c690b55713cd19b2b7ba815030`. The historical Stage 5 report records a different full image ID; the engine hash matches its receipt.
- `STRATA_SM70_PERF=0`, `STRATA_SELECT_SIMT=1`, `STRATA_PF_WMMA=1`, `STRATA_PF_WMMA2=1`, `STRATA_STAGER_SSD=0`; inspected in both trial containers.
- A: physical GPU0, cpuset `0-2,6-8`, loopback 18084. B: physical GPU1, cpuset `3-5,9-11`, loopback 18085. Model is shared IQ3_XXS files, independent servers, 131072 context, int8 KV, resident 32768, spec 4, min-p 0.5, mmap experts, shared MTP.
- C2 manifest SHA-256 `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`. Config SHA-256: A `ea499fcd6268820a1f2beec9108b798af1b3e95e5bbc97f9499ecc95ea9c208a`, B `3e7768a9992e54af0823121f9494dbb5c0f81de0aee00a4ac50eb44b88e87ed8`.
- IQ3_XXS copied from `/srv/backup/models-archive/strata-iq3xxs` to `/srv/models/strata-iq3xxs`. GGUF shard SHA-256 values matched source and destination: `219ea929900dfa9ef091f3aa473fdba6874b65fcb36526d7d851ac9e95856d15` and `316b46f3a2dbd68c900f43136ab9449f9dcc3725dfd8c794847c204bc161e113`; remaining files compared with rsync checksum.
- Engine logged free-VRAM warnings: 499 MiB at initial request and about 273 MiB after graph capture, below its 512 MiB warning threshold. No OOM occurred. Host-wide `pgmajfault` deltas during the three measured runs were 550, 3 and 60; swap-ins were 0 and swap-outs were 3, 0 and 0 pages. These are host counters, not isolated process faults. Host swap use shown before/after runs was approximately 16 KiB.
- Test containers `strata-s5-iq3xxs-trial-a/b` were stopped after testing and left intact. GPUs returned to 0 MiB used; power limits remained 150 W. Preserved containers and the tunnel were not modified.

## Evidence and restoration

P520 raw directories: `~/v100-x2-strata-qwen3.8-flash-next/results/c2-stage5-t7fixed-iq3xxs-20261029-150844-run1`, `...-20261029-151313-run2`, `...-20261029-151717-run3`. The P520 `results/stage5-iq3xxs/` directory holds the isolated configs, runner scripts, console logs, smoke responses and preserved IQ3_S logs/configs. Raw logs and responses may contain request text and should be reviewed before sharing.

At the user's request, `/srv/models/strata-iq3s` was removed after a checksum comparison with `/srv/backup/models-archive/strata-iq3s` (excluding logs). Original IQ3_S logs and configs were separately copied to `results/stage5-iq3xxs/preserved-iq3s-logs/` and `preserved-iq3s-config/`. Current `/srv/models` free space was about 79 GiB after the IQ3_XXS copy, while IQ3_S occupied about 80 GiB; Stage 6 requires restoring IQ3_S and may require first reclaiming space from the new IQ3_XXS copy. Verify the archive, stop any users of the files, preserve new evidence, restore with `rsync -a` and checksum-verify before resuming Stage 6. Do not delete or modify preserved containers, historical results or shared MTP.
