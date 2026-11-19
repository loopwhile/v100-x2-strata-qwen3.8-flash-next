# Stage 11X S11X-D2 Receipt: `d2-20261119T003229`

- **Verdict**: `PASS`
- **Host**: `p520-llm` (boot `e80b19de-4242-4e94-b756-6f500d43a07b`)
- **Engine**: `strata-v100:stage11x-d2` (`7f6fc8f7858739d1...`)
- **Overrides**: `{"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1", "STRATA_PF_WMMA2": "1", "STRATA_PF_WMMA_LEAN": "1", "STRATA_PF_WMMA_SKINNY": "1", "STRATA_AVX512BW_IQ": "22", "STRATA_IQ_MT_MIN": "1", "STRATA_IQ_GATHER": "1", "STRATA_IQ256_GATHER": "1", "STRATA_Q2_BITPLANE": "1", "STRATA_SIDE_MIXER": "2", "STRATA_ATTN_DAILY": "1", "STRATA_GR_UP75": "1", "STRATA_GU_SWIGLU": "1", "STRATA_QSA_ROWS": "1", "STRATA_FUSE_WAIT": "2", "STRATA_MMAP_ADAPT_ASYNC": "1", "STRATA_COLD_OVERLAP": "5", "STRATA_PREFILL_TIMING": "1", "STRATA_DECODE_TIMING": "1"}`
- **DFlash2 Config**: `spec 8`, `conf 0.7`, `prefill auto`

## Diagnostic C2 Batch (Non-Scored)

| Phase | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Overlap | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| d2-20261119T003229-diagnostic-1 | 883.3 | 862.4 | 34.9 | 38.3 | 143.99 | 147.67 | Yes | DIAGNOSTIC_PASS_NOT_SCORED |

### Agent A Profiling Notes (`d2-20261119T003229-diagnostic-1`)
```text
[strata] 2026-11-19 00:33:09 engine started: /opt/strata/engine/strata --serve --pack /stage10-data/packs/iq3_xxs-native --native /iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf --ple-gguf /iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf --expert-profile /opt/strata/data/expert-profile.bin --mmap-experts --max-context 131072 --kv int8 --kv-resident 32768 --spec 8 --prefill auto --expert-cache auto --draft dflash2 --draft-model /stage10-data/dflash2/qwen3.8-flash-next-dflash2.q4_0-selq4.pack --draft-fallback none --mtp-draft-vocab /shared-mtp/rt/draft_vocab.bin --draft-conf 0.7
strata generate: memory guard: limit 61.1 GiB (source: meminfo), current 2.3 GiB, reclaimable cache credited 0.0 GiB; available 58.8 GiB (MemAvailable 58.8 GiB), floor 2560 MiB
strata generate: CPU expert kernels: AVX-2 + AVX-512BW (STRATA_AVX512BW_IQ=22, STRATA_Q2_BITPLANE=1, STRATA_IQ_MT_MIN=1, STRATA_IQ256_GATHER=1, STRATA_IQ_GATHER=1)
strata generate: native pack: /stage10-data/packs/iq3_xxs-native experts (largest blob 2.33 MB), token embedding IQ3_S in mapped host memory (260 MiB, 0.2 s)
strata generate: profile /opt/strata/data/expert-profile.bin: 24576 ranked pairs, built for 24576 slots
strata generate: KV streaming: 32768 of 131072 cells per QSA layer in VRAM, the K/V in 1.55 GiB of pinned RAM
strata generate: experts via mmap (--mmap-experts; the GGUF shards in place, no experts.bin)
strata generate: file tier (Linux defaults, the GGUF read in place): page-cached experts computed from the mapping (STRATA_COLD_OVERLAP=5), io prefetch with whole-blob preads on 8 I/O threads, the decode's read-ahead only while the page cache has room for it and it pays (STRATA_IO_PF_GATE=1); off: STRATA_COLD_OVERLAP=0, STRATA_IO_PREFETCH=0, STRATA_IO_PF_GATE=0
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
prefill: the GGUF experts are 96% in the page cache; the stager takes the RAM profile
strata verify: window up to 8 tokens, 81.5 MiB of device buffers
strata dflash2: 106299-token draft head (178.4 MiB), drafter 591 MiB of VRAM (Q4_0 weights)
strata dflash2: selector codebooks: Q4_0 rows (about 174 MiB less than bf16)
strata serve: DFlash2 drafter on (/stage10-data/dflash2/qwen3.8-flash-next-dflash2.q4_0-selq4.pack, graphs captured in 4 ms); windows up to 8 tokens; no MTP layer is loaded (--draft-fallback none)
strata serve: conversation cache sized from the free RAM: 8192 MiB for up to 4 parked conversations, so an agent's next turn reuses its prompt (--conversation-cache-mib N sets it, 0 turns it off)
strata serve: PCIe share: start 0.65 from 2 pool workers (assumed 8 GB/s of expert bytes) and the 12.3 GB/s link (was 0.34)
strata serve: STRATA_ROUTE_TAIL_SKIP=7 is ON (default): a missed expert that every token of a verify window routes at rank 7 or lower is skipped (+10..20% decode on 12-16 GB cards that miss experts, answers differ slightly from 0.1.41); STRATA_ROUTE_TAIL_SKIP=0 turns it off
strata prefill: QSA layers: norm + rope in one pass on, attention gate in the attention epilogue off
strata prefill timing: 126960 tokens, GPU timeline 141965 ms, wall 142018 ms, host staging 126024 ms: embed+steps 1117 (0.8%) hc read 40 (0.0%) gdn 5886 (4.1%) qsa proj 2974 (2.1%) qsa indexer 6 (0.0%) qsa select 4728 (3.3%) qsa attn 9808 (6.9%) router+shared 1964 (1.4%) host grouping 1332 (0.9%) gather 9 (0.0%) wait copy 12365 (8.7%) dequant 50424 (35.5%) gemm gate/up 20855 (14.7%) gemm down 9642 (6.8%) combine 935 (0.7%) ple 438 (0.3%) kv stage 1061 (0.7%) gdn conv+gates 509 (0.4%) gdn recurrence 4999 (3.5%) gdn out proj 2017 (1.4%) hc write 3242 (2.3%) hc read: down+silu 2628 (1.9%) hc read: up 1698 (1.2%) hc read: inject 1506 (1.1%) hc read: mix 1590 (1.1%) qsa: indexer gemms 176 (0.1%) qsa: norm/rope/kv append/q prep 15 (0.0%)
strata prefill timing: host: chunk setup (PLE rows, the expert stream plan) 93 ms, waiting for each chunk 65 ms, after each chunk (the draft layer, progress) 1023 ms, PLE 145 ms
strata verify: capturing the 6-token window (707 MiB of VRAM free)
strata verify: captured the 6-token window (upload no error, sync no error) in 18.9 ms
strata verify: capturing the 1-token window (691 MiB of VRAM free)
strata verify: captured the 1-token window (upload no error, sync no error) in 18.0 ms
strata verify: capturing the 4-token window (675 MiB of VRAM free)
strata verify: captured the 4-token window (upload no error, sync no error) in 20.4 ms
strata verify: capturing the 2-token window (655 MiB of VRAM free)
strata verify: captured the 2-token window (upload no error, sync no error) in 25.2 ms
strata verify: capturing the 5-token window (635 MiB of VRAM free)
strata verify: captured the 5-token window (upload no error, sync no error) in 19.1 ms
strata verify: capturing the 3-token window (619 MiB of VRAM free)
strata verify: captured the 3-token window (upload no error, sync no error) in 21.6 ms
strata verify: capturing the 8-token window (601 MiB of VRAM free)
strata verify: captured the 8-token window (upload no error, sync no error) in 375.2 ms
strata serve: PCIe share: the CPU pool takes 336 us per missed expert (5.2 GB/s of expert bytes), the link 12.3 GB/s -> pcie_frac 0.75 (was 0.65; --pcie-frac N fixes it, STRATA_PCIE_FRAC_DEFAULT=old keeps the start-up rule)
strata verify: capturing the 7-token window (583 MiB of VRAM free)
strata verify: captured the 7-token window (upload no error, sync no error) in 35.6 ms
strata serve: PCIe share: the CPU pool takes 278 us per missed expert (6.3 GB/s of expert bytes), the link 12.3 GB/s -> pcie_frac 0.70 (was 0.75; --pcie-frac N fixes it, STRATA_PCIE_FRAC_DEFAULT=old keeps the start-up rule)
strata decode timing: 679 windows, avg T 2.72, 2.42 tokens/window, 69.42 ms/window = adapt wait 0.10 + verify 66.16 (GPU-reach wait 19.85 + per-layer host 43.97 [plan 0.29 actq 0.22 jobs 0.11 CPU 42.88] + stage 0.16) + commit/emit 0.03 + draft 3.11 + adapt join 0.00 + other 0.03; per layer-window: CPU experts 3.34 (4.45 entries), VRAM hits 20.64, PCIe 0.00; 22.7 swaps/window
strata serve: prompt 126967 tokens = 0 reused + 126967 read in 143740 ms (883.3 tok/s), 1645 generated in 47139 ms (34.9 tok/s), drafts accepted 966 of 1167, 6 checkpoints
strata serve: decode expert cache hit rate: 82.3% (672631 hits / 817576 lookups)
strata serve: route tail skip: 65115 missed experts skipped (68758 entries) since the start
strata serve: asynchronous adaptive tier: 169 rounds, 15399 experts swapped in, 75.5 ms per round (start to flip, between windows)
strata serve: expert tiers: GPU 672631 hits this request; since the start RAM 0 blobs, files 0 blobs 820751.5 MB read (the GGUF in place)
strata serve: file tier I/O this request: the OS read 13436.4 MB from storage (6012 major faults) for 820751.5 MB of expert reads; page cache held 801988.7 MB at the read, not 18762.8 MB; io prefetch: 43 read ahead (39749.6 MB by pread), 0 used, 0 unused, 18173 skipped (cached), 0 dropped; decode waited 3517.3 ms in 7833 fetches; decode gate: cache room 1.27 of the experts, read-ahead used 100%, page cache held 100% of the decode's reads (EWMA), closed, closed in 631 windows so far, 5 flips; read ahead 74.5 MB, 0.0 MB of it used; 0 late, 0 not admitted (confidence), 0 (budget 0 MB/window)
strata serve: cold reads (STRATA_COLD_OVERLAP=5) this request: 109429 experts from the mapping directly; 0 layers with a blob to read (0 such experts, 0 ready beside them, 0 pool batches); per such layer: R 0.000 ms, C_r 0.000 ms, C_c 0.000 ms, the decode waited 0.000 ms; total waited 0.0 ms, min(R, C_r) 0.0 ms
strata serve: KV streaming: 97.69% of 11412048 block reads hit VRAM, 1062.0 MiB read from RAM
strata serve: suffix drafts: 55 windows, 74 of 92 drafts accepted
[strata] drafting: DFlash2 alone (--draft dflash2, --draft-conf 0.7)
[strata] mapping the experts from the model files (about 47 GB, --mmap-experts): they are not loaded into RAM - the OS file cache reads them as the GPU's expert cache fills and as requests need them.
[strata] filling the GPU's expert cache (5653 experts, 9.16 GiB of VRAM) ...
[strata] done: 1645 tokens in 191 s (34.9 tok/s) (stop, cancel=False), expert cache 82.3% hit
```

### Agent B Profiling Notes (`d2-20261119T003229-diagnostic-1`)
```text
[strata] 2026-11-19 00:33:09 engine started: /opt/strata/engine/strata --serve --pack /stage10-data/packs/iq3_xxs-native --native /iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf --ple-gguf /iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf --expert-profile /opt/strata/data/expert-profile.bin --mmap-experts --max-context 131072 --kv int8 --kv-resident 32768 --spec 8 --prefill auto --expert-cache auto --draft dflash2 --draft-model /stage10-data/dflash2/qwen3.8-flash-next-dflash2.q4_0-selq4.pack --draft-fallback none --mtp-draft-vocab /shared-mtp/rt/draft_vocab.bin --draft-conf 0.7
strata generate: memory guard: limit 61.1 GiB (source: meminfo), current 2.8 GiB, reclaimable cache credited 0.0 GiB; available 58.3 GiB (MemAvailable 58.3 GiB), floor 2560 MiB
strata generate: CPU expert kernels: AVX-2 + AVX-512BW (STRATA_AVX512BW_IQ=22, STRATA_Q2_BITPLANE=1, STRATA_IQ_MT_MIN=1, STRATA_IQ256_GATHER=1, STRATA_IQ_GATHER=1)
strata generate: native pack: /stage10-data/packs/iq3_xxs-native experts (largest blob 2.33 MB), token embedding IQ3_S in mapped host memory (260 MiB, 0.2 s)
strata generate: profile /opt/strata/data/expert-profile.bin: 24576 ranked pairs, built for 24576 slots
strata generate: KV streaming: 32768 of 131072 cells per QSA layer in VRAM, the K/V in 1.55 GiB of pinned RAM
strata generate: experts via mmap (--mmap-experts; the GGUF shards in place, no experts.bin)
strata generate: file tier (Linux defaults, the GGUF read in place): page-cached experts computed from the mapping (STRATA_COLD_OVERLAP=5), io prefetch with whole-blob preads on 8 I/O threads, the decode's read-ahead only while the page cache has room for it and it pays (STRATA_IO_PF_GATE=1); off: STRATA_COLD_OVERLAP=0, STRATA_IO_PREFETCH=0, STRATA_IO_PF_GATE=0
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
prefill: the GGUF experts are 96% in the page cache; the stager takes the RAM profile
strata verify: window up to 8 tokens, 81.5 MiB of device buffers
strata dflash2: 106299-token draft head (178.4 MiB), drafter 591 MiB of VRAM (Q4_0 weights)
strata dflash2: selector codebooks: Q4_0 rows (about 174 MiB less than bf16)
strata serve: DFlash2 drafter on (/stage10-data/dflash2/qwen3.8-flash-next-dflash2.q4_0-selq4.pack, graphs captured in 4 ms); windows up to 8 tokens; no MTP layer is loaded (--draft-fallback none)
strata serve: conversation cache sized from the free RAM: 8192 MiB for up to 4 parked conversations, so an agent's next turn reuses its prompt (--conversation-cache-mib N sets it, 0 turns it off)
strata serve: PCIe share: start 0.65 from 2 pool workers (assumed 8 GB/s of expert bytes) and the 12.3 GB/s link (was 0.34)
strata serve: STRATA_ROUTE_TAIL_SKIP=7 is ON (default): a missed expert that every token of a verify window routes at rank 7 or lower is skipped (+10..20% decode on 12-16 GB cards that miss experts, answers differ slightly from 0.1.41); STRATA_ROUTE_TAIL_SKIP=0 turns it off
strata prefill: QSA layers: norm + rope in one pass on, attention gate in the attention epilogue off
strata prefill timing: 126961 tokens, GPU timeline 141870 ms, wall 141932 ms, host staging 125210 ms: embed+steps 1287 (0.9%) hc read 40 (0.0%) gdn 5887 (4.1%) qsa proj 3008 (2.1%) qsa indexer 6 (0.0%) qsa select 4757 (3.4%) qsa attn 10083 (7.1%) router+shared 1995 (1.4%) host grouping 1284 (0.9%) gather 13 (0.0%) wait copy 12347 (8.7%) dequant 49214 (34.7%) gemm gate/up 21336 (15.0%) gemm down 9910 (7.0%) combine 927 (0.7%) ple 442 (0.3%) kv stage 1074 (0.8%) gdn conv+gates 509 (0.4%) gdn recurrence 5007 (3.5%) gdn out proj 2026 (1.4%) hc write 3117 (2.2%) hc read: down+silu 2599 (1.8%) hc read: up 1709 (1.2%) hc read: inject 1516 (1.1%) hc read: mix 1589 (1.1%) qsa: indexer gemms 176 (0.1%) qsa: norm/rope/kv append/q prep 15 (0.0%)
strata prefill timing: host: chunk setup (PLE rows, the expert stream plan) 103 ms, waiting for each chunk 61 ms, after each chunk (the draft layer, progress) 1184 ms, PLE 154 ms
strata verify: capturing the 6-token window (707 MiB of VRAM free)
strata verify: captured the 6-token window (upload no error, sync no error) in 78.0 ms
strata verify: capturing the 1-token window (691 MiB of VRAM free)
strata verify: captured the 1-token window (upload no error, sync no error) in 89.1 ms
strata verify: capturing the 3-token window (675 MiB of VRAM free)
strata verify: captured the 3-token window (upload no error, sync no error) in 64.7 ms
strata verify: capturing the 2-token window (655 MiB of VRAM free)
strata verify: captured the 2-token window (upload no error, sync no error) in 45.5 ms
strata verify: capturing the 4-token window (635 MiB of VRAM free)
strata verify: captured the 4-token window (upload no error, sync no error) in 50.3 ms
strata verify: capturing the 5-token window (617 MiB of VRAM free)
strata verify: captured the 5-token window (upload no error, sync no error) in 35.4 ms
strata verify: capturing the 8-token window (601 MiB of VRAM free)
strata verify: captured the 8-token window (upload no error, sync no error) in 43.7 ms
strata serve: PCIe share: the CPU pool takes 314 us per missed expert (5.6 GB/s of expert bytes), the link 12.3 GB/s -> pcie_frac 0.75 (was 0.65; --pcie-frac N fixes it, STRATA_PCIE_FRAC_DEFAULT=old keeps the start-up rule)
strata verify: capturing the 7-token window (583 MiB of VRAM free)
strata verify: captured the 7-token window (upload no error, sync no error) in 22.0 ms
strata serve: PCIe share: the CPU pool takes 273 us per missed expert (6.4 GB/s of expert bytes), the link 12.3 GB/s -> pcie_frac 0.70 (was 0.75; --pcie-frac N fixes it, STRATA_PCIE_FRAC_DEFAULT=old keeps the start-up rule)
strata decode timing: 901 windows, avg T 2.38, 2.03 tokens/window, 52.89 ms/window = adapt wait 0.09 + verify 49.54 (GPU-reach wait 19.33 + per-layer host 28.34 [plan 0.25 actq 0.17 jobs 0.08 CPU 27.25] + stage 0.35) + commit/emit 0.03 + draft 3.20 + adapt join 0.00 + other 0.02; per layer-window: CPU experts 2.10 (2.77 entries), VRAM hits 19.53, PCIe 0.00; 21.2 swaps/window
strata serve: prompt 126968 tokens = 0 reused + 126968 read in 147221 ms (862.4 tok/s), 1825 generated in 47653 ms (38.3 tok/s), drafts accepted 924 of 1239, 6 checkpoints
strata serve: decode expert cache hit rate: 87.6% (844546 hits / 964167 lookups)
strata serve: route tail skip: 59954 missed experts skipped (63286 entries) since the start
strata serve: asynchronous adaptive tier: 225 rounds, 19093 experts swapped in, 58.5 ms per round (start to flip, between windows)
strata serve: expert tiers: GPU 844546 hits this request; since the start RAM 0 blobs, files 0 blobs 796065.1 MB read (the GGUF in place)
strata serve: file tier I/O this request: the OS read 13258.6 MB from storage (40042 major faults) for 796065.1 MB of expert reads; page cache held 777266.3 MB at the read, not 18798.8 MB; io prefetch: 45 read ahead (40042.9 MB by pread), 0 used, 0 unused, 14417 skipped (cached), 0 dropped; decode waited 6789.7 ms in 7833 fetches; decode gate: cache room 1.27 of the experts, read-ahead used 100%, page cache held 100% of the decode's reads (EWMA), closed, closed in 837 windows so far, 7 flips; read ahead 77.6 MB, 0.0 MB of it used; 0 late, 0 not admitted (confidence), 0 (budget 0 MB/window)
strata serve: cold reads (STRATA_COLD_OVERLAP=5) this request: 91452 experts from the mapping directly; 0 layers with a blob to read (0 such experts, 0 ready beside them, 0 pool batches); per such layer: R 0.000 ms, C_r 0.000 ms, C_c 0.000 ms, the decode waited 0.000 ms; total waited 0.0 ms, min(R, C_r) 0.0 ms
strata serve: KV streaming: 98.49% of 13223568 block reads hit VRAM, 804.7 MiB read from RAM
strata serve: suffix drafts: 10 windows, 12 of 16 drafts accepted
[strata] drafting: DFlash2 alone (--draft dflash2, --draft-conf 0.7)
[strata] mapping the experts from the model files (about 47 GB, --mmap-experts): they are not loaded into RAM - the OS file cache reads them as the GPU's expert cache fills and as requests need them.
[strata] filling the GPU's expert cache (5653 experts, 9.16 GiB of VRAM) ...
[strata] done: 1825 tokens in 195 s (38.3 tok/s) (stop, cancel=False), expert cache 87.6% hit
```

