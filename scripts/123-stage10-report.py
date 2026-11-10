#!/usr/bin/env python3
"""Export sanitized Stage 10 receipts, metrics, and comparisons against baseline."""
import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import statistics as st

CANDIDATES = ("P0", "D2", "D3", "K1", "K2", "K3", "P1", "P2", "P3", "D4", "C1")


def load(path):
    return json.loads(path.read_text())


def stats(values):
    return {"mean": st.mean(values), "min": min(values), "peak": max(values)} if values else None


def phase_receipt(raw, phase):
    name = phase["id"].removeprefix(raw.name + "-")
    d = raw / name
    row = {"phase": phase, "gpu_full_lifetime": {}, "request_metrics": {}, "engine_notes": {}, "processes": {}}
    if (d / "c2/summary.json").exists():
        summary = load(d / "c2/summary.json")
        row["summary"] = summary
        row["workload"] = load(d / "c2/workload.json")
        row["summary_sha256"] = hashlib.sha256((d / "c2/summary.json").read_bytes()).hexdigest()
        if phase.get("verdict") == "PASS":
            assert summary["pass_mechanical"] and summary["active_overlap"] and summary["post_health"] and summary["warmup_count"] == 0
            assert [r["prompt_tokens"] for r in summary["requests"]] == [126967, 126968]
            for request in summary["requests"]:
                assert request["output_tokens"] >= 1024 and request["finish_reason"] == "stop"
                assert request["cache_n"] == request["cached_tokens"] == 0

    samples = list(csv.reader((d / "gpu-telemetry.csv").read_text().splitlines())) if (d / "gpu-telemetry.csv").exists() else []
    for i, side in enumerate("ab"):
        selected = [r for r in samples if len(r) == 8 and r[1].strip() == str(i)]
        if selected:
            row["gpu_full_lifetime"][side] = {
                key: stats([float(r[ix]) for r in selected])
                for key, ix in (("temperature_c", 2), ("power_w", 3), ("util_pct", 5), ("vram_mib", 6), ("sm_mhz", 7))
            }
            row["gpu_full_lifetime"][side]["sample_count"] = len(selected)

        for filename, key in ((f"engine-process-{side}.json", "processes"), (f"metrics-after-{side}.json", "request_metrics")):
            if (d / filename).exists():
                value = load(d / filename)
                if key == "request_metrics":
                    value = (value.get("requests") or [{}])[0]
                row[key][side] = value

        log = d / f"logs/agent-{side}.log"
        notes = log.read_text(errors="replace").splitlines() if log.exists() else []
        records = []
        for line in notes:
            match = re.search(r"prompt (\d+) tokens = (\d+) reused \+ (\d+) read in ([\d.]+) ms.*?, (\d+) generated in ([\d.]+) ms", line)
            if match:
                values = match.groups()
                records.append(dict(
                    prompt_tokens=int(values[0]), reused=int(values[1]), read_tokens=int(values[2]),
                    prompt_ms=float(values[3]), generated=int(values[4]), decode_ms=float(values[5])
                ))
            elif records:
                physical = re.search(r"file tier I/O this request: the OS read ([\d.]+) MB", line)
                kv = re.search(r"KV streaming: ([\d.]+)%", line)
                if physical:
                    records[-1]["physical_read_mb"] = float(physical[1])
                if kv:
                    records[-1]["kv_vram_hit_pct"] = float(kv[1])
        row.setdefault("engine_request_records", {})[side] = records

        row["engine_notes"][side] = [
            line for line in notes
            if any(term in line.lower() for term in (
                "strata decode timing", "strata decode gpu stages", "dflash2", "prefill", "chunk",
                "resident", "expert", "cache", "kv streaming", "acceptance", "drafts"
            ))
        ]

        if row["processes"].get(side, {}).get("args", []).count("dflash2"):
            offered = row["request_metrics"].get(side, {}).get("drafts_offered")
            accepted = row["request_metrics"].get(side, {}).get("drafts_accepted")
            if isinstance(offered, int) and isinstance(accepted, int):
                row.setdefault("dflash2_acceptance", {})[side] = {
                    "offered": offered, "accepted": accepted,
                    "rate": accepted / offered if offered else 0.0
                }

    return row


def generate_report(raw_dir, out_dir):
    progress = load(raw_dir / "progress.json")
    phases = [phase_receipt(raw_dir, p) for p in progress["batches"]]
    scored = [p for p in phases if p["phase"].get("scored") and p["phase"].get("verdict") == "PASS"]

    report_lines = [
        f"# Stage 10 {progress['arm']} Receipt: `{progress['id']}`",
        "",
        f"- **Verdict**: `{progress['verdict']}`",
        f"- **Host**: `{progress['host']}` (boot `{progress['boot_id']}`)",
        f"- **Engine**: `{progress['image_id']}` (`{progress['engine_sha256'][:16]}...`)",
        f"- **Overrides**: `{json.dumps(progress.get('overrides', {}))}`",
        f"- **DFlash2 Config**: `spec {progress.get('spec', 6)}`, `conf {progress.get('draft_conf', 0.7)}`, `prefill {progress.get('prefill', 'auto')}`",
        "",
        "## Scored C2 Batches",
        "",
        "| Batch | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Overlap | Verdict |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |"
    ]

    prefill_a, prefill_b, decode_a, decode_b, ttft_a, ttft_b = [], [], [], [], [], []
    for p in scored:
        reqs = p["summary"]["requests"]
        pa, pb = reqs[0]["prefill_tok_s"], reqs[1]["prefill_tok_s"]
        da, db = reqs[0]["decode_tok_s"], reqs[1]["decode_tok_s"]
        ta, tb = reqs[0]["ttft_s"], reqs[1]["ttft_s"]
        overlap = "Yes" if p["summary"]["active_overlap"] else "No"
        report_lines.append(f"| {p['phase']['id']} | {pa:.1f} | {pb:.1f} | {da:.1f} | {db:.1f} | {ta:.2f} | {tb:.2f} | {overlap} | {p['phase']['verdict']} |")
        prefill_a.append(pa)
        prefill_b.append(pb)
        decode_a.append(da)
        decode_b.append(db)
        ttft_a.append(ta)
        ttft_b.append(tb)

    if scored:
        med_pa, med_pb = st.median(prefill_a), st.median(prefill_b)
        med_da, med_db = st.median(decode_a), st.median(decode_b)
        med_ta, med_tb = st.median(ttft_a), st.median(ttft_b)
        report_lines.append(f"| **Median** | **{med_pa:.1f}** | **{med_pb:.1f}** | **{med_da:.1f}** | **{med_db:.1f}** | **{med_ta:.2f}** | **{med_tb:.2f}** | - | **PASS** |")
        report_lines.extend([
            "",
            "## Summary Metrics",
            "",
            f"- **Prefill A / B Median**: {med_pa:.1f} / {med_pb:.1f} tok/s",
            f"- **Decode A / B Median**: {med_da:.1f} / {med_db:.1f} tok/s",
            f"- **TTFT A / B Median**: {med_ta:.2f} / {med_tb:.2f} s",
            f"- **Target Met (Prefill >= 1100 & Decode >= 30.0)**: {'YES' if (min(med_pa, med_pb) >= 1100 and min(med_da, med_db) >= 30.0) else 'NO'}"
        ])

    out_dir.mkdir(parents=True, exist_ok=True)
    report_file = out_dir / "report.md"
    report_file.write_text("\n".join(report_lines) + "\n")
    receipts_file = out_dir / "receipts.json"
    receipts_file.write_text(json.dumps({"progress": progress, "phases": phases}, indent=2) + "\n")
    print(f"Report written to {report_file}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("raw_dir", type=Path)
    p.add_argument("--out-dir", type=Path)
    args = p.parse_args()
    out = args.out_dir or args.raw_dir
    generate_report(args.raw_dir, out)


if __name__ == "__main__":
    main()
