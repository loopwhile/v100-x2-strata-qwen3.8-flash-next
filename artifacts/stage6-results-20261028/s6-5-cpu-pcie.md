# S6-5 CPU / PCIe screening — 2026-10-28

S6-1 identified substantial CPU expert work and waitCPU, while waitB was small. These separate one-batch screens retain the baseline CPU affinities. S6-0 decode medians: A/B 22.3/21.2 tok/s. Neither result establishes an improvement; no waitCPU comparison was collected for these unprofiled scored screens.

| Change | A decode | B decode | Output A/B | C2 | Result |
| --- | ---: | ---: | ---: | --- | --- |
| pool-workers 3 (runtime baseline 2) | 21.7 | 21.0 | 1332 / 1489 | PASS | No dual improvement |
| pcie-frac 0.65 (baseline auto) | 22.2 | 21.4 | 1358 / 1495 | PASS | No clear dual improvement |

Effective runtime values confirmed on both agents. Baseline auto PCIe share adjusted to around 0.55 in an observed request; fixed 0.65 disables that auto choice. Raw results and logs on P520 in `results/c2-stage6-s6-5-*`.
