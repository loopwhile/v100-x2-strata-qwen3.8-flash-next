# S6-2 MTP screening — 2026-10-28

One frozen dual C2 batch per candidate, compared with the existing S6-0 baseline (A/B decode medians 22.3/21.2 tok/s). These are screens, not replicated performance estimates. All use the pinned image, 128K context and INT8 KV; only the specified arguments differ from the baseline. No candidate demonstrated an improvement on both agents exceeding baseline variability; none advanced to three-batch confirmation.

| spec / min-p | A decode | B decode | Output A / B | C2 | Decision |
| --- | ---: | ---: | ---: | --- | --- |
| 4 / 0.7 | 20.7 | 22.6 | 1581 / 979 | FAIL: B <1024 | Reject this measured batch; speed is not a valid C2 score |
| 6 / 0.5 | 18.6 | 18.8 | 1597 / 1962 | PASS | Do not advance; both lower in screen |
| 6 / 0.7 | 21.4 | 21.3 | 1979 / 1703 | PASS | Do not advance; no clear dual improvement |
| 8 / 0.5 | 18.7 | 19.6 | 1424 / 1077 | PASS | Do not advance; both lower in screen |
| 8 / 0.7 | 20.5 | 21.7 | 1796 / 1376 | PASS | Do not advance; A lower in screen |

The engine source `src/program/generate.cpp` sets `mtp_max_t` to the configured `--spec`, then, when default suffix drafting is active, expands the maximum verification window by two up to eight. Therefore baseline `spec=6, mtp_max=4` is consistent with configured `--spec 4`, rather than proof the setting was ignored. Raw results and logs are on P520 under `results/c2-stage6-s6-2-*`. No failed measurement was retried.

Actual engine-reported accepted/offered drafts (A; B): 4/0.7: 855/1092; 454/623 (invalid C2); 6/0.5: 956/1828; 1165/2316; 6/0.7: 1238/1639; 923/1373; 8/0.5: 904/1785; 627/1271; 8/0.7: 1004/1513; 717/1078. Scored runs did not enable timing instrumentation, so tokens/window and verify cost were not collected for these candidates.
