# Current operation — S8-M1 and S8-M2 complete; M3 evaluated (not run), 2026-11-07

**No remote experiment remains running. User-scoped prioritized continuation (`M1 → M2`, evaluate `M3` without executing, no combinations) is COMPLETE.**
C1/C2/C3/M1/M2 each completed 3/3 concurrent 128K C2 (15/15 follow-up scored batches; 18/18 total Stage 8 scored batches with U1), plus one unscored D1 diagnostic. Dual-agent 30 tok/s goal NOT MET; no verified overall upgrade or promotion.

- Active task: none executing. Final review `docs/STAGE8_CONTINUATION_REVIEW.md`; full metrics/resources `artifacts/stage8-followup-results-20261107/summary.md` (`summary.csv`, `summary.json`).
- Newly completed IDs (CLOSED, no reuse/retry):
  - **S8-M1** (`m1-20261107T170315`, `--spec 6` on U1): `3/3 PASS`, finished 17:15:04 KST, exit 0. Medians A/B: Prefill `996.7 / 1003.7 tok/s`, Decode `25.3 / 26.1 tok/s`, TTFT `127.64 / 126.77 s`, MTP acceptance `49.4% / 52.6%`, Expert hit `0.881 / 0.874`.
  - **S8-M2** (`m2-20261107T171915`, `--expert-cache-per-layer` on U1): `3/3 PASS`, finished 17:31:26 KST, exit 0. Medians A/B: Prefill `994.6 / 1000.9 tok/s`, Decode `25.8 / 26.2 tok/s`, TTFT `127.89 / 127.12 s`, Expert hit `0.840 / 0.864` (`5472` slots, `114/layer`, `8.90 GiB`), MTP acceptance `66.3% / 59.1%`.
- **S8-M3 (`--kv-resident 40960`)**: NOT EXECUTED per user scope. Offline planner/source evaluation confirmed mechanical feasibility (+~113.0 MiB QSA VRAM, auto-shrinking GPU expert cache by ~65–70 slots while keeping 1.55 GiB pinned KV RAM and 700 MiB VRAM reserve unchanged), but judged it unnecessary/counterproductive because `--kv-resident 32768` already yields `97.7%–98.9%` KV VRAM hit rate (`0.41–0.45 ms/window` `kv-resolve`) whereas decode is bottlenecked by CPU expert misses (`41–53 ms/window`).
- Dedicated runner: `scripts/111-stage8-m1-m2.py` (SHA-256 `ba69cf7a92f3d10c3ba539b8191d3ae93627b32d7e61ab3fba2f9e13da009b36`), snapshot retained in `results/stage8-followup-runners/`. `scripts/107-stage8-followup.py` (`cec637b7...`) preserved byte-for-byte unchanged. P520 launcher tree `/tmp/stage8-m1m2-20261107/` retains logs and exit markers (`0`).
- Raw backups: all **952 follow-up files SHA-256 matched** (`D1` 87 + `C1/C2/C3/M1/M2` 173 each) in `artifacts/stage8-followup-results-20261107/raw-backup-sha256.json` and `results/raw/<id>/`.
- Final live check (`17:32:30 KST`): no running containers or GPU workloads; GPU0/GPU1 `0 MiB`, `150 W` limits, `135 MHz` idle, all scored SM peaks `<=1110 MHz`, `v100-clock-lock.service` `active`, no `S8-M3` directory created. Historical serving containers (`strata-s7-xxs14-serve-a/b`, `strata-jmn-iq2xs-agent-a/b`), images, models, ports `8080/8081` and ThinkPad `strata-tunnel.service` (`active` since `12:23:02 KST`) untouched.
- User requested committing, pushing, and synchronizing ThinkPad, `origin/main`, and the P520 checkout. No GPU, container, serving, power, clock or tunnel operation is authorized by Git synchronization. Do not launch M3, combination arms, retries or production operations without a new explicit user scope.

## Archived C1–C3 completion handoff — 2026-11-07

**No remote experiment remains running. Latest user scope: “C3까지만 진행해줘.”**
C1/C2/C3 each completed 3/3 concurrent 128K C2 (9/9), D1 separately unscored.
M1/M2/M3 were never launched and must not be started from retained plans/runners.
Dual-agent 30 tok/s goal NOT MET; no verified overall upgrade or promotion.

- Active task: none executing. Final review docs/STAGE8_CONTINUATION_REVIEW.md;
  full metrics/resources artifacts/stage8-followup-results-20261107/summary.md,
  with CSV/JSON medians, ranges, GPU/CPU/RAM/swap/cache/MTP/I/O evidence.
- Completed IDs (all CLOSED, no reuse/retry):
  D1 d1-20261107T140752 PROFILE_PASS_NOT_SCORED (one diagnostic, zero scored);
  C1 c1-20261107T141343 3/3 PASS;
  C2 c2-20261107T142619 3/3 PASS;
  C3 c3-20261107T144114 3/3 PASS, finished 14:56:18 KST, exit 0.
- C3 medians A/B: Prefill 820.5/825.0 tok/s, Decode29.0/28.7 tok/s,
  TTFT155.00/154.14s. No batch had both agents >=30 tok/s. C1 medians:
  998.1/1007.2 Prefill, 26.2/28.3 Decode, TTFT127.45/126.32. C2:
  823.4/827.2 Prefill, 26.6/27.9 Decode, TTFT154.44/153.75.
- P520 raw results/stage8/S8-<arm>/<id>/ under the checkout. ThinkPad
  results/raw/<id>/. All **606 files SHA-256 matched**: D1 87; C1/C2/C3
  173 each. Hash manifest artifacts/stage8-followup-results-20261107/raw-backup-sha256.json.
  Earlier U1/preparation backup remains separately preserved, 216 files.
- C2 changed only --resident-budget-gib 2 to activate mapped pinned expert
  work sharing (plain mmap's actual PCIe share was zero). C3 inherits that
  explicitly validated reference and adds --adapt-async 1. Existing upstream
  code was used; all agents/batches logged nonzero asynchronous rounds.
  No custom source patch, quality suite, or unlisted tuning combination.
- Runner snapshots by hash: results/stage8-followup-runners/.
  D1 runner166f06ad..., C1 runner14290dbf..., C2/C3 runnercec637b7...
  P520 launchers /tmp/stage8-followup-20261107/ (D1),
  /tmp/stage8-followup-v2-20261107/ (C1), /tmp/stage8-followup-v3-20261107/
  (C2/C3); logs and exit markers retained. No future job is queued.
- Same immutable 0.1.57 image590b604d9bcf..., binary77519ceb88fc...,
  sourcec3b3f5035506f3e966f1b4b7b188aeaabae92f1d, CUDA12.9/sm70.
  Workload/harness/model/pack/MTP pins and original CPU/GPU mapping preserved.
- Final live check: no running containers/GPU work; GPU0/GPU1 0 MiB,
  150 W configured limits. All scored SM peaks <=1110 MHz; lock service active.
  Initial serving state empty and unchanged; historical serving containers,
  all images/models/results, 8080/8081 and tunnel/18080/18081 preserved.
  ThinkPad tunnel remains active since 12:23:02 KST. No host/power/clock change.
- P520 Git worktree still at62eb4a54..., original untracked script103 intact.
  User requested committing/pushing the local code/docs/results. Publication
  affects Git/GitHub only; no P520 synchronization or operation is included.
  After interruption, compare local/remote heads before repeating transport
  or creating another commit; never force-push to resolve uncertainty.
- Next action: review reports or perform user-requested Git work only. Do not
  launch M arms, new diagnostics, completed IDs, or production operations
  without a new explicit user scope. Stage6 stays closed; Stage7 other
  quantization tracks are unaffected.

## Completed U1 handoff (preserved history)

### Archived U1 completion handoff — 2026-11-07 KST

**No remote experiment remains running. S8-U1: 3/3 valid concurrent 128K C2
PASS; dual-agent 30 tok/s target NOT MET; no verified overall upgrade or promotion.**

- Active WBS/task: none executing. Completed scoped task S8-P0/S8-U1; review
  in `docs/STAGE8_REVIEW.md`, measured report and receipts under
  `artifacts/stage8-results-20261107/`. This checkout has no docs/WBS.md.
- Completed ID **u1-20261107T124518**, phase `results_saved`, verdict `PASS`,
  runner/launcher exit 0. Started 12:45:54, finished 12:59:04 KST.
  Decode medians A/B **25.2 / 27.7 tok/s**; Prefill **871.0 / 877.2 tok/s**;
  TTFT **146.02 / 145.01 s**. All three batches retained; no baseline rerun.
- P520 raw: `results/stage8/S8-U1/u1-20261107T124518/` (relative to checkout).
  ThinkPad backup `results/raw/u1-20261107T124518/`: all **173 files SHA-256
  matched**. Progress/identities/commands remain in that immutable raw tree.
  Launcher `/tmp/stage8-execution-20261107-v2/u1-20261107T124518.log`, `.exit`.
- Closed preparation-only ID **u1-20261107T124317**, overall INCONCLUSIVE:
  short startup inference passed; a bind probe rejected TIME_WAIT before any
  C2 was allocated/launched. Original runner/checkpoint/logs preserved; its
  exception handler incorrectly relabeled the completed startup row, while the
  standalone startup verdict/API receipts remain valid. Corrected runner used
  a new ID for the still-unexecuted three C2 batches. **43 original files match
  the ThinkPad backup** `results/raw/u1-20261107T124317/`. No scored retry.
- Both IDs are **closed; never reuse or resume them**. Two unscored startup
  checks and exactly three scored C2 batches were executed in total. Additional
  C1/C2/C3/M1/M2/M3 candidates were reviewed and not selected; no extra
  diagnostic or GPU execution is authorized by retained scripts or handoffs.
- New image `strata-stage8-upstream:0.1.57-c3b3f50`, immutable ID
  `sha256:590b604d9bcf5268ea03f6ab5b786e4051e69884eee8a328b6de54a4c55033d2`;
  engine SHA-256 `77519ceb88fc6413666a0c5f9f7dc8447023a0c61d09cd22e7151711076c89d1`.
  Source `c3b3f5035506f3e966f1b4b7b188aeaabae92f1d`; actual binary 0.1.57,
  CUDA12.9/sm70. Model/pack/MTP checksums and original C2 calibration verified.
  Preparation backup `results/stage8-preparation-20261107/`; P520 originals
  `/tmp/stage8-build-20261107/` and `/tmp/stage8-source-audit-20261107/`.
- Final live check: no running containers/GPU workloads, both GPUs 0 MiB,
  150 W configured limits. Observed scored SM peaks <=1110 MHz; boot-applied
  135–1110 lock preserved. No power/clock/host settings changed. Historical
  `strata-s7-xxs14-serve-a/b` stay stopped/preserved, as at entry. Serving ports
  and ThinkPad tunnel untouched; tunnel remains active since 12:23:02 KST.
- P520 checkout remains at `62eb4a54d81502a18fab9a0ad22cff23e98dd676`, with
  its original untracked script 103; no remote Git pull/reset/overwrite.
- Documentation/code/results are local, uncommitted; commit/push was not
  requested. Next action: review recorded findings. Any further diagnostic,
  candidate or promotion needs a distinct scope and unique IDs. Do not relaunch
  completed work merely because an archived runner is present.

## Previous operation — cooling C2 completed; serving stopped, 2026-11-04 KST

User-authorized cooling measurement `cooling-20261104T003222` completed **3/3 fresh-process dual-agent 128K C2 PASS**, 00:34:21–00:46:27 KST. No benchmark remains running. Original S7-XXS-14 recipe, workload, power/clocks and historical evidence are preserved; closed S7-XXS IDs were not reused.

- Raw P520: `results/stage7-cooling/cooling-20261104T003222/`.
- Raw ThinkPad backup: `results/raw/cooling-20261104T003222/`; all **99 files SHA-256 matched**. Local checksum manifest: `results/raw/cooling-20261104T003222-sha256.json`.
- User requested **raw data only**, no separate report/database update, then commit/push Git changes and stop serving.
- S7-XXS-14 serving A/B (`strata-s7-xxs14-serve-a/b`) stopped at the user's request. Containers/images/configs/models remain preserved. ThinkPad tunnel unchanged. Host power settings unchanged.
- Runner `scripts/103-stage7-cooling-c2.py` is retained for audit; it is not a new execution order. This ID is completed; do not rerun or retry it. No further experiment is authorized.
- Next action: no additional GPU work; inspect local/remote Git HEAD before repeating any commit/push operation.

## Previous operation — S7-XXS-14/15/16 completed, 2026-11-01 23:17 KST

User requested three fresh dual-agent 128K C2 batches per arm. **14, 15 and 16 each completed 3/3 PASS, 9/9 total. All IDs are CLOSED; do not rerun.**

| Arm | Prefill A/B median tok/s | Decode A/B median tok/s |
| --- | ---: | ---: |
| 14 | 997.6 / 1006.6 | 26.4 / 26.2 |
| 15 | 961.2 / 969.6 | 26.3 / 26.1 |
| 16 | 990.8 / 998.7 | 26.4 / 27.0 |

Final live check at 23:17:45 KST: no running containers; GPU0/GPU1 both 0 MiB and 0% utilization; configured limits 150 W. No power/clock/host setting changes, model restoration, production promotion, endpoint or tunnel change. Original serving state was empty and remains empty.

Results: `artifacts/stage7-results-20261101/stage7-iq3xxs-14-16-report.md`; full sanitized receipts and source/build audit beside it. P520 original `results/stage7-iq3xxs-v100-port/` is preserved and all nine raw C2 directories are backed up on ThinkPad. Preparation receipts are additionally backed up under `results/stage7-v100-port-build-records/`.

14 uses immutable upstream image 2095eed79b00; 15 is pinned derived WMMA2 image 95b0e4a50a77; 16 is pinned LEAN image 57b951d4375d. CUDA 12.9/sm_70. Source/parity/128K/dispatch/allocation gates passed. Compile failures and the agent-added non-scored 14 diagnostic are explicitly documented; no diagnostics are mixed into scored C2.

Cache/swap variation was substantial in first port-image batches, so these results do not establish a causal throughput win. No separate quality suite or promotion. Stage 6 remains closed. Stage 7 IQ2_XS/IQ3_S and other quantization tracks remain separate and unexecuted by this task. The user separately requested updating the consolidated Markdown/CSV, committing/pushing, and synchronizing the P520 checkout. This is a documentation/code synchronization operation, not a new experiment; consult Git HEAD on both hosts for the synchronized revision. Future experiments require new explicit scope.

Consolidated database: `docs/CONSOLIDATED_BENCHMARKS.md` and `docs/consolidated-benchmarks.csv`, regenerated by script 98. The prior 95 records are unchanged; nine scored batch rows and three median rows bring the total to 107. Committed sanitized telemetry supports reproducible 14–16 export without raw prompts/responses.
