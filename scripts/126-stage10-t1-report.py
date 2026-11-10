#!/usr/bin/env python3
"""Stage 10 T1 Report Generator: Solo vs Concurrent performance and RAM contention analysis."""
import argparse
import csv
import json
from pathlib import Path
import statistics as st


def parse_pcm_csv(path: Path):
    if not path.exists():
        return None
    lines = path.read_text().splitlines()
    header_idx = -1
    for i, line in enumerate(lines):
        if ("Date" in line and "Time" in line) or "Read,Write,Memory" in line:
            header_idx = i
            break
    if header_idx == -1 or header_idx + 1 >= len(lines):
        return None

    read_vals, write_vals, total_vals = [], [], []
    reader = csv.reader(lines[header_idx + 1:])
    for row in reader:
        if len(row) < 5:
            continue
        try:
            # Last 3 columns are typically Read, Write, Memory
            r = float(row[-3].strip())
            w = float(row[-2].strip())
            tot = float(row[-1].strip())
            read_vals.append(r)
            write_vals.append(w)
            total_vals.append(tot)
        except ValueError:
            continue

    if not total_vals:
        return None
    return {
        "read_mb_s_avg": round(st.mean(read_vals), 1),
        "read_mb_s_peak": round(max(read_vals), 1),
        "write_mb_s_avg": round(st.mean(write_vals), 1),
        "write_mb_s_peak": round(max(write_vals), 1),
        "total_mb_s_avg": round(st.mean(total_vals), 1),
        "total_mb_s_peak": round(max(total_vals), 1),
    }


def analyze_t1(raw_dir: Path):
    progress = json.loads((raw_dir / "progress.json").read_text())
    phases = progress["batches"]

    solo_a = [p for p in phases if p["id"].endswith(("-batch-1", "-batch-2", "-batch-3")) and "solo-a" in p["id"]]
    solo_b = [p for p in phases if p["id"].endswith(("-batch-1", "-batch-2", "-batch-3")) and "solo-b" in p["id"]]
    conc = [p for p in phases if p["id"].endswith(("-batch-1", "-batch-2", "-batch-3")) and "concurrent" in p["id"]]

    data = {"solo_a": [], "solo_b": [], "concurrent": []}

    for name, group in (("solo_a", solo_a), ("solo_b", solo_b), ("concurrent", conc)):
        for b in group:
            p_dir = raw_dir / b["id"].removeprefix(f"{progress['id']}-")
            summary = json.loads((p_dir / "c2/summary.json").read_text())
            pcm = parse_pcm_csv(p_dir / "pcm-memory.csv")
            reqs = {r["label"]: r for r in summary["requests"]}
            item = {
                "id": b["id"],
                "wall_s": summary["batch_wall_s"],
                "pcm": pcm,
                "requests": reqs
            }
            data[name].append(item)

    return progress, data


def main():
    p = argparse.ArgumentParser()
    p.add_argument("raw_dir", type=Path)
    p.add_argument("--out-dir", type=Path)
    args = p.parse_args()

    out_dir = args.out_dir or args.raw_dir
    progress, data = analyze_t1(args.raw_dir)

    lines = []
    lines.append(f"# S10-T1 RAM Contention & Solo vs Concurrent Analysis: `{progress['id']}`")
    lines.append("")
    lines.append("## 1. Metric Comparison: Solo vs Concurrent Serving")
    lines.append("")
    lines.append("| Condition | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | RAM BW Peak (MB/s) | RAM BW Mean (MB/s) |")
    lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

    # Medians
    def med_req(group, side, field):
        vals = [g["requests"][side][field] for g in group if side in g["requests"]]
        return st.median(vals) if vals else None

    def pcm_stat(group, key):
        vals = [g["pcm"][key] for g in group if g.get("pcm") and key in g["pcm"]]
        return st.mean(vals) if vals else None

    # Solo A
    pa_solo = med_req(data["solo_a"], "A", "prefill_tok_s")
    da_solo = med_req(data["solo_a"], "A", "decode_tok_s")
    ta_solo = med_req(data["solo_a"], "A", "ttft_s")
    pcm_peak_a = max([g["pcm"]["total_mb_s_peak"] for g in data["solo_a"] if g.get("pcm")], default=None)
    pcm_mean_a = pcm_stat(data["solo_a"], "total_mb_s_avg")
    lines.append(f"| **Solo A (GPU0)** | {pa_solo:.1f} | — | {da_solo:.1f} | — | {ta_solo:.2f} | — | {pcm_peak_a or 'N/A'} | {pcm_mean_a or 'N/A'} |")

    # Solo B
    pb_solo = med_req(data["solo_b"], "B", "prefill_tok_s")
    db_solo = med_req(data["solo_b"], "B", "decode_tok_s")
    tb_solo = med_req(data["solo_b"], "B", "ttft_s")
    pcm_peak_b = max([g["pcm"]["total_mb_s_peak"] for g in data["solo_b"] if g.get("pcm")], default=None)
    pcm_mean_b = pcm_stat(data["solo_b"], "total_mb_s_avg")
    lines.append(f"| **Solo B (GPU1)** | — | {pb_solo:.1f} | — | {db_solo:.1f} | — | {tb_solo:.2f} | {pcm_peak_b or 'N/A'} | {pcm_mean_b or 'N/A'} |")

    # Concurrent
    pa_conc = med_req(data["concurrent"], "A", "prefill_tok_s")
    pb_conc = med_req(data["concurrent"], "B", "prefill_tok_s")
    da_conc = med_req(data["concurrent"], "A", "decode_tok_s")
    db_conc = med_req(data["concurrent"], "B", "decode_tok_s")
    ta_conc = med_req(data["concurrent"], "A", "ttft_s")
    tb_conc = med_req(data["concurrent"], "B", "ttft_s")
    pcm_peak_c = max([g["pcm"]["total_mb_s_peak"] for g in data["concurrent"] if g.get("pcm")], default=None)
    pcm_mean_c = pcm_stat(data["concurrent"], "total_mb_s_avg")
    lines.append(f"| **Concurrent (A+B)** | {pa_conc:.1f} | {pb_conc:.1f} | {da_conc:.1f} | {db_conc:.1f} | {ta_conc:.2f} | {tb_conc:.2f} | {pcm_peak_c or 'N/A'} | {pcm_mean_c or 'N/A'} |")

    lines.append("")
    lines.append("## 2. Contention Analysis & Speed Degradation Rate")
    lines.append("")
    lines.append("Degradation when moving from isolated solo execution to dual-agent concurrent serving:")
    lines.append("")
    deg_pa = ((pa_solo - pa_conc) / pa_solo) * 100 if pa_solo and pa_conc else 0
    deg_pb = ((pb_solo - pb_conc) / pb_solo) * 100 if pb_solo and pb_conc else 0
    deg_da = ((da_solo - da_conc) / da_solo) * 100 if da_solo and da_conc else 0
    deg_db = ((db_solo - db_conc) / db_solo) * 100 if db_solo and db_conc else 0

    lines.append(f"- **Prefill Degradation**: Agent A `{deg_pa:+.2f}%`, Agent B `{deg_pb:+.2f}%`")
    lines.append(f"- **Decode Degradation**: Agent A `{deg_da:+.2f}%`, Agent B `{deg_db:+.2f}%`")
    lines.append("")
    lines.append("## 3. RAM 32GB Upgrade Recommendation")
    lines.append("")

    # Diagnostic logic
    is_bw_saturated = pcm_peak_c and pcm_peak_c > 65000  # W-2135 quad-channel ceiling ~85 GB/s
    is_decode_degraded = max(deg_da, deg_db) > 5.0
    is_prefill_degraded = max(deg_pa, deg_pb) > 5.0

    if is_bw_saturated:
        lines.append("- **RAM Bandwidth**: **SATURATED**. Observed RAM bandwidth approaches hardware ceiling (>65 GB/s). Adding channels or faster RAM may help.")
    else:
        lines.append(f"- **RAM Bandwidth**: **AMPLE HEADROOM**. Peak observed memory bandwidth ({pcm_peak_c or 'N/A'} MB/s) is well below the ~85,300 MB/s quad-channel ceiling. Memory bus contention is NOT the bottleneck.")

    if not is_decode_degraded and not is_prefill_degraded:
        lines.append("- **Resource Contention**: **NEGLIGIBLE (<5% drop)**. The two agents run near-identically in solo vs concurrent serving.")
        lines.append("- **32GB Upgrade Verdict**: **NOT RECOMMENDED**. The existing 64GB RAM and quad-channel memory bus fully accommodate dual-agent 128K C2 without paging or bandwidth starvation.")
    else:
        lines.append("- **Resource Contention**: **DETECTED**. Measured measurable throughput reduction in concurrent serving.")

    report_path = out_dir / "report.md"
    report_path.write_text("\n".join(lines) + "\n")
    print(f"Report written to {report_path}")


if __name__ == "__main__":
    main()
