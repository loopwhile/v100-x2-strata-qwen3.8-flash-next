# Stage 11X S11X-P0 Receipt: `p0-20261119T035717`

- **Verdict**: `PASS`
- **Host**: `p520-llm` (boot `e80b19de-4242-4e94-b756-6f500d43a07b`)
- **Engine**: `sha256:dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d` (`ccca488231f12da4...`)
- **Overrides**: `{"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1", "STRATA_PREFILL_TIMING": "1", "STRATA_DECODE_TIMING": "1", "STRATA_VERIFY_PROFILE": "1"}`
- **DFlash2 Config**: `spec 8`, `conf 0.7`, `prefill auto`

## Diagnostic C2 Batch (Non-Scored)

| Phase | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Overlap | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| p0-20261119T035717-diagnostic-1 | 822.9 | 826.1 | 28.8 | 28.5 | 154.56 | 153.97 | Yes | DIAGNOSTIC_PASS_NOT_SCORED |

### Agent A Profiling Notes (`p0-20261119T035717-diagnostic-1`)
```text
[strata] 2026-11-18 18:58:36 engine started: /opt/strata/engine/strata --serve --pack /stage10-data/packs/iq3_xxs-native --native /iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf --ple-gguf /iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf --expert-profile /opt/strata/data/expert-profile.bin --mmap-experts --max-context 131072 --kv int8 --kv-resident 32768 --spec 8 --prefill auto --expert-cache auto --draft dflash2 --draft-model /stage10-data/dflash2/qwen3.8-flash-next-dflash2.q4_0-selq4.pack --draft-fallback none --mtp-draft-vocab /shared-mtp/rt/draft_vocab.bin --draft-conf 0.7
strata generate: memory guard: limit 61.1 GiB (source: meminfo), current 2.3 GiB, reclaimable cache credited 0.0 GiB; available 58.8 GiB (MemAvailable 58.8 GiB), floor 2560 MiB
strata generate: CPU expert kernels: AVX-2
strata generate: native pack: /stage10-data/packs/iq3_xxs-native experts (largest blob 2.33 MB), token embedding IQ3_S in mapped host memory (260 MiB, 0.3 s)
strata generate: profile /opt/strata/data/expert-profile.bin: 24576 ranked pairs, built for 24576 slots
strata generate: KV streaming: 32768 of 131072 cells per QSA layer in VRAM, the K/V in 1.55 GiB of pinned RAM
strata generate: experts via mmap (--mmap-experts; the GGUF shards in place, no experts.bin)
strata generate: file tier (Linux defaults, the GGUF read in place): page-cached experts computed from the mapping (STRATA_COLD_OVERLAP=4), io prefetch with whole-blob preads on 8 I/O threads, the decode's read-ahead only while the page cache has room for it and it pays (STRATA_IO_PF_GATE=1); off: STRATA_COLD_OVERLAP=0, STRATA_IO_PREFETCH=0, STRATA_IO_PF_GATE=0
strata generate: expert cache auto: 10.43 GiB free, 700 MiB reserved (+346 MiB for the draft head, +256 MiB for what is allocated after the cache) -> 4221 slots
strata generate: expert cache 5653 slots, 9.16 GiB of VRAM; policy is
strata generate: the GPU computes the experts in the cache; it rounds differently from the CPU,
                 so a reply can differ slightly from a run without the cache (same quality:
                 bench/results/2026-09-27-cache-parity).
strata generate: R4 hit path ON - resident experts are computed on the GPU
strata generate: 2 expert-pool workers + the host thread
strata generate: token graph hit path: 5653 resident experts, decided on the device
prefill: the CPU share is ON by default for prompt chunks up to 3072 tokens (the idle CPU takes some of the experts the GPU would stream; answers can differ slightly from 0.1.40.3, mean KL ~0.004 below 1024 tokens, ~0.011 at 1-3K). STRATA_PREFILL_CPU_SHARE=0 turns it off, STRATA_PREFILL_CPU_SHARE_MAX=1024 keeps the old limit.
strata: prefill plan: chunk 8192, ring 96 kept: file set 35.1 GiB fits the page cache 51.7 GiB -> about 0.0 GB read from the drive per 32768-token prompt (4 chunks)
strata: prefill plan inputs: 40.0 GiB experts, 9.2 GiB in the GPU caches, 0.0 GiB RAM copy (0 lend slots kept), file tier 30.8 GiB; 51.7 GiB available for the page cache; PCIe 12.3 GB/s; drive 2.50 GB/s (nvme1n1 is NVMe); a 32768-token prompt
strata serve: prompt chunk auto: 8192 tokens, a 96-slot ring
strata serve: the prompt path borrows 2489 CUDA0 cache slots (3.99 GiB)
strata verify: window up to 8 tokens, 81.5 MiB of device buffers
strata dflash2: 106299-token draft head (178.4 MiB), drafter 591 MiB of VRAM (Q4_0 weights)
strata dflash2: selector codebooks: Q4_0 rows (about 174 MiB less than bf16)
strata serve: DFlash2 drafter on (/stage10-data/dflash2/qwen3.8-flash-next-dflash2.q4_0-selq4.pack, graphs captured in 4 ms); windows up to 8 tokens; no MTP layer is loaded (--draft-fallback none)
strata serve: conversation cache sized from the free RAM: 8192 MiB for up to 4 parked conversations, so an agent's next turn reuses its prompt (--conversation-cache-mib N sets it, 0 turns it off)
strata serve: PCIe share: start 0.65 from 2 pool workers (assumed 8 GB/s of expert bytes) and the 12.3 GB/s link (was 0.34)
strata serve: STRATA_ROUTE_TAIL_SKIP=7 is ON (default): a missed expert that every token of a verify window routes at rank 7 or lower is skipped (+10..20% decode on 12-16 GB cards that miss experts, answers differ slightly from 0.1.41); STRATA_ROUTE_TAIL_SKIP=0 turns it off
strata prefill: QSA layers: norm + rope in one pass on, attention gate in the attention epilogue off
strata prefill timing: 126960 tokens, GPU timeline 152874 ms, wall 152924 ms, host staging 122320 ms: embed+steps 738 (0.5%) hc read 40 (0.0%) gdn 5910 (3.9%) qsa proj 2984 (2.0%) qsa indexer 4 (0.0%) qsa select 4726 (3.1%) qsa attn 9792 (6.4%) router+shared 1962 (1.3%) host grouping 1165 (0.8%) gather 798 (0.5%) wait copy 6164 (4.0%) dequant 59914 (39.2%) gemm gate/up 24817 (16.2%) gemm down 12639 (8.3%) combine 940 (0.6%) ple 639 (0.4%) kv stage 1284 (0.8%) gdn conv+gates 510 (0.3%) gdn recurrence 4997 (3.3%) gdn out proj 2020 (1.3%) hc write 3250 (2.1%) hc read: down+silu 2610 (1.7%) hc read: up 1695 (1.1%) hc read: inject 1497 (1.0%) hc read: mix 1585 (1.0%) qsa: indexer gemms 177 (0.1%) qsa: norm/rope/kv append/q prep 15 (0.0%)
strata prefill timing: host: chunk setup (PLE rows, the expert stream plan) 152 ms, waiting for each chunk 209 ms, after each chunk (the draft layer, progress) 583 ms, PLE 328 ms
strata verify: capturing the 6-token window (709 MiB of VRAM free)
strata verify: captured the 6-token window (upload no error, sync no error) in 26.5 ms
strata verify: capturing the 1-token window (685 MiB of VRAM free)
strata verify: captured the 1-token window (upload no error, sync no error) in 24.9 ms
strata verify: capturing the 4-token window (663 MiB of VRAM free)
strata verify: captured the 4-token window (upload no error, sync no error) in 30.5 ms
strata verify: capturing the 2-token window (639 MiB of VRAM free)
strata verify: captured the 2-token window (upload no error, sync no error) in 27.8 ms
strata verify: capturing the 3-token window (617 MiB of VRAM free)
strata verify: captured the 3-token window (upload no error, sync no error) in 30.8 ms
strata verify: capturing the 8-token window (593 MiB of VRAM free)
strata verify: captured the 8-token window (upload no error, sync no error) in 27.3 ms
strata verify: capturing the 5-token window (571 MiB of VRAM free)
strata verify: captured the 5-token window (upload no error, sync no error) in 28.2 ms
strata verify: capturing the 7-token window (549 MiB of VRAM free)
strata verify: captured the 7-token window (upload no error, sync no error) in 30.1 ms
strata serve: PCIe share: the CPU pool takes 334 us per missed expert (5.2 GB/s of expert bytes), the link 12.3 GB/s -> pcie_frac 0.75 (was 0.65; --pcie-frac N fixes it, STRATA_PCIE_FRAC_DEFAULT=old keeps the start-up rule)
strata decode timing: 903 windows, avg T 2.59, 2.23 tokens/window, 77.58 ms/window = adapt wait 0.02 + verify 64.89 (GPU-reach wait 21.43 + per-layer host 40.38 [plan 0.27 actq 0.18 jobs 2.78 CPU 36.87] + stage 0.02) + commit/emit 0.05 + draft 3.16 + adapt join 9.43 + other 0.02; per layer-window: CPU experts 2.41 (3.27 entries), VRAM hits 21.03, PCIe 0.00; 22.1 swaps/window
strata decode GPU stages (ms/window): GDN layers: q8+qkv/q-idx gemv 1.89 conv 0.20 ab 0.51 z 1.18 rec 0.58 out-proj 1.31 router+plan+bell 1.31 shared+quant 1.62 waitA 1.49 VRAM hits 2.98 waitB 0.40 PCIe grp 0.37 waitCPU 29.30 copy+combine 0.69 (gap) 0.08 head 1.10   hc0 norm 0.57   hc0 down 0.89   hc0 up 0.79   hc1 norm 0.34   hc1 down 0.86   hc1 up 0.76 | QSA layers: q8+kv-idx 0.14 k/v+norm-rope 0.29 kv+idx append 0.18 q+q-idx 0.89 scores+topk 2.22 kv-resolve 0.36 attention 0.73 gate 0.06 out-proj 0.49 router+plan+bell 0.44 shared+quant 0.54 waitA 0.12 VRAM hits 1.00 waitB 0.13 PCIe grp 0.12 waitCPU 6.13 copy+combine 0.22 (gap) 0.03   hc0 norm 0.11   hc0 down 0.30   hc0 up 0.26   hc1 norm 0.12   hc1 down 0.30   hc1 up 0.26 | total 64.67 ms/window over 904 windows
strata serve: prompt 126967 tokens = 0 reused + 126967 read in 154298 ms (822.9 tok/s), 2017 generated in 70053 ms (28.8 tok/s), drafts accepted 1114 of 1437, 6 checkpoints
strata serve: decode expert cache hit rate: 86.5% (911525 hits / 1053184 lookups)
strata serve: route tail skip: 66349 missed experts skipped (70272 entries) since the start
strata serve: expert tiers: GPU 911525 hits this request; since the start RAM 0 blobs, files 0 blobs 829209.3 MB read (the GGUF in place)
strata serve: file tier I/O this request: the OS read 21166.4 MB from storage (2078 major faults) for 829209.3 MB of expert reads; page cache held 796754.0 MB at the read, not 32455.3 MB; io prefetch: 79 read ahead (37171.2 MB by pread), 46 used, 33 unused, 28229 skipped (cached), 0 dropped; decode waited 10335.5 ms in 29584 fetches; decode gate: cache room 1.22 of the experts, read-ahead used 60%, page cache held 100% of the decode's reads (EWMA), closed, closed in 839 windows so far, 7 flips; read ahead 136.2 MB, 79.7 MB of it used; 0 late, 0 not admitted (confidence), 0 (budget 0 MB/window)
strata serve: KV streaming: 98.39% of 14455992 block reads hit VRAM, 936.1 MiB read from RAM
strata serve: suffix drafts: 14 windows, 20 of 29 drafts accepted
[strata] drafting: DFlash2 alone (--draft dflash2, --draft-conf 0.7)
[strata] mapping the experts from the model files (about 47 GB, --mmap-experts): they are not loaded into RAM - the OS file cache reads them as the GPU's expert cache fills and as requests need them.
[strata] filling the GPU's expert cache (5653 experts, 9.16 GiB of VRAM) ...
[strata] done: 2017 tokens in 224 s (28.8 tok/s) (stop, cancel=False), expert cache 86.5% hit
```

### Agent B Profiling Notes (`p0-20261119T035717-diagnostic-1`)
```text
[strata] 2026-11-18 18:58:36 engine started: /opt/strata/engine/strata --serve --pack /stage10-data/packs/iq3_xxs-native --native /iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf --ple-gguf /iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf --expert-profile /opt/strata/data/expert-profile.bin --mmap-experts --max-context 131072 --kv int8 --kv-resident 32768 --spec 8 --prefill auto --expert-cache auto --draft dflash2 --draft-model /stage10-data/dflash2/qwen3.8-flash-next-dflash2.q4_0-selq4.pack --draft-fallback none --mtp-draft-vocab /shared-mtp/rt/draft_vocab.bin --draft-conf 0.7
strata generate: memory guard: limit 61.1 GiB (source: meminfo), current 2.8 GiB, reclaimable cache credited 0.0 GiB; available 58.3 GiB (MemAvailable 58.3 GiB), floor 2560 MiB
strata generate: CPU expert kernels: AVX-2
strata generate: native pack: /stage10-data/packs/iq3_xxs-native experts (largest blob 2.33 MB), token embedding IQ3_S in mapped host memory (260 MiB, 0.2 s)
strata generate: profile /opt/strata/data/expert-profile.bin: 24576 ranked pairs, built for 24576 slots
strata generate: KV streaming: 32768 of 131072 cells per QSA layer in VRAM, the K/V in 1.55 GiB of pinned RAM
strata generate: experts via mmap (--mmap-experts; the GGUF shards in place, no experts.bin)
strata generate: file tier (Linux defaults, the GGUF read in place): page-cached experts computed from the mapping (STRATA_COLD_OVERLAP=4), io prefetch with whole-blob preads on 8 I/O threads, the decode's read-ahead only while the page cache has room for it and it pays (STRATA_IO_PF_GATE=1); off: STRATA_COLD_OVERLAP=0, STRATA_IO_PREFETCH=0, STRATA_IO_PF_GATE=0
strata generate: expert cache auto: 10.43 GiB free, 700 MiB reserved (+346 MiB for the draft head, +256 MiB for what is allocated after the cache) -> 4221 slots
strata generate: expert cache 5653 slots, 9.16 GiB of VRAM; policy is
strata generate: the GPU computes the experts in the cache; it rounds differently from the CPU,
                 so a reply can differ slightly from a run without the cache (same quality:
                 bench/results/2026-09-27-cache-parity).
strata generate: R4 hit path ON - resident experts are computed on the GPU
strata generate: 2 expert-pool workers + the host thread
strata generate: token graph hit path: 5653 resident experts, decided on the device
prefill: the CPU share is ON by default for prompt chunks up to 3072 tokens (the idle CPU takes some of the experts the GPU would stream; answers can differ slightly from 0.1.40.3, mean KL ~0.004 below 1024 tokens, ~0.011 at 1-3K). STRATA_PREFILL_CPU_SHARE=0 turns it off, STRATA_PREFILL_CPU_SHARE_MAX=1024 keeps the old limit.
strata: prefill plan: chunk 8192, ring 96 kept: file set 35.1 GiB fits the page cache 51.7 GiB -> about 0.0 GB read from the drive per 32768-token prompt (4 chunks)
strata: prefill plan inputs: 40.0 GiB experts, 9.2 GiB in the GPU caches, 0.0 GiB RAM copy (0 lend slots kept), file tier 30.8 GiB; 51.7 GiB available for the page cache; PCIe 12.3 GB/s; drive 2.50 GB/s (nvme1n1 is NVMe); a 32768-token prompt
strata serve: prompt chunk auto: 8192 tokens, a 96-slot ring
strata serve: the prompt path borrows 2489 CUDA0 cache slots (3.99 GiB)
strata verify: window up to 8 tokens, 81.5 MiB of device buffers
strata dflash2: 106299-token draft head (178.4 MiB), drafter 591 MiB of VRAM (Q4_0 weights)
strata dflash2: selector codebooks: Q4_0 rows (about 174 MiB less than bf16)
strata serve: DFlash2 drafter on (/stage10-data/dflash2/qwen3.8-flash-next-dflash2.q4_0-selq4.pack, graphs captured in 4 ms); windows up to 8 tokens; no MTP layer is loaded (--draft-fallback none)
strata serve: conversation cache sized from the free RAM: 8192 MiB for up to 4 parked conversations, so an agent's next turn reuses its prompt (--conversation-cache-mib N sets it, 0 turns it off)
strata serve: PCIe share: start 0.65 from 2 pool workers (assumed 8 GB/s of expert bytes) and the 12.3 GB/s link (was 0.34)
strata serve: STRATA_ROUTE_TAIL_SKIP=7 is ON (default): a missed expert that every token of a verify window routes at rank 7 or lower is skipped (+10..20% decode on 12-16 GB cards that miss experts, answers differ slightly from 0.1.41); STRATA_ROUTE_TAIL_SKIP=0 turns it off
strata prefill: QSA layers: norm + rope in one pass on, attention gate in the attention epilogue off
strata prefill timing: 126961 tokens, GPU timeline 152259 ms, wall 152310 ms, host staging 121669 ms: embed+steps 703 (0.5%) hc read 40 (0.0%) gdn 5905 (3.9%) qsa proj 3007 (2.0%) qsa indexer 4 (0.0%) qsa select 4755 (3.1%) qsa attn 10050 (6.6%) router+shared 1975 (1.3%) host grouping 1118 (0.7%) gather 803 (0.5%) wait copy 5741 (3.8%) dequant 58546 (38.5%) gemm gate/up 25637 (16.8%) gemm down 12865 (8.4%) combine 953 (0.6%) ple 655 (0.4%) kv stage 1286 (0.8%) gdn conv+gates 510 (0.3%) gdn recurrence 4998 (3.3%) gdn out proj 2013 (1.3%) hc write 3155 (2.1%) hc read: down+silu 2572 (1.7%) hc read: up 1688 (1.1%) hc read: inject 1503 (1.0%) hc read: mix 1585 (1.0%) qsa: indexer gemms 177 (0.1%) qsa: norm/rope/kv append/q prep 15 (0.0%)
strata prefill timing: host: chunk setup (PLE rows, the expert stream plan) 135 ms, waiting for each chunk 216 ms, after each chunk (the draft layer, progress) 552 ms, PLE 338 ms
strata verify: capturing the 6-token window (709 MiB of VRAM free)
strata verify: captured the 6-token window (upload no error, sync no error) in 30.4 ms
strata verify: capturing the 1-token window (685 MiB of VRAM free)
strata verify: captured the 1-token window (upload no error, sync no error) in 26.7 ms
strata verify: capturing the 3-token window (663 MiB of VRAM free)
strata verify: captured the 3-token window (upload no error, sync no error) in 30.8 ms
strata verify: capturing the 2-token window (639 MiB of VRAM free)
strata verify: captured the 2-token window (upload no error, sync no error) in 29.3 ms
strata verify: capturing the 4-token window (617 MiB of VRAM free)
strata verify: captured the 4-token window (upload no error, sync no error) in 30.7 ms
strata verify: capturing the 5-token window (593 MiB of VRAM free)
strata verify: captured the 5-token window (upload no error, sync no error) in 27.0 ms
strata serve: PCIe share: the CPU pool takes 330 us per missed expert (5.3 GB/s of expert bytes), the link 12.3 GB/s -> pcie_frac 0.75 (was 0.65; --pcie-frac N fixes it, STRATA_PCIE_FRAC_DEFAULT=old keeps the start-up rule)
strata verify: capturing the 8-token window (571 MiB of VRAM free)
strata verify: captured the 8-token window (upload no error, sync no error) in 25.8 ms
strata verify: capturing the 7-token window (549 MiB of VRAM free)
strata verify: captured the 7-token window (upload no error, sync no error) in 26.6 ms
strata decode timing: 923 windows, avg T 2.38, 2.05 tokens/window, 72.13 ms/window = adapt wait 0.02 + verify 59.85 (GPU-reach wait 20.85 + per-layer host 35.99 [plan 0.26 actq 0.18 jobs 2.93 CPU 32.35] + stage 0.02) + commit/emit 0.06 + draft 3.16 + adapt join 9.02 + other 0.03; per layer-window: CPU experts 2.13 (2.76 entries), VRAM hits 19.56, PCIe 0.00; 22.0 swaps/window
strata decode GPU stages (ms/window): GDN layers: q8+qkv/q-idx gemv 1.81 conv 0.20 ab 0.47 z 1.14 rec 0.57 out-proj 1.27 router+plan+bell 1.26 shared+quant 1.58 waitA 1.50 VRAM hits 2.86 waitB 0.40 PCIe grp 0.37 waitCPU 26.26 copy+combine 0.66 (gap) 0.08 head 1.04   hc0 norm 0.54   hc0 down 0.86   hc0 up 0.76   hc1 norm 0.33   hc1 down 0.82   hc1 up 0.74 | QSA layers: q8+kv-idx 0.13 k/v+norm-rope 0.28 kv+idx append 0.18 q+q-idx 0.85 scores+topk 2.17 kv-resolve 0.35 attention 0.70 gate 0.06 out-proj 0.48 router+plan+bell 0.42 shared+quant 0.52 waitA 0.12 VRAM hits 0.96 waitB 0.13 PCIe grp 0.12 waitCPU 5.09 copy+combine 0.21 (gap) 0.03   hc0 norm 0.11   hc0 down 0.29   hc0 up 0.26   hc1 norm 0.12   hc1 down 0.29   hc1 up 0.25 | total 59.64 ms/window over 924 windows
strata serve: prompt 126968 tokens = 0 reused + 126968 read in 153694 ms (826.1 tok/s), 1895 generated in 66580 ms (28.5 tok/s), drafts accepted 972 of 1273, 6 checkpoints
strata serve: decode expert cache hit rate: 87.6% (866647 hits / 989038 lookups)
strata serve: route tail skip: 61969 missed experts skipped (65308 entries) since the start
strata serve: expert tiers: GPU 866647 hits this request; since the start RAM 0 blobs, files 0 blobs 812014.8 MB read (the GGUF in place)
strata serve: file tier I/O this request: the OS read 20561.9 MB from storage (2462 major faults) for 812014.8 MB of expert reads; page cache held 779550.9 MB at the read, not 32463.9 MB; io prefetch: 48 read ahead (37137.1 MB by pread), 20 used, 28 unused, 23346 skipped (cached), 0 dropped; decode waited 10533.3 ms in 30177 fetches; decode gate: cache room 1.22 of the experts, read-ahead used 100%, page cache held 100% of the decode's reads (EWMA), closed, closed in 859 windows so far, 7 flips; read ahead 77.2 MB, 32.4 MB of it used; 0 late, 0 not admitted (confidence), 0 (budget 0 MB/window)
strata serve: KV streaming: 98.35% of 13568724 block reads hit VRAM, 901.6 MiB read from RAM
strata serve: suffix drafts: 8 windows, 10 of 18 drafts accepted
[strata] drafting: DFlash2 alone (--draft dflash2, --draft-conf 0.7)
[strata] mapping the experts from the model files (about 47 GB, --mmap-experts): they are not loaded into RAM - the OS file cache reads them as the GPU's expert cache fills and as requests need them.
[strata] filling the GPU's expert cache (5653 experts, 9.16 GiB of VRAM) ...
[strata] done: 1895 tokens in 220 s (28.5 tok/s) (stop, cancel=False), expert cache 87.6% hit
```

