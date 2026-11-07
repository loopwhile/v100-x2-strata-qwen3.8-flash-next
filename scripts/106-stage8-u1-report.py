#!/usr/bin/env python3
"""Export sanitized S8-U1 receipts and a report from immutable raw evidence."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import statistics as st


def load(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vm(path):
    return {k: int(v) for k, v in (line.split() for line in path.read_text().splitlines())}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("raw", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    raw, out = args.raw, args.output
    progress = load(raw / "progress.json")
    assert progress["verdict"] == "PASS" and progress["phase"] == "results_saved"
    assert (raw / "verdict").read_text().strip() == "PASS"
    assert not out.exists(), "Refuse to overwrite an existing result export"
    rows = []
    for n in range(1, 4):
        d = raw / f"batch-{n}"
        assert (d / "verdict").read_text().strip() == "PASS"
        summary = load(d / "c2/summary.json")
        assert summary["pass_mechanical"] and summary["active_overlap"] and summary["post_health"]
        before, after = vm(d / "vmstat-before.txt"), vm(d / "vmstat-after.txt")
        memory = {k: after[k] - before[k] for k in ("pgmajfault", "pswpin", "pswpout", "pgpgin", "pgpgout")}
        cache = {}
        for phase in ("before", "after"):
            cache[phase] = load(d / f"cache-{phase}.json")["fincore"]
        samples = list(csv.reader((d / "gpu-telemetry.csv").read_text().splitlines()))
        telemetry, engines, processes = {}, {}, {}
        for i, s in enumerate("ab"):
            selected = [r for r in samples if len(r) == 8 and int(r[1]) == i]
            assert selected
            telemetry[s] = {"samples": len(selected)}
            for k, ix in (("temperature_c", 2), ("power_w", 3), ("util_pct", 5), ("vram_mib", 6), ("sm_mhz", 7)):
                vals = [float(r[ix]) for r in selected]
                telemetry[s][k] = {"mean": st.mean(vals), "peak": max(vals), "min": min(vals)}
            assert telemetry[s]["sm_mhz"]["peak"] <= 1110
            assert all(float(r[4]) == 150 for r in selected)
            log = (d / f"logs/agent-{s}.log").read_text(errors="replace")
            mtp = re.findall(r"(\d+) generated in (\d+) ms .*?drafts accepted (\d+) of (\d+)", log)
            engines[s] = {"mtp_windows": [{"output_tokens": int(a), "decode_ms": int(b), "accepted": int(c), "proposed": int(e)} for a, b, c, e in mtp],
                          "runtime_notes": [line for line in log.splitlines() if any(k in line for k in ("PCIe share:", "PCIe probe:", "CPU pool:", "pool workers on", "expert cache auto:", "expert cache ", "prompt path borrows", "prefill plan:", "prefill: chunk", "draft layer loaded", "file tier I/O this request:", "decode expert cache hit rate:", "suffix drafts:", "--lookup-max-t"))]}
            processes[s] = load(d / f"engine-process-{s}.json")
        rows.append({"batch": n, "id": f"{progress['id']}-batch-{n}", "summary": summary,
                     "summary_sha256": digest(d / "c2/summary.json"), "gpu_full_process_lifetime": telemetry,
                     "host_vmstat_delta": memory, "page_cache": cache, "engine": engines,
                     "effective_processes": processes, "config_sha256": load(d / "config-sha256.json")})
    receipt = {"arm": "S8-U1", "id": progress["id"], "image_id": progress["image_id"],
               "source_sha": progress["source_sha"], "engine_sha256": progress["engine_sha256"],
               "runner_sha256": progress["runner_sha256"], "harness_sha256": progress["harness_sha256"],
               "manifest_sha256": progress["manifest_sha256"], "started": progress["started"], "finished": progress["finished"],
               "startup": "PASS_NOT_C2", "c2": "3/3 PASS", "raw_remote": f"results/stage8/S8-U1/{progress['id']}/",
               "assets": load(raw / "assets.json"), "batches": rows}
    lines = ["# Stage 8 S8-U1 — upstream 0.1.57 IQ3_XXS, 2026-11-07", "",
             "Startup and short inference passed; **3/3 fresh-process concurrent 128K C2 PASS**. No baseline rerun, scored retry, promotion or quality-suite claim.", "",
             f"Run `{progress['id']}`; {progress['started']} to {progress['finished']}.", "",
             f"Source `{progress['source_sha']}`; image `{progress['image_id']}`; engine SHA-256 `{progress['engine_sha256']}`.", "",
             "A=GPU0/cpuset 0-2,6-8; B=GPU1/cpuset 3-5,9-11. Ports 18086/18087. Context 131072, INT8 KV/resident 32768, MTP spec4/min-p0.5, auto prefill/cache, mmap experts. SIMT=1, SM70_TABLE=1, PF_WMMA=1. New upstream defaults are recorded in the [source audit](../../docs/STAGE8_SOURCE_AUDIT.md) and effective child environments in the receipts.", "",
             "| Batch | Prefill A/B tok/s | Decode A/B tok/s | TTFT A/B s | Output A/B | Overlap s | Wall s |", "|---|---:|---:|---:|---:|---:|---:|"]
    grouped = {k: {s: [] for s in "ab"} for k in ("prefill_tok_s", "decode_tok_s", "ttft_s")}
    stretch = True
    for row in rows:
        a, b = row["summary"]["requests"]
        for key in grouped:
            for s, req in zip("ab", (a, b)):
                grouped[key][s].append(req[key])
        stretch &= a["decode_tok_s"] >= 30 and b["decode_tok_s"] >= 30
        lines.append(f"| {row['batch']} | {a['prefill_tok_s']:.1f} / {b['prefill_tok_s']:.1f} | {a['decode_tok_s']:.1f} / {b['decode_tok_s']:.1f} | {a['ttft_s']:.2f} / {b['ttft_s']:.2f} | {a['output_tokens']} / {b['output_tokens']} | {row['summary']['decode_overlap_s']:.2f} | {row['summary']['batch_wall_s']:.2f} |")
    receipt["medians"] = {key: {s: st.median(vals) for s, vals in group.items()} for key, group in grouped.items()}
    receipt["decode_30_each_batch_both_agents"] = stretch
    lines += ["", "| Metric | U1 A median (range) | U1 B median (range) | Archived S7-XXS-14 A/B median |", "|---|---:|---:|---:|"]
    historical = {"prefill_tok_s": (997.6, 1006.6), "decode_tok_s": (26.4, 26.2), "ttft_s": (127.53, 126.48)}
    for key, title in (("prefill_tok_s", "Prefill tok/s"), ("decode_tok_s", "Decode tok/s"), ("ttft_s", "TTFT s")):
        vals = grouped[key]
        cells = [f"{st.median(vals[s]):.2f} ({min(vals[s]):.2f}–{max(vals[s]):.2f})" for s in "ab"]
        lines.append(f"| {title} | {cells[0]} | {cells[1]} | {historical[key][0]} / {historical[key][1]} |")
    lines += ["", f"Both-agent >=30 tok/s in every batch: **{'YES (mechanical throughput only; quality pending)' if stretch else 'NO'}**.", "",
              "All prompts are A=126967/B=126968 tokens; no prompt reuse (cache_n=cached_tokens=0), outputs >=1024, finish_reason=stop, synchronized concurrent decode and post-health passed. Per-agent wall time, output hashes, cache hits, MTP counters and runtime share notes are in [receipts](stage8-u1-receipts.json).", "",
              "## GPU and host conditions", "",
              "Telemetry below covers each pair's full process lifetime, including loading and shutdown. It is not isolated prefill/decode power. Configured limits stayed 150 W; SM clocks never exceeded 1110 MHz. Instantaneous power readings can exceed the configured limit.", "",
              "| Batch | GPU | Temp mean/peak C | Power mean/peak W | SM mean/peak MHz | VRAM mean/peak MiB |", "|---|---|---:|---:|---:|---:|"]
    for row in rows:
        for s in "ab":
            t = row["gpu_full_process_lifetime"][s]
            cells = [f"{t[k]['mean']:.1f} / {t[k]['peak']:.1f}" for k in ("temperature_c", "power_w", "sm_mhz", "vram_mib")]
            lines.append(f"| {row['batch']} | {s.upper()} | " + " | ".join(cells) + " |")
    lines += ["", "| Batch | Major faults | Swap in/out pages | Page cache before/after GiB (GGUF + dense) |", "|---|---:|---:|---:|"]
    for row in rows:
        v = row["host_vmstat_delta"]
        cache = {p: sum(f["res"] for f in files) / 2**30 for p, files in row["page_cache"].items()}
        lines.append(f"| {row['batch']} | {v['pgmajfault']} | {v['pswpin']} / {v['pswpout']} | {cache['before']:.2f} / {cache['after']:.2f} |")
    lines += ["", "## Interpretation and preservation", "",
              "**No verified overall upgrade; the dual-agent 30 tok/s goal was not met.** Against the archived medians, descriptive differences are Prefill A/B -12.7%/-12.9%, Decode -4.5%/+5.7%, and TTFT +14.5%/+14.6%. The B-only decode difference does not establish an overall gain. All three measured batches, including the first, remain in the median; none is discarded as warmup.", "",
              "Comparison to S7-XXS-14 is descriptive across dates, not a controlled causal engine speedup. Model checksum reads populate Linux page cache, and this host rebooted before preparation. Page cache, swap, output lengths/MTP acceptance, temperature and actual throttling differ across runs. Logical file_mb is not physical SSD traffic. MTP counters and identical-output comparisons must be considered before interpreting decode deltas. No quality validation follows from mechanical C2 PASS.", "",
              "A separate initial preparation attempt, `u1-20261107T124317`, passed short inference but stopped before allocating or launching any C2 because a bind probe misidentified its own TIME_WAIT sockets as occupied ports. Its original progress/logs and 43-file verified backup are retained; see [preparation failure](preparation-failure.json). A new ID used the corrected listener check for the three scored batches above. There were two unscored startup checks in total and exactly three scored C2 batches; no scored retry or reused ID.", "",
              "All 173 files of the completed run match the P520 originals by SHA-256 in the ThinkPad backup. Candidate decisions and evidence limits are documented in the [Stage 8 review](../../docs/STAGE8_REVIEW.md).", "",
              "Historical containers/images/models and all prior results are preserved. Initial serving state was empty; owned Stage 8 containers are stopped and retained. Serving 8080/8081, ThinkPad tunnel/18080/18081, power, clock and host settings were untouched. Raw data remain on P520 and have a checksum-verified ThinkPad backup. Conditional C/M arms require evidence from this review; none is implied by retaining the runner.", "",
              f"Raw P520: `{receipt['raw_remote']}`. Immutable sanitized metrics and provenance: [receipts](stage8-u1-receipts.json)."]
    out.mkdir(parents=True)
    (out / "stage8-u1-receipts.json").write_text(json.dumps(receipt, indent=2) + "\n")
    (out / "stage8-u1-report.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"run": progress["id"], "medians": receipt["medians"], "decode_30_each_batch_both_agents": stretch}, indent=2))


if __name__ == "__main__":
    main()
