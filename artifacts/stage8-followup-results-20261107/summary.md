# Stage 8 continuation — full metric summary

Rows below include completed scored candidates only; incomplete arms retain their explicit status and available valid-batch count. D1 is a separate instrumented diagnostic and is excluded from candidate medians. Historical U1 medians: Prefill 871.0/877.2 tok/s, Decode 25.2/27.7 tok/s, TTFT 146.02/145.01 s. Cache/swap/output/temperature conditions differ; these are descriptive comparisons, not controlled causal gains.

| Arm | Status | Prefill A/B tok/s | Decode A/B tok/s | TTFT A/B s | Request wall A/B s | Batch wall s | Output A/B | Decode overlap s |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| [S8-C1](c1-20261107T141343/report.md) | 3/3 C2 PASS | 998.1 / 1007.2 | 26.2 / 28.3 | 127.45 / 126.32 | 196.42 / 204.09 | 204.09 | 1775 / 2230 | 68.98 |
| [S8-C2](c2-20261107T142619/report.md) | 3/3 C2 PASS | 823.4 / 827.2 | 26.6 / 27.9 | 154.44 / 153.75 | 201.87 / 232.96 | 232.96 | 1361 / 2144 | 49.69 |
| [S8-C3](c3-20261107T144114/report.md) | 3/3 C2 PASS | 820.5 / 825.0 | 29.0 / 28.7 | 155.00 / 154.14 | 226.63 / 226.23 | 226.64 | 2074 / 2382 | 64.30 |
| [S8-M1](m1-20261107T170315/report.md) | 3/3 C2 PASS | 996.7 / 1003.7 | 25.3 / 26.1 | 127.64 / 126.77 | 174.49 / 191.06 | 191.07 | 1189 / 1683 | 46.85 |
| [S8-M2](m2-20261107T171915/report.md) | 3/3 C2 PASS | 994.6 / 1000.9 | 25.8 / 26.2 | 127.89 / 127.12 | 173.49 / 203.55 | 203.55 | 1179 / 2140 | 45.60 |

## GPU conditions

Means are unweighted averages of each scored batch's full process-lifetime means, including loading/shutdown; peaks are maxima across batches. These are not isolated prefill/decode power measurements. Configured caps stay 150 W and 1110 MHz. Instantaneous readings may exceed the configured power limit.

| Arm | Temp mean A/B C | Temp peak A/B C | Power mean A/B W | Power peak A/B W | Util mean A/B % | VRAM mean A/B MiB | VRAM peak A/B MiB | SM mean A/B MHz | SM peak A/B MHz |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| S8-C1 | 53.9 / 55.9 | 62.0 / 63.0 | 80.8 / 85.9 | 172.4 / 187.8 | 76.2 / 79.0 | 15033.9 / 14789.7 | 15651.0 / 15619.0 | 1101.0 / 1085.6 | 1110.0 / 1110.0 |
| S8-C2 | 52.9 / 54.7 | 63.0 / 63.0 | 74.4 / 78.5 | 171.0 / 182.2 | 57.9 / 67.0 | 14876.5 / 14682.3 | 15657.0 / 15659.0 | 1103.3 / 1087.2 | 1110.0 / 1110.0 |
| S8-C3 | 53.6 / 54.7 | 63.0 / 63.0 | 74.7 / 76.1 | 169.6 / 180.4 | 64.4 / 66.4 | 14894.7 / 14713.1 | 15661.0 / 15659.0 | 1101.9 / 1087.2 | 1110.0 / 1110.0 |
| S8-M1 | 54.3 / 56.3 | 62.0 / 63.0 | 82.7 / 87.7 | 168.1 / 186.9 | 71.1 / 78.7 | 15015.3 / 14761.1 | 15623.0 / 15641.0 | 1100.7 / 1083.4 | 1110.0 / 1110.0 |
| S8-M2 | 53.8 / 56.1 | 63.0 / 63.0 | 81.1 / 85.7 | 174.0 / 188.3 | 67.4 / 78.5 | 15011.2 / 14794.0 | 15609.0 / 15641.0 | 1101.6 / 1088.5 | 1110.0 / 1110.0 |

## Cache, MTP and physical reads

All entries are per-agent medians. MTP counts are accepted/proposed; acceptance is the median of each batch's ratio, not the ratio of median counts. file_mb is API-reported logical expert-read traffic. Physical read MB comes from each engine's own OS counters and must not be summed as unique disk-device traffic. Disk latency/throughput time series remain in each raw iostat.log.

| Arm | Expert hit A/B | Actual PCIe share A/B | MTP accepted A/B | MTP proposed A/B | MTP acceptance A/B % | Logical file MB A/B | Physical read MB A/B | KV VRAM hit A/B % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| S8-C1 | 0.828 / 0.879 | 0.000 / 0.000 | 1058.0 / 1254.0 | 1556.0 / 2101.0 | 68.0 / 60.0 | 260065.8 / 261119.7 | 1096.0 / 353.2 | 98.0 / 98.9 |
| S8-C2 | 0.861 / 0.881 | 0.015 / 0.012 | 760.0 / 1180.0 | 1240.0 / 1972.0 | 62.5 / 60.8 | 151014.7 / 224792.4 | 24176.9 / 23066.5 | 98.0 / 98.6 |
| S8-C3 | 0.855 / 0.839 | 0.015 / 0.014 | 1208.0 / 1379.0 | 1834.0 / 2086.0 | 66.3 / 65.4 | 238663.5 / 295435.5 | 24301.2 / 22918.1 | 98.4 / 98.5 |
| S8-M1 | 0.881 / 0.874 | 0.000 / 0.000 | 675.0 / 1009.0 | 1367.0 / 1917.0 | 49.4 / 52.6 | 149618.2 / 212724.9 | 291.3 / 325.5 | 98.2 / 98.6 |
| S8-M2 | 0.840 / 0.864 | 0.000 / 0.000 | 688.0 / 1136.0 | 1037.0 / 1941.0 | 66.3 / 59.1 | 163533.8 / 249506.8 | 267.2 / 320.9 | 97.7 / 98.3 |

## Shared host conditions

Host rows are whole-host snapshot/counter medians per batch, not independent per-agent RAM. Before/after below mean before container creation and after owned-container cleanup. Active post-health RAM snapshots and trailing sensor history are shown separately. Swap columns are pages in/out during a batch, not total swap occupancy.

| Arm | RAM used before/after GiB | RAM available before/after GiB | Tracked page cache before/after GiB | Major faults | Swap in/out pages |
|---|---:|---:|---:|---:|---:|
| S8-C1 | 1.44 / 1.43 | 59.65 / 59.66 | 43.18 / 43.18 | 87 | 20 / 399 |
| S8-C2 | 1.46 / 1.44 | 59.63 / 59.65 | 38.83 / 38.83 | 1859 | 35 / 0 |
| S8-C3 | 1.46 / 1.45 | 59.63 / 59.65 | 38.77 / 38.86 | 1931 | 20 / 0 |
| S8-M1 | 1.50 / 1.48 | 59.59 / 59.61 | 43.81 / 43.81 | 10 | 8 / 0 |
| S8-M2 | 1.50 / 1.50 | 59.59 / 59.60 | 43.81 / 43.81 | 9 | 5 / 0 |

RAM sensors during serving: post-health used is a median across batches, and the history mean averages each batch's trailing sensor mean. History peaks cover only the retained trailing samples (normally 60), not the entire process lifetime.

| Arm | Active post-health RAM used GiB | Trailing history mean GiB | Trailing observed peak GiB | Minimum retained samples/batch |
|---|---:|---:|---:|---:|
| S8-C1 | 11.99 | 11.99 | 12.02 | 60.00 |
| S8-C2 | 16.94 | 16.97 | 17.05 | 60.00 |
| S8-C3 | 17.47 | 17.43 | 17.49 | 60.00 |
| S8-M1 | 12.04 | 12.03 | 12.06 | 60.00 |
| S8-M2 | 12.03 | 12.02 | 12.07 | 60.00 |

Whole-host CPU utilization below averages each batch's full process lifetime, including loading; vmstat's since-boot first sample is excluded. These are not per-agent or decode-only CPU rates.

| Arm | User % | System % | Idle % | I/O wait % |
|---|---:|---:|---:|---:|
| S8-C1 | 32.1 | 5.2 | 62.6 | 0.1 |
| S8-C2 | 21.6 | 6.5 | 70.6 | 1.3 |
| S8-C3 | 23.4 | 6.7 | 68.5 | 1.3 |
| S8-M1 | 24.6 | 5.2 | 70.1 | 0.1 |
| S8-M2 | 24.3 | 5.0 | 70.6 | 0.1 |

Ranges and all individual batches are in [summary.csv](summary.csv), [summary.json](summary.json), and each arm's report/receipts. Raw CPU utilization, disk I/O, GPU samples and post-health evidence are preserved. A mechanical C2 PASS is not semantic quality validation or permission to promote.
