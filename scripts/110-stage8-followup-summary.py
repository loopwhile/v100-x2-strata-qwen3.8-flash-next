#!/usr/bin/env python3
"""Summarize all completed Stage 8 follow-ups, including resource and MTP data."""
import csv
import json
from pathlib import Path
import re
import statistics as st

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/stage8-followup-results-20261107"


def stats(row, name, values):
    values = [v for v in values if isinstance(v, (int, float))]
    if values:
        row[name], row[name + "_min"], row[name + "_max"] = st.median(values), min(values), max(values)


def main():
    rows, diagnostic = [], []
    for f in sorted(OUT.glob("*/receipts.json")):
        data = json.loads(f.read_text())
        progress = data["progress"]
        if progress["arm"] == "S8-D1":
            diagnostic.append({"id": progress["id"], "status": data["status"], "scored": False})
            continue
        phases = [p for p in data["phases"] if p["phase"]["scored"] and p["phase"].get("verdict") == "PASS" and "summary" in p]
        row = {"arm": progress["arm"], "id": progress["id"], "status": data["status"], "valid_batches": len(phases),
               "reference": data.get("reference_id", "u1-20261107T124518"), "primary": json.dumps(progress.get("overrides", {})) + " " + " ".join(progress.get("extra_flags", [])),
               "report": str(f.parent.relative_to(OUT) / "report.md")}
        for metric in ("batch_wall_s", "decode_overlap_s", "submission_skew_s"):
            stats(row, metric, [p["summary"][metric] for p in phases])
        for i, s in enumerate("ab"):
            for metric in ("prefill_tok_s", "decode_tok_s", "ttft_s", "wall_s", "output_tokens", "expert_hit_rate", "file_mb"):
                stats(row, metric + "_" + s, [p["summary"]["requests"][i].get(metric) for p in phases])
            accepted, proposed, physical, kv_hits = [], [], [], []
            for p in phases:
                notes = "\n".join(p["engine_notes"].get(s, []))
                match = re.search(r"drafts accepted (\d+) of (\d+)", notes)
                if match:
                    accepted.append(int(match[1])); proposed.append(int(match[2]))
                match = re.search(r"file tier I/O this request: the OS read ([\d.]+) MB", notes)
                if match:
                    physical.append(float(match[1]))
                matches = re.findall(r"KV streaming: ([\d.]+)%", notes)
                if matches:
                    kv_hits.append(float(matches[-1]))
            stats(row, "mtp_accepted_" + s, accepted)
            stats(row, "mtp_proposed_" + s, proposed)
            stats(row, "mtp_acceptance_pct_" + s, [100 * x / y for x, y in zip(accepted, proposed) if y])
            stats(row, "physical_read_mb_" + s, physical)
            stats(row, "kv_vram_hit_pct_" + s, kv_hits)
            shares = []
            for p in phases:
                metrics = p.get("request_metrics", {}).get(s)
                if metrics is None:
                    name = p["phase"]["id"].removeprefix(progress["id"] + "-")
                    path = ROOT / "results/raw" / progress["id"] / name / f"metrics-after-{s}.json"
                    items = json.loads(path.read_text()).get("requests", []) if path.exists() else []
                    metrics = items[0] if items else {}
                shares.append(metrics.get("pcie_share"))
            stats(row, "actual_pcie_share_" + s, shares)
            for metric in ("temperature_c", "power_w", "util_pct", "vram_mib", "sm_mhz"):
                values = [p["gpu_full_lifetime"].get(s, {}).get(metric) for p in phases]
                # Earlier C1 receipts predate the util field; its original CSV is available.
                if metric == "util_pct" and any(v is None for v in values):
                    values = []
                    for p in phases:
                        phase_name = p["phase"]["id"].removeprefix(progress["id"] + "-")
                        path = ROOT / "results/raw" / progress["id"] / phase_name / "gpu-telemetry.csv"
                        samples = [float(r[5]) for r in csv.reader(path.read_text().splitlines()) if len(r) == 8 and r[1].strip() == str(i)]
                        values.append({"mean": st.mean(samples), "peak": max(samples)})
                values = [v for v in values if v]
                if values:
                    row[metric + "_mean_" + s] = st.mean(v["mean"] for v in values)
                    row[metric + "_peak_" + s] = max(v["peak"] for v in values)
        for key in ("pgmajfault", "pswpin", "pswpout"):
            stats(row, key, [p.get("host_vmstat_delta", {}).get(key) for p in phases])
        live_used, trailing_means, trailing_peaks, trailing_counts = [], [], [], []
        for p in phases:
            snapshot = p.get("host_post_health")
            history = p.get("host_trailing_ram_samples")
            if snapshot is None:
                name = p["phase"]["id"].removeprefix(progress["id"] + "-")
                path = ROOT / "results/raw" / progress["id"] / name / "metrics-after-a.json"
                metrics = json.loads(path.read_text()) if path.exists() else {}
                snapshot = metrics.get("hardware", {})
                history = metrics.get("history", {}).get("ram_used", [])
            if isinstance(snapshot.get("ram_used"), (int, float)):
                live_used.append(snapshot["ram_used"] / 2**30)
            samples = [v / 2**30 for v in (history or []) if isinstance(v, (int, float))]
            if samples:
                trailing_means.append(st.mean(samples)); trailing_peaks.append(max(samples)); trailing_counts.append(len(samples))
        stats(row, "ram_post_health_used_gib", live_used)
        if trailing_means:
            row["ram_trailing_history_mean_gib"] = st.mean(trailing_means)
            row["ram_trailing_history_peak_gib"] = max(trailing_peaks)
            row["ram_trailing_history_samples_min"] = min(trailing_counts)
        cpu = []
        for p in phases:
            name = p["phase"]["id"].removeprefix(progress["id"] + "-")
            path = ROOT / "results/raw" / progress["id"] / name / "vmstat.log"
            if not path.exists():
                continue
            header, samples, first = [], [], True
            for line in path.read_text().splitlines():
                parts = line.split()
                if parts[:3] == ["r", "b", "swpd"]:
                    header = parts
                elif header and len(parts) == len(header) and all(v.replace(".", "", 1).isdigit() for v in parts):
                    if first:
                        first = False  # vmstat's initial row is since boot, not this phase.
                    else:
                        samples.append(dict(zip(header, map(float, parts))))
            if samples:
                cpu.append({k: st.mean(x[k] for x in samples) for k in ("us", "sy", "id", "wa")})
        for key, label in (("us", "cpu_user_pct"), ("sy", "cpu_system_pct"), ("id", "cpu_idle_pct"), ("wa", "cpu_iowait_pct")):
            if cpu:
                row[label] = st.mean(x[key] for x in cpu)
        for when in ("before", "after"):
            cache, available, used = [], [], []
            for p in phases:
                page = p.get("page_cache_" + when, {}).get("fincore", [])
                if page:
                    cache.append(sum(x["res"] for x in page) / 2**30)
                mem = p.get("memory_" + when, "")
                for line in mem.splitlines():
                    if line.startswith("Mem:"):
                        v = line.split()
                        used.append(int(v[2]) / 2**30); available.append(int(v[-1]) / 2**30)
            stats(row, "page_cache_gib_" + when, cache)
            stats(row, "ram_available_gib_" + when, available)
            stats(row, "ram_used_gib_" + when, used)
        rows.append(row)
    rows.sort(key=lambda r: r["arm"])
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with (OUT / "summary.csv").open("w") as f:
        writer = csv.DictWriter(f, fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    (OUT / "summary.json").write_text(json.dumps({"arms": rows, "diagnostics": diagnostic}, indent=2) + "\n")
    fmt = lambda v, n=2: "—" if v is None else f"{v:.{n}f}"
    pair = lambda r, key, n=2: " / ".join(fmt(r.get(key + "_" + s), n) for s in "ab")
    lines = ["# Stage 8 continuation — full metric summary", "",
             "Rows below include completed scored candidates only; incomplete arms retain their explicit status and available valid-batch count. D1 is a separate instrumented diagnostic and is excluded from candidate medians. Historical U1 medians: Prefill 871.0/877.2 tok/s, Decode 25.2/27.7 tok/s, TTFT 146.02/145.01 s. Cache/swap/output/temperature conditions differ; these are descriptive comparisons, not controlled causal gains.", "",
             "| Arm | Status | Prefill A/B tok/s | Decode A/B tok/s | TTFT A/B s | Request wall A/B s | Batch wall s | Output A/B | Decode overlap s |", "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        lines.append(f"| [{r['arm']}]({r['report']}) | {r['status']} | {pair(r, 'prefill_tok_s', 1)} | {pair(r, 'decode_tok_s', 1)} | {pair(r, 'ttft_s')} | {pair(r, 'wall_s')} | {fmt(r.get('batch_wall_s'))} | {pair(r, 'output_tokens', 0)} | {fmt(r.get('decode_overlap_s'))} |")
    lines += ["", "## GPU conditions", "",
              "Means are unweighted averages of each scored batch's full process-lifetime means, including loading/shutdown; peaks are maxima across batches. These are not isolated prefill/decode power measurements. Configured caps stay 150 W and 1110 MHz. Instantaneous readings may exceed the configured power limit.", "",
              "| Arm | Temp mean A/B C | Temp peak A/B C | Power mean A/B W | Power peak A/B W | Util mean A/B % | VRAM mean A/B MiB | VRAM peak A/B MiB | SM mean A/B MHz | SM peak A/B MHz |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        keys = ("temperature_c_mean", "temperature_c_peak", "power_w_mean", "power_w_peak", "util_pct_mean", "vram_mib_mean", "vram_mib_peak", "sm_mhz_mean", "sm_mhz_peak")
        lines.append(f"| {r['arm']} | " + " | ".join(pair(r, key, 1) for key in keys) + " |")
    lines += ["", "## Cache, MTP and physical reads", "",
              "All entries are per-agent medians. MTP counts are accepted/proposed; acceptance is the median of each batch's ratio, not the ratio of median counts. file_mb is API-reported logical expert-read traffic. Physical read MB comes from each engine's own OS counters and must not be summed as unique disk-device traffic. Disk latency/throughput time series remain in each raw iostat.log.", "",
              "| Arm | Expert hit A/B | Actual PCIe share A/B | MTP accepted A/B | MTP proposed A/B | MTP acceptance A/B % | Logical file MB A/B | Physical read MB A/B | KV VRAM hit A/B % |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        keys = ("expert_hit_rate", "actual_pcie_share", "mtp_accepted", "mtp_proposed", "mtp_acceptance_pct", "file_mb", "physical_read_mb", "kv_vram_hit_pct")
        lines.append(f"| {r['arm']} | " + " | ".join(pair(r, key, 3 if key in ('expert_hit_rate', 'actual_pcie_share') else 1) for key in keys) + " |")
    lines += ["", "## Shared host conditions", "",
              "Host rows are whole-host snapshot/counter medians per batch, not independent per-agent RAM. Before/after below mean before container creation and after owned-container cleanup. Active post-health RAM snapshots and trailing sensor history are shown separately. Swap columns are pages in/out during a batch, not total swap occupancy.", "",
              "| Arm | RAM used before/after GiB | RAM available before/after GiB | Tracked page cache before/after GiB | Major faults | Swap in/out pages |", "|---|---:|---:|---:|---:|---:|"]
    for r in rows:
        cells = [f"{fmt(r.get(key+'_before'))} / {fmt(r.get(key+'_after'))}" for key in ("ram_used_gib", "ram_available_gib", "page_cache_gib")]
        lines.append(f"| {r['arm']} | " + " | ".join(cells) + f" | {fmt(r.get('pgmajfault'), 0)} | {fmt(r.get('pswpin'), 0)} / {fmt(r.get('pswpout'), 0)} |")
    lines += ["", "RAM sensors during serving: post-health used is a median across batches, and the history mean averages each batch's trailing sensor mean. History peaks cover only the retained trailing samples (normally 60), not the entire process lifetime.", "",
              "| Arm | Active post-health RAM used GiB | Trailing history mean GiB | Trailing observed peak GiB | Minimum retained samples/batch |", "|---|---:|---:|---:|---:|"]
    for r in rows:
        lines.append(f"| {r['arm']} | " + " | ".join(fmt(r.get(key)) for key in ("ram_post_health_used_gib", "ram_trailing_history_mean_gib", "ram_trailing_history_peak_gib", "ram_trailing_history_samples_min")) + " |")
    lines += ["", "Whole-host CPU utilization below averages each batch's full process lifetime, including loading; vmstat's since-boot first sample is excluded. These are not per-agent or decode-only CPU rates.", "",
              "| Arm | User % | System % | Idle % | I/O wait % |", "|---|---:|---:|---:|---:|"]
    for r in rows:
        lines.append(f"| {r['arm']} | " + " | ".join(fmt(r.get(key), 1) for key in ("cpu_user_pct", "cpu_system_pct", "cpu_idle_pct", "cpu_iowait_pct")) + " |")
    lines += ["", "Ranges and all individual batches are in [summary.csv](summary.csv), [summary.json](summary.json), and each arm's report/receipts. Raw CPU utilization, disk I/O, GPU samples and post-health evidence are preserved. A mechanical C2 PASS is not semantic quality validation or permission to promote.", ""]
    (OUT / "summary.md").write_text("\n".join(lines))
    print(json.dumps({"completed_exported_arms": [r["arm"] for r in rows], "diagnostics": diagnostic}))


if __name__ == "__main__":
    main()
