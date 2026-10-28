# Stage 6 — isolated IQ3_S dual-agent decode optimization infrastructure

**Status:** Container definitions and launch/stop/C2 scripts prepared in GitHub; **NOT built, started, tested or deployed on P520.**
**Prepared:** 2026-10-28 (Asia/Seoul).
**Objective:** Two independent IQ3_S agents, **each >=30 decode tokens/s simultaneously** under frozen dual 128K C2; not aggregate throughput, not single-agent performance.

## Frozen Stage 6 hardware / topology

| Property | Agent A | Agent B |
| --- | --- | --- |
| Physical GPU | V100 16GB GPU0 | V100 16GB GPU1 |
| CPU affinity | `0-2,6-8` | `3-5,9-11` |
| Host listening address | `127.0.0.1:18082` | `127.0.0.1:18083` |
| Internal engine port | `8080` | `8080` |
| Container | `strata-s6-iq3s-agent-a` | `strata-s6-iq3s-agent-b` |
| Model ID | `qwen3.8-flash-next-iq3_s-s6-a` | `qwen3.8-flash-next-iq3_s-s6-b` |

Both agents retain the same 64 GB shared host RAM, same physical IQ3_S GGUF mmap/page-cache, same NVMe and MTP mount, 150W/GPU cap, 131072 context, INT8 KV with resident 32768, and no layer split. No RAM/GPU/power/CPU-affinity change is within scope.

## Pinned Stage 5 T7-Fixed baseline (NOT a new Stage 6 result)

- Existing **local** image `strata-v100-jmnargi:2c9b1dd` (Docker image ID `sha256:5b62fa861bbd66bf11600f153e1f277145ed0c41d118a39a6d5fc8c9735147fa`, verified by launch and benchmark scripts) (fork source commit `2c9b1dd7bda3102c4a8e65fbe56c45f5c6882926`); Stage 6 **reuses the image**, rather than building a new one. This repo contains its original reproducible Dockerfile `Dockerfile.jmnargi-v100-stage5` and build script `scripts/87-docker-build-jmnargi-stage5.sh`.
- Frozen flags: `STRATA_SM70_PERF=0 STRATA_SELECT_SIMT=1 STRATA_PF_WMMA=1 STRATA_PF_WMMA2=1 STRATA_STAGER_SSD=0`.
- Frozen args: `--spec 4 --spec-min-p 0.5 --expert-cache auto --prefill auto --max-context 131072 --kv int8 --kv-resident 32768 --mmap-experts`, and same native pack, expert profile and MTP.
- Archived Stage 5 3-batch baseline: prefill **899.23 tok/s**, decode **21.45 tok/s** *A/B mean*, TTFT **141.64 s**. [Full record](../artifacts/stage5-results-20261027/stage5-t7-jmnargi-summary.md).
- Stage 6 success requires **both** individual agent rates >=30 tok/s in **each of at least three valid dual-agent C2 batches**, with positive concurrent-decode overlap and C2 correctness. The benchmark includes >=1024 generated tokens per agent; prompt A=126967, B=126968; workload SHA256 `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`.

## Files prepared

| Path | Purpose |
| --- | --- |
| `artifacts/stage6-configs-20261028/iq3s/strata-s6-iq3s-agent-a.json` | Independent A model config |
| `artifacts/stage6-configs-20261028/iq3s/strata-s6-iq3s-agent-b.json` | Independent B model config |
| `scripts/88-start-stage6-agents.sh` | Create new Stage 6 containers, with port/GPU/preserved-container preflights |
| `scripts/89-stop-stage6-agents.sh` | Stop **only** Stage 6 containers, preserve container objects and logs |
| `scripts/90-status-stage6-agents.sh` | Read-only status and /health check |
| `scripts/91-bench-stage6-c2.sh` | Restart **only** Stage 6 A/B, run frozen C2, archive local results |
| `scripts/92-remove-stage6-only.sh` | Optional explicit reset of *stopped* Stage 6 objects only; required confirmation argument |

Logs are new files under the checkout's gitignored `results/stage6/logs/`; C2 output goes into `results/c2-stage6-*/`. The original model, pack, MTP, image, Stage 5 config/logs and existing containers are not modified.

## Safety gates (must pass before any P520 execution)

1. All of this commit is **GitHub file preparation only**. A Git commit cannot create an actual P520 Docker container. Do not treat prepared files as tested deployment.
2. **Do not stop an existing production or experiment agent automatically.** The start script rejects running `strata-*` containers and ANY active NVIDIA compute PID. This intentionally prevents starting Stage 6 on busy GPUs, even though the host ports differ. The user must explicitly approve a test window and decide how to stop any running pair.
3. Never delete/recreate `strata-jmn-iq2xs-agent-a/b`, the preserved Stage 5 pair, original images, GGUF, native packs, historical benchmark evidence, or the persistent ThinkPad `strata-tunnel.service`. The latter's `18080/18081` local endpoints and P520 `8080/8081` remain unchanged.
4. **P520 18082/18083 are loopback-only**; they are *not* exposed on Tailscale or the ThinkPad SSH tunnel. To use them from ThinkPad, establish a separate user-approved SSH forwarding, using **different ThinkPad local ports**, e.g. `ssh -N -L 28082:127.0.0.1:18082 -L 28083:127.0.0.1:18083 p520`; do not edit the existing tunnel service.
5. `docker start` does not apply changed environment/JSON. A new arm requires stopping Stage 6 containers, invoking `92-remove-stage6-only.sh --confirm-stage6-only`, then creating Stage 6 containers with revised Stage 6 configuration/explicit flags. These operations affect Stage 6 only. No script automatically removes containers or runs a benchmark upon creation.
6. Use source-pinned CUDA12.9 Volta-compatible image. Never compile `sm_70` using CUDA13 or change host power caps.

## When a test window has been approved: manual P520 commands (NOT executed yet)

Work from a clean P520 checkout synced using `git pull --ff-only` only if safe and clean. Check the image before running; do not build just to satisfy the preflight without separate approval.

```bash
# Read-only local syntax and JSON validation (does not create/start any container):
for f in scripts/{88,89,90,91,92}-*.sh; do bash -n "$f"; done
python3 -m json.tool artifacts/stage6-configs-20261028/iq3s/strata-s6-iq3s-agent-a.json >/dev/null
python3 -m json.tool artifacts/stage6-configs-20261028/iq3s/strata-s6-iq3s-agent-b.json >/dev/null

docker image inspect strata-v100-jmnargi:2c9b1dd
docker ps
nvidia-smi

# Only after approved test downtime and AFTER both GPUs are free:
bash scripts/88-start-stage6-agents.sh both
bash scripts/90-status-stage6-agents.sh

# When both services report loaded and 131072 context:
bash scripts/91-bench-stage6-c2.sh s6-baseline 1
bash scripts/91-bench-stage6-c2.sh s6-baseline 2
bash scripts/91-bench-stage6-c2.sh s6-baseline 3

# Stop only Stage 6 when finished. This preserves its container definitions.
bash scripts/89-stop-stage6-agents.sh
```

The benchmark script checks frozen manifest SHA, exact Stage 6 container names/image, both /health model IDs/131072 context, requests_kept=0 after each **Stage 6-only** restart, and saves a sanitized summary under local results. The engine's exact effective environment and Docker inspect records are stored locally; review/redact before publishing.

## Candidate research flags for later Stage 6 experiments

New test containers can be created with selected allowlisted flags exported in the shell, e.g. `STRATA_SIDE_MIXER=2 bash scripts/88-start-stage6-agents.sh both`. Supported research toggles include `STRATA_SIDE_MIXER`, `STRATA_GU_SWIGLU`, `STRATA_GR_UP75`, `STRATA_ATTN_DAILY`, `STRATA_GR_NORM_FAST`, `STRATA_ARGMAX_ROWS_SM70`, `STRATA_SM70_TABLE`, `STRATA_EXPDEC`, `STRATA_ADAPT_OVERLAP` and `STRATA_Q8_GATHER_WIDE`. Keep source-version support and actual effective kernel activation under review.

- Diagnostic-only: `STRATA_DECODE_TIMING=1 STRATA_VERIFY_PROFILE=1`. These perturb measured decode timings. **Never use with scored C2**; the benchmark script refuses profiling-enabled containers.
- MTP settings (`--spec`, `--spec-min-p`) are in the new Stage 6 JSON configs and should be changed only in dedicated candidate branches/files; the committed baseline JSON remains a reference.
- Further tuning (cache policy, pool-worker count, PCIe work balance, KV residency) follows **measured** decode bottlenecks, not presumptions.
- Never combine a first-time decode optimization with other new changes in a single arm. Start by reproducing the Stage 5 reference (S6-0), then a separate instrumented profiling pass (S6-1).

**This commit does not claim 30 tok/s, does not modify host Docker state, and does not promote Stage 6 to production.**
