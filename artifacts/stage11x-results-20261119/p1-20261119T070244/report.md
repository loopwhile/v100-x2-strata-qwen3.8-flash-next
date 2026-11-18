# Stage 11X S11X-P1 Receipt: `p1-20261119T070244`

- **Verdict**: `PASS`
- **Host**: `p520-llm` (boot `e80b19de-4242-4e94-b756-6f500d43a07b`)
- **Engine**: `strata-v100:stage11x-p1` (`062f6e3bcf41288e...`)
- **Overrides**: `{"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1", "STRATA_PF_WMMA2": "1", "STRATA_PF_WMMA_SKINNY": "1", "STRATA_PF_WMMA_LEAN": "0", "STRATA_PREFILL_TIMING": "1"}`
- **DFlash2 Config**: `spec 8`, `conf 0.7`, `prefill auto`

## Diagnostic C2 Batch (Non-Scored)

| Phase | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Overlap | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| p1-20261119T070244-diagnostic-1 | 1024.1 | 1024.8 | 28.1 | 30.3 | 124.22 | 124.15 | Yes | DIAGNOSTIC_PASS_NOT_SCORED |

### Agent A Profiling Notes (`p1-20261119T070244-diagnostic-1`)
```text
[strata] 2026-11-18 22:03:22 engine started: /opt/strata/engine/strata --serve --pack /stage10-data/packs/iq3_xxs-native --native /iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf --ple-gguf /iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf --expert-profile /opt/strata/data/expert-profile.bin --mmap-experts --max-context 131072 --kv int8 --kv-resident 32768 --spec 8 --prefill auto --expert-cache auto --draft dflash2 --draft-model /stage10-data/dflash2/qwen3.8-flash-next-dflash2.q4_0-selq4.pack --draft-fallback none --mtp-draft-vocab /shared-mtp/rt/draft_vocab.bin --draft-conf 0.7
strata generate: memory guard: limit 61.1 GiB (source: meminfo), current 2.3 GiB, reclaimable cache credited 0.0 GiB; available 58.8 GiB (MemAvailable 58.8 GiB), floor 2560 MiB
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
strata: prefill plan: chunk 8192, ring 96 kept: file set 35.1 GiB fits the page cache 51.5 GiB -> about 0.0 GB read from the drive per 32768-token prompt (4 chunks)
strata: prefill plan inputs: 40.0 GiB experts, 9.2 GiB in the GPU caches, 0.0 GiB RAM copy (0 lend slots kept), file tier 30.8 GiB; 51.5 GiB available for the page cache; PCIe 12.3 GB/s; drive 2.50 GB/s (nvme1n1 is NVMe); a 32768-token prompt
strata serve: prompt chunk auto: 8192 tokens, a 96-slot ring
strata serve: the prompt path borrows 2489 CUDA0 cache slots (3.99 GiB)
prefill: the GGUF experts are 100% in the page cache; the stager takes the RAM profile
strata verify: window up to 8 tokens, 81.5 MiB of device buffers
strata dflash2: 106299-token draft head (178.4 MiB), drafter 591 MiB of VRAM (Q4_0 weights)
strata dflash2: selector codebooks: Q4_0 rows (about 174 MiB less than bf16)
strata serve: DFlash2 drafter on (/stage10-data/dflash2/qwen3.8-flash-next-dflash2.q4_0-selq4.pack, graphs captured in 4 ms); windows up to 8 tokens; no MTP layer is loaded (--draft-fallback none)
strata serve: conversation cache sized from the free RAM: 8192 MiB for up to 4 parked conversations, so an agent's next turn reuses its prompt (--conversation-cache-mib N sets it, 0 turns it off)
strata serve: PCIe share: start 0.65 from 2 pool workers (assumed 8 GB/s of expert bytes) and the 12.3 GB/s link (was 0.34)
strata serve: STRATA_ROUTE_TAIL_SKIP=7 is ON (default): a missed expert that every token of a verify window routes at rank 7 or lower is skipped (+10..20% decode on 12-16 GB cards that miss experts, answers differ slightly from 0.1.41); STRATA_ROUTE_TAIL_SKIP=0 turns it off
strata prefill: QSA layers: norm + rope in one pass on, attention gate in the attention epilogue off
strata prefill timing: 126960 tokens, GPU timeline 122511 ms, wall 122562 ms, host staging 105905 ms: embed+steps 667 (0.5%) hc read 40 (0.0%) gdn 5893 (4.8%) qsa proj 2983 (2.4%) qsa indexer 6 (0.0%) qsa select 4734 (3.9%) qsa attn 9854 (8.0%) router+shared 1967 (1.6%) host grouping 1311 (1.1%) gather 779 (0.6%) wait copy 13848 (11.3%) dequant 30698 (25.1%) gemm gate/up 20079 (16.4%) gemm down 9063 (7.4%) combine 927 (0.8%) ple 362 (0.3%) kv stage 1072 (0.9%) gdn conv+gates 509 (0.4%) gdn recurrence 4998 (4.1%) gdn out proj 2020 (1.6%) hc write 3145 (2.6%) hc read: down+silu 2581 (2.1%) hc read: up 1687 (1.4%) hc read: inject 1508 (1.2%) hc read: mix 1587 (1.3%) qsa: indexer gemms 176 (0.1%) qsa: norm/rope/kv append/q prep 15 (0.0%)
strata prefill timing: host: chunk setup (PLE rows, the expert stream plan) 78 ms, waiting for each chunk 66 ms, after each chunk (the draft layer, progress) 588 ms, PLE 70 ms
strata verify: capturing the 6-token window (709 MiB of VRAM free)
strata verify: captured the 6-token window (upload no error, sync no error) in 19.4 ms
strata verify: capturing the 1-token window (691 MiB of VRAM free)
strata verify: captured the 1-token window (upload no error, sync no error) in 19.0 ms
strata verify: capturing the 4-token window (675 MiB of VRAM free)
strata verify: captured the 4-token window (upload no error, sync no error) in 20.7 ms
strata verify: capturing the 2-token window (659 MiB of VRAM free)
strata verify: captured the 2-token window (upload no error, sync no error) in 23.3 ms
strata verify: capturing the 3-token window (641 MiB of VRAM free)
strata verify: captured the 3-token window (upload no error, sync no error) in 20.4 ms
strata verify: capturing the 8-token window (625 MiB of VRAM free)
strata verify: captured the 8-token window (upload no error, sync no error) in 19.7 ms
strata verify: capturing the 5-token window (609 MiB of VRAM free)
strata verify: captured the 5-token window (upload no error, sync no error) in 22.5 ms
strata verify: capturing the 7-token window (591 MiB of VRAM free)
strata verify: captured the 7-token window (upload no error, sync no error) in 21.0 ms
strata serve: PCIe share: the CPU pool takes 324 us per missed expert (5.4 GB/s of expert bytes), the link 12.3 GB/s -> pcie_frac 0.75 (was 0.65; --pcie-frac N fixes it, STRATA_PCIE_FRAC_DEFAULT=old keeps the start-up rule)
strata serve: prompt 126967 tokens = 0 reused + 126967 read in 123975 ms (1024.1 tok/s), 2509 generated in 89292 ms (28.1 tok/s), drafts accepted 1553 of 1977, 6 checkpoints
strata serve: decode expert cache hit rate: 82.5% (1069806 hits / 1296553 lookups)
strata serve: route tail skip: 105212 missed experts skipped (111543 entries) since the start
strata serve: expert tiers: GPU 1069806 hits this request; since the start RAM 0 blobs, files 0 blobs 946553.1 MB read (the GGUF in place)
strata serve: file tier I/O this request: the OS read 581.0 MB from storage (3 major faults) for 946553.1 MB of expert reads; page cache held 946499.4 MB at the read, not 53.7 MB; io prefetch: 0 read ahead (142.3 MB by pread), 0 used, 0 unused, 34390 skipped (cached), 0 dropped; decode waited 8594.2 ms in 30398 fetches; decode gate: cache room 1.23 of the experts, read-ahead used 100%, page cache held 100% of the decode's reads (EWMA), closed, closed in 892 windows so far, 7 flips; read ahead 0.0 MB, 0.0 MB of it used; 0 late, 0 not admitted (confidence), 0 (budget 0 MB/window)
strata serve: KV streaming: 98.25% of 18109968 block reads hit VRAM, 1279.5 MiB read from RAM
strata serve: suffix drafts: 144 windows, 389 of 462 drafts accepted
[strata] drafting: DFlash2 alone (--draft dflash2, --draft-conf 0.7)
[strata] mapping the experts from the model files (about 47 GB, --mmap-experts): they are not loaded into RAM - the OS file cache reads them as the GPU's expert cache fills and as requests need them.
[strata] filling the GPU's expert cache (5653 experts, 9.16 GiB of VRAM) ...
[strata] done: 2509 tokens in 213 s (28.1 tok/s) (stop, cancel=False), expert cache 82.5% hit
```

### Agent B Profiling Notes (`p1-20261119T070244-diagnostic-1`)
```text
[strata] 2026-11-18 22:03:23 engine started: /opt/strata/engine/strata --serve --pack /stage10-data/packs/iq3_xxs-native --native /iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf --ple-gguf /iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf --expert-profile /opt/strata/data/expert-profile.bin --mmap-experts --max-context 131072 --kv int8 --kv-resident 32768 --spec 8 --prefill auto --expert-cache auto --draft dflash2 --draft-model /stage10-data/dflash2/qwen3.8-flash-next-dflash2.q4_0-selq4.pack --draft-fallback none --mtp-draft-vocab /shared-mtp/rt/draft_vocab.bin --draft-conf 0.7
strata generate: memory guard: limit 61.1 GiB (source: meminfo), current 3.0 GiB, reclaimable cache credited 0.0 GiB; available 58.1 GiB (MemAvailable 58.1 GiB), floor 2560 MiB
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
strata: prefill plan: chunk 8192, ring 96 kept: file set 35.1 GiB fits the page cache 51.2 GiB -> about 0.0 GB read from the drive per 32768-token prompt (4 chunks)
strata: prefill plan inputs: 40.0 GiB experts, 9.2 GiB in the GPU caches, 0.0 GiB RAM copy (0 lend slots kept), file tier 30.8 GiB; 51.2 GiB available for the page cache; PCIe 12.3 GB/s; drive 2.50 GB/s (nvme1n1 is NVMe); a 32768-token prompt
strata serve: prompt chunk auto: 8192 tokens, a 96-slot ring
strata serve: the prompt path borrows 2489 CUDA0 cache slots (3.99 GiB)
prefill: the GGUF experts are 100% in the page cache; the stager takes the RAM profile
strata verify: window up to 8 tokens, 81.5 MiB of device buffers
strata dflash2: 106299-token draft head (178.4 MiB), drafter 591 MiB of VRAM (Q4_0 weights)
strata dflash2: selector codebooks: Q4_0 rows (about 174 MiB less than bf16)
strata serve: DFlash2 drafter on (/stage10-data/dflash2/qwen3.8-flash-next-dflash2.q4_0-selq4.pack, graphs captured in 4 ms); windows up to 8 tokens; no MTP layer is loaded (--draft-fallback none)
strata serve: conversation cache sized from the free RAM: 8192 MiB for up to 4 parked conversations, so an agent's next turn reuses its prompt (--conversation-cache-mib N sets it, 0 turns it off)
strata serve: PCIe share: start 0.65 from 2 pool workers (assumed 8 GB/s of expert bytes) and the 12.3 GB/s link (was 0.34)
strata serve: STRATA_ROUTE_TAIL_SKIP=7 is ON (default): a missed expert that every token of a verify window routes at rank 7 or lower is skipped (+10..20% decode on 12-16 GB cards that miss experts, answers differ slightly from 0.1.41); STRATA_ROUTE_TAIL_SKIP=0 turns it off
strata prefill: QSA layers: norm + rope in one pass on, attention gate in the attention epilogue off
strata prefill timing: 126961 tokens, GPU timeline 122439 ms, wall 122491 ms, host staging 105007 ms: embed+steps 676 (0.6%) hc read 40 (0.0%) gdn 5896 (4.8%) qsa proj 2991 (2.4%) qsa indexer 6 (0.0%) qsa select 4784 (3.9%) qsa attn 10130 (8.3%) router+shared 1991 (1.6%) host grouping 1202 (1.0%) gather 783 (0.6%) wait copy 13017 (10.6%) dequant 30458 (24.9%) gemm gate/up 20667 (16.9%) gemm down 9188 (7.5%) combine 927 (0.8%) ple 365 (0.3%) kv stage 1062 (0.9%) gdn conv+gates 508 (0.4%) gdn recurrence 5006 (4.1%) gdn out proj 2018 (1.6%) hc write 3147 (2.6%) hc read: down+silu 2580 (2.1%) hc read: up 1706 (1.4%) hc read: inject 1513 (1.2%) hc read: mix 1586 (1.3%) qsa: indexer gemms 176 (0.1%) qsa: norm/rope/kv append/q prep 15 (0.0%)
strata prefill timing: host: chunk setup (PLE rows, the expert stream plan) 90 ms, waiting for each chunk 63 ms, after each chunk (the draft layer, progress) 583 ms, PLE 72 ms
strata verify: capturing the 6-token window (709 MiB of VRAM free)
strata verify: captured the 6-token window (upload no error, sync no error) in 21.2 ms
strata verify: capturing the 1-token window (691 MiB of VRAM free)
strata verify: captured the 1-token window (upload no error, sync no error) in 17.7 ms
strata verify: capturing the 3-token window (675 MiB of VRAM free)
strata verify: captured the 3-token window (upload no error, sync no error) in 19.2 ms
strata verify: capturing the 2-token window (659 MiB of VRAM free)
strata verify: captured the 2-token window (upload no error, sync no error) in 21.6 ms
strata verify: capturing the 4-token window (641 MiB of VRAM free)
strata verify: captured the 4-token window (upload no error, sync no error) in 19.6 ms
strata verify: capturing the 5-token window (625 MiB of VRAM free)
strata verify: captured the 5-token window (upload no error, sync no error) in 21.0 ms
strata serve: PCIe share: the CPU pool takes 321 us per missed expert (5.4 GB/s of expert bytes), the link 12.3 GB/s -> pcie_frac 0.75 (was 0.65; --pcie-frac N fixes it, STRATA_PCIE_FRAC_DEFAULT=old keeps the start-up rule)
strata verify: capturing the 8-token window (609 MiB of VRAM free)
strata verify: captured the 8-token window (upload no error, sync no error) in 21.0 ms
strata verify: capturing the 7-token window (591 MiB of VRAM free)
strata verify: captured the 7-token window (upload no error, sync no error) in 19.3 ms
strata serve: prompt 126968 tokens = 0 reused + 126968 read in 123891 ms (1024.8 tok/s), 1895 generated in 62549 ms (30.3 tok/s), drafts accepted 972 of 1273, 6 checkpoints
strata serve: decode expert cache hit rate: 87.6% (866647 hits / 989038 lookups)
strata serve: route tail skip: 61969 missed experts skipped (65308 entries) since the start
strata serve: expert tiers: GPU 866647 hits this request; since the start RAM 0 blobs, files 0 blobs 813334.6 MB read (the GGUF in place)
strata serve: file tier I/O this request: the OS read 481.2 MB from storage (0 major faults) for 813334.6 MB of expert reads; page cache held 813298.8 MB at the read, not 35.8 MB; io prefetch: 0 read ahead (79.3 MB by pread), 0 used, 0 unused, 23324 skipped (cached), 0 dropped; decode waited 7877.1 ms in 28404 fetches; decode gate: cache room 1.23 of the experts, read-ahead used 100%, page cache held 100% of the decode's reads (EWMA), closed, closed in 859 windows so far, 7 flips; read ahead 0.0 MB, 0.0 MB of it used; 0 late, 0 not admitted (confidence), 0 (budget 0 MB/window)
strata serve: KV streaming: 98.35% of 13568724 block reads hit VRAM, 901.6 MiB read from RAM
strata serve: suffix drafts: 8 windows, 10 of 18 drafts accepted
[strata] drafting: DFlash2 alone (--draft dflash2, --draft-conf 0.7)
[strata] mapping the experts from the model files (about 47 GB, --mmap-experts): they are not loaded into RAM - the OS file cache reads them as the GPU's expert cache fills and as requests need them.
[strata] filling the GPU's expert cache (5653 experts, 9.16 GiB of VRAM) ...
[strata] done: 1895 tokens in 186 s (30.3 tok/s) (stop, cancel=False), expert cache 87.6% hit
```

