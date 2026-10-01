# V100 x2 + Strata + Qwen3.8-Flash-Next

Experimental harness for a Lenovo ThinkStation P520 with:

- Intel Xeon W-2135
- 64 GB DDR4-2400
- 2 x Tesla V100 PCIe 16 GB (sm_70)
- Ubuntu Server
- First target: Qwen3.8-Flash-Next Coder IQ1_M
- Target context: 128K

## Goals

Two configurations are tested separately.

1. **Multi-GPU / one Strata server**
   - V100 #0 + V100 #1
   - one model
   - 128K INT8 KV
   - Strata layer split
   - establishes the best single-agent baseline on this machine.

2. **Two independent 128K agents**
   - server A -> V100 #0 -> port 8080
   - server B -> V100 #1 -> port 8081
   - both use the same model files
   - low-RAM mmap experts
   - requests can execute concurrently.

Do not mix the two tests. Strata itself serves one request at a time per server.

## Why Volta needs a local build

Tesla V100 is compute capability 7.0. Strata's ready-made NVIDIA engine targets newer cards. Community tests have shown V100 works when Strata is built locally for sm_70. Upstream issue #236 states that engine 0.1.31 admits Volta through the experimental build path; this harness also carries a narrow compatibility patch so it can work with the currently published source if those checks are still present.

V100 must use a CUDA 12.x toolkit. CUDA 13 dropped Volta code generation. On distributions with a very new GCC, the harness also selects an installed gcc/g++ 12-14 pair for the CUDA 12 build.

References:

- https://github.com/Niko1221/Strata/issues/236
- https://github.com/Niko1221/Strata/pull/130
- https://github.com/Niko1221/Strata/pull/139
- https://github.com/Niko1221/Strata/blob/main/docs/MULTI_GPU.md

## Test order

Run these from the root of this repository on the P520.

```bash
bash scripts/00-preflight.sh
bash scripts/01-prepare-strata.sh
```

The preflight is non-destructive. Stop if it does not see two V100 16 GB cards, if no CUDA 12.x toolkit is installed, or if no CUDA-12-compatible host compiler is available.

### Baseline A: Coder IQ1_M

```bash
bash scripts/02-setup-coder-128k-multigpu.sh
bash scripts/03-start-multigpu.sh
```

In another SSH terminal:

```bash
bash scripts/04-smoke-api.sh http://127.0.0.1:8080
python3 bench/api_bench.py \
  --config configs/coder-iq1-m-128k-multigpu.json \
  --url http://127.0.0.1:8080 \
  --targets 32000 64000 125000
```

### Baseline B: original Qwen3.8-Flash-Next

The same setup script is parameterized. For example, to reproduce the original model rather than the pruned Coder:

```bash
STRATA_FAMILY=qwen STRATA_MODEL=IQ2_XS \
  bash scripts/02-setup-coder-128k-multigpu.sh
```

Other valid original sizes are `Q2_0`, `IQ3_XXS`, and `IQ3_S`. Start with Coder and IQ2_XS before moving to the larger variants.

### True two-agent layout

Only after the single-server 128K baseline is stable:

```bash
bash scripts/10-setup-dual-agents.sh
bash scripts/11-start-dual-agents.sh
python3 bench/api_bench.py \
  --config configs/agent-a.json \
  --url http://127.0.0.1:8080 \
  --url http://127.0.0.1:8081 \
  --targets 32000 64000 125000 \
  --parallel
```

Stop both agent servers with:

```bash
bash scripts/12-stop-dual-agents.sh
```

## Data location

The scripts use this order:

1. `STRATA_DATA_DIR` if explicitly set.
2. `/srv/models/strata-data` if `/srv/models` is writable.
3. `$HOME/strata-data`.

To force a location:

```bash
export STRATA_DATA_DIR=/srv/models/strata-data
```

The upstream Strata source is kept under `.work/Strata` and is not committed here. Test logs and generated configs go under `results/` and `configs/`.

## Why Coder first

Coder IQ1_M is the easiest model for the two-independent-server test because its expert arena is much smaller than the original Q2/IQ2/IQ3 variants. It is used first to validate the architecture rather than to claim it is the only useful model.

The first pass validates:

- Volta build correctness
- 2 x V100 layer split
- actual 128K prompt processing
- INT8 KV streaming
- expert-cache residency
- prefill/decode throughput
- RAM/VRAM usage
- true concurrent two-server behavior

Once that works, Q2_0 / IQ2_XS / IQ3 variants can be added as comparison matrices.

## Important measurement rule

A model merely starting with `--max-context 131072` is not a 128K benchmark. The harness sends actual long prompts and records the API usage plus Strata status/metrics after each request.

For the parallel two-agent test, both requests are launched at the same time. This is the test that determines whether W-2135 CPU work, DDR4 bandwidth, page cache, or NVMe becomes the host-side bottleneck.
