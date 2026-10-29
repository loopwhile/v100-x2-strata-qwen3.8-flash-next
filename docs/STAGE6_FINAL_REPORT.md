# Stage 6 — final results (2026-10-28)

**Status: CLOSED — dual-agent IQ3_S Decode 30 tok/s target NOT MET.** The eight-phase campaign was assessed through S6-7. S6-7 was an assessment only: **no combination run or three-batch optimized-candidate confirmation** took place. No production promotion.

## Fixed goal and topology

Lenovo P520, two independent Qwen3.8-Flash-Next IQ3_S agents: A on Tesla V100 16GB GPU0 (CPU cpuset 0-2,6-8); B on V100 16GB GPU1 (3-5,9-11). Existing Xeon W-2135, 64GB shared host RAM, same SSD/model files and page cache, 150 W GPU limits, 131072-token context, INT8 KV and MTP remain unchanged. No layer split or GPU aggregation.

**Success criterion:** A >=30 tok/s **and** B >=30 tok/s, concurrently in **each of at least three valid 128K C2 batches**, with >=1024 output tokens per agent, zero prompt-prefix cache reuse, overlapping decode and passing post-health. Neither aggregate throughput nor one fast agent qualifies.

## Only replicated Stage 6 reference: S6-0

Three independent fresh-process dual-agent C2 batches all passed mechanical, output, overlap and post-health checks. Stage 6 S6-0 per-agent **decode median: A 22.3 / B 21.2 tok/s**. Per-agent prefill medians: A 908.2 / B 923.1 tok/s; first batch was substantially slower in prefill, with no definitive root cause. These medians are *not* the Stage 5 pooled arithmetic mean of 21.45 tok/s.

| Batch | A Decode tok/s | B Decode tok/s | A Prefill tok/s | B Prefill tok/s |
| --- | ---: | ---: | ---: | ---: |
| 1 | 21.6 | 21.2 | 653.8 | 655.1 |
| 2 | 22.6 | 21.3 | 915.8 | 923.1 |
| 3 | 22.3 | 21.1 | 908.2 | 931.4 |
| **Median** | **22.3** | **21.2** | **908.2** | **923.1** |

[Original baseline receipt](../artifacts/stage6-results-20261028/s6-baseline.md). Engine binary SHA256 matched Stage 5 T7-Fixed: f0da5abf41115c9c0707751ec940f0f1977d04c690b55713cd19b2b7ba815030. Frozen C2 manifest: e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca.

## S6-0 to S6-7 evidence matrix

| Stage | Measured work | Outcome |
| --- | --- | --- |
| **S6-0** | [Three valid dual-agent C2 baseline batches](../artifacts/stage6-results-20261028/s6-baseline.md) | **COMPLETE** — reference 22.3 / 21.2 medians; 30+ not reached. |
| **S6-1** | [One instrumented C2 diagnostic](../artifacts/stage6-results-20261028/s6-1-profile.md) | **DIAGNOSTIC COMPLETE** — large CPU Expert / GPU waitCPU component; profiling affects tok/s. |
| **S6-2** | [Five one-batch MTP candidate screens](../artifacts/stage6-results-20261028/s6-2-mtp.md) | **SCREENED** — no validated dual-agent win; one C2 failed minimum output (B 979). |
| **S6-3** | [Six one-batch decode kernel screens](../artifacts/stage6-results-20261028/s6-3-kernels.md) | **SCREENED** — no validated dual-agent win; small differences not proven beyond variability. |
| **S6-4** | [Three one-batch SM70 flag screens](../artifacts/stage6-results-20261028/s6-4-sm70.md) | **SCREENED** — no validated win; ADAPT_OVERLAP=1 observed A 18.7 / B 18.6 in one C2, not full causal proof. |
| **S6-5** | [Two one-batch CPU/PCIe screens](../artifacts/stage6-results-20261028/s6-5-cpu-pcie.md) | **SCREENED** — pool-workers=3 A 21.7/B 21.0; PCIe-frac=.65 A 22.2/B 21.4, no clear win. |
| **S6-6** | [KV and expert-cache tests](../artifacts/stage6-results-20261028/s6-6-cache.md) | **NO VALID CANDIDATE** — KV resident 24576 failed C2 (B 937 output); cache 4400 failed VRAM startup planning. |
| **S6-7** | [Final assessment](../artifacts/stage6-results-20261028/s6-7-assessment.md) | **SKIPPED** — no verified candidate to combine; no three-batch final combination run. |

## Technical interpretation and limits

**S6-1 instrumentation indicates CPU Expert processing and GPU waitCPU dominate observed waiting.** Its GPU waitCPU GDN+QSA components were A 48.64+9.32 and B 45.34+8.74 ms/window; CPU expert host components A 62.15 and B 57.05 ms/window. These times **overlap** and must not be summed. The PCIe waitB parts were much smaller. Draft acceptance was A 62.6%, B 60.7%. Expert hit was A 82.4%, B 83.9%. Free VRAM was only about 495 MiB initially and 255 MiB at a later graph capture; manual cache resizing is constrained.

S6-2 through S6-6 candidate throughput data are overwhelmingly **one-batch screens**, not repeated performance estimates. A C2 mechanical PASS is not a semantic coding-quality PASS. Unmeasured parameter combinations cannot be ruled out; these tests **do not prove a universal performance ceiling** or that CPU wait can be eliminated by changing a single flag.

**Retained reference:** original Stage 5 T7-Fixed / unchanged S6-0 settings, *not* a new Stage 6 speed optimization. Further investigation would require a new, separately scoped source-level CPU Expert / host-GPU synchronization study. No 30 tok/s solution was validated.

## Data protection and archival

Results were committed in [d458495](https://github.com/loopwhile/v100-x2-strata-qwen3.8-flash-next/commit/d458495879e613bf53661f25ffd6709ab7a0bf41); original per-stage receipts were **not edited** by this documentation closure. Raw C2 files are stored locally on P520 under gitignored results/. No inference about current running container state follows from GitHub records. Production IQ2_XS containers, previous stage images/models, GPU caps and ThinkPad tunnel were not modified by this documentation update.

[Archived Stage 6 plan](STAGE6_PLAN.md) · [Archived Codex handoff](STAGE6_CODEX_HANDOFF.md) · [Container details](STAGE6_PREP.md). These archival documents are **not active instructions to restart experiments**.
