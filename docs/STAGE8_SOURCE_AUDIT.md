# Stage 8 S8-P0 source and host audit — 2026-11-07

Execution authorized by the user's request to proceed with Stage 8, followed by
“그래 잘 진행해서 기록해줘.” Scope starts with P0 and U1. No baseline remeasurement,
production promotion, hardware changes, or service interruption is authorized.

## Pins and source findings

**Continuation correction:** [S8-D1 findings](STAGE8_D1_FINDINGS.md) demonstrate
that plain mmap does not pass FileExpertSource's final pinned/PCIe dispatch
gate. The controller is present and logs adjustments, but U1's actual offload
share is zero. Do not infer real offload work from the balancing-rule log alone.

- Upstream release [v0.2.11](https://github.com/Niko1221/Strata/releases/tag/v0.2.11),
  published 2026-11-05, bundles Qwen engine **0.1.57**.
- Annotated tag object `4a4160162e4a402e082f41aa0a88e6eed629d913` resolves to
  source **`c3b3f5035506f3e966f1b4b7b188aeaabae92f1d`**.
- Archived baseline source is `870aedd9e1ebe1c91f94da93b59af17729f6c5c0`
  (0.1.54). S7-XXS-14 remains closed and is not rerun.
- `CMakeLists.txt` still supports the explicit experimental CUDA12/Volta build:
  `STRATA_EXPERIMENTAL_SM60=ON`, `STRATA_ENABLE_CUDA=ON`,
  `CMAKE_CUDA_ARCHITECTURES=70`. Image uses CUDA **12.9.1**; the host driver's
  reported CUDA 13.0 capability is not the compiler/toolkit used for this build.
- `setup.py` pins llama.cpp to `3cf03257f219afbe7334045ff7c6a06ac68c627d`.
  `requirements.txt` and `requirements-build.txt` pin Python/build dependencies.

### Applicable changes and exclusions

1. The CPU/PCIe missed-expert balancing rule now permits a **0.95** ceiling on
   discrete GPUs (previously 0.60). Its pool factor falls from 1.85 at >=30 GB/s
   toward 0.8 at <=12 GB/s. `src/program/generate.cpp` calls the rule for the
   single-GPU PcieAuto path; it is not exclusively a layer-split optimization.
   This is applicable to the independent V100 agents. Actual effective fractions
   must be read from the measured logs; the source does not prove a speed gain.
2. `serve/server.py:gdn_stack_env` adds `STRATA_GDN_TC=1` and
   `STRATA_GDN_CONVL2=2` on Linux CUDA. The TC scan has a cc>=8 runtime gate and
   falls back on V100. The fused convolution mode 2 in
   `src/prefill/kernels.cu:gdn_conv` has no equivalent cc>=8 gate and can apply.
   Therefore new GDN defaults cannot all be dismissed as inactive on Volta.
   These defaults are disclosed as part of the U1 engine change; no extra tuning
   overrides are silently added to the archived baseline.
3. NVIDIA K-quant MMQ defaults and the bare-auto 32768 prompt-chunk ceiling
   require cc>=8. V100 retains the 8192 ceiling, subject to the normal planner.
   This model remains the original GSQ-RCO IQ3_XXS, not the newly released
   Unsloth Dynamic v3.1 files. No download/repack/quantization substitution.
4. `nv_defaults.cpp` has architecture tables for sm_60, sm_86 and sm_121, with
   no sm_70 speed bundle. Other-GPU release claims are not P520 evidence.
5. Server drafting defaults have changed. U1 explicitly chooses `drafting=mtp`
   and retains `--spec 4 --spec-min-p 0.5`; no DFlash2 model is introduced.
   The frozen context, KV, resident window and runtime values are also written
   as explicit `user_args`, preventing the new `vram_fit` policy from silently
   shrinking KV. The runner verifies actual child arguments before scoring.
6. No Stage 7 WMMA2/LEAN source patch, SSD override or custom CUDA port is
   applied. Runtime overrides remain exactly SIMT=1, SM70_TABLE=1, PF_WMMA=1.
7. `generate.cpp` adds a default lookup window up to 12 rows for a narrow-window,
   single-GPU serve build with suffix drafting, without a cc>=8 restriction.
   `--spec 4` still fixes the MTP's own window; lookup can extend farther than
   the old spec+2 rule. This is another upstream default to verify in startup
   logs, not an independently tuned M1 arm. Output/MTP comparability may change.

Prior S7-XXS-DIAG-1 reported verify-window CPU waits (GDN 36.68 + QSA 7.19 ms
within verify 79.40 ms). Stage 6 IQ3_S profiling also found large CPU waits but
negative/noisy one-batch tuning screens. These are investigation clues, not
proof that waits are removable or that the same tuning transfers to IQ3_XXS.
U1 tests the applicable upstream balance changes first. C1/C2/C3/M1/M2/M3 are
conditional and are not automatically launched or combined.

## Live preflight and clock correction

P520 identity: `p520-llm`; clean GPUs and no running containers at 12:27 KST.
Existing `strata-s7-xxs14-serve-a/b` are stopped and preserved. GPU0/GPU1 each
0 MiB, 150 W. Approximately 59 GiB RAM available, no swap used, 144 GiB free
on `/srv/models`, 181 GiB free on root. Test ports 18086/18087 were free;
8080/8081 and ThinkPad tunnel configuration are untouched.

The first inspection incorrectly treated application clocks of 1312 MHz and
recent startup clock samples as evidence of a missing 1110 MHz lock. The user
question prompted inspection of the actual boot service: **both GPUs were
successfully locked to 135–1110 MHz at 12:22:21 KST**, as recorded by the
current boot's `v100-clock-lock.service` journal. Application clocks are a
different setting. No power/clock/service configuration was changed. The
runner requires this journal evidence and rejects telemetry above 1110 MHz.

ThinkPad HEAD at entry: `67a9b224052d3820706b14e30855f0c8f1ec09de`.
P520 HEAD: `62eb4a54d81502a18fab9a0ad22cff23e98dd676`, with an untracked
`scripts/103-stage7-cooling-c2.py`. No pull/reset or overwrite of that worktree.
Preparation files are transferred to dedicated `/tmp/stage8-*` paths.
The referenced `docs/WBS.md` and `docs/methodology.md` do not exist in this
checkout; Stage 8 plan and current-state handoff govern this execution.

## Execution and preservation

New independent files: `Dockerfile.stage8-0.1.57`,
`docker/build_upstream_0157_v100_engine.py`, scripts 104/105.
New image tag: `strata-stage8-upstream:0.1.57-c3b3f50`; existing tags cannot be
overwritten by script 105. Build and asset SHA receipts are under
`/tmp/stage8-build-20261107/` on P520 and backed up locally as preparation
evidence. Hashing the original model reads its files into Linux page cache;
this is disclosed as a cache confounder, not benchmark warmup/inference.

Build completed with exit 0. Immutable image:
`sha256:590b604d9bcf5268ea03f6ab5b786e4051e69884eee8a328b6de54a4c55033d2`;
engine SHA-256 `77519ceb88fc6413666a0c5f9f7dc8447023a0c61d09cd22e7151711076c89d1`.
BUILD.json version 0.1.57, archs [70], toolkit 12, source hash
`e098a67d9f6e6a24` matches setup's computed source hash. cuobjdump lists 76
sm_70 ELF entries. All 15 original model/pack/tokenizer/MTP files were hashed
successfully. Offline original-harness calibration produced 126967/126968
tokens and prompt SHA-256 A `882a3617750ab8dbcb61d3e8e1d42641555a6b1450d060d7bb22a4f1161670b6`,
B `5a19042f67dd7702e843595467e1d6c2b96414f565b0fbfa8036590709dba557`.
No GPU inference was used for these packaging/calibration checks.

Runner 104 admits only a unique U1 ID, takes both Stage 7 and Stage 8 locks,
records PID/start ticks/boot ID, uses immutable image and engine hashes,
checks source/harness/workload pins, and refuses any live GPU/container work.
It performs one unscored short startup check, stops its owned pair, and then
creates fresh independent A/B containers for exactly three frozen C2 batches.
Each phase has dedicated configs, logs, telemetry and checkpoints. There are
no retries; failures preserve evidence and stop the campaign. Serving ports
are never bound. Cleanup stops only recorded experiment container IDs and
retains all containers, models, images and raw evidence.

Initial serving state is empty. Rollback is stopping owned experiment IDs and
returning to that empty state. Historical serving containers stay stopped;
starting them or promoting U1 is a separate user operation.

Build, startup and scored verdicts are recorded in the execution report only
after their respective gates complete. This audit itself is not a C2 result.

## Preparation correction before scoring

`u1-20261107T124317` passed startup/short inference on both GPUs (observed SM
1110 MHz). Before allocating/launching batch 1, the runner's bind-based port
check rejected its own stopped phase's TCP TIME_WAIT sockets. `ss -ltn` showed
no listener; no container/GPU workload remained. No C2 was launched. This is
a runner preparation failure, not an engine C2 failure or speed result.
The original attempt, logs and runner hash `31e4d432...` are preserved.
Its exception handler incorrectly overwrote the completed startup checkpoint
row; the independent startup verdict and API receipts remain intact.

Runner revision `3f1f4252ea96afadc4b03db1f692a93372b69793e438520210abc4d2b7a1e534`
checks LISTEN sockets (including IPv4/IPv6) and preserves completed phase
verdicts. Mocked listener gates and syntax checks passed. New unique campaign
`u1-20261107T124518` uses the same approved U1 recipe and the three scored
batches that have not yet run. No scored retry, baseline rerun or ID reuse.
