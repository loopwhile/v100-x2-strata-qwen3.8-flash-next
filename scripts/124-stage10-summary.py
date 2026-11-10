#!/usr/bin/env python3
"""Consolidate completed Stage 10 candidate receipts with baseline S9-D1 and historical references."""
import argparse
import csv
import json
from pathlib import Path
import statistics as st


def distribution(row, key, values):
    values = [v for v in values if isinstance(v, (int, float))]
    if values:
        row[key] = st.median(values)
        row[key + "_min"], row[key + "_max"] = min(values), max(values)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("output", type=Path)
    args = p.parse_args()

    rows, batches = [], []
    for path in sorted(args.output.glob("*/receipts.json")):
        data = json.loads(path.read_text())
        progress = data["progress"]
        phases = [r for r in data["phases"] if r["phase"].get("scored") and r["phase"].get("verdict") == "PASS" and "summary" in r]

        row = dict(
            arm=progress["arm"],
            id=progress["id"],
            status=progress["verdict"],
            valid_batches=len(phases),
            image=progress["image_id"],
            engine_sha256=progress["engine_sha256"],
            draft_conf=progress.get("draft_conf"),
            spec=progress.get("spec"),
            prefill=progress.get("prefill"),
            overrides=progress.get("overrides", {}),
            report=str(path.parent.relative_to(args.output) / "report.md")
        )

        for i, side in enumerate("ab"):
            for metric in ("prefill_tok_s", "decode_tok_s", "ttft_s", "output_tokens"):
                distribution(row, metric + "_" + side, [r["summary"]["requests"][i].get(metric) for r in phases])
            distribution(row, "draft_acceptance_pct_" + side, [
                100 * r["request_metrics"][side]["drafts_accepted"] / r["request_metrics"][side]["drafts_offered"]
                for r in phases if r["request_metrics"].get(side, {}).get("drafts_offered")
            ])
            for metric in ("temperature_c", "power_w", "vram_mib", "sm_mhz", "util_pct"):
                gpu = [r["gpu_full_lifetime"][side][metric] for r in phases if side in r["gpu_full_lifetime"]]
                if gpu:
                    row[metric + "_mean_" + side] = st.mean(v["mean"] for v in gpu)
                    row[metric + "_peak_" + side] = max(v["peak"] for v in gpu)

        if phases:
            row["slower_agent_decode_median"] = min(row.get("decode_tok_s_a", 0), row.get("decode_tok_s_b", 0))
            row["slower_agent_prefill_median"] = min(row.get("prefill_tok_s_a", 0), row.get("prefill_tok_s_b", 0))
            row["target_met"] = (row["slower_agent_prefill_median"] >= 1100 and row["slower_agent_decode_median"] >= 30.0)

        for r in phases:
            batch = dict(arm=row["arm"], id=r["phase"]["id"], overlap=r["summary"].get("active_overlap", False))
            for i, side in enumerate("ab"):
                for key in ("prefill_tok_s", "decode_tok_s", "ttft_s", "output_tokens"):
                    batch[key + "_" + side] = r["summary"]["requests"][i][key]
            batches.append(batch)
        rows.append(row)

    for skip in sorted(args.output.glob("*-skipped.json")):
        rows.append(json.loads(skip.read_text()))

    # Sort order
    order = {"S10-P0": 0, "S10-D2": 1, "S10-D3": 2, "S10-K1": 3, "S10-K2": 4, "S10-K3": 5, "S10-P1": 6, "S10-P2": 7, "S10-P3": 8, "S10-D4": 9, "S10-C1": 10, "S10-D5": 11}
    rows.sort(key=lambda r: order.get(r["arm"], 99))

    for name, data in (("summary", rows), ("batches", batches)):
        (args.output / (name + ".json")).write_text(json.dumps(data, indent=2) + "\n")
        fields = list(dict.fromkeys(k for row in data for k in row))
        with (args.output / (name + ".csv")).open("w") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(data)

    def pair(row, metric, digits=1):
        return " / ".join(f"{row[metric + '_' + s]:.{digits}f}" if metric + "_" + s in row else "—" for s in "ab")

    lines = [
        "# Stage 10 Results Summary — 2026-11-10",
        "",
        "## Performance Table (Prefill >= 1100 & Decode >= 30.0 target)",
        "",
        "| Arm | Valid C2 | Prefill A/B tok/s | Decode A/B tok/s | TTFT A/B s | Target Met |",
        "|---|---:|---:|---:|---:|:---:|",
        "| S7-XXS-14 (archived) | 3/3 | 997.6 / 1006.6 | 26.4 / 26.2 | 127.53 / 126.48 | NO |",
        "| S8-C0 (archived) | 3/3 | 997.2 / 1006.3 | 25.6 / 27.9 | 127.57 / 126.42 | NO |",
        "| S8-C1 (archived) | 3/3 | 998.1 / 1007.2 | 26.2 / 28.3 | 127.45 / 126.32 | NO |",
        "| **S9-D1 (baseline)** | 3/3 | **1026.5 / 1032.6** | **28.2 / 29.4** | **123.92 / 123.21** | **NO** |"
    ]

    for r in rows:
        label = f"[{r['arm']}]({r['report']})" if r.get("report") else r["arm"]
        valid = f"{r.get('valid_batches', 0)}/3 ({r.get('status', 'SKIPPED')})"
        target_str = "YES" if r.get("target_met") else "NO"
        lines.append(f"| **{label}** | {valid} | {pair(r, 'prefill_tok_s')} | {pair(r, 'decode_tok_s')} | {pair(r, 'ttft_s', 2)} | {target_str} |")

    lines += [
        "",
        "## GPU Thermals and Power",
        "",
        "| Arm | GPU mean/peak temp °C A/B | GPU mean/peak W A/B |",
        "|---|---:|---:|",
        "| S9-D1 (baseline) | 60.1 / 67 / 61.2 / 67 | 84.44 / 173.19 / 87.35 / 177.26 |"
    ]

    for r in rows:
        if r.get("valid_batches", 0) > 0:
            temp = pair(r, "temperature_c_mean") + " / peak " + pair(r, "temperature_c_peak")
            power = pair(r, "power_w_mean", 2) + " / peak " + pair(r, "power_w_peak", 2)
            lines.append(f"| {r['arm']} | {temp} | {power} |")

    (args.output / "summary.md").write_text("\n".join(lines) + "\n")
    print(f"Summary written to {args.output / 'summary.md'}")


if __name__ == "__main__":
    main()
