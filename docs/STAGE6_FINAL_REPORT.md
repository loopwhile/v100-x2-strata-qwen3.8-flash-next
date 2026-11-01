# Stage 6 — final results (2026-10-28)

**Status: CLOSED — dual-agent IQ3_S Decode 30 tok/s target NOT MET.** The eight-phase campaign was assessed through S6-7. S6-7 was an assessment only: **no combination run or three-batch optimized-candidate confirmation** took place. No production promotion.

## Fixed goal and topology

Lenovo P520, two independent Qwen3.8-Flash-Next IQ3_S agents: A on Tesla V100 16GB GPU0 (CPU cpuset 0-2,6-8); B on V100 16GB GPU1 (3-5,9-11). Existing Xeon W-2135, 64GB shared host RAM, same SSD/model files and page cache, 150 W GPU limits, 131072-token context, INT8 KV and MTP remain unchanged. No layer split or GPU aggregation.

**Success criterion:** A >=30 tok/s **and** B >=30 tok/s, concurrently in **each of at least three valid 128K C2 batches**, with >=1024 output tokens per agent, zero prompt-prefix cache reuse, overlapping decode and passing post-health. Neither aggregate throughput nor one fast agent qualifies.

## Only replicated Stage 6 reference: S6-0

Three independent fresh-process dual-agent C2 batches all passed mechanical, output, overlap and post-health checks. Stage 6 S6-0 per-agent **decode median: A 22.3 / B 21.2 tok/s**. Per-agent prefill medians: A 908.2 / B 923.1 tok/s; first batch was substantially slower in prefill, with no definitive root cause. These medians are *not* the Stage 5 pooled arithmetic mean of 21.45 tok/s.

| Batch | A Decode tok/s | B Decode tok/s | A Prefill tok/s | B Prefill tok/s | A TTFT s | B TTFT s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 21.6 | 21.2 | 653.8 | 655.1 | 194.47 | 194.11 |
| 2 | 22.6 | 21.3 | 915.8 | 923.1 | 138.92 | 137.84 |
| 3 | 22.3 | 21.1 | 908.2 | 931.4 | 140.09 | 136.61 |
| **Median** | **22.3** | **21.2** | **908.2** | **923.1** | **140.09** | **137.84** |

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

### Consolidated candidate screening measurements (Prefill, TTFT, Decode)

All C2 evaluations captured prefill throughput and TTFT alongside decode throughput. While individual screening phase reports originally highlighted decode throughput for the 30 tok/s target assessment, the full measurements preserved in raw `summary.json` receipts are consolidated below:

| Phase | Candidate / Parameter | A / B Prefill tok/s | A / B TTFT s | A / B Decode tok/s | Output A / B | C2 Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **S6-0** | Baseline Median (3 batches) | 908.2 / 923.1 | 140.09 / 137.84 | 22.3 / 21.2 | — | PASS (3/3) |
| **S6-1** | Profile (`TIMING=1`, `VERIFY=1`) | 923.6 / 936.4 | 137.75 / 135.93 | 20.5 / 21.0 | 1607 / 1221 | PASS (Diagnostic) |
| **S6-2** | MTP spec 4 / min-p 0.7 | 933.5 / 942.6 | 136.29 / 134.99 | 20.7 / 22.6 | 1581 / 979 | FAIL (B < 1024) |
| **S6-2** | MTP spec 6 / min-p 0.5 | 930.7 / 940.5 | 136.70 / 135.36 | 18.6 / 18.8 | 1597 / 1962 | PASS |
| **S6-2** | MTP spec 6 / min-p 0.7 | 915.0 / 923.7 | 139.04 / 137.75 | 21.4 / 21.3 | 1979 / 1703 | PASS |
| **S6-2** | MTP spec 8 / min-p 0.5 | 907.4 / 920.4 | 140.21 / 138.26 | 18.7 / 19.6 | 1424 / 1077 | PASS |
| **S6-2** | MTP spec 8 / min-p 0.7 | 930.9 / 941.3 | 136.69 / 135.17 | 20.5 / 21.7 | 1796 / 1376 | PASS |
| **S6-3** | SIDE_MIXER=2 | 934.1 / 943.9 | 136.20 / 134.80 | 22.8 / 21.4 | 1332 / 1261 | PASS |
| **S6-3** | GU_SWIGLU=1 | 893.7 / 912.7 | 142.37 / 139.40 | 22.3 / 21.4 | 1332 / 1495 | PASS |
| **S6-3** | GR_UP75=1 | 933.0 / 942.5 | 136.37 / 134.99 | 22.7 / 21.4 | 1332 / 1503 | PASS |
| **S6-3** | ATTN_DAILY=1 | 919.4 / 934.3 | 138.40 / 136.17 | 22.1 / 21.3 | 1485 / 1489 | PASS |
| **S6-3** | GR_NORM_FAST=1 | 929.5 / 943.1 | 136.86 / 134.93 | 21.7 / 21.0 | 1315 / 1646 | PASS |
| **S6-3** | ARGMAX_ROWS_SM70=1 | 899.2 / 912.3 | 141.54 / 139.48 | 21.8 / 21.3 | 1315 / 1706 | PASS |
| **S6-4** | SM70_TABLE=1 | 931.7 / 941.6 | 136.54 / 135.15 | 21.2 / 21.3 | 1408 / 1410 | PASS |
| **S6-4** | EXPDEC=1 | 931.0 / 941.2 | 136.66 / 135.18 | 22.4 / 21.4 | 1371 / 1495 | PASS |
| **S6-4** | ADAPT_OVERLAP=1 | 933.3 / 941.6 | 136.32 / 135.13 | 18.7 / 18.6 | 1756 / 1553 | PASS |
| **S6-5** | pool-workers 3 | 892.2 / 906.6 | 142.60 / 140.36 | 21.7 / 21.0 | 1332 / 1489 | PASS |
| **S6-5** | pcie-frac 0.65 | 928.9 / 939.9 | 136.96 / 135.38 | 22.2 / 21.4 | 1358 / 1495 | PASS |
| **S6-6** | KV resident 24576 | 935.0 / 943.9 | 136.07 / 134.80 | 21.5 / 21.6 | 1564 / 937 | FAIL (B < 1024) |
| **S6-6** | Expert cache 4400 | — | — | — | — | FAIL (VRAM plan short) |

## Technical interpretation and limits

**S6-1 instrumentation indicates CPU Expert processing and GPU waitCPU dominate observed waiting.** Its GPU waitCPU GDN+QSA components were A 48.64+9.32 and B 45.34+8.74 ms/window; CPU expert host components A 62.15 and B 57.05 ms/window. These times **overlap** and must not be summed. The PCIe waitB parts were much smaller. Draft acceptance was A 62.6%, B 60.7%. Expert hit was A 82.4%, B 83.9%. Free VRAM was only about 495 MiB initially and 255 MiB at a later graph capture; manual cache resizing is constrained.

S6-2 through S6-6 candidate throughput data are overwhelmingly **one-batch screens**, not repeated performance estimates. A C2 mechanical PASS is not a semantic coding-quality PASS. Unmeasured parameter combinations cannot be ruled out; these tests **do not prove a universal performance ceiling** or that CPU wait can be eliminated by changing a single flag.

**Retained reference:** original Stage 5 T7-Fixed / unchanged S6-0 settings, *not* a new Stage 6 speed optimization. Further investigation would require a new, separately scoped source-level CPU Expert / host-GPU synchronization study. No 30 tok/s solution was validated.

## Data protection and archival

Results were committed in [d458495](https://github.com/loopwhile/v100-x2-strata-qwen3.8-flash-next/commit/d458495879e613bf53661f25ffd6709ab7a0bf41); original per-stage receipts were **not edited** by this documentation closure. Raw C2 files are stored locally on P520 under gitignored results/. No inference about current running container state follows from GitHub records. Production IQ2_XS containers, previous stage images/models, GPU caps and ThinkPad tunnel were not modified by this documentation update.

[Archived Stage 6 plan](STAGE6_PLAN.md) · [Archived Codex handoff](STAGE6_CODEX_HANDOFF.md) · [Container details](STAGE6_PREP.md). These archival documents are **not active instructions to restart experiments**.
