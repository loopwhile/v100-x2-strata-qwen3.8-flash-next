# Stage 8 review — S8-P0 and S8-U1, 2026-11-07

**S8-U1 completed 3/3 concurrent 128K C2 PASS. No verified overall upgrade;
dual-agent 30 tok/s target NOT MET. No promotion.**

[Measured report](../artifacts/stage8-results-20261107/stage8-u1-report.md) ·
[Source/host audit](STAGE8_SOURCE_AUDIT.md) ·
[Sanitized receipts](../artifacts/stage8-results-20261107/stage8-u1-receipts.json).

## Decision from the three measurements

| Per-agent median | U1 A / B | Archived S7-XXS-14 A / B |
| --- | ---: | ---: |
| Prefill tok/s | 871.0 / 877.2 | 997.6 / 1006.6 |
| Decode tok/s | 25.2 / 27.7 | 26.4 / 26.2 |
| TTFT s | 146.02 / 145.01 | 127.53 / 126.48 |

All three U1 batches missed 30 tok/s on both agents. Agent B's descriptive
median decode difference is +5.7%, while A is -4.5%; prefill and TTFT are worse
than the archived medians. This is not a useful verified overall improvement.
All three scored batches are retained, including the first. There is no extra
baseline, screening batch, final rerun or semantic coding suite.

The sessions are not interleaved with S7, so these are not causal engine deltas.
Within U1, prefill rose monotonically from 789.6/793.0 to 944.1/951.8 tok/s;
tracked GGUF+dense residency grew from 38.27 to 42.83 GiB. Engine-reported
physical read traffic per agent fell from roughly 18.7/19.8 GB to 6.4/4.7 GB.
Do not sum those process counters as unique block-device traffic. Cache and
storage conditions therefore remain material confounders, even with zero
prompt-prefix reuse. Logical expert file_mb is much larger than physical I/O.

All six outputs differ in hash. MTP acceptance varied (A roughly 65.7–68.3%,
B 60.0–61.9%), with output lengths 1797–2314 tokens. These differences also
affect decode speed and wall time. No identical-output causal comparison is
available. New lookup/GDN/PCIe defaults were observed and are disclosed in the
audit; they are not individually isolated by U1.

Configured power stayed 150 W, SM peaks 1110 MHz, maximum temperature 62 C.
Some power samples exceeded 150 W transiently; this is not a power-limit
change. GPU telemetry covers full process lifetimes, including loading and
shutdown, and must not be compared as isolated decode power. Swap traffic is
reported in the measured receipts; it is not silently treated as zero.

## Conditional candidate decisions

**Superseded on 2026-11-07:** the user explicitly requested progressing the
remaining candidates. The table below preserves the initial stop decision;
it is not evidence that these settings failed. The agent treated missing
evidence too broadly as a reason to stop instead of completing the necessary
gates. Follow the [continuation plan](STAGE8_CONTINUATION_PLAN.md) and current
handoff for active diagnostics/candidate work. Completed U1 remains closed.

The plan does not require executing all slots. No additional C/M slot is
selected from this evidence; they remain conditional and **unexecuted**, not
proven ineffective. No new diagnostic is launched by this review.

| Slot | Decision / evidence needed before selecting settings |
| --- | --- |
| S8-P0 | DONE: pinned source/default/path audit, preserved host preflight and build/calibration receipts. |
| S8-U1 | DONE / CLOSED: startup gate + 3/3 C2; no overall upgrade. Never rerun/reuse its IDs. |
| S8-C1 | NOT SELECTED: actual allocation is 2 workers plus draining host on 3 physical cores per agent. No fresh evidence of thread oversubscription or a better placement; prior IQ3_S screens do not justify another worker-count guess. |
| S8-C2 | NOT SELECTED: new policy is demonstrably active (start 0.65, adapt to 0.70–0.75, pool 5.4–5.9 GB/s, link probe 12.3 GB/s), below its 0.95 ceiling. Current records do not isolate transfer versus CPU wait under 0.1.57, while cache/storage conditions drift. A further fixed-fraction or rule override would be an unverified guess without that distinction. |
| S8-C3 | NOT SELECTED: no new serialized-wait proof or source patch. Separate source-change approval/parity gates would be required. |
| S8-M1 | NOT SELECTED: aggregate acceptance varies but there is no per-window evidence supporting a particular spec/min-p change. Keep spec4/0.5; no blind repeat of old MTP screens. |
| S8-M2 | NOT SELECTED: approximately 721 MiB free at initial readiness and around 525 MiB before a 12-row graph capture; misses alone do not justify enlarging an already near-full VRAM plan. |
| S8-M3 | NOT SELECTED: no demonstrated safe surplus for a KV change; context/KV/resident allocation remain frozen. |

The next useful investigation would distinguish file-tier/prefill cache effects
from CPU/PCIe synchronization under 0.1.57 before choosing a runtime change.
That requires a separately defined diagnostic scope; it is not an instruction
to add instrumentation or run more C2 automatically. The archived S7-XXS-14
operational reference remains unchanged. Any future selected candidate needs
its own explicit setting, unique IDs, startup gate and three C2 batches.

## Preservation and preparation failure

There were exactly **3 scored C2 batches**, all in campaign
`u1-20261107T124518`. Both unscored startup checks are accounted for:
the first campaign `u1-20261107T124317` completed short inference, then stopped
before allocating any C2 because the runner misclassified TIME_WAIT as a
listener. That preparation failure and its checkpoint-labeling bug are recorded
in [the immutable failure receipt](../artifacts/stage8-results-20261107/preparation-failure.json).
No failed scored measurement was retried. Original raw files were not edited.

P520 raw paths: `results/stage8/S8-U1/<campaign-id>/`. ThinkPad backups:
`results/raw/<campaign-id>/`. All **173 completed-run files + 43 preparation
failure files match SHA-256** against P520; [hash manifest](../artifacts/stage8-results-20261107/raw-backup-sha256.json).
Build/source preparation is backed up under
`results/stage8-preparation-20261107/`. Only sanitized metrics/provenance are
published in the new artifact tree; raw prompts/responses remain gitignored.

At completion: no running containers or GPU work; both GPUs 0 MiB. Historical
serving containers stay stopped and preserved, as at entry. All existing
images, models, packs, MTP, serving ports and tunnel are retained. ThinkPad
`strata-tunnel.service` remains active with its original start timestamp.
No power/clock/host setting was changed. No deployment, commit or push is
implied by this review. Stage 6 stays closed and Stage 7's other quantization
tracks are unaffected.
