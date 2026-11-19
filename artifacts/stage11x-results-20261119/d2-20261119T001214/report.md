# Stage 11X S11X-D2 Receipt: `d2-20261119T001214`

- **Verdict**: `PASS`
- **Host**: `p520-llm` (boot `e80b19de-4242-4e94-b756-6f500d43a07b`)
- **Engine**: `strata-v100:stage11x-c1` (`6c8f0ca8885284de...`)
- **Overrides**: `{"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1", "STRATA_PF_WMMA2": "1", "STRATA_PF_WMMA_LEAN": "1", "STRATA_PF_WMMA_SKINNY": "1", "STRATA_AVX512BW_IQ": "22", "STRATA_IQ_MT_MIN": "1", "STRATA_IQ_GATHER": "1", "STRATA_IQ256_GATHER": "1", "STRATA_Q2_BITPLANE": "1", "STRATA_SIDE_MIXER": "2", "STRATA_ATTN_DAILY": "1", "STRATA_GR_UP75": "1", "STRATA_GU_SWIGLU": "1", "STRATA_QSA_ROWS": "1", "STRATA_FUSE_WAIT": "2", "STRATA_AUX_CPUS": "auto", "STRATA_PREFILL_TIMING": "1", "STRATA_DECODE_TIMING": "1"}`
- **DFlash2 Config**: `spec 8`, `conf 0.7`, `prefill auto`

## Diagnostic C2 Batch (Non-Scored)

| Phase | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Overlap | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| d2-20261119T001214-diagnostic-1 | 705.5 | 715.7 | 32.8 | 32.1 | 180.21 | 177.66 | Yes | DIAGNOSTIC_PASS_NOT_SCORED |

### Agent A Profiling Notes (`d2-20261119T001214-diagnostic-1`)
```text
[strata] 2026-11-19 00:12:49 engine started: /opt/strata/engine/strata --serve --pack /stage10-data/packs/iq3_xxs-native --native /iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf --ple-gguf /iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf --expert-profile /opt/strata/data/expert-profile.bin --mmap-experts --max-context 131072 --kv int8 --kv-resident 32768 --spec 8 --prefill auto --expert-cache auto --draft dflash2 --draft-model /stage10-data/dflash2/qwen3.8-flash-next-dflash2.q4_0-selq4.pack --draft-fallback none --mtp-draft-vocab /shared-mtp/rt/draft_vocab.bin --draft-conf 0.7
strata generate: memory guard: limit 61.1 GiB (source: meminfo), current 2.3 GiB, reclaimable cache credited 0.0 GiB; available 58.8 GiB (MemAvailable 58.8 GiB), floor 2560 MiB
strata generate: CPU expert kernels: AVX-2 + AVX-512BW (STRATA_AVX512BW_IQ=22, STRATA_Q2_BITPLANE=1, STRATA_IQ_MT_MIN=1, STRATA_IQ256_GATHER=1, STRATA_IQ_GATHER=1)
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
strata: prefill plan: chunk 8192, ring 96 kept: file set 34.6 GiB fits the page cache 51.6 GiB -> about 0.0 GB read from the drive per 32768-token prompt (4 chunks)
strata: prefill plan inputs: 40.0 GiB experts, 9.2 GiB in the GPU caches, 0.0 GiB RAM copy (0 lend slots kept), file tier 30.8 GiB; 51.6 GiB available for the page cache; PCIe 12.3 GB/s; drive 2.50 GB/s (nvme1n1 is NVMe); a 32768-token prompt
strata serve: prompt chunk auto: 8192 tokens, a 96-slot ring
strata serve: the prompt path borrows 2179 CUDA0 cache slots (3.48 GiB)
prefill: the GGUF experts are 100% in the page cache; the stager takes the RAM profile
strata verify: window up to 8 tokens, 81.5 MiB of device buffers
strata dflash2: 106299-token draft head (178.4 MiB), drafter 591 MiB of VRAM (Q4_0 weights)
strata dflash2: selector codebooks: Q4_0 rows (about 174 MiB less than bf16)
strata serve: DFlash2 drafter on (/stage10-data/dflash2/qwen3.8-flash-next-dflash2.q4_0-selq4.pack, graphs captured in 4 ms); windows up to 8 tokens; no MTP layer is loaded (--draft-fallback none)
strata serve: conversation cache sized from the free RAM: 8192 MiB for up to 4 parked conversations, so an agent's next turn reuses its prompt (--conversation-cache-mib N sets it, 0 turns it off)
strata serve: PCIe share: start 0.65 from 2 pool workers (assumed 8 GB/s of expert bytes) and the 12.3 GB/s link (was 0.34)
strata serve: STRATA_ROUTE_TAIL_SKIP=7 is ON (default): a missed expert that every token of a verify window routes at rank 7 or lower is skipped (+10..20% decode on 12-16 GB cards that miss experts, answers differ slightly from 0.1.41); STRATA_ROUTE_TAIL_SKIP=0 turns it off
strata prefill: QSA layers: norm + rope in one pass on, attention gate in the attention epilogue off
strata prefill timing: 126960 tokens, GPU timeline 178739 ms, wall 178790 ms, host staging 150040 ms: embed+steps 574 (0.3%) hc read 41 (0.0%) gdn 5907 (3.3%) qsa proj 2957 (1.7%) qsa indexer 5 (0.0%) qsa select 4688 (2.6%) qsa attn 9713 (5.4%) router+shared 1942 (1.1%) host grouping 1094 (0.6%) gather 6 (0.0%) wait copy 17476 (9.8%) dequant 81929 (45.8%) gemm gate/up 20437 (11.4%) gemm down 11377 (6.4%) combine 934 (0.5%) ple 401 (0.2%) kv stage 1090 (0.6%) gdn conv+gates 511 (0.3%) gdn recurrence 4989 (2.8%) gdn out proj 2007 (1.1%) hc write 3161 (1.8%) hc read: down+silu 2534 (1.4%) hc read: up 1671 (0.9%) hc read: inject 1507 (0.8%) hc read: mix 1595 (0.9%) qsa: indexer gemms 177 (0.1%) qsa: norm/rope/kv append/q prep 15 (0.0%)
strata prefill timing: host: chunk setup (PLE rows, the expert stream plan) 20 ms, waiting for each chunk 64 ms, after each chunk (the draft layer, progress) 534 ms, PLE 98 ms
strata verify: capturing the 6-token window (707 MiB of VRAM free)
strata verify: captured the 6-token window (upload no error, sync no error) in 19.1 ms
strata verify: capturing the 1-token window (691 MiB of VRAM free)
strata verify: captured the 1-token window (upload no error, sync no error) in 18.7 ms
strata verify: capturing the 4-token window (675 MiB of VRAM free)
strata verify: captured the 4-token window (upload no error, sync no error) in 21.2 ms
strata verify: capturing the 2-token window (655 MiB of VRAM free)
strata verify: captured the 2-token window (upload no error, sync no error) in 22.5 ms
strata verify: capturing the 5-token window (635 MiB of VRAM free)
strata verify: captured the 5-token window (upload no error, sync no error) in 17.9 ms
strata verify: capturing the 3-token window (619 MiB of VRAM free)
strata verify: captured the 3-token window (upload no error, sync no error) in 21.7 ms
strata verify: capturing the 8-token window (601 MiB of VRAM free)
strata verify: captured the 8-token window (upload no error, sync no error) in 19.7 ms
strata serve: PCIe share: the CPU pool takes 256 us per missed expert (6.8 GB/s of expert bytes), the link 12.3 GB/s -> pcie_frac 0.70 (was 0.65; --pcie-frac N fixes it, STRATA_PCIE_FRAC_DEFAULT=old keeps the start-up rule)
strata verify: capturing the 7-token window (583 MiB of VRAM free)
strata verify: captured the 7-token window (upload no error, sync no error) in 17.6 ms
strata decode timing: 930 windows, avg T 3.04, 2.68 tokens/window, 81.98 ms/window = adapt wait 0.02 + verify 68.80 (GPU-reach wait 20.81 + per-layer host 46.18 [plan 0.41 actq 0.34 jobs 2.50 CPU 42.49] + stage 0.17) + commit/emit 0.05 + draft 3.25 + adapt join 9.84 + other 0.03; per layer-window: CPU experts 3.55 (4.82 entries), VRAM hits 23.28, PCIe 0.00; 22.9 swaps/window
strata serve: prompt 126967 tokens = 0 reused + 126967 read in 179972 ms (705.5 tok/s), 2497 generated in 76242 ms (32.8 tok/s), drafts accepted 1567 of 1901, 6 checkpoints
strata serve: decode expert cache hit rate: 82.9% (1039417 hits / 1254378 lookups)
strata serve: route tail skip: 98218 missed experts skipped (104756 entries) since the start
strata serve: expert tiers: GPU 1039417 hits this request; since the start RAM 0 blobs, files 0 blobs 917012.8 MB read (the GGUF in place)
strata serve: file tier I/O this request: the OS read 1300.5 MB from storage (0 major faults) for 917012.8 MB of expert reads; page cache held 916992.5 MB at the read, not 20.3 MB; io prefetch: 0 read ahead (125.7 MB by pread), 0 used, 0 unused, 21699 skipped (cached), 0 dropped; decode waited 8409.6 ms in 29166 fetches; decode gate: cache room 1.23 of the experts, read-ahead used 100%, page cache held 100% of the decode's reads (EWMA), closed, closed in 866 windows so far, 7 flips; read ahead 0.0 MB, 0.0 MB of it used; 0 late, 0 not admitted (confidence), 0 (budget 0 MB/window)
strata serve: KV streaming: 98.21% of 17481696 block reads hit VRAM, 1260.8 MiB read from RAM
strata serve: suffix drafts: 19 windows, 33 of 48 drafts accepted
[strata] drafting: DFlash2 alone (--draft dflash2, --draft-conf 0.7)
[strata] mapping the experts from the model files (about 47 GB, --mmap-experts): they are not loaded into RAM - the OS file cache reads them as the GPU's expert cache fills and as requests need them.
[strata] filling the GPU's expert cache (5653 experts, 9.16 GiB of VRAM) ...
[strata] done: 2497 tokens in 256 s (32.8 tok/s) (stop, cancel=False), expert cache 82.9% hit
```

### Agent B Profiling Notes (`d2-20261119T001214-diagnostic-1`)
```text
[strata] 2026-11-19 00:12:49 engine started: /opt/strata/engine/strata --serve --pack /stage10-data/packs/iq3_xxs-native --native /iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf --ple-gguf /iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf --expert-profile /opt/strata/data/expert-profile.bin --mmap-experts --max-context 131072 --kv int8 --kv-resident 32768 --spec 8 --prefill auto --expert-cache auto --draft dflash2 --draft-model /stage10-data/dflash2/qwen3.8-flash-next-dflash2.q4_0-selq4.pack --draft-fallback none --mtp-draft-vocab /shared-mtp/rt/draft_vocab.bin --draft-conf 0.7
strata generate: memory guard: limit 61.1 GiB (source: meminfo), current 2.9 GiB, reclaimable cache credited 0.0 GiB; available 58.2 GiB (MemAvailable 58.2 GiB), floor 2560 MiB
strata generate: CPU expert kernels: AVX-2 + AVX-512BW (STRATA_AVX512BW_IQ=22, STRATA_Q2_BITPLANE=1, STRATA_IQ_MT_MIN=1, STRATA_IQ256_GATHER=1, STRATA_IQ_GATHER=1)
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
strata: prefill plan: chunk 8192, ring 96 kept: file set 34.6 GiB fits the page cache 51.6 GiB -> about 0.0 GB read from the drive per 32768-token prompt (4 chunks)
strata: prefill plan inputs: 40.0 GiB experts, 9.2 GiB in the GPU caches, 0.0 GiB RAM copy (0 lend slots kept), file tier 30.8 GiB; 51.6 GiB available for the page cache; PCIe 12.3 GB/s; drive 2.50 GB/s (nvme1n1 is NVMe); a 32768-token prompt
strata serve: prompt chunk auto: 8192 tokens, a 96-slot ring
strata serve: the prompt path borrows 2179 CUDA0 cache slots (3.48 GiB)
prefill: the GGUF experts are 100% in the page cache; the stager takes the RAM profile
strata verify: window up to 8 tokens, 81.5 MiB of device buffers
strata dflash2: 106299-token draft head (178.4 MiB), drafter 591 MiB of VRAM (Q4_0 weights)
strata dflash2: selector codebooks: Q4_0 rows (about 174 MiB less than bf16)
strata serve: DFlash2 drafter on (/stage10-data/dflash2/qwen3.8-flash-next-dflash2.q4_0-selq4.pack, graphs captured in 4 ms); windows up to 8 tokens; no MTP layer is loaded (--draft-fallback none)
strata serve: conversation cache sized from the free RAM: 8192 MiB for up to 4 parked conversations, so an agent's next turn reuses its prompt (--conversation-cache-mib N sets it, 0 turns it off)
strata serve: PCIe share: start 0.65 from 2 pool workers (assumed 8 GB/s of expert bytes) and the 12.3 GB/s link (was 0.34)
strata serve: STRATA_ROUTE_TAIL_SKIP=7 is ON (default): a missed expert that every token of a verify window routes at rank 7 or lower is skipped (+10..20% decode on 12-16 GB cards that miss experts, answers differ slightly from 0.1.41); STRATA_ROUTE_TAIL_SKIP=0 turns it off
strata prefill: QSA layers: norm + rope in one pass on, attention gate in the attention epilogue off
strata prefill timing: 126961 tokens, GPU timeline 176160 ms, wall 176210 ms, host staging 146739 ms: embed+steps 565 (0.3%) hc read 42 (0.0%) gdn 5909 (3.4%) qsa proj 2981 (1.7%) qsa indexer 5 (0.0%) qsa select 4723 (2.7%) qsa attn 10022 (5.7%) router+shared 1969 (1.1%) host grouping 1071 (0.6%) gather 7 (0.0%) wait copy 17281 (9.8%) dequant 78607 (44.6%) gemm gate/up 20770 (11.8%) gemm down 11587 (6.6%) combine 934 (0.5%) ple 366 (0.2%) kv stage 1113 (0.6%) gdn conv+gates 512 (0.3%) gdn recurrence 4991 (2.8%) gdn out proj 2009 (1.1%) hc write 3162 (1.8%) hc read: down+silu 2536 (1.4%) hc read: up 1701 (1.0%) hc read: inject 1512 (0.9%) hc read: mix 1594 (0.9%) qsa: indexer gemms 177 (0.1%) qsa: norm/rope/kv append/q prep 15 (0.0%)
strata prefill timing: host: chunk setup (PLE rows, the expert stream plan) 21 ms, waiting for each chunk 65 ms, after each chunk (the draft layer, progress) 527 ms, PLE 62 ms
strata verify: capturing the 6-token window (707 MiB of VRAM free)
strata verify: captured the 6-token window (upload no error, sync no error) in 20.2 ms
strata verify: capturing the 1-token window (691 MiB of VRAM free)
strata verify: captured the 1-token window (upload no error, sync no error) in 17.7 ms
strata verify: capturing the 3-token window (675 MiB of VRAM free)
strata verify: captured the 3-token window (upload no error, sync no error) in 23.2 ms
strata verify: capturing the 2-token window (655 MiB of VRAM free)
strata verify: captured the 2-token window (upload no error, sync no error) in 22.4 ms
strata verify: capturing the 5-token window (635 MiB of VRAM free)
strata verify: captured the 5-token window (upload no error, sync no error) in 20.4 ms
strata verify: capturing the 8-token window (619 MiB of VRAM free)
strata verify: captured the 8-token window (upload no error, sync no error) in 17.6 ms
strata verify: capturing the 4-token window (603 MiB of VRAM free)
strata verify: captured the 4-token window (upload no error, sync no error) in 20.2 ms
strata serve: PCIe share: the CPU pool takes 252 us per missed expert (6.9 GB/s of expert bytes), the link 12.3 GB/s -> pcie_frac 0.70 (was 0.65; --pcie-frac N fixes it, STRATA_PCIE_FRAC_DEFAULT=old keeps the start-up rule)
strata verify: capturing the 7-token window (583 MiB of VRAM free)
strata verify: captured the 7-token window (upload no error, sync no error) in 18.8 ms
strata decode timing: 871 windows, avg T 2.59, 2.16 tokens/window, 67.45 ms/window = adapt wait 0.02 + verify 54.90 (GPU-reach wait 19.66 + per-layer host 33.57 [plan 0.35 actq 0.25 jobs 1.81 CPU 30.68] + stage 0.24) + commit/emit 0.05 + draft 3.24 + adapt join 9.20 + other 0.03; per layer-window: CPU experts 2.49 (3.32 entries), VRAM hits 20.89, PCIe 0.00; 22.0 swaps/window
strata serve: prompt 126968 tokens = 0 reused + 126968 read in 177412 ms (715.7 tok/s), 1883 generated in 58747 ms (32.1 tok/s), drafts accepted 1013 of 1385, 6 checkpoints
strata serve: decode expert cache hit rate: 86.3% (873215 hits / 1012174 lookups)
strata serve: route tail skip: 67140 missed experts skipped (70959 entries) since the start
strata serve: expert tiers: GPU 873215 hits this request; since the start RAM 0 blobs, files 0 blobs 818389.2 MB read (the GGUF in place)
strata serve: file tier I/O this request: the OS read 475.8 MB from storage (1 major faults) for 818389.2 MB of expert reads; page cache held 818364.5 MB at the read, not 24.7 MB; io prefetch: 0 read ahead (158.9 MB by pread), 0 used, 0 unused, 19107 skipped (cached), 0 dropped; decode waited 7698.5 ms in 27024 fetches; decode gate: cache room 1.23 of the experts, read-ahead used 100%, page cache held 100% of the decode's reads (EWMA), closed, closed in 807 windows so far, 7 flips; read ahead 0.0 MB, 0.0 MB of it used; 0 late, 0 not admitted (confidence), 0 (budget 0 MB/window)
strata serve: KV streaming: 98.40% of 13938396 block reads hit VRAM, 899.8 MiB read from RAM
strata serve: suffix drafts: 3 windows, 4 of 7 drafts accepted
[strata] drafting: DFlash2 alone (--draft dflash2, --draft-conf 0.7)
[strata] mapping the experts from the model files (about 47 GB, --mmap-experts): they are not loaded into RAM - the OS file cache reads them as the GPU's expert cache fills and as requests need them.
[strata] filling the GPU's expert cache (5653 experts, 9.16 GiB of VRAM) ...
[strata] done: 1883 tokens in 236 s (32.1 tok/s) (stop, cancel=False), expert cache 86.3% hit
```

