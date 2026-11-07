#!/usr/bin/env python3
"""Export a completed or failed Stage 8 follow-up without claiming partial PASS."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import statistics as st


def load(path):
    return json.loads(path.read_text())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("raw", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    assert not a.output.exists(), "Refuse to overwrite an export"
    progress = load(a.raw / "progress.json")
    diagnostic = progress["arm"] == "S8-D1"
    rows = []
    for phase in progress["batches"]:
        name = phase["id"].removeprefix(progress["id"] + "-")
        d = a.raw / name
        r = {"phase": phase, "config_sha256": load(d / "config-sha256.json") if (d / "config-sha256.json").exists() else {}}
        if (d / "c2/summary.json").exists():
            r["summary"] = load(d / "c2/summary.json")
            r["summary_sha256"] = hashlib.sha256((d / "c2/summary.json").read_bytes()).hexdigest()
        r["processes"], r["engine_notes"], r["gpu_full_lifetime"], r["request_metrics"] = {}, {}, {}, {}
        samples = list(csv.reader((d / "gpu-telemetry.csv").read_text().splitlines())) if (d / "gpu-telemetry.csv").exists() else []
        for i, s in enumerate("ab"):
            metric_path = d / f"metrics-after-{s}.json"
            if metric_path.exists():
                metrics = load(metric_path)
                if s == "a":  # Whole host; do not double-count Agent B's same RAM sensor.
                    r["host_post_health"] = {k: metrics.get("hardware", {}).get(k) for k in ("ram_used", "ram_total", "cpu", "disk_read_mb", "disk_write_mb")}
                    r["host_trailing_ram_samples"] = metrics.get("history", {}).get("ram_used", [])
                requests = metrics.get("requests", [])
                if requests:
                    r["request_metrics"][s] = {k: requests[0].get(k) for k in ("prompt_tokens", "output_tokens", "finish", "hit_rate", "pcie_share", "file_mb", "ram_blobs", "file_blobs", "drafts_offered", "drafts_accepted")}
            proc = d / f"engine-process-{s}.json"
            if proc.exists():
                r["processes"][s] = load(proc)
            log = d / f"logs/agent-{s}.log"
            if log.exists():
                r["engine_notes"][s] = [line for line in log.read_text(errors="replace").splitlines()
                                         if line.startswith(("strata", "FileExpertSource:")) and any(k in line.lower() for k in
                                         ("profile", "timing", "decode:", "cpu pool", "pool workers", "cpu workers", "pcie", "cache", "prefill plan", "window", "drafts accepted", "file tier i/o", "kv streaming", "resident", "vram free", "workers on", "adaptive", "pinned", "complement ready", "per-layer slots"))]
            selected = [row for row in samples if len(row) == 8 and row[1].strip() == str(i)]
            if selected:
                r["gpu_full_lifetime"][s] = {k: {"mean": st.mean(float(row[ix]) for row in selected),
                                                        "peak": max(float(row[ix]) for row in selected)}
                                                     for k, ix in (("temperature_c", 2), ("power_w", 3), ("util_pct", 5), ("vram_mib", 6), ("sm_mhz", 7))}
        for when in ("before", "after"):
            f = d / f"cache-{when}.json"
            if f.exists():
                r[f"page_cache_{when}"] = load(f)
            f = d / f"memory-{when}.txt"
            if f.exists():
                r[f"memory_{when}"] = f.read_text()
        before, after = d / "vmstat-before.txt", d / "vmstat-after.txt"
        if before.exists() and after.exists():
            v0, v1 = ({k: int(v) for k, v in (line.split() for line in path.read_text().splitlines())} for path in (before, after))
            r["host_vmstat_delta"] = {k: v1[k] - v0[k] for k in ("pgmajfault", "pswpin", "pswpout", "pgpgin", "pgpgout")}
        rows.append(r)
    scored = [r for r in rows if r["phase"]["scored"]]
    passed = [r for r in scored if r["phase"].get("verdict") == "PASS" and "summary" in r]
    for r in passed:
        x = r["summary"]
        assert x["pass_mechanical"] and x["active_overlap"] and x["post_health"] and x["warmup_count"] == 0
        assert [q["prompt_tokens"] for q in x["requests"]] == [126967, 126968]
        for q in x["requests"]:
            assert q["output_tokens"] >= 1024 and q["finish_reason"] == "stop" and q["cache_n"] == q["cached_tokens"] == 0
    complete = not diagnostic and len(passed) == 3 and progress["verdict"] == "PASS"
    if complete:
        for r in passed:
            for s in "ab":
                notes = "\n".join(r["engine_notes"].get(s, []))
                if progress["arm"] == "S8-C3":
                    assert re.search(r"asynchronous adaptive tier: [1-9]\d* rounds", notes), "Async scheduler had no executed rounds"
                if progress["arm"] == "S8-M1":
                    assert "MTP windows up to 6 tokens" in notes
                if progress["arm"] == "S8-M2":
                    assert "per-layer slots use each layer's blob:" in notes
                if progress["arm"] == "S8-M3":
                    assert "KV streaming: 40960 of 131072 cells per QSA layer in VRAM" in notes
    title = "PROFILE_PASS_NOT_SCORED" if diagnostic and progress["verdict"] == "PROFILE_PASS_NOT_SCORED" else ("3/3 C2 PASS" if complete else f"INCOMPLETE: {len(passed)}/3 scored PASS")
    medians = {}
    if complete:
        for metric in ("prefill_tok_s", "decode_tok_s", "ttft_s"):
            medians[metric] = {s: st.median(r["summary"]["requests"][i][metric] for r in passed) for i, s in enumerate("ab")}
    output = {"progress": progress, "status": title, "medians": medians, "phases": rows,
              "decode_30_each_batch_both_agents": complete and all(q["decode_tok_s"] >= 30 for r in passed for q in r["summary"]["requests"])}
    reference_id = progress.get("reference_id", "u1-20261107T124518")
    reference_dir = a.raw.parent / reference_id
    reference_summaries = [load(reference_dir / f"batch-{n}/c2/summary.json") for n in range(1, 4)] if all((reference_dir / f"batch-{n}/c2/summary.json").exists() for n in range(1, 4)) else []
    reference_medians = {metric: {s: st.median(r["requests"][i][metric] for r in reference_summaries) for i, s in enumerate("ab")}
                         for metric in ("prefill_tok_s", "decode_tok_s", "ttft_s")} if reference_summaries else {}
    output["reference_id"], output["reference_medians"] = reference_id, reference_medians
    lines = [f"# {progress['arm']} — {progress['id']}", "", f"**{title}**", "",
             f"Primary arguments: `{json.dumps(progress.get('overrides', {}))}`; extra flags `{json.dumps(progress.get('extra_flags', []))}`.", "",
             f"Reference: `{progress.get('reference_id', 'u1-20261107T124518')}`. C3 inherits the validated C2 resident budget and adds only adapt-async; other scored arms change one primary policy from U1. D1 instead has instrumentation and is never a scored comparison. Context 131072, original IQ3_XXS/native pack/MTP, fixed workload, CPU/GPU isolation, 150 W/1110 MHz and serving/tunnel preservation apply.", "",
             "| Phase | Scored | Verdict | Prefill A/B | Decode A/B | TTFT A/B s | Output A/B | Overlap s | Wall s |", "|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        ph = r["phase"]
        if "summary" in r:
            x = r["summary"]
            q, w = x["requests"]
            pair = lambda k, fmt: f"{q[k]:{fmt}} / {w[k]:{fmt}}"
            lines.append(f"| {ph['id'].removeprefix(progress['id']+'-')} | {ph['scored']} | {ph.get('verdict', 'missing')} | {pair('prefill_tok_s', '.1f')} | {pair('decode_tok_s', '.1f')} | {pair('ttft_s', '.2f')} | {pair('output_tokens', 'd')} | {x['decode_overlap_s']:.2f} | {x['batch_wall_s']:.2f} |")
        else:
            lines.append(f"| {ph['id'].removeprefix(progress['id']+'-')} | {ph['scored']} | {ph.get('verdict', 'missing')} | — | — | — | — | — | — |")
    if medians:
        lines += ["", f"| Median | A | B | Reference {reference_id} A/B |", "|---|---:|---:|---:|"]
        for key, label, ref in (("prefill_tok_s", "Prefill tok/s", "871.0 / 877.2"), ("decode_tok_s", "Decode tok/s", "25.2 / 27.7"), ("ttft_s", "TTFT s", "146.02 / 145.01")):
            if reference_medians:
                ref = f"{reference_medians[key]['a']:.2f} / {reference_medians[key]['b']:.2f}"
            lines.append(f"| {label} | {medians[key]['a']:.2f} | {medians[key]['b']:.2f} | {ref} |")
    lines += ["", "## Conditions and interpretation", "",
              "All phases and failures remain in the raw tree; startup is not C2. There are no scored retries or baseline reruns. Differences from U1/S7 are descriptive across changing cache/swap/output/temperature conditions, not controlled causal gains. A mechanical PASS does not validate semantic coding/tool-call quality or authorize promotion.", "",
              "GPU statistics in receipts cover each full process lifetime, including loading/shutdown; they are not decode-only power. Physical I/O, page-cache and swap evidence, effective child args/env and profiler lines are retained in the sanitized receipts. Raw prompts/responses remain outside Git.", "",
              f"Raw P520: `results/stage8/{progress['arm']}/{progress['id']}/`. Source/image/binary/harness pins and process identity are in [receipts](receipts.json).", ""]
    if progress.get("error"):
        lines += ["Recorded error: `" + progress["error"] + "`", ""]
    a.output.mkdir(parents=True)
    (a.output / "receipts.json").write_text(json.dumps(output, indent=2) + "\n")
    (a.output / "report.md").write_text("\n".join(lines))
    print(json.dumps({"id": progress["id"], "status": title, "medians": medians}, indent=2))


if __name__ == "__main__":
    main()
