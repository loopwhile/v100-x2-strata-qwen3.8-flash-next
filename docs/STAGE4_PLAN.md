# Stage 4 — upstream Strata V100 engine comparison plan

Status: **PLAN ONLY (not implemented, not measured)**  
Created: 2026-10-21 (Asia/Seoul)  
Execution: ThinkPad E14 / Antigravity CLI → `ssh p520` → ThinkStation P520  
Scope: Qwen3.8-Flash-Next **IQ2_XS**, dual independent **128K** agents on V100 16 GB ×2.

> Stage 4 changes the **Strata engine** only for its primary comparison. Keep the model, data, INT8 (`q8_0`) KV, symmetrical Agent A/B recipe, GPU/CPU topology, C2 workload, and host power settings unchanged. This document authorizes preparation/planning, not an automatic replacement of the live service.

## 0. Non-negotiable preservation rules

1. **Do not delete, recreate, rename, or overwrite** current containers `strata-jmn-iq2xs-agent-a` and `strata-jmn-iq2xs-agent-b`. Also preserve historical `strata-iq2xs-*` containers and both existing Docker images (`strata-v100-jmnargi:9d77749`, `strata-v100:0.1.31`).
2. Do not alter the ThinkPad `strata-tunnel.service`, its local endpoints (`127.0.0.1:18080`, `127.0.0.1:18081`), or the P520 endpoint contract (A: host 8080, B: host 8081). `docker start` does **not** upgrade an existing container's image.
3. **NO POWER CHANGES**: do not run `nvidia-smi -pl`, change GPU clocks, PSU, power limits, persistence policies or host power-management configuration. No 225 W trial is part of Stage 4. Do not attribute any prior reset to power without new evidence.
4. Never mutate/delete GGUF shards, native pack, shared MTP assets, model configuration JSON, or existing logs. Prefer read-only model/MTP bind mounts and separate Stage 4 log/result paths. Do not re-download or re-pack the IQ2_XS model.
5. Do not run `docker rm -f`, `docker system prune`, `docker image prune`, destructive `git reset`, or substitute new containers under old names.
6. A/B should be symmetric **except** for expected identity, GPU assignment, CPU affinity, port, log path, and container name. Keep separate CPUs per agent; do not share both V100s into a single model.
7. Prior to a test needing host ports 8080/8081 or the same GPUs, **ask the user before stopping either currently serving agent**. Build and offline validation must not interrupt service. Stop old and start new only for an agreed test window; rollback must be explicit.
8. Do not silently promote Stage 4 to production, retarget the SSH tunnel, or edit host services. Promotion is a separate, user-approved task.
9. No inference that an untested improvement is guaranteed. Distinguish upstream claims, calculations and measured P520 outcomes.

## 1. Verified baseline and frozen inputs

| Item | Stage 3-A reference (keep fixed) |
| --- | --- |
| Host | ThinkStation P520, Xeon W-2135, RAM 64 GiB, V100-SXM2 16 GiB ×2 (`sm_70`) |
| Current engine | `jmnargi/Strata-V100`, 0.1.36, commit `9d7774919e26d235359bc2c3001f61f607eb288d` |
| Existing image | `strata-v100-jmnargi:9d77749` (must remain) |
| CUDA | `nvidia/cuda:12.9.1-devel-ubuntu24.04` |
| Model | existing IQ2_XS GGUF, native expert pack and MTP data, **no conversion** |
| Agent configs | `artifacts/stage3-configs-20261004/iq2xs/strata-jmn-iq2xs-agent-{a,b}.json` |
| Context / KV | `--max-context 131072 --kv int8 --kv-resident 32768` |
| Engine recipe | `--expert-cache auto --prefill auto --spec 4 --spec-min-p 0.5 --mmap-experts` |
| Forbidden baseline flags | Do not set `STRATA_PROMPT_ATTN_OLD=1`, `STRATA_EXPERT_PAIR=1`, `STRATA_SELECT_SIMT=1` in Stage 4-A's primary arm |
| C2 workload | `bench/workloads/v100-performance-v1.json` |
| C2 manifest SHA-256 | `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca` |

Baseline Stage 3-A IQ2_XS results (average of A and B; **recorded earlier, not new Stage 4 data**):

- Prefill **909.90 tokens/s**, decode **22.20 tokens/s**, TTFT **140.09 s**.
- C2 inputs A = **126,967** tokens and B = **126,968** tokens; independent cold prompts, no prefix-cache reuse.
- C2 requires minimum **1,024 generated** tokens per agent and **4,096-token output budget**. The original C2 contract includes a common launch barrier, active-overlap check, post-run health, and **no warmup**.
- Stage 3-B (`--spec 8`, `--spec-min-p 0.7`, `STRATA_EXPERT_PAIR=1`) is a **different recipe** and must **not** replace the Stage 3-A baseline.

Important: both archived Agent JSON files say `"gpu": 0`, because each container exposes only its assigned physical GPU. Preserve the distinction between **host GPU0 / GPU1** and **container-local GPU0**. Check actual `docker inspect` GPU and `CpusetCpus` before reproducing them; the historical split is A: `0-2,6-8`, B: `3-5,9-11`.

## 2. Stage order and checkpoints

### Stage 4-0 — non-destructive inventory and reproducibility receipt

Work on ThinkPad's local checkout; run P520 commands using `ssh p520`. Before editing/deploying anything:

1. Confirm clean Git state and record both ThinkPad/P520 commit SHAs. `git pull --ff-only` on P520 **only if its checkout is clean**, never overwrite P520 changes.
2. Record `docker ps -a`, `docker inspect` for current Agent A/B (image **ID/digest**, environment, entrypoint, runtime, GPU visibility, mounts, network, CPU affinity, memory, port mappings), image inspect, exact config-file SHA-256, kernel/CUDA/driver versions, and free disk/RAM/VRAM. Do not publish secrets from `docker inspect` into the repo.
3. Verify that the archived Stage 3-A configs match the intended **live** operational recipe. Record discrepancies instead of silently assuming equality.
4. Verify **frozen manifest SHA** and the original C2 prompt/tokenizer calibration method.
5. Save a sanitized, timestamped **receipt** in a new Stage 4 results directory (local `results/` is gitignored; later archive only safe summary/evidence).

**Gate:** no pre-existing resources modified, provenance captured, A/B mapping understood.

### Stage 4-A — upstream 0.1.44.1, isolated build

Target: `Niko1221/Strata` tag **`v0.1.44.1`** (release of 2026-10-14). Pin and record its resolved **commit SHA**, not just an unversioned `main` branch.

- New files, e.g. `Dockerfile.upstream-v100`, `docker/build_upstream_v100_engine.py`, `scripts/55-docker-build-upstream-v100.sh` (names may vary but must remain separate from Stage 3-A's `Dockerfile.jmnargi-v100` and script 54).
- New image tag: `strata-v100-upstream:0.1.44.1`; **never reuse** `strata-v100-jmnargi:9d77749`.
- Continue CUDA **12.9.1**; target `sm_70`; text-only.
- Required CMake parameters:
  ```sh
  -DSTRATA_ENABLE_CUDA=ON
  -DSTRATA_BUILD_TESTS=OFF
  -DSTRATA_EXPERIMENTAL_SM60=ON
  -DCMAKE_CUDA_ARCHITECTURES=70
  ```
- Include the pinned GGML/llama.cpp source requirements of this exact release. Inspect `setup.py`, CMake targets, and entrypoint expectations before adapting the current legacy-Docker-compatible build helper. If the upstream implementation differs, adapt and test; **do not** assume a tag substitution is sufficient.
- Check engine binary architecture, `BUILD.json`, resolved source SHA, and expected `strata` entrypoint. Prevent `setup.py` / entrypoint auto-rebuild, download or reconfiguration at first run when using existing data.
- Keep existing model data and both archived Stage 3-A agent recipes fixed. Do **not** add speculative tuning flags in this arm. Document new defaults that the version enables automatically (notably `STRATA_COMMIT_BATCH`, route-tail skip, PCIe fraction behavior); a frozen JSON does not imply an identical execution path between versions.

**Gate:** image builds, proven provenance and a compatible runtime are verified, no production container touched.

### Stage 4-A smoke and C2

1. Create **new**, uniquely named, disposable Stage 4-A containers (`strata-s4a-iq2xs-agent-a`, `strata-s4a-iq2xs-agent-b`), one physical GPU each. Use separate logs. Never replace an existing `strata-jmn-...` container.
2. Keep host port mapping A 8080 / B 8081 **during the agreed test window only**; there cannot be two servers binding the same host port simultaneously. Maintain ThinkPad tunnel unchanged.
3. Confirm both `/health` (`status=ok`, `loaded=true`, `max_context=131072`) and `/v1/models`; basic short API checks (`/v1/chat/completions`, and `/v1/responses` only if compatible) before an expensive C2 run. Confirm no surprise downloads.
4. Adapt `scripts/52-bench-v100-contract-c2-performance.sh` **without changing its original** or the frozen workload. The old script hardcodes Stage 2 model IDs (`qwen3.8-flash-next-iq2_xs-mmap-a/b`) in `wait_health`; simply pointing its environment variables to Stage 4 containers would **fail**. Implement a separate Stage 4 wrapper with explicit expected A/B model IDs, dynamic ports/paths and accurate version and image checks, preserving its safety assertions.
5. Run the exact `V100-PERFORMANCE-C2-128K-v1` contract: distinct prompts with verified token counts/hashes, fresh processes each repetition, **no warmup**, shared start barrier, minimum 1,024 output tokens per agent, `cache_n=0` and `cached_tokens=0` (or an explained equivalent for new telemetry), verified concurrent decode, post-health. Avoid automatic retries of a failed measurement.
6. Repeat **three independent cold batches** for Stage 4-A, saving raw logs, metrics, source/build receipts and per-run summaries. Also compare against archived Stage 3-A results; if uncertainty remains, rerun Stage 3-A under the same measurement schedule rather than treating +1 ~ 4% as established.
7. Track each agent's prefill, TTFT, decode, output counts, wall time, expert-cache hit rate, cache slots, host RAM/swap, VRAM, CPU allocation and any changed defaults. Report **median and per-run spread**, not only pooled averages. Attribute no performance change solely to commit batching without an isolation experiment.

**Gate:** no correctness/contract failure, stable container health and measured evidence sufficient to decide whether to keep testing. An inconclusive or slower engine is a valid result.

### Stage 4-B — upstream 0.1.47 (optional, separate approval)

The current **Strata 0.2.2** release bundles engine **0.1.47**. This is a **separate migration**, not a trivial Stage 4-A Dockerfile tag bump:

- `v0.2.2` replaced the old Docker `docker-entrypoint.sh` layout with `docker/entrypoint.sh` and component packaging. Investigate build/run compatibility and volume migration before running it against any existing directory.
- `v0.2.2` documents repaired CUDA12 Linux packages with `sm_60/61/70` code, but do not assume packaged runtime compatibility with this repository's preserved Stage 3-A JSON and data.
- Use **new image** `strata-v100-upstream:0.1.47`, new containers and Stage 4-B logs. Keep the same IQ2_XS model, `q8_0` KV, symmetrical 128K recipe and C2 methodology.
- Record defaults separately. Source's newer automatic route-tail and PCIe policies can alter answers/performance even if the JSON is unchanged. If needed, add a **clearly labeled diagnostic arm**, not an unreported baseline mutation, that explores `STRATA_ROUTE_TAIL_SKIP=0`, `STRATA_PCIE_FRAC_DEFAULT=old`, etc. Compare actual effective flags and log output.
- Stage 4-B may start **only after** Stage 4-A findings have been reviewed with the user.

### Stage 4-C — optional V100 tuning (not part of engine-only comparison)

Consider **one change per arm** and only after the upstream baseline is established: `STRATA_SM70_TABLE=1` (documented bitwise decode-kernel change), then (separately, if warranted) `STRATA_SELECT_SIMT=1` or `STRATA_PF_WMMA=1` (numeric behavior may differ). Test short correctness prompts and C2; do not claim performance improvement before measuring. This is not required for Stage 4 completion.

## 3. Result format and promotion policy

Stage 4 work should leave:

- Reproducible, pinned build Dockerfile/helper/script, **without modifying Stage 3-A originals**.
- Non-destructive Stage 4 start/stop/smoke/C2 scripts with explicit protection of existing containers and ports.
- A sanitized `artifacts/stage4-results-<date>/` summary, config snapshot/checksum, commit/image IDs, exact commands, per-agent per-run metrics, compare table and caveats. Keep bulky raw logs under ignored `results/`; never commit keys/tokens.
- A README Stage 4 result link and a **separate** recommendation: keep old runtime / candidate for production / needs more testing.
- A **rollback recipe** based on the untouched `strata-jmn-iq2xs-agent-a/b` containers.

Promotion is **not** part of Stage 4-A evaluation. Do not rename/recreate current Agent A/B, change the tunnel, or make a newer container persistent as production without explicit user instruction. Do not make host power changes at any stage.

## 4. ThinkPad E14 / Antigravity CLI entry point

In the ThinkPad terminal:

```bash
cd ~/Data/Workspace_VSCode/v100-x2-strata-qwen3.8-flash-next
git pull --ff-only
git status --short
cat docs/STAGE4_ANTIGRAVITY_HANDOFF.md
```

Run the CLI in **this local repository**; all P520 operations must be explicit `ssh p520 '...'` commands. On P520 verify the worktree **before** synchronizing code:

```bash
ssh p520 'cd ~/v100-x2-strata-qwen3.8-flash-next && git status --short && git rev-parse --short HEAD'
```

Use the handoff in [STAGE4_ANTIGRAVITY_HANDOFF.md](STAGE4_ANTIGRAVITY_HANDOFF.md). Start with Stage 4-0 and 4-A only; request an approved test window before interrupting either live agent.

## Source references

- [Existing Stage 3-A preserved build](../Dockerfile.jmnargi-v100)
- [Stage 3-A build helper](../docker/build_jmnargi_v100_engine.py)
- [Preserved C2 harness (Stage 2 hardcoded health-model ID)](../scripts/52-bench-v100-contract-c2-performance.sh)
- [Archived symmetric Stage 3-A IQ2_XS configs](../artifacts/stage3-configs-20261004/iq2xs)
- [Upstream v0.1.44.1 release](https://github.com/Niko1221/Strata/releases/tag/v0.1.44.1)
- [Upstream v0.2.2 release (engine 0.1.47)](https://github.com/Niko1221/Strata/releases/tag/v0.2.2)
- [Upstream Volta build support](https://github.com/Niko1221/Strata/blob/main/docs/OLDER_GPUS.md)
- [Upstream V100 kernel notes](https://github.com/Niko1221/Strata/blob/main/docs/NVIDIA_V100.md)
