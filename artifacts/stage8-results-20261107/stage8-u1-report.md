# Stage 8 S8-U1 — upstream 0.1.57 IQ3_XXS, 2026-11-07

Startup and short inference passed; **3/3 fresh-process concurrent 128K C2 PASS**. No baseline rerun, scored retry, promotion or quality-suite claim.

Run `u1-20261107T124518`; 2026-11-07T12:45:54.621052+09:00 to 2026-11-07T12:59:04.365398+09:00.

Source `c3b3f5035506f3e966f1b4b7b188aeaabae92f1d`; image `sha256:590b604d9bcf5268ea03f6ab5b786e4051e69884eee8a328b6de54a4c55033d2`; engine SHA-256 `77519ceb88fc6413666a0c5f9f7dc8447023a0c61d09cd22e7151711076c89d1`.

A=GPU0/cpuset 0-2,6-8; B=GPU1/cpuset 3-5,9-11. Ports 18086/18087. Context 131072, INT8 KV/resident 32768, MTP spec4/min-p0.5, auto prefill/cache, mmap experts. SIMT=1, SM70_TABLE=1, PF_WMMA=1. New upstream defaults are recorded in the [source audit](../../docs/STAGE8_SOURCE_AUDIT.md) and effective child environments in the receipts.

| Batch | Prefill A/B tok/s | Decode A/B tok/s | TTFT A/B s | Output A/B | Overlap s | Wall s |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 789.6 / 793.0 | 23.9 / 26.5 | 161.05 / 160.36 | 1916 / 2179 | 79.92 | 242.62 |
| 2 | 871.0 / 877.2 | 25.2 / 27.7 | 146.02 / 145.01 | 1867 / 1951 | 69.25 | 220.16 |
| 3 | 944.1 / 951.8 | 25.8 / 28.0 | 134.73 / 133.65 | 1797 / 2314 | 69.63 | 216.14 |

| Metric | U1 A median (range) | U1 B median (range) | Archived S7-XXS-14 A/B median |
|---|---:|---:|---:|
| Prefill tok/s | 871.00 (789.60–944.10) | 877.20 (793.00–951.80) | 997.6 / 1006.6 |
| Decode tok/s | 25.20 (23.90–25.80) | 27.70 (26.50–28.00) | 26.4 / 26.2 |
| TTFT s | 146.02 (134.73–161.05) | 145.01 (133.65–160.36) | 127.53 / 126.48 |

Both-agent >=30 tok/s in every batch: **NO**.

All prompts are A=126967/B=126968 tokens; no prompt reuse (cache_n=cached_tokens=0), outputs >=1024, finish_reason=stop, synchronized concurrent decode and post-health passed. Per-agent wall time, output hashes, cache hits, MTP counters and runtime share notes are in [receipts](stage8-u1-receipts.json).

## GPU and host conditions

Telemetry below covers each pair's full process lifetime, including loading and shutdown. It is not isolated prefill/decode power. Configured limits stayed 150 W; SM clocks never exceeded 1110 MHz. Instantaneous power readings can exceed the configured limit.

| Batch | GPU | Temp mean/peak C | Power mean/peak W | SM mean/peak MHz | VRAM mean/peak MiB |
|---|---|---:|---:|---:|---:|
| 1 | A | 49.8 / 59.0 | 71.8 / 169.5 | 1104.5 / 1110.0 | 15143.5 / 15651.0 |
| 1 | B | 52.5 / 61.0 | 75.2 / 172.5 | 1097.2 / 1110.0 | 14886.1 / 15603.0 |
| 2 | A | 53.0 / 61.0 | 75.6 / 169.2 | 1104.5 / 1110.0 | 14817.7 / 15651.0 |
| 2 | B | 54.9 / 62.0 | 77.2 / 177.8 | 1087.2 / 1110.0 | 14604.2 / 15619.0 |
| 3 | A | 54.0 / 62.0 | 77.5 / 169.1 | 1099.6 / 1110.0 | 14951.6 / 15651.0 |
| 3 | B | 55.6 / 62.0 | 80.1 / 178.5 | 1084.9 / 1110.0 | 14742.3 / 15603.0 |

| Batch | Major faults | Swap in/out pages | Page cache before/after GiB (GGUF + dense) |
|---|---:|---:|---:|
| 1 | 20573 | 36696 / 111657 | 38.27 / 38.94 |
| 2 | 2467 | 9 / 2160 | 38.94 / 40.33 |
| 3 | 1380 | 56 / 7220 | 40.33 / 42.83 |

## Interpretation and preservation

**No verified overall upgrade; the dual-agent 30 tok/s goal was not met.** Against the archived medians, descriptive differences are Prefill A/B -12.7%/-12.9%, Decode -4.5%/+5.7%, and TTFT +14.5%/+14.6%. The B-only decode difference does not establish an overall gain. All three measured batches, including the first, remain in the median; none is discarded as warmup.

Comparison to S7-XXS-14 is descriptive across dates, not a controlled causal engine speedup. Model checksum reads populate Linux page cache, and this host rebooted before preparation. Page cache, swap, output lengths/MTP acceptance, temperature and actual throttling differ across runs. Logical file_mb is not physical SSD traffic. MTP counters and identical-output comparisons must be considered before interpreting decode deltas. No quality validation follows from mechanical C2 PASS.

A separate initial preparation attempt, `u1-20261107T124317`, passed short inference but stopped before allocating or launching any C2 because a bind probe misidentified its own TIME_WAIT sockets as occupied ports. Its original progress/logs and 43-file verified backup are retained; see [preparation failure](preparation-failure.json). A new ID used the corrected listener check for the three scored batches above. There were two unscored startup checks in total and exactly three scored C2 batches; no scored retry or reused ID.

All 173 files of the completed run match the P520 originals by SHA-256 in the ThinkPad backup. Candidate decisions and evidence limits are documented in the [Stage 8 review](../../docs/STAGE8_REVIEW.md).

Historical containers/images/models and all prior results are preserved. Initial serving state was empty; owned Stage 8 containers are stopped and retained. Serving 8080/8081, ThinkPad tunnel/18080/18081, power, clock and host settings were untouched. Raw data remain on P520 and have a checksum-verified ThinkPad backup. Conditional C/M arms require evidence from this review; none is implied by retaining the runner.

Raw P520: `results/stage8/S8-U1/u1-20261107T124518/`. Immutable sanitized metrics and provenance: [receipts](stage8-u1-receipts.json).
