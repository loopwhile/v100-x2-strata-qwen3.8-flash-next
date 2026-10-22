# Stage 4-B MIXED: AGY handoff (A IQ3_XXS + B IQ2_XS)

Status: **committed/test scripts prepared, NOT yet run against the P520.**
This is a dual-independent-GPU *mixed quantization* test, not a production promotion.

| | Agent A | Agent B |
| --- | --- | --- |
| Model | IQ3_XXS | IQ2_XS |
| Host GPU | 0 (V100 16GB) | 1 (V100 16GB) |
| Host CPU affinity | 0-2,6-8 | 3-5,9-11 |
| Container-local GPU | 0 | 0 |
| P520 port | 127.0.0.1:8080 | 127.0.0.1:8081 |
| ThinkPad forwarded port | 127.0.0.1:18080/v1 | 127.0.0.1:18081/v1 |
| Docker container | strata-s4b-mixed-iq3xxs-agent-a | strata-s4b-mixed-iq2xs-agent-b |
| API model name | qwen3.8-flash-next-iq3_xxs-s4b-mixed-a | qwen3.8-flash-next-iq2_xs-s4b-mixed-b |

Both reuse **existing** pinned `strata-v100-upstream:0.1.47` image (ID
`sha256:19c3b72a1097486eeae3fd9b964179a36a1c137615e5c93f6d6e70eacdab8e9d`) with *no* `STRATA_SM70_TABLE=1` and the original 131072
context, `--kv int8 --kv-resident 32768`, `--spec 4 --spec-min-p 0.5`,
native packs, mmap experts and read-only shared MTP. Keep GPU power limits,
clocks and `strata-tunnel.service` completely unchanged.

## AGY instruction (paste into Antigravity CLI on ThinkPad E14)

```text
Read AGENTS.md and docs/STAGE4B_MIXED_AGY_HANDOFF.md.
Stage 4-B MIXED: launch host GPU0 Agent A with IQ3_XXS and host GPU1
Agent B with IQ2_XS, using the existing pinned vanilla Strata 0.1.47 image.
All P520 commands must run through ssh p520.

1. Inspect the ThinkPad/P520 git worktrees. On P520 only pull --ff-only
   after verifying its worktree is clean.
2. Inspect currently running containers, GPU occupancy and ports 8080/8081.
   Never stop serving agents without first asking me. Never remove any
   existing container or image. Do not alter power or tunnel settings.
3. Run the --preflight mode of scripts/78-start-stage4b-mixed-agents.sh.
   Verify both model paths, both native packs and the image ID.
4. After any necessary approval and after ports are free, launch only the
   two new mixed containers using scripts/78-start-stage4b-mixed-agents.sh.
   Check A=IQ3_XXS on 8080/18080 and B=IQ2_XS on 8081/18081.
5. Check /health, /v1/models and isolated short API requests for both.
   Then run scripts/80-bench-stage4b-mixed-c2.sh 1.
   The runner checks equal model tokenizer files, cold-process requests,
   model IDs, GPU affinity, cache reuse, output minimum and active decode overlap.
6. Compare mixed run A to previous homogeneous IQ3_XXS host GPU0 A:
     prefill 720.4, decode 27.1 tok/s, TTFT 176.50s, expert hit 88.4%.
   Compare mixed run B to previous homogeneous IQ2_XS host GPU1 B:
     prefill 988.5, decode 36.6 tok/s, TTFT 128.69s, expert hit 92.6%.
   Note CPU/RAM/NVMe and swap contention. Repeat three cold batches
   for variability only after reviewing the first result.
7. Save raw results in ignored results/, archive a sanitized benchmark
   summary after validation and report any failures. Stop only the mixed
   containers with scripts/79-stop-stage4b-mixed-agents.sh.
   Do not delete new or old containers, or promote mixed deployment.
```

## ThinkPad commands

```bash
cd ~/Data/Workspace_VSCode/v100-x2-strata-qwen3.8-flash-next
git pull --ff-only
git status --short
cat docs/STAGE4B_MIXED_AGY_HANDOFF.md
ssh p520 'cd ~/v100-x2-strata-qwen3.8-flash-next && git status --short && git rev-parse --short HEAD'
```

After verifying the P520 worktree and pulling there (if clean):

```bash
ssh p520 'cd ~/v100-x2-strata-qwen3.8-flash-next && bash scripts/78-start-stage4b-mixed-agents.sh --preflight'
# Only after checking GPU/port availability and approving any service stop:
ssh p520 'cd ~/v100-x2-strata-qwen3.8-flash-next && bash scripts/78-start-stage4b-mixed-agents.sh'
ssh p520 'cd ~/v100-x2-strata-qwen3.8-flash-next && bash scripts/80-bench-stage4b-mixed-c2.sh 1'
ssh p520 'cd ~/v100-x2-strata-qwen3.8-flash-next && bash scripts/79-stop-stage4b-mixed-agents.sh'
```

To reuse stopped mixed containers later, first ensure ports are free; use
`ssh p520 'docker start strata-s4b-mixed-iq3xxs-agent-a strata-s4b-mixed-iq2xs-agent-b'`.
To restore untouched Stage 3-A IQ2_XS containers after mixed stop:
`ssh p520 'docker start strata-jmn-iq2xs-agent-a strata-jmn-iq2xs-agent-b'`.
Restoration should be user-directed, never automatic.

**C2 interpretation:** frozen manifest SHA-256
`e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`.
Different C2 prompts are issued to A/B; this measures concurrent **co-residency**
not a fair model-quality A/B contest. Existing C2 calibrator uses Agent A
tokenizer for both, so mixed runner compares vocab/merges/token_type/chat
template bytes and fails if they differ. Use identical independent coding
tasks in separate worktrees for a genuine quality comparison.
