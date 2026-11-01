#!/usr/bin/env python3
"""
scripts/98-export-consolidated-benchmarks.py

Generates consolidated benchmark reports across ALL stages (Stages 2, 3, 4, 5, 6, 7):
  - docs/consolidated-benchmarks.csv
  - docs/CONSOLIDATED_BENCHMARKS.md

Extracts performance metrics (Prefill, TTFT, Decode, C2 status) and
hardware telemetry (GPU0/1 Avg & Peak Temp, Avg & Peak Power) verified against
authoritative repository artifact summaries and raw JSON/telemetry receipts.
"""

import os
import sys
import csv
import json
import glob
import statistics
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

CSV_OUT = DOCS_DIR / "consolidated-benchmarks.csv"
MD_OUT = DOCS_DIR / "CONSOLIDATED_BENCHMARKS.md"

def collect_records():
    records = []

    # -------------------------------------------------------------
    # Stage 2 (Strata 0.1.31)
    # -------------------------------------------------------------
    records.append({
        "stage": "Stage 2",
        "arm_id": "S2-IQ2XS",
        "run_id": "EXP-V100-Q38-STRATA-IQ2XS-2GPU2-C2-PERF-20261001-001",
        "run_type": "baseline",
        "engine": "Strata 0.1.31",
        "quant": "IQ2_XS",
        "config": "Cold dual-independent baseline",
        "c2_verdict": "PASS",
        "prefill_a": 700.5, "prefill_b": 714.0, "prefill_mean": 707.25,
        "ttft_a": 181.76, "ttft_b": 178.35, "ttft_mean": 180.05,
        "decode_a": 21.2, "decode_b": 22.5, "decode_mean": 21.85,
        "out_tokens_a": 1024, "out_tokens_b": 1024,
        "wall_s": 247.93,
        "gpu0_t_avg": None, "gpu0_t_peak": None, "gpu0_p_avg": None, "gpu0_p_peak": None,
        "gpu1_t_avg": None, "gpu1_t_peak": None, "gpu1_p_avg": None, "gpu1_p_peak": None,
        "notes": "Original dual-V100 IQ2_XS reference"
    })
    records.append({
        "stage": "Stage 2",
        "arm_id": "S2-Q4",
        "run_id": "c2-q4-v100-contract-20261002-164957",
        "run_type": "feasibility",
        "engine": "Strata 0.1.31",
        "quant": "UD-Q4_K_XL",
        "config": "High-bit feasibility check",
        "c2_verdict": "PASS (Impractical)",
        "prefill_a": 149.4, "prefill_b": 149.4, "prefill_mean": 149.40,
        "ttft_a": 850.71, "ttft_b": 851.15, "ttft_mean": 850.93,
        "decode_a": 3.1, "decode_b": 3.3, "decode_mean": 3.20,
        "out_tokens_a": 1024, "out_tokens_b": 1024,
        "wall_s": 1471.43,
        "gpu0_t_avg": None, "gpu0_t_peak": None, "gpu0_p_avg": None, "gpu0_p_peak": None,
        "gpu1_t_avg": None, "gpu1_t_peak": None, "gpu1_p_avg": None, "gpu1_p_peak": None,
        "notes": "Passed mechanically; impractically slow at 128K"
    })
    records.append({
        "stage": "Stage 2",
        "arm_id": "S2-IQ3XXS",
        "run_id": "c2-jmn-iq3xxs-v100-contract-20261004-163227",
        "run_type": "baseline",
        "engine": "Strata 0.1.31",
        "quant": "IQ3_XXS",
        "config": "Dual-independent baseline",
        "c2_verdict": "PASS",
        "prefill_a": 623.05, "prefill_b": 623.05, "prefill_mean": 623.05,
        "ttft_a": None, "ttft_b": None, "ttft_mean": None,
        "decode_a": 11.45, "decode_b": 11.45, "decode_mean": 11.45,
        "out_tokens_a": 1024, "out_tokens_b": 1024,
        "wall_s": None,
        "gpu0_t_avg": None, "gpu0_t_peak": None, "gpu0_p_avg": None, "gpu0_p_peak": None,
        "gpu1_t_avg": None, "gpu1_t_peak": None, "gpu1_p_avg": None, "gpu1_p_peak": None,
        "notes": "First IQ3_XXS dual-agent test"
    })
    records.append({
        "stage": "Stage 2",
        "arm_id": "S2-IQ3S",
        "run_id": "c2-jmn-iq3s-v100-contract-20261004-164626",
        "run_type": "baseline",
        "engine": "Strata 0.1.31",
        "quant": "IQ3_S",
        "config": "Dual-independent baseline",
        "c2_verdict": "PASS",
        "prefill_a": 602.40, "prefill_b": 602.40, "prefill_mean": 602.40,
        "ttft_a": None, "ttft_b": None, "ttft_mean": None,
        "decode_a": 10.75, "decode_b": 10.75, "decode_mean": 10.75,
        "out_tokens_a": 1024, "out_tokens_b": 1024,
        "wall_s": None,
        "gpu0_t_avg": None, "gpu0_t_peak": None, "gpu0_p_avg": None, "gpu0_p_peak": None,
        "gpu1_t_avg": None, "gpu1_t_peak": None, "gpu1_p_avg": None, "gpu1_p_peak": None,
        "notes": "First IQ3_S dual-agent test"
    })

    # -------------------------------------------------------------
    # Stage 3-A & Stage 3-B (Strata 0.1.36 jmnargi fork)
    # -------------------------------------------------------------
    records.append({
        "stage": "Stage 3-A",
        "arm_id": "S3A-IQ2XS",
        "run_id": "c2-jmn-iq2xs-v100-contract-20261004-162142",
        "run_type": "baseline",
        "engine": "Strata 0.1.36 (jmnargi fork 9d77749)",
        "quant": "IQ2_XS",
        "config": "spec 4, min-p 0.5",
        "c2_verdict": "PASS",
        "prefill_a": 900.1, "prefill_b": 919.7, "prefill_mean": 909.90,
        "ttft_a": 141.56, "ttft_b": 138.61, "ttft_mean": 140.09,
        "decode_a": 21.7, "decode_b": 22.7, "decode_mean": 22.20,
        "out_tokens_a": 1664, "out_tokens_b": 1066,
        "wall_s": 218.04,
        "gpu0_t_avg": None, "gpu0_t_peak": None, "gpu0_p_avg": None, "gpu0_p_peak": None,
        "gpu1_t_avg": None, "gpu1_t_peak": None, "gpu1_p_avg": None, "gpu1_p_peak": None,
        "notes": "Preserved operational reference pair"
    })
    records.append({
        "stage": "Stage 3-A",
        "arm_id": "S3A-IQ3XXS",
        "run_id": "c2-jmn3b-iq3xxs-v100-contract-20261004-173816",
        "run_type": "baseline",
        "engine": "Strata 0.1.36 (jmnargi fork 9d77749)",
        "quant": "IQ3_XXS",
        "config": "spec 4, min-p 0.5",
        "c2_verdict": "PASS",
        "prefill_a": 790.95, "prefill_b": 790.95, "prefill_mean": 790.95,
        "ttft_a": 161.08, "ttft_b": 161.08, "ttft_mean": 161.08,
        "decode_a": 12.70, "decode_b": 12.70, "decode_mean": 12.70,
        "out_tokens_a": 1024, "out_tokens_b": 1024,
        "wall_s": None,
        "gpu0_t_avg": None, "gpu0_t_peak": None, "gpu0_p_avg": None, "gpu0_p_peak": None,
        "gpu1_t_avg": None, "gpu1_t_peak": None, "gpu1_p_avg": None, "gpu1_p_peak": None,
        "notes": "Fork prefill +26.9% vs Stage 2"
    })
    records.append({
        "stage": "Stage 3-A",
        "arm_id": "S3A-IQ3S",
        "run_id": "c2-jmn3b-iq3s-v100-contract-20261004-175414",
        "run_type": "baseline",
        "engine": "Strata 0.1.36 (jmnargi fork 9d77749)",
        "quant": "IQ3_S",
        "config": "spec 4, min-p 0.5",
        "c2_verdict": "PASS",
        "prefill_a": 721.30, "prefill_b": 721.30, "prefill_mean": 721.30,
        "ttft_a": 176.62, "ttft_b": 176.62, "ttft_mean": 176.62,
        "decode_a": 10.65, "decode_b": 10.65, "decode_mean": 10.65,
        "out_tokens_a": 1024, "out_tokens_b": 1024,
        "wall_s": None,
        "gpu0_t_avg": None, "gpu0_t_peak": None, "gpu0_p_avg": None, "gpu0_p_peak": None,
        "gpu1_t_avg": None, "gpu1_t_peak": None, "gpu1_p_avg": None, "gpu1_p_peak": None,
        "notes": "Fork prefill +19.7% vs Stage 2"
    })
    records.append({
        "stage": "Stage 3-B",
        "arm_id": "S3B-IQ2XS",
        "run_id": "c2-s3b-iq2xs",
        "run_type": "tuning",
        "engine": "Strata 0.1.36 (jmnargi fork 9d77749)",
        "quant": "IQ2_XS",
        "config": "spec 8, min-p 0.7, EXPERT_PAIR=1",
        "c2_verdict": "PASS",
        "prefill_a": 925.45, "prefill_b": 925.45, "prefill_mean": 925.45,
        "ttft_a": 137.73, "ttft_b": 137.73, "ttft_mean": 137.73,
        "decode_a": 23.90, "decode_b": 23.90, "decode_mean": 23.90,
        "out_tokens_a": 1024, "out_tokens_b": 1024,
        "wall_s": None,
        "gpu0_t_avg": None, "gpu0_t_peak": None, "gpu0_p_avg": None, "gpu0_p_peak": None,
        "gpu1_t_avg": None, "gpu1_t_peak": None, "gpu1_p_avg": None, "gpu1_p_peak": None,
        "notes": "Tuning bundle test"
    })

    # -------------------------------------------------------------
    # Stage 4-A, 4-B, 4-C
    # -------------------------------------------------------------
    records.append({
        "stage": "Stage 4-A",
        "arm_id": "S4A-IQ2XS",
        "run_id": "c2-stage4a-v100-contract-20261021-215736-runB",
        "run_type": "baseline",
        "engine": "Strata 0.1.44.1",
        "quant": "IQ2_XS",
        "config": "Vanilla 0.1.44.1",
        "c2_verdict": "PASS",
        "prefill_a": 930.3, "prefill_b": 948.5, "prefill_mean": 939.40,
        "ttft_a": 136.72, "ttft_b": 134.09, "ttft_mean": 135.41,
        "decode_a": 29.9, "decode_b": 33.4, "decode_mean": 31.65,
        "out_tokens_a": 1747, "out_tokens_b": 2056,
        "wall_s": 195.06,
        "gpu0_t_avg": None, "gpu0_t_peak": None, "gpu0_p_avg": None, "gpu0_p_peak": None,
        "gpu1_t_avg": None, "gpu1_t_peak": None, "gpu1_p_avg": None, "gpu1_p_peak": None,
        "notes": "Decode +42.6% over Stage 3-A"
    })
    records.append({
        "stage": "Stage 4-B",
        "arm_id": "S4B-IQ2XS",
        "run_id": "c2-stage4b-v100-contract-20261021-222010-runB",
        "run_type": "baseline",
        "engine": "Strata 0.1.47",
        "quant": "IQ2_XS",
        "config": "Vanilla 0.1.47",
        "c2_verdict": "PASS",
        "prefill_a": 977.4, "prefill_b": 985.7, "prefill_mean": 981.55,
        "ttft_a": 130.15, "ttft_b": 129.02, "ttft_mean": 129.58,
        "decode_a": 38.1, "decode_b": 38.9, "decode_mean": 38.50,
        "out_tokens_a": 2470, "out_tokens_b": 2490,
        "wall_s": 193.75,
        "gpu0_t_avg": None, "gpu0_t_peak": None, "gpu0_p_avg": None, "gpu0_p_peak": None,
        "gpu1_t_avg": None, "gpu1_t_peak": None, "gpu1_p_avg": None, "gpu1_p_peak": None,
        "notes": "Upstream 0.1.47 throughput reference"
    })
    records.append({
        "stage": "Stage 4-B",
        "arm_id": "S4B-IQ3XXS",
        "run_id": "c2-stage4b-iq3xxs-v100-contract-20261021-233533-runB",
        "run_type": "baseline",
        "engine": "Strata 0.1.47",
        "quant": "IQ3_XXS",
        "config": "Vanilla 0.1.47",
        "c2_verdict": "PASS",
        "prefill_a": 738.0, "prefill_b": 744.1, "prefill_mean": 741.05,
        "ttft_a": 172.30, "ttft_b": 170.90, "ttft_mean": 171.60,
        "decode_a": 19.1, "decode_b": 19.5, "decode_mean": 19.30,
        "out_tokens_a": 1221, "out_tokens_b": 1410,
        "wall_s": 243.60,
        "gpu0_t_avg": None, "gpu0_t_peak": None, "gpu0_p_avg": None, "gpu0_p_peak": None,
        "gpu1_t_avg": None, "gpu1_t_peak": None, "gpu1_p_avg": None, "gpu1_p_peak": None,
        "notes": "Vanilla 0.1.47 IQ3_XXS"
    })
    records.append({
        "stage": "Stage 4-B",
        "arm_id": "S4B-IQ3S",
        "run_id": "c2-stage4b-iq3s-v100-contract-20261021-235127-runB",
        "run_type": "baseline",
        "engine": "Strata 0.1.47",
        "quant": "IQ3_S",
        "config": "Vanilla 0.1.47",
        "c2_verdict": "PASS",
        "prefill_a": 533.2, "prefill_b": 536.8, "prefill_mean": 535.00,
        "ttft_a": 238.40, "ttft_b": 237.08, "ttft_mean": 237.74,
        "decode_a": 17.5, "decode_b": 19.0, "decode_mean": 18.25,
        "out_tokens_a": 1085, "out_tokens_b": 1495,
        "wall_s": 316.02,
        "gpu0_t_avg": None, "gpu0_t_peak": None, "gpu0_p_avg": None, "gpu0_p_peak": None,
        "gpu1_t_avg": None, "gpu1_t_peak": None, "gpu1_p_avg": None, "gpu1_p_peak": None,
        "notes": "Vanilla 0.1.47 IQ3_S (pre-NVMe1 cleanup)"
    })
    records.append({
        "stage": "Stage 4-B",
        "arm_id": "S4B-Mixed",
        "run_id": "c2-stage4b-mixed-v100-contract-20261022-144236-runB",
        "run_type": "mixed_quant",
        "engine": "Strata 0.1.47",
        "quant": "Mixed (A:IQ3_XXS / B:IQ2_XS)",
        "config": "Vanilla 0.1.47 asymmetric",
        "c2_verdict": "FAIL (Active overlap 0.0s)",
        "prefill_a": 138.8, "prefill_b": 593.9, "prefill_mean": 366.35,
        "ttft_a": 914.90, "ttft_b": 214.04, "ttft_mean": 564.47,
        "decode_a": 7.9, "decode_b": 22.6, "decode_mean": 15.25,
        "out_tokens_a": 1289, "out_tokens_b": 2036,
        "wall_s": 1077.62,
        "gpu0_t_avg": None, "gpu0_t_peak": None, "gpu0_p_avg": None, "gpu0_p_peak": None,
        "gpu1_t_avg": None, "gpu1_t_peak": None, "gpu1_p_avg": None, "gpu1_p_peak": None,
        "notes": "Thrashing: 18,690 faults, 1.6GB swap, decode overlap 0s (FAIL)"
    })
    records.append({
        "stage": "Stage 4-C",
        "arm_id": "S4C-IQ2XS",
        "run_id": "c2-stage4c-v100-contract-20261021-222823-runB",
        "run_type": "tuning",
        "engine": "Strata 0.1.47",
        "quant": "IQ2_XS",
        "config": "spec 8, min-p 0.7, EXPERT_PAIR=1",
        "c2_verdict": "PASS",
        "prefill_a": 992.1, "prefill_b": 999.3, "prefill_mean": 995.70,
        "ttft_a": 128.21, "ttft_b": 127.27, "ttft_mean": 127.74,
        "decode_a": 39.3, "decode_b": 39.9, "decode_mean": 39.60,
        "out_tokens_a": 2645, "out_tokens_b": 2645,
        "wall_s": 194.50,
        "gpu0_t_avg": None, "gpu0_t_peak": None, "gpu0_p_avg": None, "gpu0_p_peak": None,
        "gpu1_t_avg": None, "gpu1_t_peak": None, "gpu1_p_avg": None, "gpu1_p_peak": None,
        "notes": "Peak repository throughput (39.6 tok/s decode)"
    })

    # -------------------------------------------------------------
    # Stage 5 (IQ3_S & IQ3_XXS)
    # Verified against artifacts/stage5-results-20261027/stage5-t7-jmnargi-summary.md
    # and artifacts/stage5-results-20261029/stage5-iq3xxs-matrix-summary.md
    # -------------------------------------------------------------
    stage5_telems = {
        ("IQ3_S", "T1"): {"t0": 62.1, "t0_pk": 70.0, "p0": 98.7, "p0_pk": 223.6, "t1": 54.4, "t1_pk": 61.0, "p1": 92.7, "p1_pk": 205.7},
        ("IQ3_S", "T2"): {"t0": 62.5, "t0_pk": 69.0, "p0": 97.8, "p0_pk": 211.8, "t1": 54.3, "t1_pk": 61.0, "p1": 91.1, "p1_pk": 192.6},
        ("IQ3_S", "T3"): {"t0": 61.8, "t0_pk": 68.0, "p0": 95.4, "p0_pk": 225.9, "t1": 53.9, "t1_pk": 60.0, "p1": 87.0, "p1_pk": 209.1},
        ("IQ3_S", "T4"): {"t0": 61.2, "t0_pk": 67.0, "p0": 93.4, "p0_pk": 217.2, "t1": 52.7, "t1_pk": 59.0, "p1": 86.2, "p1_pk": 189.1},
        ("IQ3_S", "T6"): {"t0": 59.7, "t0_pk": 69.0, "p0": 91.1, "p0_pk": 217.8, "t1": 52.1, "t1_pk": 61.0, "p1": 84.2, "p1_pk": 201.8},
        ("IQ3_S", "T7-Fixed"): {"t0": 59.4, "t0_pk": 66.0, "p0": 89.3, "p0_pk": 210.8, "t1": 51.8, "t1_pk": 58.0, "p1": 84.2, "p1_pk": 190.2},
        ("IQ3_S", "T8"): {"t0": 60.4, "t0_pk": 66.0, "p0": 91.4, "p0_pk": 211.6, "t1": 52.2, "t1_pk": 58.0, "p1": 83.2, "p1_pk": 204.1},
        ("IQ3_XXS", "T1"): {"t0": 58.3, "t0_pk": 69.0, "p0": 94.3, "p0_pk": 227.0, "t1": 54.7, "t1_pk": 64.0, "p1": 98.3, "p1_pk": 209.5},
        ("IQ3_XXS", "T2"): {"t0": 61.2, "t0_pk": 70.0, "p0": 102.2, "p0_pk": 197.8, "t1": 57.9, "t1_pk": 65.0, "p1": 100.3, "p1_pk": 213.5},
        ("IQ3_XXS", "T3"): {"t0": 56.7, "t0_pk": 66.0, "p0": 87.5, "p0_pk": 202.7, "t1": 55.5, "t1_pk": 62.0, "p1": 93.5, "p1_pk": 201.2},
        ("IQ3_XXS", "T4"): {"t0": 57.7, "t0_pk": 64.0, "p0": 88.2, "p0_pk": 174.1, "t1": 55.4, "t1_pk": 61.0, "p1": 89.4, "p1_pk": 181.1},
        ("IQ3_XXS", "T6"): {"t0": 60.1, "t0_pk": 68.0, "p0": 97.4, "p0_pk": 199.6, "t1": 57.2, "t1_pk": 64.0, "p1": 100.8, "p1_pk": 197.5},
        ("IQ3_XXS", "T7-Fixed"): {"t0": 57.7, "t0_pk": 67.0, "p0": 87.3, "p0_pk": 205.0, "t1": 53.0, "t1_pk": 61.0, "p1": 86.3, "p1_pk": 192.5},
        ("IQ3_XXS", "T8"): {"t0": 56.9, "t0_pk": 63.0, "p0": 90.0, "p0_pk": 169.8, "t1": 56.8, "t1_pk": 67.0, "p1": 90.9, "p1_pk": 176.8},
    }

    s5_iq3s_arms = [
        ("T1", "Strata 0.1.47", "upstream baseline", 741.80, 747.30, 744.55, 172.54, 169.66, 171.10, 21.07, 21.83, 21.45, 254.48),
        ("T2", "Strata 0.1.47", "SELECT_SIMT=1", 875.50, 882.50, 879.00, 145.20, 144.42, 144.81, 20.20, 20.40, 20.30, 204.60),
        ("T3", "Strata 0.1.47", "PF_WMMA=1", 794.97, 802.37, 798.67, 160.10, 158.50, 159.30, 18.20, 18.34, 18.27, 233.50),
        ("T4", "Strata 0.1.47", "SIMT=1 + PF_WMMA=1", 883.63, 891.10, 887.37, 143.80, 142.92, 143.36, 21.10, 21.30, 21.20, 228.92),
        ("T6-Fixed", "Strata 0.1.50", "STAGER_SSD=0", 747.30, 756.23, 751.77, 170.20, 168.68, 169.44, 17.70, 17.90, 17.80, 233.98),
        ("T7-Fixed", "Strata 0.1.45.3 (jmnargi fork 2c9b1dd)", "SM70_PERF=0, SIMT=1, WMMA=1, WMMA2=1, SSD=0", 889.93, 908.53, 899.23, 142.71, 140.57, 141.64, 21.40, 21.50, 21.45, 212.18),
        ("T8", "Strata 0.1.50", "SIMT=1, WMMA=1, SSD=0", 871.47, 880.53, 876.00, 145.90, 144.54, 145.22, 20.60, 20.86, 20.73, 210.02),
    ]
    for arm, eng, cfg, pfa, pfb, pfm, tta, ttb, ttm, deca, decb, decm, wall in s5_iq3s_arms:
        telem = stage5_telems.get(("IQ3_S", arm), {})
        records.append({
            "stage": "Stage 5",
            "arm_id": f"S5-IQ3S-{arm}",
            "run_id": f"s5-iq3s-{arm.lower()}-mean",
            "run_type": "3-run mean",
            "engine": eng,
            "quant": "IQ3_S",
            "config": cfg,
            "c2_verdict": "PASS",
            "prefill_a": pfa, "prefill_b": pfb, "prefill_mean": pfm,
            "ttft_a": tta, "ttft_b": ttb, "ttft_mean": ttm,
            "decode_a": deca, "decode_b": decb, "decode_mean": decm,
            "out_tokens_a": 1024, "out_tokens_b": 1024,
            "wall_s": wall,
            "gpu0_t_avg": telem.get("t0"), "gpu0_t_peak": telem.get("t0_pk"),
            "gpu0_p_avg": telem.get("p0"), "gpu0_p_peak": telem.get("p0_pk"),
            "gpu1_t_avg": telem.get("t1"), "gpu1_t_peak": telem.get("t1_pk"),
            "gpu1_p_avg": telem.get("p1"), "gpu1_p_peak": telem.get("p1_pk"),
            "notes": "Stage 5 IQ3_S 3-run mean"
        })

    s5_iq3xxs_medians = [
        ("T1", "Strata 0.1.47", "upstream baseline", 889.6, 902.7, 896.15, 142.99, 140.93, 141.96, 27.1, 25.7, 26.40, 235.02),
        ("T2", "Strata 0.1.47", "SELECT_SIMT=1", 1010.4, 1019.2, 1014.80, 125.91, 124.86, 125.39, 25.9, 26.7, 26.30, 203.41),
        ("T3", "Strata 0.1.47", "PF_WMMA=1", 890.3, 894.1, 892.20, 142.86, 142.27, 142.57, 25.3, 25.8, 25.55, 228.36),
        ("T4", "Strata 0.1.47", "SIMT=1 + PF_WMMA=1", 992.8, 1000.6, 996.70, 128.12, 127.16, 127.64, 26.5, 26.2, 26.35, 198.33),
        ("T6-Fixed", "Strata 0.1.50", "STAGER_SSD=0", 887.3, 896.7, 892.00, 143.36, 141.86, 142.61, 26.4, 25.6, 26.00, 216.46),
        ("T7-Fixed", "Strata 0.1.45.3 (jmnargi fork 2c9b1dd)", "SM70_PERF=0, SIMT=1, WMMA=1, WMMA2=1, SSD=0", 1030.7, 1044.9, 1037.80, 123.46, 121.78, 122.62, 26.6, 26.7, 26.65, 214.49),
        ("T8", "Strata 0.1.50", "SIMT=1, WMMA=1, SSD=0", 990.5, 996.8, 993.65, 128.45, 127.64, 128.05, 26.7, 26.0, 26.35, 199.44),
    ]
    for arm, eng, cfg, pfa, pfb, pfm, tta, ttb, ttm, deca, decb, decm, wall in s5_iq3xxs_medians:
        telem = stage5_telems.get(("IQ3_XXS", arm), {})
        records.append({
            "stage": "Stage 5",
            "arm_id": f"S5-IQ3XXS-{arm}",
            "run_id": f"s5-iq3xxs-{arm.lower()}-median",
            "run_type": "median (3 batches)",
            "engine": eng,
            "quant": "IQ3_XXS",
            "config": cfg,
            "c2_verdict": "PASS",
            "prefill_a": pfa, "prefill_b": pfb, "prefill_mean": pfm,
            "ttft_a": tta, "ttft_b": ttb, "ttft_mean": ttm,
            "decode_a": deca, "decode_b": decb, "decode_mean": decm,
            "out_tokens_a": 1024, "out_tokens_b": 1024,
            "wall_s": wall,
            "gpu0_t_avg": telem.get("t0"), "gpu0_t_peak": telem.get("t0_pk"),
            "gpu0_p_avg": telem.get("p0"), "gpu0_p_peak": telem.get("p0_pk"),
            "gpu1_t_avg": telem.get("t1"), "gpu1_t_peak": telem.get("t1_pk"),
            "gpu1_p_avg": telem.get("p1"), "gpu1_p_peak": telem.get("p1_pk"),
            "notes": "Stage 5 IQ3_XXS 3-batch median"
        })

    # -------------------------------------------------------------
    # Stage 6 (Strata 0.1.45.3 jmnargi fork, IQ3_S)
    # Verified against docs/STAGE6_FINAL_REPORT.md
    # -------------------------------------------------------------
    records.append({
        "stage": "Stage 6",
        "arm_id": "S6-0",
        "run_id": "s6-baseline-median",
        "run_type": "median (3 batches)",
        "engine": "Strata 0.1.45.3 (jmnargi fork 2c9b1dd)",
        "quant": "IQ3_S",
        "config": "T7-Fixed baseline replication",
        "c2_verdict": "PASS",
        "prefill_a": 908.2, "prefill_b": 923.1, "prefill_mean": 915.65,
        "ttft_a": 140.09, "ttft_b": 137.84, "ttft_mean": 138.97,
        "decode_a": 22.3, "decode_b": 21.2, "decode_mean": 21.75,
        "out_tokens_a": 1400, "out_tokens_b": 1400,
        "wall_s": 204.0,
        "gpu0_t_avg": None, "gpu0_t_peak": None, "gpu0_p_avg": None, "gpu0_p_peak": None,
        "gpu1_t_avg": None, "gpu1_t_peak": None, "gpu1_p_avg": None, "gpu1_p_peak": None,
        "notes": "Stage 6 verified baseline median"
    })
    s6_screens = [
        ("S6-1", "profile", "Profile (TIMING=1, VERIFY=1)", "PASS (Diag)", 923.6, 936.4, 930.0, 137.75, 135.93, 136.84, 20.5, 21.0, 20.75, 1607, 1221),
        ("S6-2", "spec4-p07", "MTP spec 4, min-p 0.7", "FAIL (B<1024)", 933.5, 942.6, 938.05, 136.29, 134.99, 135.64, 20.7, 22.6, 21.65, 1581, 979),
        ("S6-2", "spec6-p05", "MTP spec 6, min-p 0.5", "PASS", 930.7, 940.5, 935.6, 136.70, 135.36, 136.03, 18.6, 18.8, 18.70, 1597, 1962),
        ("S6-2", "spec6-p07", "MTP spec 6, min-p 0.7", "PASS", 915.0, 923.7, 919.35, 139.04, 137.75, 138.40, 21.4, 21.3, 21.35, 1979, 1703),
        ("S6-2", "spec8-p05", "MTP spec 8, min-p 0.5", "PASS", 907.4, 920.4, 913.9, 140.21, 138.26, 139.24, 18.7, 19.6, 19.15, 1424, 1077),
        ("S6-2", "spec8-p07", "MTP spec 8, min-p 0.7", "PASS", 930.9, 941.3, 936.1, 136.69, 135.17, 135.93, 20.5, 21.7, 21.10, 1796, 1376),
        ("S6-3", "side-mixer", "SIDE_MIXER=2", "PASS", 934.1, 943.9, 939.0, 136.20, 134.80, 135.50, 22.8, 21.4, 22.10, 1332, 1261),
        ("S6-3", "gu-swiglu", "GU_SWIGLU=1", "PASS", 893.7, 912.7, 903.2, 142.37, 139.40, 140.89, 22.3, 21.4, 21.85, 1332, 1495),
        ("S6-3", "gr-up75", "GR_UP75=1", "PASS", 933.0, 942.5, 937.75, 136.37, 134.99, 135.68, 22.7, 21.4, 22.05, 1332, 1503),
        ("S6-3", "attn-daily", "ATTN_DAILY=1", "PASS", 919.4, 934.3, 926.85, 138.40, 136.17, 137.29, 22.1, 21.3, 21.70, 1485, 1489),
        ("S6-3", "gr-norm", "GR_NORM_FAST=1", "PASS", 929.5, 943.1, 936.3, 136.86, 134.93, 135.90, 21.7, 21.0, 21.35, 1315, 1646),
        ("S6-3", "argmax", "ARGMAX_ROWS_SM70=1", "PASS", 899.2, 912.3, 905.75, 141.54, 139.48, 140.51, 21.8, 21.3, 21.55, 1315, 1706),
        ("S6-4", "sm70-table", "SM70_TABLE=1", "PASS", 931.7, 941.6, 936.65, 136.54, 135.15, 135.85, 21.2, 21.3, 21.25, 1408, 1410),
        ("S6-4", "expdec", "EXPDEC=1", "PASS", 931.0, 941.2, 936.1, 136.66, 135.18, 135.92, 22.4, 21.4, 21.90, 1371, 1495),
        ("S6-4", "adapt-overlap", "ADAPT_OVERLAP=1", "PASS", 933.3, 941.6, 937.45, 136.32, 135.13, 135.73, 18.7, 18.6, 18.65, 1756, 1553),
        ("S6-5", "pool-3", "pool-workers 3", "PASS", 892.2, 906.6, 899.4, 142.60, 140.36, 141.48, 21.7, 21.0, 21.35, 1332, 1489),
        ("S6-5", "pcie-065", "pcie-frac 0.65", "PASS", 928.9, 939.9, 934.4, 136.96, 135.38, 136.17, 22.2, 21.4, 21.80, 1358, 1495),
        ("S6-6", "kv-24576", "KV resident 24576", "FAIL (B<1024)", 935.0, 943.9, 939.45, 136.07, 134.80, 135.44, 21.5, 21.6, 21.55, 1564, 937),
    ]
    for arm, rid, cfg, vrd, pfa, pfb, pfm, tta, ttb, ttm, deca, decb, decm, outa, outb in s6_screens:
        records.append({
            "stage": "Stage 6",
            "arm_id": f"{arm}-{rid}",
            "run_id": f"c2-stage6-{rid}",
            "run_type": "single_batch_screen",
            "engine": "Strata 0.1.45.3 (jmnargi fork 2c9b1dd)",
            "quant": "IQ3_S",
            "config": cfg,
            "c2_verdict": vrd,
            "prefill_a": pfa, "prefill_b": pfb, "prefill_mean": pfm,
            "ttft_a": tta, "ttft_b": ttb, "ttft_mean": ttm,
            "decode_a": deca, "decode_b": decb, "decode_mean": decm,
            "out_tokens_a": outa, "out_tokens_b": outb,
            "wall_s": None,
            "gpu0_t_avg": None, "gpu0_t_peak": None, "gpu0_p_avg": None, "gpu0_p_peak": None,
            "gpu1_t_avg": None, "gpu1_t_peak": None, "gpu1_p_avg": None, "gpu1_p_peak": None,
            "notes": "Candidate screening"
        })

    # -------------------------------------------------------------
    # Stage 7 (Strata 0.1.54, IQ3_XXS)
    # Verified against artifacts/stage7-results-20261101/iq3xxs-progress.md,
    # stage7-iq3xxs-final-report.md, and raw summary.json receipts
    # -------------------------------------------------------------
    s7_telems = {
        ("S7-XXS-1", "median"): {"t0": 58.6, "t0_pk": 69.0, "p0": 87.4, "p0_pk": 194.3, "t1": 57.9, "t1_pk": 66.0, "p1": 91.8, "p1_pk": 199.3},
        ("S7-XXS-2", "median"): {"t0": 59.8, "t0_pk": 69.0, "p0": 90.5, "p0_pk": 177.2, "t1": 58.3, "t1_pk": 66.0, "p1": 92.8, "p1_pk": 182.5},
        ("S7-XXS-3", "median"): {"t0": 59.1, "t0_pk": 67.0, "p0": 87.9, "p0_pk": 194.0, "t1": 57.8, "t1_pk": 65.0, "p1": 90.5, "p1_pk": 201.0},
        ("S7-XXS-4", "median"): {"t0": 57.9, "t0_pk": 66.0, "p0": 81.6, "p0_pk": 167.6, "t1": 56.9, "t1_pk": 63.0, "p1": 83.4, "p1_pk": 180.8},
        ("S7-XXS-5", "median"): {"t0": 60.3, "t0_pk": 70.0, "p0": 91.4, "p0_pk": 193.7, "t1": 58.7, "t1_pk": 66.0, "p1": 95.8, "p1_pk": 203.5},
        ("S7-XXS-6", "median"): {"t0": 58.0, "t0_pk": 66.0, "p0": 83.8, "p0_pk": 176.0, "t1": 57.0, "t1_pk": 63.0, "p1": 86.4, "p1_pk": 183.6},
        # Per-batch telemetries
        ("S7-XXS-1", "1"): {"t0": 57.4, "t0_pk": 68.0, "p0": 85.6, "p0_pk": 194.1, "t1": 57.2, "t1_pk": 66.0, "p1": 90.8, "p1_pk": 199.3},
        ("S7-XXS-1", "2"): {"t0": 59.2, "t0_pk": 69.0, "p0": 88.0, "p0_pk": 194.3, "t1": 58.3, "t1_pk": 66.0, "p1": 91.3, "p1_pk": 197.7},
        ("S7-XXS-1", "3"): {"t0": 59.3, "t0_pk": 69.0, "p0": 88.6, "p0_pk": 186.2, "t1": 58.3, "t1_pk": 66.0, "p1": 93.4, "p1_pk": 191.5},
        ("S7-XXS-2", "1"): {"t0": 59.1, "t0_pk": 68.0, "p0": 90.6, "p0_pk": 177.2, "t1": 57.9, "t1_pk": 65.0, "p1": 93.3, "p1_pk": 182.5},
        ("S7-XXS-2", "2"): {"t0": 59.9, "t0_pk": 68.0, "p0": 88.4, "p0_pk": 176.3, "t1": 58.3, "t1_pk": 65.0, "p1": 93.2, "p1_pk": 182.0},
        ("S7-XXS-2", "3"): {"t0": 60.4, "t0_pk": 69.0, "p0": 92.4, "p0_pk": 172.6, "t1": 58.5, "t1_pk": 66.0, "p1": 91.8, "p1_pk": 180.9},
        ("S7-XXS-3", "1"): {"t0": 59.2, "t0_pk": 67.0, "p0": 86.7, "p0_pk": 194.0, "t1": 57.8, "t1_pk": 64.0, "p1": 89.4, "p1_pk": 191.3},
        ("S7-XXS-3", "2"): {"t0": 59.2, "t0_pk": 67.0, "p0": 89.5, "p0_pk": 191.3, "t1": 58.0, "t1_pk": 65.0, "p1": 92.4, "p1_pk": 198.8},
        ("S7-XXS-3", "3"): {"t0": 58.9, "t0_pk": 67.0, "p0": 87.4, "p0_pk": 176.4, "t1": 57.7, "t1_pk": 64.0, "p1": 89.7, "p1_pk": 201.0},
        ("S7-XXS-4", "1"): {"t0": 57.6, "t0_pk": 65.0, "p0": 78.7, "p0_pk": 167.6, "t1": 56.7, "t1_pk": 63.0, "p1": 84.5, "p1_pk": 180.8},
        ("S7-XXS-4", "2"): {"t0": 58.2, "t0_pk": 66.0, "p0": 83.5, "p0_pk": 167.2, "t1": 57.1, "t1_pk": 63.0, "p1": 84.3, "p1_pk": 177.9},
        ("S7-XXS-4", "3"): {"t0": 58.0, "t0_pk": 66.0, "p0": 82.7, "p0_pk": 166.3, "t1": 57.0, "t1_pk": 63.0, "p1": 81.3, "p1_pk": 178.4},
        ("S7-XXS-5", "1"): {"t0": 60.1, "t0_pk": 70.0, "p0": 90.0, "p0_pk": 192.6, "t1": 58.7, "t1_pk": 66.0, "p1": 94.5, "p1_pk": 198.2},
        ("S7-XXS-5", "2"): {"t0": 60.4, "t0_pk": 70.0, "p0": 92.9, "p0_pk": 193.7, "t1": 58.7, "t1_pk": 66.0, "p1": 96.6, "p1_pk": 203.5},
        ("S7-XXS-5", "3"): {"t0": 60.4, "t0_pk": 70.0, "p0": 91.4, "p0_pk": 189.0, "t1": 58.8, "t1_pk": 66.0, "p1": 96.2, "p1_pk": 203.2},
        ("S7-XXS-6", "1"): {"t0": 58.1, "t0_pk": 66.0, "p0": 85.4, "p0_pk": 176.0, "t1": 56.9, "t1_pk": 63.0, "p1": 87.6, "p1_pk": 175.3},
        ("S7-XXS-6", "2"): {"t0": 58.0, "t0_pk": 66.0, "p0": 81.5, "p0_pk": 174.7, "t1": 56.9, "t1_pk": 63.0, "p1": 85.5, "p1_pk": 183.6},
        ("S7-XXS-6", "3"): {"t0": 57.9, "t0_pk": 66.0, "p0": 84.5, "p0_pk": 173.6, "t1": 57.0, "t1_pk": 63.0, "p1": 86.1, "p1_pk": 181.4},
    }

    # S7 Medians (Exact from iq3xxs-progress.md & final report)
    s7_arms = [
        ("S7-XXS-1", "Vanilla (기본)", 880.9, 884.0, 882.45, 144.40, 143.89, 144.15, 24.0, 24.4, 24.20, 251.61),
        ("S7-XXS-2", "SIMT=1", 992.6, 1000.5, 996.55, 128.17, 127.20, 127.69, 25.0, 24.6, 24.80, 212.01),
        ("S7-XXS-3", "WMMA=1", 885.5, 890.0, 887.75, 143.65, 142.93, 143.29, 24.1, 25.0, 24.55, 229.69),
        ("S7-XXS-4", "SIMT=1, WMMA=1", 988.1, 994.4, 991.25, 128.76, 127.93, 128.35, 24.6, 24.4, 24.50, 215.46),
        ("S7-XXS-5", "STRATA_STAGER_SSD=0", 885.4, 892.0, 888.70, 143.66, 142.63, 143.15, 24.1, 24.6, 24.35, 238.47),
        ("S7-XXS-6", "SIMT=1, WMMA=1, SSD=0", 989.7, 995.6, 992.65, 128.56, 127.79, 128.18, 24.8, 24.5, 24.65, 213.57),
    ]

    for arm, cfg, pfa, pfb, pfm, tta, ttb, ttm, deca, decb, decm, wall in s7_arms:
        telem = s7_telems.get((arm, "median"), {})
        records.append({
            "stage": "Stage 7",
            "arm_id": arm,
            "run_id": f"{arm.lower()}-median",
            "run_type": "median (3 batches)",
            "engine": "Strata 0.1.54",
            "quant": "IQ3_XXS",
            "config": cfg,
            "c2_verdict": "PASS",
            "prefill_a": pfa, "prefill_b": pfb, "prefill_mean": pfm,
            "ttft_a": tta, "ttft_b": ttb, "ttft_mean": ttm,
            "decode_a": deca, "decode_b": decb, "decode_mean": decm,
            "out_tokens_a": 1024, "out_tokens_b": 1024,
            "wall_s": wall,
            "gpu0_t_avg": telem.get("t0"), "gpu0_t_peak": telem.get("t0_pk"),
            "gpu0_p_avg": telem.get("p0"), "gpu0_p_peak": telem.get("p0_pk"),
            "gpu1_t_avg": telem.get("t1"), "gpu1_t_peak": telem.get("t1_pk"),
            "gpu1_p_avg": telem.get("p1"), "gpu1_p_peak": telem.get("p1_pk"),
            "notes": "Stage 7 0.1.54 IQ3_XXS verified median"
        })

    # Individual 18 runs of Stage 7 (Exact from summary.json)
    s7_batch_runs = [
        ("S7-XXS-1", "1", 847.9, 853.6, 850.75, 150.02, 149.02, 149.52, 23.9, 24.8, 24.35, 1818, 2645, 255.46),
        ("S7-XXS-1", "2", 880.9, 884.0, 882.45, 144.40, 143.89, 144.15, 24.1, 24.4, 24.25, 1818, 2645, 250.70),
        ("S7-XXS-1", "3", 883.6, 891.5, 887.55, 143.97, 142.68, 143.33, 24.0, 24.1, 24.05, 1818, 2645, 251.61),
        ("S7-XXS-2", "1", 992.6, 996.9, 994.75, 128.18, 127.63, 127.91, 24.9, 24.6, 24.75, 1818, 2645, 212.01),
        ("S7-XXS-2", "2", 994.3, 1001.2, 997.75, 127.97, 127.10, 127.54, 25.0, 24.7, 24.85, 1818, 2645, 211.65),
        ("S7-XXS-2", "3", 992.6, 1000.5, 996.55, 128.17, 127.20, 127.69, 25.6, 24.6, 25.10, 1818, 2645, 212.26),
        ("S7-XXS-3", "1", 882.4, 888.7, 885.55, 144.16, 143.15, 143.66, 24.2, 24.8, 24.50, 1818, 2645, 229.69),
        ("S7-XXS-3", "2", 885.5, 891.5, 888.50, 143.65, 142.69, 143.17, 23.7, 25.5, 24.60, 1818, 2645, 221.03),
        ("S7-XXS-3", "3", 885.6, 890.0, 887.80, 143.61, 142.93, 143.27, 24.1, 25.0, 24.55, 1818, 2645, 233.69),
        ("S7-XXS-4", "1", 988.1, 994.4, 991.25, 128.76, 127.93, 128.35, 24.5, 24.1, 24.30, 1818, 2645, 216.50),
        ("S7-XXS-4", "2", 992.0, 996.3, 994.15, 128.25, 127.70, 127.98, 24.8, 24.4, 24.60, 1818, 2645, 209.30),
        ("S7-XXS-4", "3", 987.7, 993.5, 990.60, 128.78, 128.09, 128.44, 24.6, 24.6, 24.60, 1818, 2645, 215.46),
        ("S7-XXS-5", "1", 885.4, 892.0, 888.70, 143.66, 142.63, 143.15, 24.2, 25.0, 24.60, 1818, 2645, 242.83),
        ("S7-XXS-5", "2", 885.2, 891.4, 888.30, 143.67, 142.70, 143.19, 23.8, 23.9, 23.85, 1818, 2645, 238.47),
        ("S7-XXS-5", "3", 886.7, 892.0, 889.35, 143.44, 142.59, 143.02, 24.1, 24.6, 24.35, 1818, 2645, 236.19),
        ("S7-XXS-6", "1", 986.9, 994.3, 990.60, 128.90, 127.98, 128.44, 24.9, 24.5, 24.70, 1818, 2645, 208.45),
        ("S7-XXS-6", "2", 989.7, 998.0, 993.85, 128.56, 127.49, 128.03, 24.3, 24.2, 24.25, 1818, 2645, 218.88),
        ("S7-XXS-6", "3", 990.6, 995.6, 993.10, 128.43, 127.79, 128.11, 24.8, 24.6, 24.70, 1818, 2645, 213.57),
    ]
    for arm, bidx, pfa, pfb, pfm, tta, ttb, ttm, deca, decb, decm, outa, outb, wall in s7_batch_runs:
        telem = s7_telems.get((arm, bidx), {})
        records.append({
            "stage": "Stage 7",
            "arm_id": f"{arm}-#{bidx}",
            "run_id": f"xxs-{arm.split('-')[-1]}-{bidx}",
            "run_type": "batch",
            "engine": "Strata 0.1.54",
            "quant": "IQ3_XXS",
            "config": f"{arm} run {bidx}",
            "c2_verdict": "PASS",
            "prefill_a": pfa, "prefill_b": pfb, "prefill_mean": pfm,
            "ttft_a": tta, "ttft_b": ttb, "ttft_mean": ttm,
            "decode_a": deca, "decode_b": decb, "decode_mean": decm,
            "out_tokens_a": outa, "out_tokens_b": outb,
            "wall_s": wall,
            "gpu0_t_avg": telem.get("t0"), "gpu0_t_peak": telem.get("t0_pk"),
            "gpu0_p_avg": telem.get("p0"), "gpu0_p_peak": telem.get("p0_pk"),
            "gpu1_t_avg": telem.get("t1"), "gpu1_t_peak": telem.get("t1_pk"),
            "gpu1_p_avg": telem.get("p1"), "gpu1_p_peak": telem.get("p1_pk"),
            "notes": f"Batch run {bidx}"
        })

    # -------------------------------------------------------------
    # Stage 7 Optimization Arms (Strata 0.1.54, IQ3_XXS S7-XXS-8..12 + DIAG-1)
    # Verified against artifacts/stage7-results-20261101/stage7-iq3xxs-opt-report.md
    # and results/stage7-iq3xxs-opt/<id>/ raw receipts
    # -------------------------------------------------------------
    s7_opt_dir = REPO_ROOT / "results" / "stage7-iq3xxs-opt"
    s7_opt_arm_meta = {
        "XXS-8": ("S7-XXS-8", "STRATA_SELECT_SIMT=2", "Prefill QSA SIMT2"),
        "XXS-9": ("S7-XXS-9", "STRATA_GDN_REC_WARP=2", "Prefill GDN recurrence warp 2"),
        "XXS-10": ("S7-XXS-10", "STRATA_Q8_GATHER_WIDE=0", "Decode INT8-KV gather non-wide"),
        "XXS-11": ("S7-XXS-11", "STRATA_SM70_TABLE=1", "Decode V100 expert/GEMV/HC lookup tables"),
        "XXS-12": ("S7-XXS-12", "STRATA_SELECT_SIMT=1 + prefill 4096", "Prefill chunk 4096 (stopped early, n=2)"),
        "XXS-13": ("S7-XXS-13", "STRATA_SELECT_SIMT=1 + STRATA_SM70_TABLE=1", "Optimal confirmed combination (SIMT=1 + SM70_TABLE=1)"),
        "XXS-DIAG": ("S7-XXS-DIAG-1", "SIMT=1, TIMING/PROFILE (Diagnostic)", "Non-scored diagnostic profiling"),
    }

    if s7_opt_dir.exists():
        opt_groups = {}
        for d in sorted(s7_opt_dir.glob("xxs-*")):
            prefix = d.name.rsplit("-", 1)[0].upper()
            opt_groups.setdefault(prefix, []).append(d)

        for prefix in ["XXS-8", "XXS-9", "XXS-10", "XXS-11", "XXS-12", "XXS-13", "XXS-DIAG"]:
            if prefix not in opt_groups:
                continue
            bdirs = opt_groups[prefix]
            arm_id, cfg, notes = s7_opt_arm_meta[prefix]

            batch_rows = []
            for d in bdirs:
                bidx = d.name.rsplit("-", 1)[1]
                with open(d / "c2" / "summary.json") as f:
                    s = json.load(f)
                reqs = {r["label"]: r for r in s["requests"]}
                v = (d / "verdict").read_text().strip() if (d / "verdict").exists() else "PASS"

                t_data = {"0": {"p": [], "t": []}, "1": {"p": [], "t": []}}
                telem_p = d / "gpu-telemetry.csv"
                if telem_p.exists():
                    with open(telem_p) as f:
                        reader = csv.reader(f)
                        for row in reader:
                            if len(row) == 8:
                                g = row[1].strip()
                                if g in t_data:
                                    try:
                                        pwr = float(row[3].split()[0])
                                        temp = int(row[2])
                                        if pwr > 60:
                                            t_data[g]["p"].append(pwr)
                                            t_data[g]["t"].append(temp)
                                    except ValueError:
                                        pass
                def stats_fn(arr):
                    return (round(sum(arr)/len(arr), 1), max(arr)) if arr else (None, None)
                g0_p_avg, g0_p_pk = stats_fn(t_data["0"]["p"])
                g0_t_avg, g0_t_pk = stats_fn(t_data["0"]["t"])
                g1_p_avg, g1_p_pk = stats_fn(t_data["1"]["p"])
                g1_t_avg, g1_t_pk = stats_fn(t_data["1"]["t"])

                pfa = reqs["A"]["prefill_tok_s"]
                pfb = reqs["B"]["prefill_tok_s"]
                tta = round(reqs["A"]["ttft_s"], 2)
                ttb = round(reqs["B"]["ttft_s"], 2)
                deca = reqs["A"]["decode_tok_s"]
                decb = reqs["B"]["decode_tok_s"]
                outa = reqs["A"]["output_tokens"]
                outb = reqs["B"]["output_tokens"]
                wall = round(s["batch_wall_s"], 2)

                batch_rows.append({
                    "stage": "Stage 7",
                    "arm_id": f"{arm_id}-#{bidx}",
                    "run_id": d.name,
                    "run_type": "batch" if prefix != "XXS-DIAG" else "diagnostic",
                    "engine": "Strata 0.1.54",
                    "quant": "IQ3_XXS",
                    "config": f"{arm_id} run {bidx}",
                    "c2_verdict": v,
                    "prefill_a": pfa, "prefill_b": pfb, "prefill_mean": round((pfa+pfb)/2, 2),
                    "ttft_a": tta, "ttft_b": ttb, "ttft_mean": round((tta+ttb)/2, 2),
                    "decode_a": deca, "decode_b": decb, "decode_mean": round((deca+decb)/2, 2),
                    "out_tokens_a": outa, "out_tokens_b": outb,
                    "wall_s": wall,
                    "gpu0_t_avg": g0_t_avg, "gpu0_t_peak": g0_t_pk,
                    "gpu0_p_avg": g0_p_avg, "gpu0_p_peak": g0_p_pk,
                    "gpu1_t_avg": g1_t_avg, "gpu1_t_peak": g1_t_pk,
                    "gpu1_p_avg": g1_p_avg, "gpu1_p_peak": g1_p_pk,
                    "notes": f"Batch run {bidx}" if prefix != "XXS-DIAG" else "Non-scored diagnostic profiling run"
                })

            if prefix != "XXS-DIAG":
                n_batches = len(batch_rows)
                run_type_label = f"median ({n_batches} batches)" if n_batches == 3 else f"mean ({n_batches} batches, stopped early)"
                med_pfa = statistics.median([r["prefill_a"] for r in batch_rows])
                med_pfb = statistics.median([r["prefill_b"] for r in batch_rows])
                med_tta = statistics.median([r["ttft_a"] for r in batch_rows])
                med_ttb = statistics.median([r["ttft_b"] for r in batch_rows])
                med_deca = statistics.median([r["decode_a"] for r in batch_rows])
                med_decb = statistics.median([r["decode_b"] for r in batch_rows])
                med_wall = statistics.median([r["wall_s"] for r in batch_rows])

                avg_g0_t = round(sum(r["gpu0_t_avg"] for r in batch_rows)/n_batches, 1)
                pk_g0_t = max(r["gpu0_t_peak"] for r in batch_rows)
                avg_g0_p = round(sum(r["gpu0_p_avg"] for r in batch_rows)/n_batches, 1)
                pk_g0_p = max(r["gpu0_p_peak"] for r in batch_rows)

                avg_g1_t = round(sum(r["gpu1_t_avg"] for r in batch_rows)/n_batches, 1)
                pk_g1_t = max(r["gpu1_t_peak"] for r in batch_rows)
                avg_g1_p = round(sum(r["gpu1_p_avg"] for r in batch_rows)/n_batches, 1)
                pk_g1_p = max(r["gpu1_p_peak"] for r in batch_rows)

                records.append({
                    "stage": "Stage 7",
                    "arm_id": arm_id,
                    "run_id": f"{arm_id.lower()}-median",
                    "run_type": run_type_label,
                    "engine": "Strata 0.1.54",
                    "quant": "IQ3_XXS",
                    "config": cfg,
                    "c2_verdict": "PASS",
                    "prefill_a": med_pfa, "prefill_b": med_pfb, "prefill_mean": round((med_pfa+med_pfb)/2, 2),
                    "ttft_a": med_tta, "ttft_b": med_ttb, "ttft_mean": round((med_tta+med_ttb)/2, 2),
                    "decode_a": med_deca, "decode_b": med_decb, "decode_mean": round((med_deca+med_decb)/2, 2),
                    "out_tokens_a": 1024, "out_tokens_b": 1024,
                    "wall_s": med_wall,
                    "gpu0_t_avg": avg_g0_t, "gpu0_t_peak": pk_g0_t,
                    "gpu0_p_avg": avg_g0_p, "gpu0_p_peak": pk_g0_p,
                    "gpu1_t_avg": avg_g1_t, "gpu1_t_peak": pk_g1_t,
                    "gpu1_p_avg": avg_g1_p, "gpu1_p_peak": pk_g1_p,
                    "notes": f"Stage 7 0.1.54 IQ3_XXS verified {run_type_label}"
                })
            records.extend(batch_rows)

    records.extend(collect_stage7_port_records())
    return records


def collect_stage7_port_records():
    """Closed 14..16 arms from committed receipts; no local raw-log dependency."""
    artifact_dir = REPO_ROOT / "artifacts" / "stage7-results-20261101"
    receipt = json.loads((artifact_dir / "stage7-iq3xxs-14-16-receipts.json").read_text())
    telemetry = json.loads((artifact_dir / "stage7-iq3xxs-14-16-telemetry.json").read_text())["runs"]
    configs = {
        14: ("Strata 0.1.54", "SIMT=1 + SM70_TABLE=1 + PF_WMMA=1"),
        15: ("Strata 0.1.54 + WMMA2 port", "SIMT=1 + SM70_TABLE=1 + PF_WMMA=1 + PF_WMMA2=1"),
        16: ("Strata 0.1.54 + WMMA2/LEAN port", "SIMT=1 + SM70_TABLE=1 + PF_WMMA=1 + PF_WMMA2=1 + PF_WMMA_LEAN=1"),
    }
    assert receipt["scored_count"] == 9
    records = []
    for arm, (engine, config) in configs.items():
        batches = sorted((r for r in receipt["records"] if r["arm"] == arm), key=lambda r: r["id"])
        assert [r["id"] for r in batches] == [f"xxs-{arm}-{n}" for n in (1, 2, 3)]
        batch_rows = []
        for batch in batches:
            summary = batch["c2"]
            assert summary["pass_mechanical"] and summary["active_overlap"] and summary["post_health"]
            a, b = summary["requests"]
            assert [a["prompt_tokens"], b["prompt_tokens"]] == [126967, 126968]
            assert all(r["output_tokens"] >= 1024 and r["cache_n"] == r["cached_tokens"] == 0 and r["finish_reason"] == "stop" for r in (a, b))
            row = {
                "stage": "Stage 7", "arm_id": f"S7-XXS-{arm}-#{batch['id'].rsplit('-', 1)[1]}",
                "run_id": batch["id"], "run_type": "batch", "engine": engine,
                "quant": "IQ3_XXS", "config": config, "c2_verdict": "PASS",
                "out_tokens_a": a["output_tokens"], "out_tokens_b": b["output_tokens"],
                "wall_s": round(summary["batch_wall_s"], 2),
            }
            for key, source_key in (("prefill", "prefill_tok_s"), ("ttft", "ttft_s"), ("decode", "decode_tok_s")):
                row[f"{key}_a"] = round(a[source_key], 2)
                row[f"{key}_b"] = round(b[source_key], 2)
                row[f"{key}_mean"] = round((a[source_key] + b[source_key]) / 2, 2)
            for gpu in (0, 1):
                t = telemetry[batch["id"]][str(gpu)]
                row.update({f"gpu{gpu}_t_avg": t["temp_mean_c"], f"gpu{gpu}_t_peak": t["temp_peak_c"],
                            f"gpu{gpu}_p_avg": t["power_mean_w"], f"gpu{gpu}_p_peak": t["power_peak_w"]})
            cache = "/".join(str(batch["details"][s]["expert_page_cache_percent"]) for s in "ab")
            vm = batch["host_vmstat_delta"]
            row["notes"] = (f"Closed scored batch; expert page cache A/B {cache}%; host major faults {vm['pgmajfault']}; "
                            f"swap in/out pages {vm['pswpin']}/{vm['pswpout']}; image {batch['image_id']}; no causal speedup claim")
            batch_rows.append(row)
        aggregate = dict(batch_rows[0])
        aggregate.update(arm_id=f"S7-XXS-{arm}", run_id=f"s7-xxs-{arm}-median", run_type="median (3 batches)")
        for key in ("prefill", "ttft", "decode"):
            for suffix in ("a", "b"):
                aggregate[f"{key}_{suffix}"] = statistics.median(row[f"{key}_{suffix}"] for row in batch_rows)
            aggregate[f"{key}_mean"] = round((aggregate[f"{key}_a"] + aggregate[f"{key}_b"]) / 2, 2)
        for key in ("out_tokens_a", "out_tokens_b", "wall_s"):
            aggregate[key] = statistics.median(row[key] for row in batch_rows)
        for gpu in (0, 1):
            for metric in ("t", "p"):
                aggregate[f"gpu{gpu}_{metric}_avg"] = round(statistics.mean(row[f"gpu{gpu}_{metric}_avg"] for row in batch_rows), 1)
                aggregate[f"gpu{gpu}_{metric}_peak"] = max(row[f"gpu{gpu}_{metric}_peak"] for row in batch_rows)
        aggregate["notes"] = (f"3/3 C2 PASS; closed; measured output-token medians; image {batches[0]['image_id']}; "
                              "cache/swap/output/MTP differences prevent causal throughput claims; no quality suite or promotion")
        records.extend([aggregate, *batch_rows])
    return records

def export_csv(records, path):
    fieldnames = [
        "stage", "arm_id", "run_id", "run_type", "engine", "quant", "config", "c2_verdict",
        "prefill_a", "prefill_b", "prefill_mean",
        "ttft_a", "ttft_b", "ttft_mean",
        "decode_a", "decode_b", "decode_mean",
        "out_tokens_a", "out_tokens_b", "wall_s",
        "gpu0_t_avg", "gpu0_t_peak", "gpu0_p_avg", "gpu0_p_peak",
        "gpu1_t_avg", "gpu1_t_peak", "gpu1_p_avg", "gpu1_p_peak",
        "notes"
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow(r)

def fmt(val, precision=1, suffix=""):
    if val is None or val == "":
        return "-"
    if isinstance(val, (int, float)):
        return f"{val:.{precision}f}{suffix}" if precision > 0 else f"{int(val)}{suffix}"
    return str(val)

def export_markdown(records, path):
    lines = []
    lines.append("# Consolidated Dual-V100 128K C2 Benchmark Database")
    lines.append("")
    lines.append("This document aggregates all formal benchmark evaluations, candidate screenings, and hardware telemetry records across **Stages 2 through 7** on the Lenovo ThinkStation P520 (dual Tesla V100 SXM2 16GB, 150W power cap, dual independent 131,072-context agents).")
    lines.append("")
    lines.append("- **Repository master CSV dataset:** [`docs/consolidated-benchmarks.csv`](consolidated-benchmarks.csv)")
    lines.append("- **Frozen C2 Workload Manifest:** `e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca`")
    lines.append("- **Hardware Baseline:** Dual independent agents (GPU 0 / cpuset `0-2,6-8` vs GPU 1 / cpuset `3-5,9-11`), INT8 KV, frozen prompts (~126,967 tokens each), minimum output 1024 tokens.")
    lines.append("- **S7-XXS-14..16:** 9/9 scored C2 PASS, three batches each; all IDs closed. [Report](../artifacts/stage7-results-20261101/stage7-iq3xxs-14-16-report.md), [source/build audit](../artifacts/stage7-results-20261101/stage7-iq3xxs-port-source-audit.md). Arms 15/16 use separate 0.1.54-derived port images. Diagnostics are excluded from their scored rows; cache/swap variation prevents causal speedup claims.")
    lines.append("- **Telemetry convention:** S7-XXS-8..16 temperature/power rows use 1-second samples with power >60 W across the process lifetime, including loading. Arm averages are unweighted means of batch averages; peaks are maxima. These are not isolated decode/prefill power measurements. S7-XXS-14..16 aggregate output counts are measured medians; older 1024 summary entries may denote only the contract minimum. A/B mean columns are descriptive averages, not summed throughput.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Executive Summary Across Stages (Key Baselines & Medians)")
    lines.append("")
    lines.append("Comparing representative operational baselines, optimization peaks, and version milestones across the project history:")
    lines.append("")
    lines.append("| Stage | Engine | Quantization | Arm / Optimization | C2 Status | Prefill tok/s (A/B) | TTFT s (A/B) | Decode tok/s (A/B) | GPU0 온도 (평균 / 피크) | GPU0 전력 (평균 / 피크) | GPU1 온도 (평균 / 피크) | GPU1 전력 (평균 / 피크) |")
    lines.append("| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

    summary_arms = [
        "S2-IQ2XS", "S2-Q4", "S2-IQ3S",
        "S3A-IQ2XS", "S3A-IQ3S",
        "S4A-IQ2XS", "S4B-IQ2XS", "S4B-IQ3XXS", "S4B-IQ3S", "S4B-Mixed", "S4C-IQ2XS",
        "S5-IQ3S-T1", "S5-IQ3S-T4", "S5-IQ3S-T7-Fixed",
        "S5-IQ3XXS-T1", "S5-IQ3XXS-T2", "S5-IQ3XXS-T7-Fixed",
        "S6-0",
        "S7-XXS-1", "S7-XXS-2", "S7-XXS-4",
        "S7-XXS-8", "S7-XXS-9", "S7-XXS-10", "S7-XXS-11", "S7-XXS-12", "S7-XXS-13",
        "S7-XXS-14", "S7-XXS-15", "S7-XXS-16"
    ]
    
    rec_by_arm = {r["arm_id"]: r for r in records if r["run_type"] in ("baseline", "median (3 batches)", "3-run mean", "mixed_quant", "tuning", "feasibility", "mean (2 batches, stopped early)")}
    for aid in summary_arms:
        r = rec_by_arm.get(aid)
        if not r: continue
        pfa_b = f"{fmt(r['prefill_a'])} / {fmt(r['prefill_b'])}"
        tta_b = f"{fmt(r['ttft_a'])} / {fmt(r['ttft_b'])}"
        deca_b = f"**{fmt(r['decode_a'])} / {fmt(r['decode_b'])}**"
        
        g0_t = f"{fmt(r['gpu0_t_avg'], 1)} / {fmt(r['gpu0_t_peak'], 0)} °C" if r['gpu0_t_avg'] is not None else "-"
        g0_p = f"{fmt(r['gpu0_p_avg'], 1)} / {fmt(r['gpu0_p_peak'], 1)} W" if r['gpu0_p_avg'] is not None else "-"
        g1_t = f"{fmt(r['gpu1_t_avg'], 1)} / {fmt(r['gpu1_t_peak'], 0)} °C" if r['gpu1_t_avg'] is not None else "-"
        g1_p = f"{fmt(r['gpu1_p_avg'], 1)} / {fmt(r['gpu1_p_peak'], 1)} W" if r['gpu1_p_avg'] is not None else "-"
        
        lines.append(f"| **{r['stage']}** | {r['engine']} | {r['quant']} | {r['config']} | {r['c2_verdict']} | {pfa_b} | {tta_b} | {deca_b} | {g0_t} | {g0_p} | {g1_t} | {g1_p} |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. Hardware Telemetry Comparison (Stages 5 & 7)")
    lines.append("")
    lines.append("Continuous 1-second sampled hardware metrics captured via `nvidia-smi` during full 128K C2 evaluations (150W TDP limit):")
    lines.append("")
    lines.append("| Stage / Arm | Quant | Engine | Overrides | GPU0 Avg Temp | GPU0 Peak Temp | GPU0 Avg Pwr | GPU0 Peak Pwr | GPU1 Avg Temp | GPU1 Peak Temp | GPU1 Avg Pwr | GPU1 Peak Pwr |")
    lines.append("| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

    for r in records:
        if r["run_type"] in ("median (3 batches)", "3-run mean", "mean (2 batches, stopped early)") and r["gpu0_t_avg"] is not None:
            lines.append(
                f"| **{r['stage']}** {r['arm_id']} | {r['quant']} | {r['engine']} | {r['config']} | "
                f"{fmt(r['gpu0_t_avg'], 1, ' °C')} | {fmt(r['gpu0_t_peak'], 0, ' °C')} | {fmt(r['gpu0_p_avg'], 1, ' W')} | {fmt(r['gpu0_p_peak'], 1, ' W')} | "
                f"{fmt(r['gpu1_t_avg'], 1, ' °C')} | {fmt(r['gpu1_t_peak'], 0, ' °C')} | {fmt(r['gpu1_p_avg'], 1, ' W')} | {fmt(r['gpu1_p_peak'], 1, ' W')} |"
            )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 3. Comprehensive Master Table (All Runs and Screenings)")
    lines.append("")
    lines.append("| Stage | Run ID | Quant | Overrides / Setting | Verdict | Prefill A / B tok/s | TTFT A / B s | Decode A / B tok/s | GPU0 온도 (평균/피크) | GPU0 전력 (평균/피크) | GPU1 온도 (평균/피크) | GPU1 전력 (평균/피크) | Notes |")
    lines.append("| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |")

    for r in records:
        pfa_b = f"{fmt(r['prefill_a'])} / {fmt(r['prefill_b'])}"
        tta_b = f"{fmt(r['ttft_a'])} / {fmt(r['ttft_b'])}"
        deca_b = f"{fmt(r['decode_a'])} / {fmt(r['decode_b'])}"
        g0_t = f"{fmt(r['gpu0_t_avg'], 1)}/{fmt(r['gpu0_t_peak'], 0)}°C" if r['gpu0_t_avg'] is not None else "-"
        g0_p = f"{fmt(r['gpu0_p_avg'], 1)}/{fmt(r['gpu0_p_peak'], 1)}W" if r['gpu0_p_avg'] is not None else "-"
        g1_t = f"{fmt(r['gpu1_t_avg'], 1)}/{fmt(r['gpu1_t_peak'], 0)}°C" if r['gpu1_t_avg'] is not None else "-"
        g1_p = f"{fmt(r['gpu1_p_avg'], 1)}/{fmt(r['gpu1_p_peak'], 1)}W" if r['gpu1_p_avg'] is not None else "-"
        lines.append(f"| {r['stage']} | `{r['run_id']}` | {r['quant']} | {r['config']} | {r['c2_verdict']} | {pfa_b} | {tta_b} | {deca_b} | {g0_t} | {g0_p} | {g1_t} | {g1_p} | {r['notes']} |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 4. Key Takeaways & Architectural Insights")
    lines.append("")
    lines.append("1. **Throughput Champion:** Two independent **IQ2_XS** servers under **Strata 0.1.47 (Stage 4-C)** remain the absolute speed champions at **995.70 tok/s prefill** and **39.60 tok/s decode**.")
    lines.append("2. **Precision / IQ3_S Champion:** Stage 5 **T7-Fixed** (`jmnargi/Strata-V100@2c9b1dd` fork v0.1.45.3 + SIMT + WMMA + SSD=0) achieved **899.23 tok/s prefill** and **21.45 tok/s decode**; upstream 0.1.47 **T4** achieved **887.37 tok/s prefill** and **21.20 tok/s decode**.")
    lines.append("3. **Stage 7 Engine 0.1.54 on IQ3_XXS:**")
    lines.append("   - Vanilla 0.1.54 achieved **882.45 tok/s prefill median (880.9 / 884.0)** and **24.20 tok/s decode median (24.0 / 24.4)**.")
    lines.append("   - Enabling `STRATA_SELECT_SIMT=1` (S7-XXS-2) boosted prefill to **996.55 tok/s median (992.6 / 1000.5, +12.9%)** and decode to **25.0 / 24.6 tok/s**.")
    lines.append("   - Earlier WMMA arms showed no established throughput gain (S7-XXS-3: 885.5 / 890.0 tok/s; S7-XXS-4: 988.1 / 994.4 tok/s); those timings alone do not prove dispatch. Later arm-14 diagnostic launches verified generic WMMA execution on this model pack.")
    lines.append("   - Disabling SSD stager (`STRATA_STAGER_SSD=0`, S7-XXS-5) yielded identical throughput (~885.4 / 892.0 tok/s) but increased GPU power consumption from 87W to 91W on GPU0 and 92W to 96W on GPU1.")
    lines.append("4. **Stage 7 Engine 0.1.54 IQ3_XXS Optimization Flag Screen (S7-XXS-8..12):**")
    lines.append("   - `STRATA_SM70_TABLE=1` (S7-XXS-11) was the **only consistent signal**, achieving **−1.4 to −2.0% decode time** on identical-output pairs.")
    lines.append("   - `STRATA_SELECT_SIMT=2` (S7-XXS-8) showed no prefill gain (−0.3% vs same-session SIMT=1 control).")
    lines.append("   - `STRATA_GDN_REC_WARP=2` (S7-XXS-9) prefill (+0.1–0.25%) was within noise while modifying FP32 summation order.")
    lines.append("   - `STRATA_Q8_GATHER_WIDE=0` (S7-XXS-10) showed no measurable decode effect.")
    lines.append("   - `--prefill 4096` (S7-XXS-12) regressed prefill by **−36.7%** (TTFT ~126 s → ~200 s) and was stopped after 2 batches.")
    lines.append("   - Common-mode shift: all arms showed ~1.2% higher prefill than archived S7-XXS-2, including decode-only switches, confirming cross-date confounders.")
    lines.append("5. **Physical Power & Thermal Profile:**")
    lines.append("   - Sustained decode power is low (~45–75 W) with SM clocks steady at 1110 MHz.")
    lines.append("   - Dense 128K prefill draws 120–140 W average with transient spikes up to 166–204 W, causing dynamic clock throttling down to 795–1050 MHz to stay within the 150W TDP envelope.")
    lines.append("   - Operating temperatures never exceeded 70 °C, comfortably below V100's 85 °C thermal throttle point.")
    lines.append("6. **S7-XXS-14..16 selective ports (9/9 C2 PASS, closed):**")
    lines.append("   - Arm 14: prefill **997.6 / 1006.6**, decode **26.4 / 26.2** tok/s. Arm 15 (verified IQ3_XXS WMMA2 port): **961.2 / 969.6**, **26.3 / 26.1**. Arm 16 (+LEAN): **990.8 / 998.7**, **26.4 / 27.0**. All values are per-agent 3-batch medians.")
    lines.append("   - LEAN reduced loaned cache slots **2489→2173** with chunk 8192/ring 96 unchanged. This is an observed allocation effect, not a throughput guarantee.")
    lines.append("   - First port-image batches had 95% expert-page-cache residency and substantial host swap/major faults; later runs warmed to 100%. Every valid first batch is retained. No causal WMMA2/LEAN speedup, quality result or production promotion is established.")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

if __name__ == "__main__":
    records = collect_records()
    export_csv(records, CSV_OUT)
    export_markdown(records, MD_OUT)
    print(f"Exported {len(records)} records to:")
    print(f"  - {CSV_OUT}")
    print(f"  - {MD_OUT}")
