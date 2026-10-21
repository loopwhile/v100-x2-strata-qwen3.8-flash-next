# Antigravity CLI handoff — Strata Stage 4

Paste the following instruction into Antigravity CLI **from the ThinkPad E14 checkout**. This is a handoff, not a record of completed work.

```text
You are working in ~/Data/Workspace_VSCode/v100-x2-strata-qwen3.8-flash-next on ThinkPad E14.
Read AGENTS.md, README.md, and docs/STAGE4_PLAN.md before taking any action.
The remote inference host is reached ONLY through: ssh p520.

Goal: implement and validate Stage 4-0 and Stage 4-A (upstream Strata v0.1.44.1,
CUDA 12.9.1, sm_70 experimental Volta build), using the frozen
IQ2_XS / INT8 q8_0 KV / symmetric dual-independent 128K Stage 3-A recipe.

FIRST:
- Audit the local worktree and remote P520 worktree without destructive changes.
- Inspect actual running old containers and their image IDs, CPU/GPU isolation,
  bind mounts, ports, logs, configs and endpoint health.
- Verify preserved C2 workload hash and archived config receipts.
- Identify and report any discrepancy between repo documentation and live P520.

IMPLEMENT:
- Add a separate pinned upstream Docker build and isolated Stage 4-A containers,
  logs and scripts; do not edit or overwrite Stage 3-A images/containers.
- For v0.1.44.1 compile with STRATA_EXPERIMENTAL_SM60=ON and
  CMAKE_CUDA_ARCHITECTURES=70 under CUDA 12.9.1.
- Preserve q8_0 (int8) KV, kv-resident 32768, 131072 context,
  mmap experts, spec 4, spec-min-p 0.5, MTP and both CPU/GPU assignments.
- Keep a new Stage 4 C2 runner separate from scripts/52; that older runner
  hardcodes the Stage 2 health model names and must not be used unchanged.
- Verify correct image provenance and runtime compatibility before tests.

DO NOT:
- Change GPU power limits, clocks, or any host power settings.
- Change the ThinkPad SSH tunnel/systemd service or existing 18080/18081 endpoints.
- Replace, delete, rename or recreate current strata-jmn-iq2xs-agent-a/b,
  preserved older containers/images, model files or MTP data.
- Trigger model redownload, repack, bulk deletion or Docker pruning.
- Turn on STRATA_SELECT_SIMT, STRATA_SM70_TABLE, STRATA_EXPERT_PAIR,
  or experimental extra knobs in Stage 4-A's primary comparison.
- Silently switch production to a new image; don't start Stage 4-B (0.1.47)
  or Stage 4-C tuning before a separate review.

BEFORE a GPU/port-conflicting smoke test or C2 measurement, ask me to approve
stopping the currently serving agents for that test window.
Never remove them. Keep a rollback path to docker start on the original agents.

BENCHMARK, after approval:
- exact frozen C2 contract and SHA; dual cold, fresh-process, no-warmup,
  both outputs >=1024; verify no prefix reuse and concurrent decode.
- run 3 independent cold batches, report per-agent measurements and medians.
- include engine defaults that differ from 0.1.36 and compare to Stage 3-A
  observed mean prefill 909.90 tok/s, decode 22.20 tok/s, TTFT 140.09 s.
- Archive safe provenance/summary and document failures or uncertainty.

At each checkpoint summarize commands, changed files, image/commit SHA,
measured evidence, any service interruption, and precise rollback commands.
Do not claim improvements without actual measurements.
```

Operational references (do not run a restart unnecessarily):

```bash
# ThinkPad: source checkout
cd ~/Data/Workspace_VSCode/v100-x2-strata-qwen3.8-flash-next
git pull --ff-only

# P520: remote check (read-only)
ssh p520 'cd ~/v100-x2-strata-qwen3.8-flash-next && git status --short && git rev-parse --short HEAD'

# Existing, preserved serving containers on P520
ssh p520 'docker ps -a --filter name=strata-jmn-iq2xs'

# ThinkPad local tunnel read-only check
systemctl --user status strata-tunnel
```
