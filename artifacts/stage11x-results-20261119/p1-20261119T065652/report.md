# Stage 11X S11X-P1 Receipt: `p1-20261119T065652`

- **Verdict**: `PASS`
- **Host**: `p520-llm` (boot `e80b19de-4242-4e94-b756-6f500d43a07b`)
- **Engine**: `strata-v100:stage11x-p1` (`062f6e3bcf41288e...`)
- **Overrides**: `{"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1", "STRATA_PF_WMMA2": "1", "STRATA_PF_WMMA_SKINNY": "1", "STRATA_PF_WMMA_LEAN": "1", "STRATA_PREFILL_TIMING": "1"}`
- **DFlash2 Config**: `spec 8`, `conf 0.7`, `prefill auto`

## Diagnostic C2 Batch (Non-Scored)

| Phase | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Overlap | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| p1-20261119T065652-diagnostic-1 | 1030.0 | 1038.1 | 27.5 | 28.1 | 123.51 | 122.54 | Yes | DIAGNOSTIC_PASS_NOT_SCORED |

### Agent A Profiling Notes (`p1-20261119T065652-diagnostic-1`)
```text
[strata] 2026-11-18 21:57:32 engine started: /opt/strata/engine/strata --serve --pack /stage10-data/packs/iq3_xxs-native --native /iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf --ple-gguf /iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf --expert-profile /opt/strata/data/expert-profile.bin --mmap-experts --max-context 131072 --kv int8 --kv-resident 32768 --spec 8 --prefill auto --expert-cache auto --draft dflash2 --draft-model /stage10-data/dflash2/qwen3.8-flash-next-dflash2.q4_0-selq4.pack --draft-fallback none --mtp-draft-vocab /shared-mtp/rt/draft_vocab.bin --draft-conf 0.7
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
strata: prefill plan: chunk 8192, ring 96 kept: file set 34.6 GiB fits the page cache 51.5 GiB -> about 0.0 GB read from the drive per 32768-token prompt (4 chunks)
strata: prefill plan inputs: 40.0 GiB experts, 9.2 GiB in the GPU caches, 0.0 GiB RAM copy (0 lend slots kept), file tier 30.8 GiB; 51.5 GiB available for the page cache; PCIe 12.3 GB/s; drive 2.50 GB/s (nvme1n1 is NVMe); a 32768-token prompt
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
strata prefill timing: 126960 tokens, GPU timeline 122002 ms, wall 122053 ms, host staging 105140 ms: embed+steps 637 (0.5%) hc read 40 (0.0%) gdn 5889 (4.8%) qsa proj 2974 (2.4%) qsa indexer 6 (0.0%) qsa select 4747 (3.9%) qsa attn 9868 (8.1%) router+shared 1977 (1.6%) host grouping 1311 (1.1%) gather 14 (0.0%) wait copy 12782 (10.5%) dequant 31172 (25.6%) gemm gate/up 20958 (17.2%) gemm down 9036 (7.4%) combine 928 (0.8%) ple 347 (0.3%) kv stage 1071 (0.9%) gdn conv+gates 509 (0.4%) gdn recurrence 5003 (4.1%) gdn out proj 2026 (1.7%) hc write 3145 (2.6%) hc read: down+silu 2583 (2.1%) hc read: up 1688 (1.4%) hc read: inject 1510 (1.2%) hc read: mix 1590 (1.3%) qsa: indexer gemms 176 (0.1%) qsa: norm/rope/kv append/q prep 15 (0.0%)
strata prefill timing: host: chunk setup (PLE rows, the expert stream plan) 78 ms, waiting for each chunk 68 ms, after each chunk (the draft layer, progress) 558 ms, PLE 47 ms
strata verify: capturing the 6-token window (709 MiB of VRAM free)
strata verify: captured the 6-token window (upload no error, sync no error) in 19.0 ms
strata verify: capturing the 1-token window (691 MiB of VRAM free)
strata verify: captured the 1-token window (upload no error, sync no error) in 21.2 ms
strata verify: capturing the 4-token window (675 MiB of VRAM free)
strata verify: captured the 4-token window (upload no error, sync no error) in 23.7 ms
strata verify: capturing the 2-token window (659 MiB of VRAM free)
strata verify: captured the 2-token window (upload no error, sync no error) in 23.2 ms
strata verify: capturing the 3-token window (641 MiB of VRAM free)
strata verify: captured the 3-token window (upload no error, sync no error) in 21.4 ms
strata verify: capturing the 8-token window (625 MiB of VRAM free)
strata verify: captured the 8-token window (upload no error, sync no error) in 19.2 ms
strata verify: capturing the 5-token window (609 MiB of VRAM free)
strata verify: captured the 5-token window (upload no error, sync no error) in 21.8 ms
strata verify: capturing the 7-token window (591 MiB of VRAM free)
strata verify: captured the 7-token window (upload no error, sync no error) in 20.6 ms
strata serve: PCIe share: the CPU pool takes 327 us per missed expert (5.3 GB/s of expert bytes), the link 12.3 GB/s -> pcie_frac 0.75 (was 0.65; --pcie-frac N fixes it, STRATA_PCIE_FRAC_DEFAULT=old keeps the start-up rule)
strata serve: prompt 126967 tokens = 0 reused + 126967 read in 123269 ms (1030.0 tok/s), 2671 generated in 97056 ms (27.5 tok/s), drafts accepted 1716 of 2153, 6 checkpoints
strata serve: decode expert cache hit rate: 80.9% (1107757 hits / 1369893 lookups)
strata serve: route tail skip: 114332 missed experts skipped (122203 entries) since the start
strata serve: expert tiers: GPU 1107757 hits this request; since the start RAM 0 blobs, files 0 blobs 975184.1 MB read (the GGUF in place)
strata serve: file tier I/O this request: the OS read 937.8 MB from storage (49 major faults) for 975184.1 MB of expert reads; page cache held 974926.2 MB at the read, not 257.9 MB; io prefetch: 0 read ahead (460.6 MB by pread), 0 used, 0 unused, 51810 skipped (cached), 0 dropped; decode waited 8795.1 ms in 30055 fetches; decode gate: cache room 1.23 of the experts, read-ahead used 100%, page cache held 100% of the decode's reads (EWMA), closed, closed in 891 windows so far, 7 flips; read ahead 0.0 MB, 0.0 MB of it used; 0 late, 0 not admitted (confidence), 0 (budget 0 MB/window)
strata serve: KV streaming: 98.29% of 19188348 block reads hit VRAM, 1323.6 MiB read from RAM
strata serve: suffix drafts: 85 windows, 209 of 253 drafts accepted
[strata] drafting: DFlash2 alone (--draft dflash2, --draft-conf 0.7)
[strata] mapping the experts from the model files (about 47 GB, --mmap-experts): they are not loaded into RAM - the OS file cache reads them as the GPU's expert cache fills and as requests need them.
[strata] filling the GPU's expert cache (5653 experts, 9.16 GiB of VRAM) ...
[strata] done: 2671 tokens in 220 s (27.5 tok/s) (stop, cancel=False), expert cache 80.9% hit
```

### Agent B Profiling Notes (`p1-20261119T065652-diagnostic-1`)
```text
[strata] 2026-11-18 21:57:32 engine started: /opt/strata/engine/strata --serve --pack /stage10-data/packs/iq3_xxs-native --native /iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf --ple-gguf /iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf --expert-profile /opt/strata/data/expert-profile.bin --mmap-experts --max-context 131072 --kv int8 --kv-resident 32768 --spec 8 --prefill auto --expert-cache auto --draft dflash2 --draft-model /stage10-data/dflash2/qwen3.8-flash-next-dflash2.q4_0-selq4.pack --draft-fallback none --mtp-draft-vocab /shared-mtp/rt/draft_vocab.bin --draft-conf 0.7
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
strata: prefill plan: chunk 8192, ring 96 kept: file set 34.6 GiB fits the page cache 51.5 GiB -> about 0.0 GB read from the drive per 32768-token prompt (4 chunks)
strata: prefill plan inputs: 40.0 GiB experts, 9.2 GiB in the GPU caches, 0.0 GiB RAM copy (0 lend slots kept), file tier 30.8 GiB; 51.5 GiB available for the page cache; PCIe 12.3 GB/s; drive 2.50 GB/s (nvme1n1 is NVMe); a 32768-token prompt
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
strata prefill timing: 126961 tokens, GPU timeline 121017 ms, wall 121068 ms, host staging 103529 ms: embed+steps 614 (0.5%) hc read 40 (0.0%) gdn 5887 (4.9%) qsa proj 3002 (2.5%) qsa indexer 6 (0.0%) qsa select 4794 (4.0%) qsa attn 10180 (8.4%) router+shared 2006 (1.7%) host grouping 1206 (1.0%) gather 14 (0.0%) wait copy 12530 (10.4%) dequant 29399 (24.3%) gemm gate/up 21487 (17.8%) gemm down 9176 (7.6%) combine 929 (0.8%) ple 373 (0.3%) kv stage 1055 (0.9%) gdn conv+gates 509 (0.4%) gdn recurrence 5014 (4.1%) gdn out proj 2032 (1.7%) hc write 3144 (2.6%) hc read: down+silu 2612 (2.2%) hc read: up 1707 (1.4%) hc read: inject 1520 (1.3%) hc read: mix 1590 (1.3%) qsa: indexer gemms 176 (0.1%) qsa: norm/rope/kv append/q prep 15 (0.0%)
strata prefill timing: host: chunk setup (PLE rows, the expert stream plan) 77 ms, waiting for each chunk 64 ms, after each chunk (the draft layer, progress) 536 ms, PLE 88 ms
strata verify: capturing the 6-token window (709 MiB of VRAM free)
strata verify: captured the 6-token window (upload no error, sync no error) in 18.1 ms
strata verify: capturing the 1-token window (691 MiB of VRAM free)
strata verify: captured the 1-token window (upload no error, sync no error) in 18.7 ms
strata verify: capturing the 3-token window (675 MiB of VRAM free)
strata verify: captured the 3-token window (upload no error, sync no error) in 22.3 ms
strata verify: capturing the 2-token window (659 MiB of VRAM free)
strata verify: captured the 2-token window (upload no error, sync no error) in 23.4 ms
strata verify: capturing the 4-token window (641 MiB of VRAM free)
strata verify: captured the 4-token window (upload no error, sync no error) in 19.4 ms
strata verify: capturing the 5-token window (625 MiB of VRAM free)
strata verify: captured the 5-token window (upload no error, sync no error) in 19.7 ms
strata serve: PCIe share: the CPU pool takes 329 us per missed expert (5.3 GB/s of expert bytes), the link 12.3 GB/s -> pcie_frac 0.75 (was 0.65; --pcie-frac N fixes it, STRATA_PCIE_FRAC_DEFAULT=old keeps the start-up rule)
strata verify: capturing the 8-token window (609 MiB of VRAM free)
strata verify: captured the 8-token window (upload no error, sync no error) in 21.1 ms
strata verify: capturing the 7-token window (591 MiB of VRAM free)
strata verify: captured the 7-token window (upload no error, sync no error) in 17.6 ms
strata serve: prompt 126968 tokens = 0 reused + 126968 read in 122303 ms (1038.1 tok/s), 2226 generated in 79252 ms (28.1 tok/s), drafts accepted 1321 of 1662, 6 checkpoints
strata serve: decode expert cache hit rate: 82.7% (941161 hits / 1138695 lookups)
strata serve: route tail skip: 88413 missed experts skipped (93731 entries) since the start
strata serve: expert tiers: GPU 941161 hits this request; since the start RAM 0 blobs, files 0 blobs 894308.0 MB read (the GGUF in place)
strata serve: file tier I/O this request: the OS read 621.1 MB from storage (8 major faults) for 894308.0 MB of expert reads; page cache held 894059.5 MB at the read, not 248.5 MB; io prefetch: 0 read ahead (500.5 MB by pread), 0 used, 0 unused, 38231 skipped (cached), 0 dropped; decode waited 8284.4 ms in 28452 fetches; decode gate: cache room 1.23 of the experts, read-ahead used 100%, page cache held 100% of the decode's reads (EWMA), closed, closed in 841 windows so far, 7 flips; read ahead 0.0 MB, 0.0 MB of it used; 0 late, 0 not admitted (confidence), 0 (budget 0 MB/window)
strata serve: KV streaming: 98.26% of 15854928 block reads hit VRAM, 1110.0 MiB read from RAM
strata serve: suffix drafts: 34 windows, 44 of 58 drafts accepted
[strata] drafting: DFlash2 alone (--draft dflash2, --draft-conf 0.7)
[strata] mapping the experts from the model files (about 47 GB, --mmap-experts): they are not loaded into RAM - the OS file cache reads them as the GPU's expert cache fills and as requests need them.
[strata] filling the GPU's expert cache (5653 experts, 9.16 GiB of VRAM) ...
[strata] done: 2226 tokens in 202 s (28.1 tok/s) (stop, cancel=False), expert cache 82.7% hit
```

