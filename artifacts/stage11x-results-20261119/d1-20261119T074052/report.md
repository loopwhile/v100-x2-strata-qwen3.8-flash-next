# Stage 11X S11X-D1 Receipt: `d1-20261119T074052`

- **Verdict**: `PASS`
- **Host**: `p520-llm` (boot `e80b19de-4242-4e94-b756-6f500d43a07b`)
- **Engine**: `strata-v100:stage11x-d1` (`97e8f19921ec7a0e...`)
- **Overrides**: `{"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1", "STRATA_AVX512BW_IQ": "22", "STRATA_IQ_MT_MIN": "1", "STRATA_IQ_GATHER": "1", "STRATA_IQ256_GATHER": "1", "STRATA_Q2_BITPLANE": "1", "STRATA_DECODE_TIMING": "1"}`
- **DFlash2 Config**: `spec 8`, `conf 0.7`, `prefill auto`

## Diagnostic C2 Batch (Non-Scored)

| Phase | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Overlap | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| d1-20261119T074052-diagnostic-1 | 831.7 | 820.1 | 32.0 | 31.2 | 152.91 | 155.12 | Yes | DIAGNOSTIC_PASS_NOT_SCORED |

### Agent A Profiling Notes (`d1-20261119T074052-diagnostic-1`)
```text
[strata] 2026-11-18 22:41:37 engine started: /opt/strata/engine/strata --serve --pack /stage10-data/packs/iq3_xxs-native --native /iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf --ple-gguf /iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf --expert-profile /opt/strata/data/expert-profile.bin --mmap-experts --max-context 131072 --kv int8 --kv-resident 32768 --spec 8 --prefill auto --expert-cache auto --draft dflash2 --draft-model /stage10-data/dflash2/qwen3.8-flash-next-dflash2.q4_0-selq4.pack --draft-fallback none --mtp-draft-vocab /shared-mtp/rt/draft_vocab.bin --draft-conf 0.7
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
strata: prefill plan: chunk 8192, ring 96 kept: file set 35.1 GiB fits the page cache 51.6 GiB -> about 0.0 GB read from the drive per 32768-token prompt (4 chunks)
strata: prefill plan inputs: 40.0 GiB experts, 9.2 GiB in the GPU caches, 0.0 GiB RAM copy (0 lend slots kept), file tier 30.8 GiB; 51.6 GiB available for the page cache; PCIe 12.3 GB/s; drive 2.50 GB/s (nvme1n1 is NVMe); a 32768-token prompt
strata serve: prompt chunk auto: 8192 tokens, a 96-slot ring
strata serve: the prompt path borrows 2489 CUDA0 cache slots (3.99 GiB)
prefill: the GGUF experts are 91% in the page cache; the stager takes the RAM profile
strata verify: window up to 8 tokens, 81.5 MiB of device buffers
strata dflash2: 106299-token draft head (178.4 MiB), drafter 591 MiB of VRAM (Q4_0 weights)
strata dflash2: selector codebooks: Q4_0 rows (about 174 MiB less than bf16)
strata serve: DFlash2 drafter on (/stage10-data/dflash2/qwen3.8-flash-next-dflash2.q4_0-selq4.pack, graphs captured in 4 ms); windows up to 8 tokens; no MTP layer is loaded (--draft-fallback none)
strata serve: conversation cache sized from the free RAM: 8192 MiB for up to 4 parked conversations, so an agent's next turn reuses its prompt (--conversation-cache-mib N sets it, 0 turns it off)
strata serve: PCIe share: start 0.65 from 2 pool workers (assumed 8 GB/s of expert bytes) and the 12.3 GB/s link (was 0.34)
strata serve: STRATA_ROUTE_TAIL_SKIP=7 is ON (default): a missed expert that every token of a verify window routes at rank 7 or lower is skipped (+10..20% decode on 12-16 GB cards that miss experts, answers differ slightly from 0.1.41); STRATA_ROUTE_TAIL_SKIP=0 turns it off
strata prefill: QSA layers: norm + rope in one pass on, attention gate in the attention epilogue off
strata verify: capturing the 6-token window (709 MiB of VRAM free)
strata verify: captured the 6-token window (upload no error, sync no error) in 19.9 ms
strata verify: capturing the 1-token window (691 MiB of VRAM free)
strata verify: captured the 1-token window (upload no error, sync no error) in 19.1 ms
strata verify: capturing the 4-token window (675 MiB of VRAM free)
strata verify: captured the 4-token window (upload no error, sync no error) in 22.0 ms
strata verify: capturing the 2-token window (659 MiB of VRAM free)
strata verify: captured the 2-token window (upload no error, sync no error) in 23.5 ms
strata verify: capturing the 3-token window (641 MiB of VRAM free)
strata verify: captured the 3-token window (upload no error, sync no error) in 21.8 ms
strata verify: capturing the 8-token window (625 MiB of VRAM free)
strata verify: captured the 8-token window (upload no error, sync no error) in 19.2 ms
strata verify: capturing the 5-token window (609 MiB of VRAM free)
strata verify: captured the 5-token window (upload no error, sync no error) in 31.5 ms
strata serve: PCIe share: the CPU pool takes 262 us per missed expert (6.7 GB/s of expert bytes), the link 12.3 GB/s -> pcie_frac 0.70 (was 0.65; --pcie-frac N fixes it, STRATA_PCIE_FRAC_DEFAULT=old keeps the start-up rule)
strata verify: capturing the 7-token window (591 MiB of VRAM free)
strata verify: captured the 7-token window (upload no error, sync no error) in 21.9 ms
strata decode timing: 709 windows, avg T 2.55, 2.15 tokens/window, 67.12 ms/window = adapt wait 0.02 + verify 54.46 (GPU-reach wait 20.46 + per-layer host 32.37 [plan 0.27 actq 0.18 jobs 3.23 CPU 28.32] + stage 0.11) + commit/emit 0.07 + draft 3.22 + adapt join 9.33 + other 0.03; per layer-window: CPU experts 2.16 (2.83 entries), VRAM hits 21.19, PCIe 0.00; 21.8 swaps/window
strata serve: prompt 126967 tokens = 0 reused + 126967 read in 152664 ms (831.7 tok/s), 1521 generated in 47589 ms (32.0 tok/s), drafts accepted 812 of 1099, 6 checkpoints
strata serve: decode expert cache hit rate: 88.2% (721037 hits / 817445 lookups)
strata serve: route tail skip: 48118 missed experts skipped (50651 entries) since the start
strata serve: expert tiers: GPU 721037 hits this request; since the start RAM 0 blobs, files 0 blobs 765949.3 MB read (the GGUF in place)
strata serve: file tier I/O this request: the OS read 22434.5 MB from storage (3675 major faults) for 765949.3 MB of expert reads; page cache held 728903.8 MB at the read, not 37045.5 MB; io prefetch: 34 read ahead (71495.9 MB by pread), 23 used, 11 unused, 15300 skipped (cached), 0 dropped; decode waited 8527.1 ms in 25453 fetches; decode gate: cache room 1.28 of the experts, read-ahead used 100%, page cache held 100% of the decode's reads (EWMA), closed, closed in 661 windows so far, 5 flips; read ahead 63.2 MB, 42.8 MB of it used; 0 late, 0 not admitted (confidence), 0 (budget 0 MB/window)
strata serve: KV streaming: 98.17% of 11177772 block reads hit VRAM, 825.0 MiB read from RAM
strata serve: suffix drafts: 8 windows, 14 of 22 drafts accepted
[strata] drafting: DFlash2 alone (--draft dflash2, --draft-conf 0.7)
[strata] mapping the experts from the model files (about 47 GB, --mmap-experts): they are not loaded into RAM - the OS file cache reads them as the GPU's expert cache fills and as requests need them.
[strata] filling the GPU's expert cache (5653 experts, 9.16 GiB of VRAM) ...
[strata] done: 1521 tokens in 200 s (32.0 tok/s) (stop, cancel=False), expert cache 88.2% hit
```

### Agent B Profiling Notes (`d1-20261119T074052-diagnostic-1`)
```text
[strata] 2026-11-18 22:41:38 engine started: /opt/strata/engine/strata --serve --pack /stage10-data/packs/iq3_xxs-native --native /iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf --ple-gguf /iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf --expert-profile /opt/strata/data/expert-profile.bin --mmap-experts --max-context 131072 --kv int8 --kv-resident 32768 --spec 8 --prefill auto --expert-cache auto --draft dflash2 --draft-model /stage10-data/dflash2/qwen3.8-flash-next-dflash2.q4_0-selq4.pack --draft-fallback none --mtp-draft-vocab /shared-mtp/rt/draft_vocab.bin --draft-conf 0.7
strata generate: memory guard: limit 61.1 GiB (source: meminfo), current 2.8 GiB, reclaimable cache credited 0.0 GiB; available 58.3 GiB (MemAvailable 58.3 GiB), floor 2560 MiB
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
strata: prefill plan: chunk 8192, ring 96 kept: file set 35.1 GiB fits the page cache 51.6 GiB -> about 0.0 GB read from the drive per 32768-token prompt (4 chunks)
strata: prefill plan inputs: 40.0 GiB experts, 9.2 GiB in the GPU caches, 0.0 GiB RAM copy (0 lend slots kept), file tier 30.8 GiB; 51.6 GiB available for the page cache; PCIe 12.3 GB/s; drive 2.50 GB/s (nvme1n1 is NVMe); a 32768-token prompt
strata serve: prompt chunk auto: 8192 tokens, a 96-slot ring
strata serve: the prompt path borrows 2489 CUDA0 cache slots (3.99 GiB)
prefill: the GGUF experts are 91% in the page cache; the stager takes the RAM profile
strata verify: window up to 8 tokens, 81.5 MiB of device buffers
strata dflash2: 106299-token draft head (178.4 MiB), drafter 591 MiB of VRAM (Q4_0 weights)
strata dflash2: selector codebooks: Q4_0 rows (about 174 MiB less than bf16)
strata serve: DFlash2 drafter on (/stage10-data/dflash2/qwen3.8-flash-next-dflash2.q4_0-selq4.pack, graphs captured in 4 ms); windows up to 8 tokens; no MTP layer is loaded (--draft-fallback none)
strata serve: conversation cache sized from the free RAM: 8192 MiB for up to 4 parked conversations, so an agent's next turn reuses its prompt (--conversation-cache-mib N sets it, 0 turns it off)
strata serve: PCIe share: start 0.65 from 2 pool workers (assumed 8 GB/s of expert bytes) and the 12.3 GB/s link (was 0.34)
strata serve: STRATA_ROUTE_TAIL_SKIP=7 is ON (default): a missed expert that every token of a verify window routes at rank 7 or lower is skipped (+10..20% decode on 12-16 GB cards that miss experts, answers differ slightly from 0.1.41); STRATA_ROUTE_TAIL_SKIP=0 turns it off
strata prefill: QSA layers: norm + rope in one pass on, attention gate in the attention epilogue off
strata verify: capturing the 6-token window (709 MiB of VRAM free)
strata verify: captured the 6-token window (upload no error, sync no error) in 69.5 ms
strata verify: capturing the 1-token window (691 MiB of VRAM free)
strata verify: captured the 1-token window (upload no error, sync no error) in 30.8 ms
strata verify: capturing the 3-token window (675 MiB of VRAM free)
strata verify: captured the 3-token window (upload no error, sync no error) in 26.7 ms
strata verify: capturing the 2-token window (659 MiB of VRAM free)
strata verify: captured the 2-token window (upload no error, sync no error) in 26.9 ms
strata verify: capturing the 5-token window (641 MiB of VRAM free)
strata verify: captured the 5-token window (upload no error, sync no error) in 21.7 ms
strata verify: capturing the 8-token window (625 MiB of VRAM free)
strata verify: captured the 8-token window (upload no error, sync no error) in 21.5 ms
strata verify: capturing the 4-token window (609 MiB of VRAM free)
strata verify: captured the 4-token window (upload no error, sync no error) in 26.3 ms
strata serve: PCIe share: the CPU pool takes 270 us per missed expert (6.5 GB/s of expert bytes), the link 12.3 GB/s -> pcie_frac 0.70 (was 0.65; --pcie-frac N fixes it, STRATA_PCIE_FRAC_DEFAULT=old keeps the start-up rule)
strata verify: capturing the 7-token window (591 MiB of VRAM free)
strata verify: captured the 7-token window (upload no error, sync no error) in 32.0 ms
strata decode timing: 871 windows, avg T 2.59, 2.16 tokens/window, 69.23 ms/window = adapt wait 0.02 + verify 56.75 (GPU-reach wait 20.52 + per-layer host 34.59 [plan 0.28 actq 0.20 jobs 2.78 CPU 30.82] + stage 0.28) + commit/emit 0.07 + draft 3.33 + adapt join 9.04 + other 0.03; per layer-window: CPU experts 2.49 (3.32 entries), VRAM hits 20.89, PCIe 0.00; 22.0 swaps/window
strata serve: prompt 126968 tokens = 0 reused + 126968 read in 154812 ms (820.1 tok/s), 1883 generated in 60296 ms (31.2 tok/s), drafts accepted 1013 of 1385, 6 checkpoints
strata serve: decode expert cache hit rate: 86.3% (873215 hits / 1012174 lookups)
strata serve: route tail skip: 67140 missed experts skipped (70959 entries) since the start
strata serve: expert tiers: GPU 873215 hits this request; since the start RAM 0 blobs, files 0 blobs 826765.2 MB read (the GGUF in place)
strata serve: file tier I/O this request: the OS read 22714.6 MB from storage (50148 major faults) for 826765.2 MB of expert reads; page cache held 790030.5 MB at the read, not 36734.7 MB; io prefetch: 51 read ahead (70772.0 MB by pread), 20 used, 31 unused, 20467 skipped (cached), 0 dropped; decode waited 11251.5 ms in 28791 fetches; decode gate: cache room 1.28 of the experts, read-ahead used 100%, page cache held 100% of the decode's reads (EWMA), closed, closed in 807 windows so far, 7 flips; read ahead 86.8 MB, 33.6 MB of it used; 0 late, 0 not admitted (confidence), 0 (budget 0 MB/window)
strata serve: KV streaming: 98.40% of 13938396 block reads hit VRAM, 899.8 MiB read from RAM
strata serve: suffix drafts: 3 windows, 4 of 7 drafts accepted
[strata] drafting: DFlash2 alone (--draft dflash2, --draft-conf 0.7)
[strata] mapping the experts from the model files (about 47 GB, --mmap-experts): they are not loaded into RAM - the OS file cache reads them as the GPU's expert cache fills and as requests need them.
[strata] filling the GPU's expert cache (5653 experts, 9.16 GiB of VRAM) ...
[strata] done: 1883 tokens in 215 s (31.2 tok/s) (stop, cancel=False), expert cache 86.3% hit
```

