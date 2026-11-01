# S7-XXS-14..16 source/build audit

User requested execution of arms 14, 15 and 16, three C2 batches each, on 2026-11-01. This authorizes the isolated experiment preparation and execution; production promotion, stopping live services, power/clock changes and model restoration remain outside scope.

## Pins and preservation

- Upstream v0.2.8 / Qwen engine 0.1.54: `870aedd9e1ebe1c91f94da93b59af17729f6c5c0`.
- Fork reference: `2c9b1dd7bda3102c4a8e65fbe56c45f5c6882926`.
- Immutable arm-14 image: `sha256:2095eed79b0038ef23d602a0490bf0d89c63ad8e84ace8654c5016b2a51d2246`.
- P520 preflight: clean checkout `20b38033ad37ea9be2d882d830cbf783f19cec73`; ThinkPad checkout `c7f50d6810fbbdc6d2e45631b03a23e67f7864f8`. Files transferred to new `/tmp/stage7-v100-port-*` directories; no remote checkout synchronization or overwrite during benchmarking. The later user-requested Git synchronization is a separate documentation/code operation.
- No running containers or GPU compute processes before execution; both GPUs 0 MiB, limits 150 W. `/srv/models` 79 GiB available, root filesystem 150 GiB available. Existing containers/images/model paths retained. ThinkPad tunnel verified active.
- Original manifest and C2 harness match their frozen SHA-256 values. Arm 14 uses the unchanged reviewed runner copy, SHA-256 `287146daaaf31b449219203373ecb5bc3d8202beae87cb03d14a45f2768f6797`.

## Source decisions

Actual pinned upstream `src/kernels/cuda/iq_kernels.cu` dispatch accepts only type 22 (IQ2_S) and type 20 (IQ4_NL) for WMMA2. Type 18 (IQ3_XXS) falls through to generic WMMA. Therefore an environment-only run cannot establish arm 15.

`docker/patches/stage7-wmma2.patch` ports only the fork's W2 decoder/tile section, adds type 18 to the existing W2 dispatch and retains upstream's generic WMMA and scheduling. It fixes the tile to 128 output rows × 64 token rows; the fork's alternate N64 orientation/default bundle, indirect weight table and other kernels are not imported. A nullable input-row-index ABI supports the lean adaptation; existing callers pass null. The upstream parity test now includes IQ3_XXS and reversed input-index cases for IQ3_XXS and IQ4_XS. One-time successful launch messages identify type, shape and indexed input.

`docker/patches/stage7-wmma-lean.patch` adapts the fork's lean allocation/gather idea to upstream's buffer planner: omit Xs, alias Hh to the dead xn16 scratch, omit the fallback DQ ring, and read mixed_h through src_dev. Accounting and carving share the same predicate. Eligibility requires one visible sm_70 GPU, native supported formats, no fallback, tails or Hadamard transforms. Reader guards fail explicitly on incompatible paths. The layer-major path declines lean because its readers are not adapted. Upstream group-weight gathering and MMQ buffers are retained; this is a selective adaptation, not a wholesale fork transplant.

The actual 48-layer native expert map is mixed: gate/up types 16 (9 layers), 17 (10), 18 (6), 21 (13), and 22 (10); down types 20 (18 layers) and 42 (30). The model's IQ3_XXS name does not mean every expert is type 18. Arm 15 adds W2 for type 18 and retains W2 for types 22/20; type 21 continues through upstream generic WMMA. The lean predicate was adapted to include the model's existing generic-WMMA types 16/17; copying the fork's narrower predicate would have left LEAN inactive on this pack. This changes buffer eligibility, not the quantization or decoder implementations of types 16/17.

The lean reduction is `64000*T + 19662336` bytes before alignment/region-max effects for the model's N=2560, K=10 geometry. Actual planner choices, VRAM/cache changes and performance must be measured; this arithmetic is not a speedup claim.

## Arm-15 preparation evidence

- New image `strata-v100-upstream:0.1.54-v100-wmma2-s7-20261101`, ID `sha256:95b0e4a50a775cd1e5bbfefa711c6e038923867961d1a9e159b9fe1f92ea189e`.
- Engine SHA-256 `7e6a7f11ed23c00e88f117d831293a539a718f5861c02979bc8570c05ac6e8a8`; BUILD.json source hash `a015eaf71d217f87`; version 0.1.54; CUDA 12.9.86, sm_70, experimental SM60 flag ON. Source diff contains only kernel/header/parity files, not nv_defaults or the scheduler.
- Build attempt 1 failed before compilation due to the helper's import path. Attempt 2 compiled/linked the engine successfully, then failed because `cmake` was outside PATH. Its owned container `2946114500bd` was preserved as new cache image `sha256:199f65f5ef61ca44a218f35a9dafe84fbb19cda5a7aea3dd6facc4bb0015dc2f`. Attempt 3 reused that exact compilation, verified BUILD.json against source_hash, built the parity target using `.venv/bin/cmake`, and passed provenance checks. All failed receipts remain; no pre-existing image was overwritten. Clean reproduction and resume Dockerfiles are separate.
- WMMA2 off and on each passed 11 matrix cases per GPU: **44 checks, zero failures across two GPUs**. Cases include IQ3_XXS, zero/partial/multiple tiles, nonzero first bounds and reversed input indices.
- Fresh dual-agent 128K compatibility `smoke15-1` passed with original prompts 126967/126968 and explicitly reduced 32-token outputs, zero cached tokens, post-health and CUPTI `gemm_iq_f16_w2_kernel<18,128,64>` launch result 0 on both GPUs. It is not a scored C2 repetition.
- Only after these gates did runner 100 admit arm 15 using the literal pinned image ID. At that point it still blocked arm 16 pending its own build/allocation checks.

## Arm-16 preparation evidence

- New image `strata-v100-upstream:0.1.54-v100-wmma2-lean-s7-20261101`, ID `sha256:57b951d4375dd397d6a0f09cd45cc340c80f1f4b7a5260378bd0c88710d66779`.
- Engine SHA-256 `3f60c47a76aae76cf5e1425f50e09ca2ec61f4965287d8852d52d12f81ab5d33`; BUILD.json source hash `d50192ee4fb6f4ee`; version/CUDA/architecture unchanged. Relative to arm 15, the tracked source difference is only `src/prefill/prefill.cpp`.
- Build verified **byte-identical** `build/pf_wmma_parity` (`be6ed08418231a408dd12bbb99d8dee31a5c6a9c9b570ee4286d897957548d49`) and `build/libstrata_kernels.a` (`7d75500de80b70792ebe1301ad3541f30511ee84c355b9f4650ad99a14ffe8d4`) against the pinned arm-15 parent. Its 44 numerical kernel checks are reused, not rerun or double-counted.
- Fresh dual-agent `smoke16-1` passed original 126967/126968-token inputs, reduced 32-token outputs, zero cache reuse and post-health. Both agents logged the LEAN predicate, successful CUPTI W2 type-18 launches and `ids=1`. Buffers Xs/DQ were omitted, Hh used xn16, and the layer reader guards passed.
- Startup plan remained chunk 8192 / ring 96. Loaned expert-cache slots decreased **2489 → 2173**, corresponding to the roughly 0.51 GiB allocation reduction. This is an observed allocation effect, not a throughput claim. First 32-token response hashes matched arm 15 independently for A and B; this is a short sanity comparison, not a quality suite.
- Only after these gates did runner 100 admit arm 16 using its literal pinned image ID and require its LEAN/indexed-input proof in each scored run. No diagnostic tracing is enabled in scored C2.

## Required empirical gates

Compile CUDA 12.x/sm_70, inspect BUILD.json/binary/image pins, run WMMA2 off/on parity on both physical GPUs, trace actual kernel launches, and run separately labeled fresh 128K compatibility checks before enabling scored 15/16 IDs. The unchanged scored arm-14 image must also have dispatch evidence from a separate diagnostic process; tracing is excluded from scored runs.

Both source/build/compatibility gates above passed before enabling their scored IDs. All nine scored C2 batches subsequently passed; see the [execution report](stage7-iq3xxs-14-16-report.md). All IDs are closed. No claim of C2 quality validation or promotion follows from mechanical PASS.

## Rollback

Initial serving state was empty. Every runner stops only the containers it created, preserving them and their logs. Returning to that initial state means stopping these owned experiment containers, leaving all historical agents stopped and the tunnel unchanged. Starting historical production agents would be a separate operation, not an automatic restoration.
