# S8-D1 diagnostic findings — 2026-11-07

ID `d1-20261107T140752`: **PROFILE_PASS_NOT_SCORED**, one fresh-process
concurrent 128K diagnostic, no scored candidate batch. Raw backup has 87 files,
all SHA-256 matched. [Receipt/report](../artifacts/stage8-followup-results-20261107/d1-20261107T140752/report.md).

| Cost per window | A ms | B ms |
| --- | ---: | ---: |
| Total decode | 97.05 | 84.02 |
| Verify | 83.00 | 70.56 |
| Host CPU expert execution within verify | 53.52 | 41.29 |
| Host plan / activation quantization / jobs | 0.34 / 0.25 / 2.00 | 0.33 / 0.23 / 1.59 |
| GPU waitCPU, GDN / QSA | 40.12 / 8.73 | 31.49 / 5.89 |
| Draft | 4.17 | 4.10 |
| Serialized adaptive-thread join | 9.67 | 9.23 |

These are overlapping views of the execution; do not add GPU waitCPU to CPU
work or to the total window. This is instrumented diagnosis, not throughput
evidence against the uninstrumented U1 or candidate measurements.

## Important source/dispatch correction

The controller prints fraction adjustments but the actual API `pcie_share`
and per-layer offloaded-expert counters are zero. Source:
`FileExpertSource::pinned` requires a ready pinned complement and
`pcie_layer` requires that complement/device alias. The native dispatcher tests
this condition before assigning any miss to PCIe. Plain mmap does not satisfy
it. The nonzero GPU `PCIe grp` profile time includes graph work even when no
useful expert is assigned. A fixed fraction alone cannot validate CPU/PCIe
balancing on this recipe.

The earlier S8-P0 source audit missed this final dispatch gate when treating
the new balancing rule as applicable to actual work. Its original observations
and U1 results are preserved; the continuation explicitly corrects that
inference. C2 is changed, before any C2 candidate execution, to the single
setting `--resident-budget-gib 2` to activate a bounded pinned subset. It keeps
mmap, original assets and default fraction; maximum proposed expert-resident
budget is 4 GiB across the pair. Startup must prove mapped pinned residency;
the empirical offload share and memory/cache effects are recorded.

## Scheduling candidate

D1 confirms a real approximately 9 ms/window join after drafting. The source
joins `adapt_thr` each window; the existing upstream `--adapt-async 1` path
advances a background job across windows. It is explicitly disabled on plain
mmap and requires resident/arena storage and pinned exchange buffers.

The continuation uses the existing upstream implementation for C3 after C2's
three-batch safety/result review. C3 inherits C2's resident budget and adds only
`--adapt-async 1`; it is not a custom source patch or a new kernel/parity claim.
The runner requires C2's completed PASS receipt and actual asynchronous startup
log. New custom source modifications would still need their separate approval
and parity gates. Fallback/unsupported startup is recorded rather than scored
as if the switch were active.

C1 tests a third worker (the extra Linux worker can be unpinned within the
unchanged cpuset); M1 tests whether larger MTP windows amortize the expensive
verify path. M2 changes cache quota policy under the existing VRAM reserve;
M3 trades cache allocation for a modestly larger KV resident window. These
remain falsifiable hypotheses, not validated improvements from D1.
