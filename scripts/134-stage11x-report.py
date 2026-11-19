#!/usr/bin/env python3
"""Export sanitized Stage 11X receipts, metrics, profiling lines, and comparisons against S10-D4 baseline."""
import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import statistics as st

CANDIDATES = ("A0", "P0", "C0", "D1", "D1W", "D2", "D3", "P1", "P2", "C1")


def load(path):
    return json.loads(path.read_text())


def stats(values):
    return {"mean": st.mean(values), "min": min(values), "peak": max(values)} if values else None


def phase_receipt(raw, phase):
    name = phase["id"].removeprefix(raw.name + "-")
    d = raw / name
    row = {
        "phase": phase,
        "gpu_full_lifetime": {},
        "request_metrics": {},
        "engine_notes": {},
        "prefill_timing": {},
        "decode_timing": {},
        "decode_gpu_stages": {},
        "verify_profile": {},
        "processes": {}
    }
    if (d / "c2/summary.json").exists():
        summary = load(d / "c2/summary.json")
        row["summary"] = summary
        row["workload"] = load(d / "c2/workload.json")
        row["summary_sha256"] = hashlib.sha256((d / "c2/summary.json").read_bytes()).hexdigest()
        if phase.get("verdict") in ("PASS", "DIAGNOSTIC_PASS_NOT_SCORED"):
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
        docker_log = d / f"docker-{side}.log"
        notes = log.read_text(errors="replace").splitlines() if log.exists() else []
        if docker_log.exists():
            for dline in docker_log.read_text(errors="replace").splitlines():
                if dline not in notes:
                    notes.append(dline)

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
                exp_hit = re.search(r"expert cache: ([\d.]+)% hit", line)
                if physical:
                    records[-1]["physical_read_mb"] = float(physical[1])
                if kv:
                    records[-1]["kv_vram_hit_pct"] = float(kv[1])
                if exp_hit:
                    records[-1]["expert_cache_hit_pct"] = float(exp_hit[1])
        row.setdefault("engine_request_records", {})[side] = records

        row["prefill_timing"][side] = [
            line for line in notes
            if any(term in line.lower() for term in ("prefill timing", "strata prefill", "[prefill]", "prefill gpu", "pf_timing"))
        ]
        row["decode_timing"][side] = [
            line for line in notes
            if "strata decode timing" in line.lower()
        ]
        row["decode_gpu_stages"][side] = [
            line for line in notes
            if "strata decode gpu stages" in line.lower()
        ]
        row["verify_profile"][side] = [
            line for line in notes
            if "verify" in line.lower() and any(k in line.lower() for k in ("ms", "profile", "strata"))
        ]

        row["engine_notes"][side] = [
            line for line in notes
            if any(term in line.lower() for term in (
                "strata decode timing", "strata decode gpu stages", "prefill timing", "strata prefill",
                "verify", "dflash2", "prefill", "chunk",
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
    diagnostics = [p for p in phases if p["phase"].get("verdict") == "DIAGNOSTIC_PASS_NOT_SCORED"]

    report_lines = [
        f"# Stage 11X {progress['arm']} Receipt: `{progress['id']}`",
        "",
        f"- **Verdict**: `{progress['verdict']}`",
        f"- **Host**: `{progress['host']}` (boot `{progress['boot_id']}`)",
        f"- **Engine**: `{progress['image_id']}` (`{progress['engine_sha256'][:16]}...`)",
        f"- **Overrides**: `{json.dumps(progress.get('overrides', {}))}`",
        f"- **DFlash2 Config**: `spec {progress.get('spec', 8)}`, `conf {progress.get('draft_conf', 0.7)}`, `prefill {progress.get('prefill', 'auto')}`",
        ""
    ]

    if diagnostics:
        report_lines.extend([
            "## Diagnostic C2 Batch (Non-Scored)",
            "",
            "| Phase | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Overlap | Verdict |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |"
        ])
        for p in diagnostics:
            reqs = p["summary"]["requests"]
            pa, pb = reqs[0]["prefill_tok_s"], reqs[1]["prefill_tok_s"]
            da, db = reqs[0]["decode_tok_s"], reqs[1]["decode_tok_s"]
            ta, tb = reqs[0]["ttft_s"], reqs[1]["ttft_s"]
            overlap = "Yes" if p["summary"]["active_overlap"] else "No"
            report_lines.append(f"| {p['phase']['id']} | {pa:.1f} | {pb:.1f} | {da:.1f} | {db:.1f} | {ta:.2f} | {tb:.2f} | {overlap} | {p['phase']['verdict']} |")
        report_lines.append("")

        for p in diagnostics:
            for side in "ab":
                report_lines.append(f"### Agent {side.upper()} Profiling Notes (`{p['phase']['id']}`)")
                report_lines.append("```text")
                for line in p["engine_notes"].get(side, []):
                    report_lines.append(line)
                report_lines.append("```")
                report_lines.append("")

    if scored:
        report_lines.extend([
            "## Scored C2 Batches",
            "",
            "| Batch | Prefill A (tok/s) | Prefill B (tok/s) | Decode A (tok/s) | Decode B (tok/s) | TTFT A (s) | TTFT B (s) | Overlap | Verdict |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |"
        ])

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

        med_pa, med_pb = st.median(prefill_a), st.median(prefill_b)
        med_da, med_db = st.median(decode_a), st.median(decode_b)
        med_ta, med_tb = st.median(ttft_a), st.median(ttft_b)
        report_lines.append(f"| **Median** | **{med_pa:.1f}** | **{med_pb:.1f}** | **{med_da:.1f}** | **{med_db:.1f}** | **{med_ta:.2f}** | **{med_tb:.2f}** | - | **PASS** |")
        report_lines.extend([
            "",
            "## Summary Metrics vs `S10-D4` (`1025.1 / 1027.8` Prefill, `30.4 / 30.3` Decode, `124.08 / 123.79 s` TTFT)",
            "",
            f"- **Prefill A / B Median**: {med_pa:.1f} / {med_pb:.1f} tok/s (vs S10-D4: {med_pa - 1025.1:+.1f} / {med_pb - 1027.8:+.1f} tok/s)",
            f"- **Decode A / B Median**: {med_da:.1f} / {med_db:.1f} tok/s (vs S10-D4: {med_da - 30.4:+.1f} / {med_db - 30.3:+.1f} tok/s)",
            f"- **TTFT A / B Median**: {med_ta:.2f} / {med_tb:.2f} s (vs S10-D4: {med_ta - 124.08:+.2f} / {med_tb - 123.79:+.2f} s)",
            f"- **Stage 11X Final Target Met (Prefill >= 1200 & Decode >= 40.0)**: {'YES' if (min(med_pa, med_pb) >= 1200 and min(med_da, med_db) >= 40.0) else 'NO'}"
        ])

    out_dir.mkdir(parents=True, exist_ok=True)
    report_file = out_dir / "report.md"
    report_file.write_text("\n".join(report_lines) + "\n")
    payload = {"progress": progress, "phases": phases}
    (out_dir / "report.json").write_text(json.dumps(payload, indent=2) + "\n")
    (out_dir / "receipts.json").write_text(json.dumps(payload, indent=2) + "\n")
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
