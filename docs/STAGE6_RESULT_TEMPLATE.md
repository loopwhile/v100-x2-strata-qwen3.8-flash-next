# Stage 6 result record template (copy for EACH S6-1...S6-7 arm)

> This document is a **template**, not a benchmark result. Use one summary per arm, e.g. `artifacts/stage6-results-20261028/s6-2-spec6-p05.md`. Never replace S6-0's committed historical record.

## Identification

- Stage / arm ID:
- State: `PLANNED` / `DIAGNOSTIC` / `PASS` / `FAIL` / `SKIPPED`
- Date / operator / Git commit:
- Hypothesis and one changed variable:
- Pinned model/pack/PLE/MTP hashes or filesystem references:
- Docker image ID / native engine SHA256:
- A/B GPU mapping and cpusets:
- Context / KV / `--kv-resident` / Expert Cache:
- Model config SHA256 A/B; effective runtime flags and arguments:
- Exact frozen manifest SHA256:
- Profiling active? `YES (diagnostic; cannot be scored)` / `NO`

## Per-batch dual-agent results (three fresh-process passes when scored)

| Batch | A decode tok/s | B decode tok/s | A prefill tok/s | B prefill tok/s | A TTFT s | B TTFT s | A tokens | B tokens | Decode overlap s | C2 mechanical/post-health |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | — | — | — | — | — | — | — | — | — | — |
| 2 | — | — | — | — | — | — | — | — | — | — |
| 3 | — | — | — | — | — | — | — | — | — | — |

- Per-agent A decode mean / median / min / max:
- Per-agent B decode mean / median / min / max:
- A/B arithmetic mean decode (informational, **never substitutes for both-agent gate**):
- Mean / median batch wall time:
- Input prompt counts: A 126967, B 126968; output >=1024 per agent?
- Reused prefix: `cache_n=0`, `cached_tokens=0` in every batch?
- Both agents actively decoding in overlap? Post-health?
- Page-cache start/residency, major faults, swap, RAM and GPU clocks/power:
- Raw local `results/c2-stage6-.../` paths; no raw prompts in Git:
- Output hashes / differences and separate coding-task quality gate:

## Decode profiling (only for instrumented diagnostics)

| Metric | Agent A | Agent B | Evidence path / field |
| --- | ---: | ---: | --- |
| ms/window | — | — | — |
| accepted tokens/window | — | — | — |
| MTP offered / accepted, accepted by depth | — | — | — |
| Draft cost | — | — | — |
| Verify GPU cost | — | — | — |
| waitCPU | — | — | — |
| waitB / PCIe | — | — | — |
| waitA / host | — | — | — |
| Cache hit / resident expert slots / adaptive swaps | — | — | — |

**Profiling instrumentation changes timing. Do not report a diagnostic rate as a scored C2 speedup.**

## Decision and next step

- Reference control batch IDs, ordering and cache-state differences:
- Measured improvement and uncertainty / inter-batch range:
- Safety or accuracy problems:
- Decision: `PROMOTE TO NEXT TEST` / `REJECT` / `SKIP WITH EVIDENCE` / `NEEDS MORE RUNS`
- Next Stage 6 arm / stage, or specific root-cause investigation:
- **Final Stage 6 PASS only at S6-7:** three valid simultaneous A+B C2 batches and A>=30, B>=30 **in each batch**, plus health/correctness gates.
