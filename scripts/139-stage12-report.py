#!/usr/bin/env python3
"""Generate sanitized Stage 12 per-run receipt report & metrics JSON on ThinkPad."""
import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import statistics as st

S11X_D2_REF = {"prefill": (1032.6, 1037.0), "decode": (37.1, 41.0), "ttft": (123.21, 122.69)}


def load(path: Path):
    return json.loads(path.read_text())


def stats(values):
    return {"mean": st.mean(values), "min": min(values), "peak": max(values)} if values else None


def phase_receipt(raw: Path, phase: dict):
    name = phase["id"].removeprefix(raw.name + "-")
    d = raw / name
    row = {"phase": phase, "gpu_full_lifetime": {}, "request_metrics": {}, "engine_request_records": {}, "timing": {}}
    if (d / "c2/summary.json").exists():
        summary = load(d / "c2/summary.json")
        row["summary"] = summary
        row["summary_sha256"] = hashlib.sha256((d / "c2/summary.json").read_bytes()).hexdigest()

    samples = list(csv.reader((d / "gpu-telemetry.csv").read_text().splitlines())) if (d / "gpu-telemetry.csv").exists() else []
    for i, side in enumerate("ab"):
        selected = [r for r in samples if len(r) == 8 and r[1].strip() == str(i)]
        if selected:
            row["gpu_full_lifetime"][side] = {
                key: stats([float(r[ix]) for r in selected])
                for key, ix in (("temperature_c", 2), ("power_w", 3), ("util_pct", 5), ("vram_mib", 6), ("sm_mhz", 7))
            }
        if (d / f"metrics-after-{side}.json").exists():
            val = load(d / f"metrics-after-{side}.json")
            row["request_metrics"][side] = (val.get("requests") or [{}])[0]

        log = d / f"logs/agent-{side}.log"
        notes = log.read_text(errors="replace").splitlines() if log.exists() else []
        records = []
        for line in notes:
            m = re.search(r"prompt (\d+) tokens = (\d+) reused \+ (\d+) read in ([\d.]+) ms.*?, (\d+) generated in ([\d.]+) ms", line)
            if m:
                g = m.groups()
                records.append(dict(prompt_tokens=int(g[0]), reused=int(g[1]), read_tokens=int(g[2]),
                                    prompt_ms=float(g[3]), generated=int(g[4]), decode_ms=float(g[5])))
            elif records:
                phys = re.search(r"file tier I/O this request: the OS read ([\d.]+) MB", line)
                kv = re.search(r"KV streaming: ([\d.]+)%", line)
                exp_hit = re.search(r"expert cache: ([\d.]+)% hit", line)
                if phys:
                    records[-1]["physical_read_mb"] = float(phys[1])
                if kv:
                    records[-1]["kv_vram_hit_pct"] = float(kv[1])
                if exp_hit:
                    records[-1]["expert_cache_hit_pct"] = float(exp_hit[1])
        row["engine_request_records"][side] = records
        row["timing"][side] = [
            l for l in notes
            if any(k in l.lower() for k in ("strata decode timing", "strata decode gpu stages", "prefill timing", "strata prefill", "verify"))
        ]
    return row


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("arm")
    p.add_argument("id")
    p.add_argument("--out-dir", type=Path, default=None)
    a = p.parse_args()

    root = Path(__file__).resolve().parents[1]
    raw = root / "results/raw" / a.id
    progress = load(raw / "progress.json")
    manifest = load(root / "results/raw" / f"{a.id}-sha256.json")
    assert manifest["all_match"]

    out_dir = a.out_dir or (root / "artifacts/stage12-results-20261125" / a.id)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = [phase_receipt(raw, ph) for ph in progress["batches"]]
    scored = [r for r in rows if r["phase"].get("scored") and r["phase"].get("verdict") == "PASS"]
    medians = {}
    if scored:
        for side_i, side in enumerate("ab"):
            reqs = [r["summary"]["requests"][side_i] for r in scored]
            medians[side] = {
                "prefill_tok_s": st.median(x["prefill_tok_s"] for x in reqs),
                "decode_tok_s": st.median(x["decode_tok_s"] for x in reqs),
                "ttft_s": st.median(x["ttft_s"] for x in reqs),
            }

    lines = [
        f"# {a.arm} (`{a.id}`) — Stage 12 Receipt Report",
        "",
        f"- **Generated:** {dt.datetime.now().astimezone().isoformat()}",
        f"- **Verdict:** `{progress.get('verdict')}` (mode `{progress.get('mode')}`)",
        f"- **Image:** `{progress.get('image_id')}`",
        f"- **Engine SHA256:** `{progress.get('engine_sha256')}`",
        f"- **Source SHA:** `{progress.get('source_sha')}`",
        f"- **Overrides:** `{json.dumps(progress.get('overrides', {}))}`",
        f"- **Backup Verified:** {manifest['files']} files (`all_match={manifest['all_match']}`)",
        "",
    ]
    if medians:
        pa, pb = medians["a"]["prefill_tok_s"], medians["b"]["prefill_tok_s"]
        da, db = medians["a"]["decode_tok_s"], medians["b"]["decode_tok_s"]
        ta, tb = medians["a"]["ttft_s"], medians["b"]["ttft_s"]
        lines.extend([
            "## Scored C2 Medians vs S11X-D2 Reference",
            "",
            "| Metric | This Run (A / B) | S11X-D2 Reference (A / B) | Delta (A / B) |",
            "|---|---:|---:|---:|",
            f"| Prefill (tok/s) | {pa:.1f} / {pb:.1f} | {S11X_D2_REF['prefill'][0]} / {S11X_D2_REF['prefill'][1]} | {pa - S11X_D2_REF['prefill'][0]:+.1f} / {pb - S11X_D2_REF['prefill'][1]:+.1f} |",
            f"| Decode (tok/s) | {da:.1f} / {db:.1f} | {S11X_D2_REF['decode'][0]} / {S11X_D2_REF['decode'][1]} | {da - S11X_D2_REF['decode'][0]:+.1f} / {db - S11X_D2_REF['decode'][1]:+.1f} |",
            f"| TTFT (s) | {ta:.2f} / {tb:.2f} | {S11X_D2_REF['ttft'][0]} / {S11X_D2_REF['ttft'][1]} | {ta - S11X_D2_REF['ttft'][0]:+.2f} / {tb - S11X_D2_REF['ttft'][1]:+.2f} |",
            "",
        ])

    lines.extend(["## Phases", ""])
    for r in rows:
        ph = r["phase"]
        lines.append(f"### `{ph['id']}` — `{ph.get('verdict')}`")
        if "summary" in r:
            reqs = r["summary"]["requests"]
            lines.append(
                f"- Prefill: `{reqs[0]['prefill_tok_s']:.1f}` / `{reqs[1]['prefill_tok_s']:.1f}` tok/s | "
                f"Decode: `{reqs[0]['decode_tok_s']:.1f}` / `{reqs[1]['decode_tok_s']:.1f}` tok/s | "
                f"TTFT: `{reqs[0]['ttft_s']:.2f}` / `{reqs[1]['ttft_s']:.2f}` s | "
                f"Overlap: `{r['summary'].get('decode_overlap_s', 0):.2f}s`"
            )
        for side in "ab":
            g = r["gpu_full_lifetime"].get(side)
            rm = r["request_metrics"].get(side, {})
            rec = (r["engine_request_records"].get(side) or [{}])[-1]
            if g:
                lines.append(
                    f"- Agent {side.upper()}: VRAM peak `{g['vram_mib']['peak']:.0f}` MiB | "
                    f"Power avg/peak `{g['power_w']['mean']:.1f}` / `{g['power_w']['peak']:.1f}` W | "
                    f"Temp max `{g['temperature_c']['peak']:.0f}` C | "
                    f"Offered/Accepted `{rm.get('drafts_offered')}`/`{rm.get('drafts_accepted')}` | "
                    f"OS read `{rec.get('physical_read_mb')}` MB | Exp hit `{rec.get('expert_cache_hit_pct')}`%"
                )
            for tl in r["timing"].get(side, [])[:6]:
                lines.append(f"  - `{tl}`")
        lines.append("")

    (out_dir / "report.md").write_text("\n".join(lines))
    (out_dir / "metrics.json").write_text(json.dumps({"id": a.id, "arm": a.arm, "progress": progress, "medians": medians, "rows": rows}, indent=2) + "\n")
    print(json.dumps({"id": a.id, "arm": a.arm, "medians": medians, "report": str(out_dir / "report.md")}))


if __name__ == "__main__":
    main()
