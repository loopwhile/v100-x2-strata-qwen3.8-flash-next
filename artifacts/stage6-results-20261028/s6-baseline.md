# Stage 6 S6-0 baseline — 2026-10-28

Three valid independent fresh-process, no-warmup dual-agent C2 batches on P520. Stage 6 goal of at least 30 decode tok/s for each agent in each batch was not met. This is a baseline, not an optimization result.

| Batch | A prefill tok/s | B prefill tok/s | A decode tok/s | B decode tok/s | A TTFT s | B TTFT s | Decode overlap s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 653.8 | 655.1 | 21.6 | 21.2 | 194.47 | 194.11 | 65.25 |
| 2 | 915.8 | 923.1 | 22.6 | 21.3 | 138.92 | 137.84 | 59.10 |
| 3 | 908.2 | 931.4 | 22.3 | 21.1 | 140.09 | 136.61 | 66.92 |
| Median | 908.2 | 923.1 | 22.3 | 21.2 | 140.09 | 137.84 | 65.25 |

All batches passed mechanical checks, active overlap and post-health; both outputs exceeded 1,024 tokens; both cache_n and cached_tokens were zero. Prompt counts A/B were 126967/126968. The first batch's prefill was substantially slower; its cause has not been established. Stage 5 T7-Fixed recorded 899.23 tok/s prefill and 21.45 tok/s decode as A/B means; the subsequent batches are closer to that reference.

Image `strata-v100-jmnargi:2c9b1dd`: `sha256:5b62fa861bbdb346f81b0b3edf88ee21396fb4e59795a14b2b092dfa2e4aa156`; engine SHA-256 `f0da5abf41115c9c0707751ec940f0f1977d04c690b55713cd19b2b7ba815030` matches Stage 5 record. Manifest SHA-256 `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`. Configuration specifies `--spec 4`; runtime metrics reported `spec=6`, `mtp_max=4`, `lookup=3`, matching Stage 5 raw telemetry; semantics not established here.

P520 raw results: `results/c2-stage6-s6-baseline-iq3s-20261028-150906-run1`, `...-20261028-151353-run2`, `...-20261028-151751-run3`. The first attempted invocation at 150830 failed before requests because the wrapper created the output directory before the harness; its receipt is retained, and the wrapper was fixed before these measurements. Containers were stopped after the three batches, preserving definitions and logs. No prior agents were stopped and power settings were unchanged.
