# Consolidated Dual-V100 128K C2 Benchmark Database

This document aggregates all formal benchmark evaluations, candidate screenings, and hardware telemetry records across **Stages 2 through 7** on the Lenovo ThinkStation P520 (dual Tesla V100 SXM2 16GB, 150W power cap, dual independent 131,072-context agents).

- **Repository master CSV dataset:** [`docs/consolidated-benchmarks.csv`](consolidated-benchmarks.csv)
- **Frozen C2 Workload Manifest:** `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`
- **Hardware Baseline:** Dual independent agents (GPU 0 / cpuset `0-2,6-8` vs GPU 1 / cpuset `3-5,9-11`), INT8 KV, frozen prompts (~126,967 tokens each), minimum output 1024 tokens.

---

## 1. Executive Summary Across Stages (Key Baselines & Medians)

Comparing representative operational baselines, optimization peaks, and version milestones across the project history:

| Stage | Engine | Quantization | Arm / Optimization | C2 Status | Prefill tok/s (A/B) | TTFT s (A/B) | Decode tok/s (A/B) | GPU0 온도 (평균 / 피크) | GPU0 전력 (평균 / 피크) | GPU1 온도 (평균 / 피크) | GPU1 전력 (평균 / 피크) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Stage 2** | Strata 0.1.31 | IQ2_XS | Cold dual-independent baseline | PASS | 700.5 / 714.0 | 181.8 / 178.3 | **21.2 / 22.5** | - | - | - | - |
| **Stage 2** | Strata 0.1.31 | UD-Q4_K_XL | High-bit feasibility check | PASS (Impractical) | 149.4 / 149.4 | 850.7 / 851.1 | **3.1 / 3.3** | - | - | - | - |
| **Stage 2** | Strata 0.1.31 | IQ3_S | Dual-independent baseline | PASS | 602.4 / 602.4 | - / - | **10.8 / 10.8** | - | - | - | - |
| **Stage 3-A** | Strata 0.1.36 (jmnargi fork 9d77749) | IQ2_XS | spec 4, min-p 0.5 | PASS | 900.1 / 919.7 | 141.6 / 138.6 | **21.7 / 22.7** | - | - | - | - |
| **Stage 3-A** | Strata 0.1.36 (jmnargi fork 9d77749) | IQ3_S | spec 4, min-p 0.5 | PASS | 721.3 / 721.3 | 176.6 / 176.6 | **10.7 / 10.7** | - | - | - | - |
| **Stage 4-A** | Strata 0.1.44.1 | IQ2_XS | Vanilla 0.1.44.1 | PASS | 930.3 / 948.5 | 136.7 / 134.1 | **29.9 / 33.4** | - | - | - | - |
| **Stage 4-B** | Strata 0.1.47 | IQ2_XS | Vanilla 0.1.47 | PASS | 977.4 / 985.7 | 130.2 / 129.0 | **38.1 / 38.9** | - | - | - | - |
| **Stage 4-B** | Strata 0.1.47 | IQ3_XXS | Vanilla 0.1.47 | PASS | 738.0 / 744.1 | 172.3 / 170.9 | **19.1 / 19.5** | - | - | - | - |
| **Stage 4-B** | Strata 0.1.47 | IQ3_S | Vanilla 0.1.47 | PASS | 533.2 / 536.8 | 238.4 / 237.1 | **17.5 / 19.0** | - | - | - | - |
| **Stage 4-B** | Strata 0.1.47 | Mixed (A:IQ3_XXS / B:IQ2_XS) | Vanilla 0.1.47 asymmetric | FAIL (Active overlap 0.0s) | 138.8 / 593.9 | 914.9 / 214.0 | **7.9 / 22.6** | - | - | - | - |
| **Stage 4-C** | Strata 0.1.47 | IQ2_XS | spec 8, min-p 0.7, EXPERT_PAIR=1 | PASS | 992.1 / 999.3 | 128.2 / 127.3 | **39.3 / 39.9** | - | - | - | - |
| **Stage 5** | Strata 0.1.47 | IQ3_S | upstream baseline | PASS | 741.8 / 747.3 | 172.5 / 169.7 | **21.1 / 21.8** | 62.1 / 70 °C | 98.7 / 223.6 W | 54.4 / 61 °C | 92.7 / 205.7 W |
| **Stage 5** | Strata 0.1.47 | IQ3_S | SIMT=1 + PF_WMMA=1 | PASS | 883.6 / 891.1 | 143.8 / 142.9 | **21.1 / 21.3** | 61.2 / 67 °C | 93.4 / 217.2 W | 52.7 / 59 °C | 86.2 / 189.1 W |
| **Stage 5** | Strata 0.1.45.3 (jmnargi fork 2c9b1dd) | IQ3_S | SM70_PERF=0, SIMT=1, WMMA=1, WMMA2=1, SSD=0 | PASS | 889.9 / 908.5 | 142.7 / 140.6 | **21.4 / 21.5** | 59.4 / 66 °C | 89.3 / 210.8 W | 51.8 / 58 °C | 84.2 / 190.2 W |
| **Stage 5** | Strata 0.1.47 | IQ3_XXS | upstream baseline | PASS | 889.6 / 902.7 | 143.0 / 140.9 | **27.1 / 25.7** | 58.3 / 69 °C | 94.3 / 227.0 W | 54.7 / 64 °C | 98.3 / 209.5 W |
| **Stage 5** | Strata 0.1.47 | IQ3_XXS | SELECT_SIMT=1 | PASS | 1010.4 / 1019.2 | 125.9 / 124.9 | **25.9 / 26.7** | 61.2 / 70 °C | 102.2 / 197.8 W | 57.9 / 65 °C | 100.3 / 213.5 W |
| **Stage 5** | Strata 0.1.45.3 (jmnargi fork 2c9b1dd) | IQ3_XXS | SM70_PERF=0, SIMT=1, WMMA=1, WMMA2=1, SSD=0 | PASS | 1030.7 / 1044.9 | 123.5 / 121.8 | **26.6 / 26.7** | 57.7 / 67 °C | 87.3 / 205.0 W | 53.0 / 61 °C | 86.3 / 192.5 W |
| **Stage 6** | Strata 0.1.45.3 (jmnargi fork 2c9b1dd) | IQ3_S | T7-Fixed baseline replication | PASS | 908.2 / 923.1 | 140.1 / 137.8 | **22.3 / 21.2** | - | - | - | - |
| **Stage 7** | Strata 0.1.54 | IQ3_XXS | Vanilla (기본) | PASS | 880.9 / 884.0 | 144.4 / 143.9 | **24.0 / 24.4** | 58.6 / 69 °C | 87.4 / 194.3 W | 57.9 / 66 °C | 91.8 / 199.3 W |
| **Stage 7** | Strata 0.1.54 | IQ3_XXS | SIMT=1 | PASS | 992.6 / 1000.5 | 128.2 / 127.2 | **25.0 / 24.6** | 59.8 / 69 °C | 90.5 / 177.2 W | 58.3 / 66 °C | 92.8 / 182.5 W |
| **Stage 7** | Strata 0.1.54 | IQ3_XXS | SIMT=1, WMMA=1 | PASS | 988.1 / 994.4 | 128.8 / 127.9 | **24.6 / 24.4** | 57.9 / 66 °C | 81.6 / 167.6 W | 56.9 / 63 °C | 83.4 / 180.8 W |

---

## 2. Hardware Telemetry Comparison (Stages 5 & 7)

Continuous 1-second sampled hardware metrics captured via `nvidia-smi` during full 128K C2 evaluations (150W TDP limit):

| Stage / Arm | Quant | Engine | Overrides | GPU0 Avg Temp | GPU0 Peak Temp | GPU0 Avg Pwr | GPU0 Peak Pwr | GPU1 Avg Temp | GPU1 Peak Temp | GPU1 Avg Pwr | GPU1 Peak Pwr |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Stage 5** S5-IQ3S-T1 | IQ3_S | Strata 0.1.47 | upstream baseline | 62.1 °C | 70 °C | 98.7 W | 223.6 W | 54.4 °C | 61 °C | 92.7 W | 205.7 W |
| **Stage 5** S5-IQ3S-T2 | IQ3_S | Strata 0.1.47 | SELECT_SIMT=1 | 62.5 °C | 69 °C | 97.8 W | 211.8 W | 54.3 °C | 61 °C | 91.1 W | 192.6 W |
| **Stage 5** S5-IQ3S-T3 | IQ3_S | Strata 0.1.47 | PF_WMMA=1 | 61.8 °C | 68 °C | 95.4 W | 225.9 W | 53.9 °C | 60 °C | 87.0 W | 209.1 W |
| **Stage 5** S5-IQ3S-T4 | IQ3_S | Strata 0.1.47 | SIMT=1 + PF_WMMA=1 | 61.2 °C | 67 °C | 93.4 W | 217.2 W | 52.7 °C | 59 °C | 86.2 W | 189.1 W |
| **Stage 5** S5-IQ3S-T7-Fixed | IQ3_S | Strata 0.1.45.3 (jmnargi fork 2c9b1dd) | SM70_PERF=0, SIMT=1, WMMA=1, WMMA2=1, SSD=0 | 59.4 °C | 66 °C | 89.3 W | 210.8 W | 51.8 °C | 58 °C | 84.2 W | 190.2 W |
| **Stage 5** S5-IQ3S-T8 | IQ3_S | Strata 0.1.50 | SIMT=1, WMMA=1, SSD=0 | 60.4 °C | 66 °C | 91.4 W | 211.6 W | 52.2 °C | 58 °C | 83.2 W | 204.1 W |
| **Stage 5** S5-IQ3XXS-T1 | IQ3_XXS | Strata 0.1.47 | upstream baseline | 58.3 °C | 69 °C | 94.3 W | 227.0 W | 54.7 °C | 64 °C | 98.3 W | 209.5 W |
| **Stage 5** S5-IQ3XXS-T2 | IQ3_XXS | Strata 0.1.47 | SELECT_SIMT=1 | 61.2 °C | 70 °C | 102.2 W | 197.8 W | 57.9 °C | 65 °C | 100.3 W | 213.5 W |
| **Stage 5** S5-IQ3XXS-T3 | IQ3_XXS | Strata 0.1.47 | PF_WMMA=1 | 56.7 °C | 66 °C | 87.5 W | 202.7 W | 55.5 °C | 62 °C | 93.5 W | 201.2 W |
| **Stage 5** S5-IQ3XXS-T4 | IQ3_XXS | Strata 0.1.47 | SIMT=1 + PF_WMMA=1 | 57.7 °C | 64 °C | 88.2 W | 174.1 W | 55.4 °C | 61 °C | 89.4 W | 181.1 W |
| **Stage 5** S5-IQ3XXS-T7-Fixed | IQ3_XXS | Strata 0.1.45.3 (jmnargi fork 2c9b1dd) | SM70_PERF=0, SIMT=1, WMMA=1, WMMA2=1, SSD=0 | 57.7 °C | 67 °C | 87.3 W | 205.0 W | 53.0 °C | 61 °C | 86.3 W | 192.5 W |
| **Stage 5** S5-IQ3XXS-T8 | IQ3_XXS | Strata 0.1.50 | SIMT=1, WMMA=1, SSD=0 | 56.9 °C | 63 °C | 90.0 W | 169.8 W | 56.8 °C | 67 °C | 90.9 W | 176.8 W |
| **Stage 7** S7-XXS-1 | IQ3_XXS | Strata 0.1.54 | Vanilla (기본) | 58.6 °C | 69 °C | 87.4 W | 194.3 W | 57.9 °C | 66 °C | 91.8 W | 199.3 W |
| **Stage 7** S7-XXS-2 | IQ3_XXS | Strata 0.1.54 | SIMT=1 | 59.8 °C | 69 °C | 90.5 W | 177.2 W | 58.3 °C | 66 °C | 92.8 W | 182.5 W |
| **Stage 7** S7-XXS-3 | IQ3_XXS | Strata 0.1.54 | WMMA=1 | 59.1 °C | 67 °C | 87.9 W | 194.0 W | 57.8 °C | 65 °C | 90.5 W | 201.0 W |
| **Stage 7** S7-XXS-4 | IQ3_XXS | Strata 0.1.54 | SIMT=1, WMMA=1 | 57.9 °C | 66 °C | 81.6 W | 167.6 W | 56.9 °C | 63 °C | 83.4 W | 180.8 W |
| **Stage 7** S7-XXS-5 | IQ3_XXS | Strata 0.1.54 | STRATA_STAGER_SSD=0 | 60.3 °C | 70 °C | 91.4 W | 193.7 W | 58.7 °C | 66 °C | 95.8 W | 203.5 W |
| **Stage 7** S7-XXS-6 | IQ3_XXS | Strata 0.1.54 | SIMT=1, WMMA=1, SSD=0 | 58.0 °C | 66 °C | 83.8 W | 176.0 W | 57.0 °C | 63 °C | 86.4 W | 183.6 W |

---

## 3. Comprehensive Master Table (All Runs and Screenings)

| Stage | Run ID | Quant | Overrides / Setting | Verdict | Prefill A / B tok/s | TTFT A / B s | Decode A / B tok/s | GPU0 온도 (평균/피크) | GPU0 전력 (평균/피크) | GPU1 온도 (평균/피크) | GPU1 전력 (평균/피크) | Notes |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| Stage 2 | `EXP-V100-Q38-STRATA-IQ2XS-2GPU2-C2-PERF-20261001-001` | IQ2_XS | Cold dual-independent baseline | PASS | 700.5 / 714.0 | 181.8 / 178.3 | 21.2 / 22.5 | - | - | - | - | Original dual-V100 IQ2_XS reference |
| Stage 2 | `c2-q4-v100-contract-20261002-164957` | UD-Q4_K_XL | High-bit feasibility check | PASS (Impractical) | 149.4 / 149.4 | 850.7 / 851.1 | 3.1 / 3.3 | - | - | - | - | Passed mechanically; impractically slow at 128K |
| Stage 2 | `c2-jmn-iq3xxs-v100-contract-20261004-163227` | IQ3_XXS | Dual-independent baseline | PASS | 623.0 / 623.0 | - / - | 11.4 / 11.4 | - | - | - | - | First IQ3_XXS dual-agent test |
| Stage 2 | `c2-jmn-iq3s-v100-contract-20261004-164626` | IQ3_S | Dual-independent baseline | PASS | 602.4 / 602.4 | - / - | 10.8 / 10.8 | - | - | - | - | First IQ3_S dual-agent test |
| Stage 3-A | `c2-jmn-iq2xs-v100-contract-20261004-162142` | IQ2_XS | spec 4, min-p 0.5 | PASS | 900.1 / 919.7 | 141.6 / 138.6 | 21.7 / 22.7 | - | - | - | - | Preserved operational reference pair |
| Stage 3-A | `c2-jmn3b-iq3xxs-v100-contract-20261004-173816` | IQ3_XXS | spec 4, min-p 0.5 | PASS | 791.0 / 791.0 | 161.1 / 161.1 | 12.7 / 12.7 | - | - | - | - | Fork prefill +26.9% vs Stage 2 |
| Stage 3-A | `c2-jmn3b-iq3s-v100-contract-20261004-175414` | IQ3_S | spec 4, min-p 0.5 | PASS | 721.3 / 721.3 | 176.6 / 176.6 | 10.7 / 10.7 | - | - | - | - | Fork prefill +19.7% vs Stage 2 |
| Stage 3-B | `c2-s3b-iq2xs` | IQ2_XS | spec 8, min-p 0.7, EXPERT_PAIR=1 | PASS | 925.5 / 925.5 | 137.7 / 137.7 | 23.9 / 23.9 | - | - | - | - | Tuning bundle test |
| Stage 4-A | `c2-stage4a-v100-contract-20261021-215736-runB` | IQ2_XS | Vanilla 0.1.44.1 | PASS | 930.3 / 948.5 | 136.7 / 134.1 | 29.9 / 33.4 | - | - | - | - | Decode +42.6% over Stage 3-A |
| Stage 4-B | `c2-stage4b-v100-contract-20261021-222010-runB` | IQ2_XS | Vanilla 0.1.47 | PASS | 977.4 / 985.7 | 130.2 / 129.0 | 38.1 / 38.9 | - | - | - | - | Upstream 0.1.47 throughput reference |
| Stage 4-B | `c2-stage4b-iq3xxs-v100-contract-20261021-233533-runB` | IQ3_XXS | Vanilla 0.1.47 | PASS | 738.0 / 744.1 | 172.3 / 170.9 | 19.1 / 19.5 | - | - | - | - | Vanilla 0.1.47 IQ3_XXS |
| Stage 4-B | `c2-stage4b-iq3s-v100-contract-20261021-235127-runB` | IQ3_S | Vanilla 0.1.47 | PASS | 533.2 / 536.8 | 238.4 / 237.1 | 17.5 / 19.0 | - | - | - | - | Vanilla 0.1.47 IQ3_S (pre-NVMe1 cleanup) |
| Stage 4-B | `c2-stage4b-mixed-v100-contract-20261022-144236-runB` | Mixed (A:IQ3_XXS / B:IQ2_XS) | Vanilla 0.1.47 asymmetric | FAIL (Active overlap 0.0s) | 138.8 / 593.9 | 914.9 / 214.0 | 7.9 / 22.6 | - | - | - | - | Thrashing: 18,690 faults, 1.6GB swap, decode overlap 0s (FAIL) |
| Stage 4-C | `c2-stage4c-v100-contract-20261021-222823-runB` | IQ2_XS | spec 8, min-p 0.7, EXPERT_PAIR=1 | PASS | 992.1 / 999.3 | 128.2 / 127.3 | 39.3 / 39.9 | - | - | - | - | Peak repository throughput (39.6 tok/s decode) |
| Stage 5 | `s5-iq3s-t1-mean` | IQ3_S | upstream baseline | PASS | 741.8 / 747.3 | 172.5 / 169.7 | 21.1 / 21.8 | 62.1/70°C | 98.7/223.6W | 54.4/61°C | 92.7/205.7W | Stage 5 IQ3_S 3-run mean |
| Stage 5 | `s5-iq3s-t2-mean` | IQ3_S | SELECT_SIMT=1 | PASS | 875.5 / 882.5 | 145.2 / 144.4 | 20.2 / 20.4 | 62.5/69°C | 97.8/211.8W | 54.3/61°C | 91.1/192.6W | Stage 5 IQ3_S 3-run mean |
| Stage 5 | `s5-iq3s-t3-mean` | IQ3_S | PF_WMMA=1 | PASS | 795.0 / 802.4 | 160.1 / 158.5 | 18.2 / 18.3 | 61.8/68°C | 95.4/225.9W | 53.9/60°C | 87.0/209.1W | Stage 5 IQ3_S 3-run mean |
| Stage 5 | `s5-iq3s-t4-mean` | IQ3_S | SIMT=1 + PF_WMMA=1 | PASS | 883.6 / 891.1 | 143.8 / 142.9 | 21.1 / 21.3 | 61.2/67°C | 93.4/217.2W | 52.7/59°C | 86.2/189.1W | Stage 5 IQ3_S 3-run mean |
| Stage 5 | `s5-iq3s-t6-fixed-mean` | IQ3_S | STAGER_SSD=0 | PASS | 747.3 / 756.2 | 170.2 / 168.7 | 17.7 / 17.9 | - | - | - | - | Stage 5 IQ3_S 3-run mean |
| Stage 5 | `s5-iq3s-t7-fixed-mean` | IQ3_S | SM70_PERF=0, SIMT=1, WMMA=1, WMMA2=1, SSD=0 | PASS | 889.9 / 908.5 | 142.7 / 140.6 | 21.4 / 21.5 | 59.4/66°C | 89.3/210.8W | 51.8/58°C | 84.2/190.2W | Stage 5 IQ3_S 3-run mean |
| Stage 5 | `s5-iq3s-t8-mean` | IQ3_S | SIMT=1, WMMA=1, SSD=0 | PASS | 871.5 / 880.5 | 145.9 / 144.5 | 20.6 / 20.9 | 60.4/66°C | 91.4/211.6W | 52.2/58°C | 83.2/204.1W | Stage 5 IQ3_S 3-run mean |
| Stage 5 | `s5-iq3xxs-t1-median` | IQ3_XXS | upstream baseline | PASS | 889.6 / 902.7 | 143.0 / 140.9 | 27.1 / 25.7 | 58.3/69°C | 94.3/227.0W | 54.7/64°C | 98.3/209.5W | Stage 5 IQ3_XXS 3-batch median |
| Stage 5 | `s5-iq3xxs-t2-median` | IQ3_XXS | SELECT_SIMT=1 | PASS | 1010.4 / 1019.2 | 125.9 / 124.9 | 25.9 / 26.7 | 61.2/70°C | 102.2/197.8W | 57.9/65°C | 100.3/213.5W | Stage 5 IQ3_XXS 3-batch median |
| Stage 5 | `s5-iq3xxs-t3-median` | IQ3_XXS | PF_WMMA=1 | PASS | 890.3 / 894.1 | 142.9 / 142.3 | 25.3 / 25.8 | 56.7/66°C | 87.5/202.7W | 55.5/62°C | 93.5/201.2W | Stage 5 IQ3_XXS 3-batch median |
| Stage 5 | `s5-iq3xxs-t4-median` | IQ3_XXS | SIMT=1 + PF_WMMA=1 | PASS | 992.8 / 1000.6 | 128.1 / 127.2 | 26.5 / 26.2 | 57.7/64°C | 88.2/174.1W | 55.4/61°C | 89.4/181.1W | Stage 5 IQ3_XXS 3-batch median |
| Stage 5 | `s5-iq3xxs-t6-fixed-median` | IQ3_XXS | STAGER_SSD=0 | PASS | 887.3 / 896.7 | 143.4 / 141.9 | 26.4 / 25.6 | - | - | - | - | Stage 5 IQ3_XXS 3-batch median |
| Stage 5 | `s5-iq3xxs-t7-fixed-median` | IQ3_XXS | SM70_PERF=0, SIMT=1, WMMA=1, WMMA2=1, SSD=0 | PASS | 1030.7 / 1044.9 | 123.5 / 121.8 | 26.6 / 26.7 | 57.7/67°C | 87.3/205.0W | 53.0/61°C | 86.3/192.5W | Stage 5 IQ3_XXS 3-batch median |
| Stage 5 | `s5-iq3xxs-t8-median` | IQ3_XXS | SIMT=1, WMMA=1, SSD=0 | PASS | 990.5 / 996.8 | 128.4 / 127.6 | 26.7 / 26.0 | 56.9/63°C | 90.0/169.8W | 56.8/67°C | 90.9/176.8W | Stage 5 IQ3_XXS 3-batch median |
| Stage 6 | `s6-baseline-median` | IQ3_S | T7-Fixed baseline replication | PASS | 908.2 / 923.1 | 140.1 / 137.8 | 22.3 / 21.2 | - | - | - | - | Stage 6 verified baseline median |
| Stage 6 | `c2-stage6-profile` | IQ3_S | Profile (TIMING=1, VERIFY=1) | PASS (Diag) | 923.6 / 936.4 | 137.8 / 135.9 | 20.5 / 21.0 | - | - | - | - | Candidate screening |
| Stage 6 | `c2-stage6-spec4-p07` | IQ3_S | MTP spec 4, min-p 0.7 | FAIL (B<1024) | 933.5 / 942.6 | 136.3 / 135.0 | 20.7 / 22.6 | - | - | - | - | Candidate screening |
| Stage 6 | `c2-stage6-spec6-p05` | IQ3_S | MTP spec 6, min-p 0.5 | PASS | 930.7 / 940.5 | 136.7 / 135.4 | 18.6 / 18.8 | - | - | - | - | Candidate screening |
| Stage 6 | `c2-stage6-spec6-p07` | IQ3_S | MTP spec 6, min-p 0.7 | PASS | 915.0 / 923.7 | 139.0 / 137.8 | 21.4 / 21.3 | - | - | - | - | Candidate screening |
| Stage 6 | `c2-stage6-spec8-p05` | IQ3_S | MTP spec 8, min-p 0.5 | PASS | 907.4 / 920.4 | 140.2 / 138.3 | 18.7 / 19.6 | - | - | - | - | Candidate screening |
| Stage 6 | `c2-stage6-spec8-p07` | IQ3_S | MTP spec 8, min-p 0.7 | PASS | 930.9 / 941.3 | 136.7 / 135.2 | 20.5 / 21.7 | - | - | - | - | Candidate screening |
| Stage 6 | `c2-stage6-side-mixer` | IQ3_S | SIDE_MIXER=2 | PASS | 934.1 / 943.9 | 136.2 / 134.8 | 22.8 / 21.4 | - | - | - | - | Candidate screening |
| Stage 6 | `c2-stage6-gu-swiglu` | IQ3_S | GU_SWIGLU=1 | PASS | 893.7 / 912.7 | 142.4 / 139.4 | 22.3 / 21.4 | - | - | - | - | Candidate screening |
| Stage 6 | `c2-stage6-gr-up75` | IQ3_S | GR_UP75=1 | PASS | 933.0 / 942.5 | 136.4 / 135.0 | 22.7 / 21.4 | - | - | - | - | Candidate screening |
| Stage 6 | `c2-stage6-attn-daily` | IQ3_S | ATTN_DAILY=1 | PASS | 919.4 / 934.3 | 138.4 / 136.2 | 22.1 / 21.3 | - | - | - | - | Candidate screening |
| Stage 6 | `c2-stage6-gr-norm` | IQ3_S | GR_NORM_FAST=1 | PASS | 929.5 / 943.1 | 136.9 / 134.9 | 21.7 / 21.0 | - | - | - | - | Candidate screening |
| Stage 6 | `c2-stage6-argmax` | IQ3_S | ARGMAX_ROWS_SM70=1 | PASS | 899.2 / 912.3 | 141.5 / 139.5 | 21.8 / 21.3 | - | - | - | - | Candidate screening |
| Stage 6 | `c2-stage6-sm70-table` | IQ3_S | SM70_TABLE=1 | PASS | 931.7 / 941.6 | 136.5 / 135.2 | 21.2 / 21.3 | - | - | - | - | Candidate screening |
| Stage 6 | `c2-stage6-expdec` | IQ3_S | EXPDEC=1 | PASS | 931.0 / 941.2 | 136.7 / 135.2 | 22.4 / 21.4 | - | - | - | - | Candidate screening |
| Stage 6 | `c2-stage6-adapt-overlap` | IQ3_S | ADAPT_OVERLAP=1 | PASS | 933.3 / 941.6 | 136.3 / 135.1 | 18.7 / 18.6 | - | - | - | - | Candidate screening |
| Stage 6 | `c2-stage6-pool-3` | IQ3_S | pool-workers 3 | PASS | 892.2 / 906.6 | 142.6 / 140.4 | 21.7 / 21.0 | - | - | - | - | Candidate screening |
| Stage 6 | `c2-stage6-pcie-065` | IQ3_S | pcie-frac 0.65 | PASS | 928.9 / 939.9 | 137.0 / 135.4 | 22.2 / 21.4 | - | - | - | - | Candidate screening |
| Stage 6 | `c2-stage6-kv-24576` | IQ3_S | KV resident 24576 | FAIL (B<1024) | 935.0 / 943.9 | 136.1 / 134.8 | 21.5 / 21.6 | - | - | - | - | Candidate screening |
| Stage 7 | `s7-xxs-1-median` | IQ3_XXS | Vanilla (기본) | PASS | 880.9 / 884.0 | 144.4 / 143.9 | 24.0 / 24.4 | 58.6/69°C | 87.4/194.3W | 57.9/66°C | 91.8/199.3W | Stage 7 0.1.54 IQ3_XXS verified median |
| Stage 7 | `s7-xxs-2-median` | IQ3_XXS | SIMT=1 | PASS | 992.6 / 1000.5 | 128.2 / 127.2 | 25.0 / 24.6 | 59.8/69°C | 90.5/177.2W | 58.3/66°C | 92.8/182.5W | Stage 7 0.1.54 IQ3_XXS verified median |
| Stage 7 | `s7-xxs-3-median` | IQ3_XXS | WMMA=1 | PASS | 885.5 / 890.0 | 143.7 / 142.9 | 24.1 / 25.0 | 59.1/67°C | 87.9/194.0W | 57.8/65°C | 90.5/201.0W | Stage 7 0.1.54 IQ3_XXS verified median |
| Stage 7 | `s7-xxs-4-median` | IQ3_XXS | SIMT=1, WMMA=1 | PASS | 988.1 / 994.4 | 128.8 / 127.9 | 24.6 / 24.4 | 57.9/66°C | 81.6/167.6W | 56.9/63°C | 83.4/180.8W | Stage 7 0.1.54 IQ3_XXS verified median |
| Stage 7 | `s7-xxs-5-median` | IQ3_XXS | STRATA_STAGER_SSD=0 | PASS | 885.4 / 892.0 | 143.7 / 142.6 | 24.1 / 24.6 | 60.3/70°C | 91.4/193.7W | 58.7/66°C | 95.8/203.5W | Stage 7 0.1.54 IQ3_XXS verified median |
| Stage 7 | `s7-xxs-6-median` | IQ3_XXS | SIMT=1, WMMA=1, SSD=0 | PASS | 989.7 / 995.6 | 128.6 / 127.8 | 24.8 / 24.5 | 58.0/66°C | 83.8/176.0W | 57.0/63°C | 86.4/183.6W | Stage 7 0.1.54 IQ3_XXS verified median |
| Stage 7 | `xxs-1-1` | IQ3_XXS | S7-XXS-1 run 1 | PASS | 847.9 / 853.6 | 150.0 / 149.0 | 23.9 / 24.8 | 57.4/68°C | 85.6/194.1W | 57.2/66°C | 90.8/199.3W | Batch run 1 |
| Stage 7 | `xxs-1-2` | IQ3_XXS | S7-XXS-1 run 2 | PASS | 880.9 / 884.0 | 144.4 / 143.9 | 24.1 / 24.4 | 59.2/69°C | 88.0/194.3W | 58.3/66°C | 91.3/197.7W | Batch run 2 |
| Stage 7 | `xxs-1-3` | IQ3_XXS | S7-XXS-1 run 3 | PASS | 883.6 / 891.5 | 144.0 / 142.7 | 24.0 / 24.1 | 59.3/69°C | 88.6/186.2W | 58.3/66°C | 93.4/191.5W | Batch run 3 |
| Stage 7 | `xxs-2-1` | IQ3_XXS | S7-XXS-2 run 1 | PASS | 992.6 / 996.9 | 128.2 / 127.6 | 24.9 / 24.6 | 59.1/68°C | 90.6/177.2W | 57.9/65°C | 93.3/182.5W | Batch run 1 |
| Stage 7 | `xxs-2-2` | IQ3_XXS | S7-XXS-2 run 2 | PASS | 994.3 / 1001.2 | 128.0 / 127.1 | 25.0 / 24.7 | 59.9/68°C | 88.4/176.3W | 58.3/65°C | 93.2/182.0W | Batch run 2 |
| Stage 7 | `xxs-2-3` | IQ3_XXS | S7-XXS-2 run 3 | PASS | 992.6 / 1000.5 | 128.2 / 127.2 | 25.6 / 24.6 | 60.4/69°C | 92.4/172.6W | 58.5/66°C | 91.8/180.9W | Batch run 3 |
| Stage 7 | `xxs-3-1` | IQ3_XXS | S7-XXS-3 run 1 | PASS | 882.4 / 888.7 | 144.2 / 143.2 | 24.2 / 24.8 | 59.2/67°C | 86.7/194.0W | 57.8/64°C | 89.4/191.3W | Batch run 1 |
| Stage 7 | `xxs-3-2` | IQ3_XXS | S7-XXS-3 run 2 | PASS | 885.5 / 891.5 | 143.7 / 142.7 | 23.7 / 25.5 | 59.2/67°C | 89.5/191.3W | 58.0/65°C | 92.4/198.8W | Batch run 2 |
| Stage 7 | `xxs-3-3` | IQ3_XXS | S7-XXS-3 run 3 | PASS | 885.6 / 890.0 | 143.6 / 142.9 | 24.1 / 25.0 | 58.9/67°C | 87.4/176.4W | 57.7/64°C | 89.7/201.0W | Batch run 3 |
| Stage 7 | `xxs-4-1` | IQ3_XXS | S7-XXS-4 run 1 | PASS | 988.1 / 994.4 | 128.8 / 127.9 | 24.5 / 24.1 | 57.6/65°C | 78.7/167.6W | 56.7/63°C | 84.5/180.8W | Batch run 1 |
| Stage 7 | `xxs-4-2` | IQ3_XXS | S7-XXS-4 run 2 | PASS | 992.0 / 996.3 | 128.2 / 127.7 | 24.8 / 24.4 | 58.2/66°C | 83.5/167.2W | 57.1/63°C | 84.3/177.9W | Batch run 2 |
| Stage 7 | `xxs-4-3` | IQ3_XXS | S7-XXS-4 run 3 | PASS | 987.7 / 993.5 | 128.8 / 128.1 | 24.6 / 24.6 | 58.0/66°C | 82.7/166.3W | 57.0/63°C | 81.3/178.4W | Batch run 3 |
| Stage 7 | `xxs-5-1` | IQ3_XXS | S7-XXS-5 run 1 | PASS | 885.4 / 892.0 | 143.7 / 142.6 | 24.2 / 25.0 | 60.1/70°C | 90.0/192.6W | 58.7/66°C | 94.5/198.2W | Batch run 1 |
| Stage 7 | `xxs-5-2` | IQ3_XXS | S7-XXS-5 run 2 | PASS | 885.2 / 891.4 | 143.7 / 142.7 | 23.8 / 23.9 | 60.4/70°C | 92.9/193.7W | 58.7/66°C | 96.6/203.5W | Batch run 2 |
| Stage 7 | `xxs-5-3` | IQ3_XXS | S7-XXS-5 run 3 | PASS | 886.7 / 892.0 | 143.4 / 142.6 | 24.1 / 24.6 | 60.4/70°C | 91.4/189.0W | 58.8/66°C | 96.2/203.2W | Batch run 3 |
| Stage 7 | `xxs-6-1` | IQ3_XXS | S7-XXS-6 run 1 | PASS | 986.9 / 994.3 | 128.9 / 128.0 | 24.9 / 24.5 | 58.1/66°C | 85.4/176.0W | 56.9/63°C | 87.6/175.3W | Batch run 1 |
| Stage 7 | `xxs-6-2` | IQ3_XXS | S7-XXS-6 run 2 | PASS | 989.7 / 998.0 | 128.6 / 127.5 | 24.3 / 24.2 | 58.0/66°C | 81.5/174.7W | 56.9/63°C | 85.5/183.6W | Batch run 2 |
| Stage 7 | `xxs-6-3` | IQ3_XXS | S7-XXS-6 run 3 | PASS | 990.6 / 995.6 | 128.4 / 127.8 | 24.8 / 24.6 | 57.9/66°C | 84.5/173.6W | 57.0/63°C | 86.1/181.4W | Batch run 3 |

---

## 4. Key Takeaways & Architectural Insights

1. **Throughput Champion:** Two independent **IQ2_XS** servers under **Strata 0.1.47 (Stage 4-C)** remain the absolute speed champions at **995.70 tok/s prefill** and **39.60 tok/s decode**.
2. **Precision / IQ3_S Champion:** Stage 5 **T7-Fixed** (`jmnargi/Strata-V100@2c9b1dd` fork v0.1.45.3 + SIMT + WMMA + SSD=0) achieved **899.23 tok/s prefill** and **21.45 tok/s decode**; upstream 0.1.47 **T4** achieved **887.37 tok/s prefill** and **21.20 tok/s decode**.
3. **Stage 7 Engine 0.1.54 on IQ3_XXS:**
   - Vanilla 0.1.54 achieved **882.45 tok/s prefill median (880.9 / 884.0)** and **24.20 tok/s decode median (24.0 / 24.4)**.
   - Enabling `STRATA_SELECT_SIMT=1` (S7-XXS-2) boosted prefill to **996.55 tok/s median (992.6 / 1000.5, +12.9%)** and decode to **25.0 / 24.6 tok/s**.
   - WMMA flags did not alter runtime execution for IQ3_XXS (S7-XXS-3: 885.5 / 890.0 tok/s; S7-XXS-4: 988.1 / 994.4 tok/s).
   - Disabling SSD stager (`STRATA_STAGER_SSD=0`, S7-XXS-5) yielded identical throughput (~885.4 / 892.0 tok/s) but increased GPU power consumption from 87W to 91W on GPU0 and 92W to 96W on GPU1.
4. **Physical Power & Thermal Profile:**
   - Sustained decode power is low (~45–75 W) with SM clocks steady at 1110 MHz.
   - Dense 128K prefill draws 120–140 W average with transient spikes up to 166–204 W, causing dynamic clock throttling down to 795–1050 MHz to stay within the 150W TDP envelope.
   - Operating temperatures never exceeded 70 °C, comfortably below V100's 85 °C thermal throttle point.
