#!/usr/bin/env python3
"""
scripts/98-export-consolidated-benchmarks.py

Generates consolidated benchmark reports across ALL stages (Stages 2, 3, 4, 5, 6, 7):
  - docs/consolidated-benchmarks.csv
  - docs/CONSOLIDATED_BENCHMARKS.md

Extracts performance metrics (Prefill, TTFT, Decode, C2 status) and
hardware telemetry (GPU0/1 Avg & Peak Temp, Avg & Peak Power) where recorded.
"""

import os
import sys
import csv
import json
import glob
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

CSV_OUT = DOCS_DIR / "consolidated-benchmarks.csv"
MD_OUT = DOCS_DIR / "CONSOLIDATED_BENCHMARKS.md"

def parse_telemetry(csv_path):
    if not os.path.exists(csv_path):
        return None
    data = {0: {"temp": [], "pwr": []}, 1: {"temp": [], "pwr": []}}
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            for row in csv.reader(f):
                if len(row) < 5:
                    continue
                try:
                    g = int(row[1].strip())
                    t = float(row[2].strip())
                    p = float(row[3].strip().replace(" W", ""))
                    data[g]["temp"].append(t)
                    data[g]["pwr"].append(p)
                except Exception:
                    continue
    except Exception:
        return None
    
    if not data[0]["temp"] or not data[1]["temp"]:
        return None

    return {
        "gpu0_t_avg": round(sum(data[0]["temp"]) / len(data[0]["temp"]), 1),
        "gpu0_t_peak": round(max(data[0]["temp"]), 1),
        "gpu0_p_avg": round(sum(data[0]["pwr"]) / len(data[0]["pwr"]), 1),
        "gpu0_p_peak": round(max(data[0]["pwr"]), 1),
        "gpu1_t_avg": round(sum(data[1]["temp"]) / len(data[1]["temp"]), 1),
        "gpu1_t_peak": round(max(data[1]["temp"]), 1),
        "gpu1_p_avg": round(sum(data[1]["pwr"]) / len(data[1]["pwr"]), 1),
        "gpu1_p_peak": round(max(data[1]["pwr"]), 1),
    }

def collect_records():
    records = []

    # -------------------------------------------------------------
    # Stage 2
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
        "prefill_a": 700.5, "prefill_b": 714.0, "prefill_mean": 707.3,
        "ttft_a": 181.76, "ttft_b": 178.35, "ttft_mean": 180.05,
        "decode_a": 21.2, "decode_b": 22.5, "decode_mean": 21.85,
        "out_tokens_a": 1414, "out_tokens_b": 1414,
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
        "c2_verdict": "PASS",
        "prefill_a": 149.4, "prefill_b": 149.4, "prefill_mean": 149.4,
        "ttft_a": 850.71, "ttft_b": 851.15, "ttft_mean": 850.93,
        "decode_a": 3.1, "decode_b": 3.3, "decode_mean": 3.20,
        "out_tokens_a": 1928, "out_tokens_b": 2048,
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
        "prefill_a": 620.1, "prefill_b": 626.0, "prefill_mean": 623.05,
        "ttft_a": 204.75, "ttft_b": 202.82, "ttft_mean": 203.79,
        "decode_a": 11.4, "decode_b": 11.5, "decode_mean": 11.45,
        "out_tokens_a": 1024, "out_tokens_b": 1024,
        "wall_s": 294.0,
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
        "prefill_a": 599.8, "prefill_b": 605.0, "prefill_mean": 602.40,
        "ttft_a": 211.68, "ttft_b": 209.86, "ttft_mean": 210.77,
        "decode_a": 10.7, "decode_b": 10.8, "decode_mean": 10.75,
        "out_tokens_a": 1024, "out_tokens_b": 1024,
        "wall_s": 306.0,
        "gpu0_t_avg": None, "gpu0_t_peak": None, "gpu0_p_avg": None, "gpu0_p_peak": None,
        "gpu1_t_avg": None, "gpu1_t_peak": None, "gpu1_p_avg": None, "gpu1_p_peak": None,
        "notes": "First IQ3_S dual-agent test"
    })

    # -------------------------------------------------------------
    # Stage 3-A & Stage 3-B
    # -------------------------------------------------------------
    records.append({
        "stage": "Stage 3-A",
        "arm_id": "S3A-IQ2XS",
        "run_id": "c2-jmn3b-iq2xs-v100-contract-20261004-172412",
        "run_type": "baseline",
        "engine": "Strata 0.1.36 (V100 fork)",
        "quant": "IQ2_XS",
        "config": "spec 4, min-p 0.5",
        "c2_verdict": "PASS",
        "prefill_a": 905.1, "prefill_b": 914.7, "prefill_mean": 909.90,
        "ttft_a": 140.28, "ttft_b": 138.90, "ttft_mean": 140.09,
        "decode_a": 22.1, "decode_b": 22.3, "decode_mean": 22.20,
        "out_tokens_a": 1414, "out_tokens_b": 1414,
        "wall_s": 204.0,
        "gpu0_t_avg": None, "gpu0_t_peak": None, "gpu0_p_avg": None, "gpu0_p_peak": None,
        "gpu1_t_avg": None, "gpu1_t_peak": None, "gpu1_p_avg": None, "gpu1_p_peak": None,
        "notes": "Preserved operational reference pair"
    })
    records.append({
        "stage": "Stage 3-A",
        "arm_id": "S3A-IQ3XXS",
        "run_id": "c2-jmn3b-iq3xxs-v100-contract-20261004-173816",
        "run_type": "baseline",
        "engine": "Strata 0.1.36 (V100 fork)",
        "quant": "IQ3_XXS",
        "config": "spec 4, min-p 0.5",
        "c2_verdict": "PASS",
        "prefill_a": 786.2, "prefill_b": 795.7, "prefill_mean": 790.95,
        "ttft_a": 161.50, "ttft_b": 160.66, "ttft_mean": 161.08,
        "decode_a": 12.6, "decode_b": 12.8, "decode_mean": 12.70,
        "out_tokens_a": 1024, "out_tokens_b": 1024,
        "wall_s": 242.0,
        "gpu0_t_avg": None, "gpu0_t_peak": None, "gpu0_p_avg": None, "gpu0_p_peak": None,
        "gpu1_t_avg": None, "gpu1_t_peak": None, "gpu1_p_avg": None, "gpu1_p_peak": None,
        "notes": "Fork prefill +26.9% vs Stage 2"
    })
    records.append({
        "stage": "Stage 3-A",
        "arm_id": "S3A-IQ3S",
        "run_id": "c2-jmn3b-iq3s-v100-contract-20261004-175414",
        "run_type": "baseline",
        "engine": "Strata 0.1.36 (V100 fork)",
        "quant": "IQ3_S",
        "config": "spec 4, min-p 0.5",
        "c2_verdict": "PASS",
        "prefill_a": 717.3, "prefill_b": 725.3, "prefill_mean": 721.30,
        "ttft_a": 177.01, "ttft_b": 176.23, "ttft_mean": 176.62,
        "decode_a": 10.6, "decode_b": 10.7, "decode_mean": 10.65,
        "out_tokens_a": 1024, "out_tokens_b": 1024,
        "wall_s": 272.0,
        "gpu0_t_avg": None, "gpu0_t_peak": None, "gpu0_p_avg": None, "gpu0_p_peak": None,
        "gpu1_t_avg": None, "gpu1_t_peak": None, "gpu1_p_avg": None, "gpu1_p_peak": None,
        "notes": "Fork prefill +19.7% vs Stage 2"
    })
    records.append({
        "stage": "Stage 3-B",
        "arm_id": "S3B-IQ2XS",
        "run_id": "c2-s3b-iq2xs",
        "run_type": "tuning",
        "engine": "Strata 0.1.36 (V100 fork)",
        "quant": "IQ2_XS",
        "config": "spec 8, min-p 0.7, EXPERT_PAIR=1",
        "c2_verdict": "PASS",
        "prefill_a": 920.4, "prefill_b": 930.5, "prefill_mean": 925.45,
        "ttft_a": 137.95, "ttft_b": 137.51, "ttft_mean": 137.73,
        "decode_a": 23.6, "decode_b": 24.2, "decode_mean": 23.90,
        "out_tokens_a": 1414, "out_tokens_b": 1414,
        "wall_s": 196.0,
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
        "notes": "Vanilla 0.1.47 IQ3_S"
    })
    records.append({
        "stage": "Stage 4-B",
        "arm_id": "S4B-Mixed",
        "run_id": "c2-stage4b-mixed-v100-contract-20261022-144236-runB",
        "run_type": "mixed_quant",
        "engine": "Strata 0.1.47",
        "quant": "Mixed (A:IQ3_XXS / B:IQ2_XS)",
        "config": "Vanilla 0.1.47 asymmetric",
        "c2_verdict": "PASS",
        "prefill_a": 737.5, "prefill_b": 985.0, "prefill_mean": 861.25,
        "ttft_a": 172.44, "ttft_b": 129.11, "ttft_mean": 150.78,
        "decode_a": 19.2, "decode_b": 38.6, "decode_mean": 28.90,
        "out_tokens_a": 1221, "out_tokens_b": 2490,
        "wall_s": 236.00,
        "gpu0_t_avg": None, "gpu0_t_peak": None, "gpu0_p_avg": None, "gpu0_p_peak": None,
        "gpu1_t_avg": None, "gpu1_t_peak": None, "gpu1_p_avg": None, "gpu1_p_peak": None,
        "notes": "Co-resident asymmetric quant trial"
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

    s5_iq3s_medians = [
        ("T1", "Strata 0.1.47", "upstream baseline", 536.27, 237.2, 18.33, 233.08),
        ("T2", "Strata 0.1.47", "SELECT_SIMT=1", 886.63, 143.4, 20.30, 204.60),
        ("T3", "Strata 0.1.47", "PF_WMMA=1", 535.80, 237.4, 18.27, 233.50),
        ("T4", "Strata 0.1.47", "SIMT=1 + PF_WMMA=1", 887.37, 143.3, 21.20, 228.92),
        ("T6", "Strata 0.1.50", "STAGER_SSD=0", 535.63, 237.5, 17.80, 233.98),
        ("T7-Fixed", "Strata 0.1.50-fork", "SM70_PERF=0, SIMT=1, WMMA=1, WMMA2=1, SSD=0", 899.23, 141.4, 21.45, 212.18),
        ("T8", "Strata 0.1.50", "SIMT=1, WMMA=1, SSD=0", 886.97, 143.4, 20.73, 210.02),
    ]
    for arm, eng, cfg, pf, ttft, dec, wall in s5_iq3s_medians:
        telem = stage5_telems.get(("IQ3_S", arm), {})
        records.append({
            "stage": "Stage 5",
            "arm_id": f"S5-IQ3S-{arm}",
            "run_id": f"s5-iq3s-{arm.lower()}-median",
            "run_type": "median (3 batches)",
            "engine": eng,
            "quant": "IQ3_S",
            "config": cfg,
            "c2_verdict": "PASS",
            "prefill_a": pf, "prefill_b": pf, "prefill_mean": pf,
            "ttft_a": ttft, "ttft_b": ttft, "ttft_mean": ttft,
            "decode_a": dec, "decode_b": dec, "decode_mean": dec,
            "out_tokens_a": 1024, "out_tokens_b": 1024,
            "wall_s": wall,
            "gpu0_t_avg": telem.get("t0"), "gpu0_t_peak": telem.get("t0_pk"),
            "gpu0_p_avg": telem.get("p0"), "gpu0_p_peak": telem.get("p0_pk"),
            "gpu1_t_avg": telem.get("t1"), "gpu1_t_peak": telem.get("t1_pk"),
            "gpu1_p_avg": telem.get("p1"), "gpu1_p_peak": telem.get("p1_pk"),
            "notes": "Stage 5 IQ3_S 3-batch median"
        })

    s5_iq3xxs_medians = [
        ("T1", "Strata 0.1.47", "upstream baseline", 889.6, 902.7, 896.15, 142.99, 140.93, 141.96, 27.1, 25.7, 26.40, 235.02),
        ("T2", "Strata 0.1.47", "SELECT_SIMT=1", 1010.4, 1019.2, 1014.80, 125.91, 124.86, 125.39, 25.9, 26.7, 26.30, 203.41),
        ("T3", "Strata 0.1.47", "PF_WMMA=1", 890.3, 894.1, 892.20, 142.86, 142.27, 142.57, 25.3, 25.8, 25.55, 228.36),
        ("T4", "Strata 0.1.47", "SIMT=1 + PF_WMMA=1", 992.8, 1000.6, 996.70, 128.12, 127.16, 127.64, 26.5, 26.2, 26.35, 198.33),
        ("T6", "Strata 0.1.50", "STAGER_SSD=0", 887.3, 896.7, 892.00, 143.36, 141.86, 142.61, 26.4, 25.6, 26.00, 216.46),
        ("T7-Fixed", "Strata 0.1.50-fork", "SM70_PERF=0, SIMT=1, WMMA=1, WMMA2=1, SSD=0", 1030.7, 1044.9, 1037.80, 123.46, 121.78, 122.62, 26.6, 26.7, 26.65, 214.49),
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
    # Stage 6 (IQ3_S 30 tok/s screens)
    # -------------------------------------------------------------
    records.append({
        "stage": "Stage 6",
        "arm_id": "S6-0",
        "run_id": "s6-baseline-median",
        "run_type": "median (3 batches)",
        "engine": "Strata 0.1.50-fork",
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
            "engine": "Strata 0.1.50-fork",
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
    # Stage 7 (IQ3_XXS 0.1.54)
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

    s7_arms = [
        ("S7-XXS-1", "Vanilla (기본)", 856.2, 859.3, 857.75, 148.51, 148.06, 148.29, 24.1, 24.8, 24.45, 237.47),
        ("S7-XXS-2", "SIMT=1", 978.8, 985.3, 982.05, 129.98, 129.13, 129.56, 24.1, 24.7, 24.40, 206.88),
        ("S7-XXS-3", "WMMA=1", 854.7, 858.9, 856.80, 148.79, 148.11, 148.45, 24.0, 24.8, 24.40, 237.52),
        ("S7-XXS-4", "SIMT=1, WMMA=1", 978.3, 984.7, 981.50, 130.04, 129.19, 129.62, 24.1, 24.7, 24.40, 207.01),
        ("S7-XXS-5", "STRATA_STAGER_SSD=0", 855.9, 860.2, 858.05, 148.59, 147.88, 148.24, 24.2, 24.9, 24.55, 237.19),
        ("S7-XXS-6", "SIMT=1, WMMA=1, SSD=0", 978.5, 985.0, 981.75, 130.01, 129.16, 129.59, 24.1, 24.8, 24.45, 206.95),
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
            "out_tokens_a": 1818, "out_tokens_b": 2645,
            "wall_s": wall,
            "gpu0_t_avg": telem.get("t0"), "gpu0_t_peak": telem.get("t0_pk"),
            "gpu0_p_avg": telem.get("p0"), "gpu0_p_peak": telem.get("p0_pk"),
            "gpu1_t_avg": telem.get("t1"), "gpu1_t_peak": telem.get("t1_pk"),
            "gpu1_p_avg": telem.get("p1"), "gpu1_p_peak": telem.get("p1_pk"),
            "notes": "Stage 7 0.1.54 IQ3_XXS median"
        })

    # Individual 18 runs of Stage 7
    s7_batch_runs = [
        ("S7-XXS-1", "1", 847.9, 853.6, 850.75, 150.02, 149.02, 149.52, 23.9, 24.8, 24.35, 1818, 2645, 255.46),
        ("S7-XXS-1", "2", 856.2, 859.3, 857.75, 148.51, 148.06, 148.29, 24.1, 24.9, 24.50, 1818, 2645, 237.47),
        ("S7-XXS-1", "3", 856.9, 860.1, 858.50, 148.37, 147.88, 148.13, 24.1, 24.8, 24.45, 1818, 2645, 237.44),
        ("S7-XXS-2", "1", 977.8, 984.3, 981.05, 130.12, 129.24, 129.68, 24.1, 24.7, 24.40, 1818, 2645, 206.94),
        ("S7-XXS-2", "2", 978.8, 985.3, 982.05, 129.98, 129.13, 129.56, 24.1, 24.7, 24.40, 1818, 2645, 206.88),
        ("S7-XXS-2", "3", 979.0, 985.7, 982.35, 129.95, 129.07, 129.51, 24.1, 24.7, 24.40, 1818, 2645, 206.85),
        ("S7-XXS-3", "1", 854.7, 858.9, 856.80, 148.79, 148.11, 148.45, 24.0, 24.8, 24.40, 1818, 2645, 237.52),
        ("S7-XXS-3", "2", 853.9, 858.2, 856.05, 148.94, 148.24, 148.59, 24.0, 24.8, 24.40, 1818, 2645, 237.60),
        ("S7-XXS-3", "3", 854.9, 859.1, 857.00, 148.76, 148.09, 148.43, 24.0, 24.8, 24.40, 1818, 2645, 237.48),
        ("S7-XXS-4", "1", 978.1, 984.4, 981.25, 130.08, 129.23, 129.66, 24.1, 24.7, 24.40, 1818, 2645, 207.05),
        ("S7-XXS-4", "2", 978.3, 984.7, 981.50, 130.04, 129.19, 129.62, 24.1, 24.7, 24.40, 1818, 2645, 207.01),
        ("S7-XXS-4", "3", 978.7, 985.1, 981.90, 129.99, 129.14, 129.57, 24.1, 24.7, 24.40, 1818, 2645, 206.91),
        ("S7-XXS-5", "1", 855.9, 860.2, 858.05, 148.59, 147.88, 148.24, 24.2, 24.9, 24.55, 1818, 2645, 237.19),
        ("S7-XXS-5", "2", 855.8, 860.0, 857.90, 148.60, 147.92, 148.26, 24.2, 24.9, 24.55, 1818, 2645, 237.21),
        ("S7-XXS-5", "3", 856.1, 860.3, 858.20, 148.55, 147.87, 148.21, 24.2, 24.9, 24.55, 1818, 2645, 237.18),
        ("S7-XXS-6", "1", 978.3, 984.8, 981.55, 130.05, 129.18, 129.62, 24.1, 24.8, 24.45, 1818, 2645, 207.00),
        ("S7-XXS-6", "2", 978.5, 985.0, 981.75, 130.01, 129.16, 129.59, 24.1, 24.8, 24.45, 1818, 2645, 206.95),
        ("S7-XXS-6", "3", 978.9, 985.4, 982.15, 129.97, 129.11, 129.54, 24.1, 24.8, 24.45, 1818, 2645, 206.89),
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
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Executive Summary Across Stages (Key Baselines & Medians)")
    lines.append("")
    lines.append("Comparing representative operational baselines, optimization peaks, and version milestones across the project history:")
    lines.append("")
    lines.append("| Stage | Engine | Quantization | Arm / Optimization | C2 Status | Prefill tok/s (A/B) | TTFT s (A/B) | Decode tok/s (A/B) | GPU0 온도 (평균 / 피크) | GPU0 전력 (평균 / 피크) | GPU1 온도 (평균 / 피크) | GPU1 전력 (평균 / 피크) |")
    lines.append("| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

    # Filter representative rows
    summary_arms = [
        "S2-IQ2XS", "S2-Q4", "S2-IQ3S",
        "S3A-IQ2XS", "S3A-IQ3S",
        "S4A-IQ2XS", "S4B-IQ2XS", "S4B-IQ3XXS", "S4B-IQ3S", "S4B-Mixed", "S4C-IQ2XS",
        "S5-IQ3S-T1", "S5-IQ3S-T4", "S5-IQ3S-T7-Fixed",
        "S5-IQ3XXS-T1", "S5-IQ3XXS-T2", "S5-IQ3XXS-T7-Fixed",
        "S6-0",
        "S7-XXS-1", "S7-XXS-2", "S7-XXS-4"
    ]
    
    rec_by_arm = {r["arm_id"]: r for r in records if r["run_type"] in ("baseline", "median (3 batches)", "mixed_quant", "tuning", "feasibility")}
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
        if r["run_type"] == "median (3 batches)" and r["gpu0_t_avg"] is not None:
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
    lines.append("2. **Precision / IQ3_S Champion:** Stage 5 **T7-Fixed** (`jmnargi/Strata-V100@2c9b1dd` fork + SIMT + WMMA + SSD=0) achieved **899.23 tok/s prefill** and **21.45 tok/s decode**; upstream 0.1.47 **T4** achieved **887.37 tok/s prefill** and **21.20 tok/s decode**.")
    lines.append("3. **Stage 7 Engine 0.1.54 on IQ3_XXS:**")
    lines.append("   - Vanilla 0.1.54 achieved **857.75 tok/s prefill** and **24.45 tok/s decode** (up from 19.30 tok/s in 0.1.47).")
    lines.append("   - Enabling `STRATA_SELECT_SIMT=1` boosted prefill to **982.05 tok/s (+14.5%)** while maintaining **24.40 tok/s decode**.")
    lines.append("   - WMMA flags did not alter runtime execution for IQ3_XXS.")
    lines.append("   - Disabling SSD stager (`STRATA_STAGER_SSD=0`) yielded identical throughput (~858 / 24.5 tok/s) but increased GPU power consumption from 87W to 91W on GPU0 and 91W to 96W on GPU1.")
    lines.append("4. **Physical Power & Thermal Profile:**")
    lines.append("   - Sustained decode power is low (~45–75 W) with SM clocks steady at 1110 MHz.")
    lines.append("   - Dense 128K prefill draws 120–140 W average with transient spikes up to 166–203 W, causing dynamic clock throttling down to 795–1050 MHz to stay within the 150W TDP envelope.")
    lines.append("   - Operating temperatures never exceeded 70 °C, comfortably below V100's 85 °C thermal throttle point.")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

if __name__ == "__main__":
    records = collect_records()
    export_csv(records, CSV_OUT)
    export_markdown(records, MD_OUT)
    print(f"Exported {len(records)} records to:")
    print(f"  - {CSV_OUT}")
    print(f"  - {MD_OUT}")
