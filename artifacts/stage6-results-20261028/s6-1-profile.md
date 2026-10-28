# S6-1 dual-agent decode profile — 2026-10-28

Diagnostic only: `STRATA_DECODE_TIMING=1`, `STRATA_VERIFY_PROFILE=1`; profiling affects timing and these figures are not scored performance. Frozen C2 passed mechanical, overlap and post-health, with 56.48 s decode overlap and no prompt reuse. Output A/B: 1607/1221. Raw receipt and engine logs are on P520 in `results/c2-stage6-s6-1-profile-iq3s-20261028-153622-run1/`.

| Metric | A | B |
| --- | ---: | ---: |
| Decode windows | 700 | 553 |
| Tokens/window | 2.30 | 2.21 |
| Total ms/window | 112.13 | 105.37 |
| Verify ms/window | 94.21 | 88.62 |
| CPU expert component of per-layer host ms/window | 62.15 | 57.05 |
| GPU stage waitCPU, GDN + QSA ms/window | 48.64 + 9.32 | 45.34 + 8.74 |
| GPU stage waitB, GDN + QSA ms/window | 0.41 + 0.14 | 0.41 + 0.14 |
| Draft accepted/offered | 907/1448 (62.6%) | 668/1100 (60.7%) |
| Expert hit rate | 0.824 | 0.839 |
| Major faults reported for request | 341 | 458 |

CPU expert work and GPU waitCPU dominate the reported instrumented timings; timing fields overlap and must not be added as independent totals. Reported page-cache coverage of decode reads was 100% (EWMA), with 637.4/643.6 MB physical storage reads. Actual GPU free memory started at 495 MiB and engine warned it was below 512 MiB; later graph captures reported as low as 255 MiB. Monitor memory and stop on paging/OOM or instability. This evidence supports exploring CPU/PCIe balance and expert capacity, subject to the safety gates; it does not prove a particular change will improve speed.

Both runtime reports showed `spec=6`, `mtp_max=4`, `lookup=3`, as in S6-0 and Stage 5, despite `--spec 4` in the config. The pinned `src/program/generate.cpp` preserves the configured MTP window in `mtp_max_t`, then extends the verification window by two (capped at eight) when default suffix drafting is enabled; this explains the display without an altered MTP configuration.
