#!/usr/bin/env python3
"""Run one frozen v100-llm-test-style C2 performance batch against two Strata endpoints.

The workload is the vendored workloads/performance/v1.json from loopwhile/v100-llm-test.
It is materialized with Strata's live tokenizer/chat template, then Project A and
Project B are released through one barrier. No warmup/retry loop is performed here.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import keyword
import re
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STRATA = Path("/opt/strata")
EXPECTED_MANIFEST_SHA256 = "e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca"
IDENTIFIER = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
KEEP_IDENTIFIERS = set(keyword.kwlist) | {"True", "False", "None", "self", "cls"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get_json(url: str, timeout: float = 10.0):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def load_tokenizer_and_template(config_path: Path):
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    tpath = Path(cfg["tokenizer"])
    sys.path[:0] = [str(STRATA), str(STRATA / "tools")]
    from strata_tokenizer import Tokenizer  # type: ignore
    from serve.frontend import ChatTemplate, openai_to_messages  # type: ignore

    vocab = json.loads((tpath / "vocab.json").read_text(encoding="utf-8"))
    tokens = [None] * len(vocab)
    for token, index in vocab.items():
        tokens[index] = token
    tok = Tokenizer(
        tokens,
        (tpath / "merges.txt").read_text(encoding="utf-8").splitlines(),
        json.loads((tpath / "token_type.json").read_text(encoding="utf-8")),
    )
    template = ChatTemplate(tpath / "chat_template.jinja")
    return tok, template, openai_to_messages


def diversify_block(block: str, project_id: str, section: int) -> str:
    suffix = f"_{project_id.lower()}_{section:06d}"

    def replace(match):
        word = match.group(0)
        if word in KEEP_IDENTIFIERS or word.startswith("__"):
            return word
        return word + suffix

    return IDENTIFIER.sub(replace, block)


def render(spec: dict, units: int, pad_units: int = 0, *, diversify_identifiers: bool = False) -> str:
    blocks = spec.get("padding_blocks") or spec.get("seed_blocks")
    anchors = spec.get("anchor_blocks") or []
    parts = [
        f"# {spec['title']}\n",
        f"# project_id={spec['project_id']}\n",
        "# Synthetic deterministic benchmark material follows.\n",
    ]
    for i, anchor in enumerate(anchors, 1):
        parts.append(f"\n# === {spec['project_id']} GROUND-TRUTH ANCHOR {i:02d} ===\n{anchor.rstrip()}\n")
    for i in range(units):
        block = blocks[i % len(blocks)]
        block = block.replace("{{SECTION}}", f"{i + 1:06d}").replace("{{PROJECT}}", spec["project_id"])
        if diversify_identifiers:
            block = diversify_block(block, spec["project_id"], i + 1)
        parts.append(f"\n# --- {spec['project_id']} SECTION {i + 1:06d} ---\n{block.rstrip()}\n")
    if pad_units:
        marker = f" {spec['project_id']}_PAD"
        parts.append("\n# deterministic calibration padding\n" + marker * pad_units + "\n")
    parts.append("\n# FINAL REQUEST\n" + spec["final_instruction"].strip() + "\n")
    return "".join(parts)


def request_body(content: str, manifest: dict) -> dict:
    return {
        "model": "strata",
        "messages": [{"role": "user", "content": content}],
        "max_tokens": manifest["output_tokens"],
        "temperature": manifest.get("sampling", {}).get("temperature", 0),
        "top_p": manifest.get("sampling", {}).get("top_p", 1),
        "seed": manifest.get("sampling", {}).get("seed", 520),
        "reasoning_effort": "none",
        "stream": True,
        "stream_options": {"include_usage": True},
    }


def post_template_count(req: dict, tok, template, openai_to_messages) -> int:
    messages, tools, kwargs = openai_to_messages(req)
    prompt = template.render(messages, tools, **kwargs)
    return len(tok.encode(prompt, parse_special=True))


def materialize_one(manifest: dict, spec: dict, tok, template, openai_to_messages):
    context = int(manifest["context_tokens"])
    reserve = int(manifest["output_tokens"])
    target = context - reserve
    minimum_total = int(context * float(manifest.get("min_context_utilization", 0.99)))
    diversify = bool(manifest.get("diversify_identifiers", False))

    def count_text(text: str) -> int:
        return post_template_count(request_body(text, manifest), tok, template, openai_to_messages)

    low = high = 1
    while True:
        n = count_text(render(spec, high, diversify_identifiers=diversify))
        if n > target:
            break
        low = high
        high *= 2
        if high > 131072:
            raise RuntimeError("unable to bracket prompt target")

    best_units = low
    lo, hi = low, high - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        n = count_text(render(spec, mid, diversify_identifiers=diversify))
        if n <= target:
            best_units = mid
            lo = mid + 1
        else:
            hi = mid - 1

    base = render(spec, best_units, diversify_identifiers=diversify)
    base_tokens = count_text(base)
    best_pad = 0
    lo, hi = 0, max(256, (target - base_tokens) * 4 + 256)
    while lo <= hi:
        mid = (lo + hi) // 2
        n = count_text(render(spec, best_units, mid, diversify_identifiers=diversify))
        if n <= target:
            best_pad = mid
            lo = mid + 1
        else:
            hi = mid - 1

    content = render(spec, best_units, best_pad, diversify_identifiers=diversify)
    req = request_body(content, manifest)
    prompt_tokens = post_template_count(req, tok, template, openai_to_messages)
    total = prompt_tokens + reserve
    if total > context or total < minimum_total:
        raise RuntimeError(f"bad calibrated budget: prompt={prompt_tokens} total={total}")

    raw_hash = sha256_bytes(
        json.dumps(req["messages"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    return {
        "id": spec["id"],
        "project_id": spec["project_id"],
        "request": req,
        "prompt_tokens": prompt_tokens,
        "reserved_output_tokens": reserve,
        "minimum_output_tokens": int(manifest.get("min_output_tokens", 1)),
        "total_budget_used": total,
        "utilization": total / context,
        "raw_prompt_sha256": raw_hash,
        "section_units": best_units,
        "padding_units": best_pad,
    }


def stream_complete(base: str, payload: dict, barrier: threading.Barrier, origin: float):
    barrier.wait(timeout=60)
    submitted = time.perf_counter()
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        base.rstrip("/") + "/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        method="POST",
    )

    first = None
    finish = None
    usage = None
    timings = None
    text_parts = []
    with urllib.request.urlopen(req, timeout=7200) as response:
        for raw in response:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
            except json.JSONDecodeError:
                continue
            usage = chunk.get("usage") or usage
            timings = chunk.get("timings") or timings
            for choice in chunk.get("choices") or []:
                finish = choice.get("finish_reason") or finish
                delta = choice.get("delta") or {}
                piece = (delta.get("content") or "") + (delta.get("reasoning_content") or "")
                if piece:
                    if first is None:
                        first = time.perf_counter()
                    text_parts.append(piece)

    ended = time.perf_counter()
    return {
        "base_url": base,
        "submitted_s": submitted - origin,
        "first_abs": first,
        "end_abs": ended,
        "ttft_s": None if first is None else first - submitted,
        "wall_s": ended - submitted,
        "finish_reason": finish or "stop",
        "usage": usage or {},
        "timings": timings or {},
        "text": "".join(text_parts),
    }


def newest_request(base: str):
    metrics = get_json(base.rstrip("/") + "/metrics", timeout=30)
    return metrics, ((metrics.get("requests") or [{}])[0])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url-a", default="http://127.0.0.1:8080")
    ap.add_argument("--url-b", default="http://127.0.0.1:8081")
    ap.add_argument("--config", type=Path, default=Path("/iq2/config/strata-iq2xs-agent-a.json"))
    ap.add_argument("--manifest", type=Path, default=ROOT / "bench/workloads/v100-performance-v1.json")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=False)

    manifest_bytes = args.manifest.read_bytes()
    manifest_sha = sha256_bytes(manifest_bytes)
    if manifest_sha != EXPECTED_MANIFEST_SHA256:
        raise SystemExit(
            f"manifest SHA256 mismatch: {manifest_sha} != {EXPECTED_MANIFEST_SHA256}"
        )
    manifest = json.loads(manifest_bytes)
    if manifest.get("workload_id") != "V100-PERFORMANCE-C2-128K-v1":
        raise SystemExit("wrong workload_id")
    if manifest.get("output_tokens") != 4096 or manifest.get("min_output_tokens") != 1024:
        raise SystemExit("workload output contract changed")

    for base, expected in (
        (args.url_a, "qwen3.8-flash-next-iq2_xs-mmap-a"),
        (args.url_b, "qwen3.8-flash-next-iq2_xs-mmap-b"),
    ):
        h = get_json(base + "/health")
        if h.get("status") != "ok" or not h.get("loaded") or h.get("model") != expected:
            raise SystemExit(f"bad health for {base}: {h}")

    tok, template, openai_to_messages = load_tokenizer_and_template(args.config)
    materialized = [
        materialize_one(manifest, spec, tok, template, openai_to_messages)
        for spec in manifest["requests"]
    ]
    if len({x["raw_prompt_sha256"] for x in materialized}) != 2:
        raise SystemExit("C2 prompt hashes are not independent")

    before = {
        "health_a": get_json(args.url_a + "/health"),
        "health_b": get_json(args.url_b + "/health"),
        "metrics_a": get_json(args.url_a + "/metrics", timeout=30),
        "metrics_b": get_json(args.url_b + "/metrics", timeout=30),
    }
    (args.out / "before.json").write_text(json.dumps(before, indent=2) + "\n")
    (args.out / "workload.json").write_text(
        json.dumps(
            {
                "source_manifest_sha256": manifest_sha,
                "workload_id": manifest["workload_id"],
                "items": [
                    {k: v for k, v in x.items() if k != "request"}
                    | {"request_sha256": sha256_bytes(json.dumps(x["request"], ensure_ascii=False, sort_keys=True).encode())}
                    for x in materialized
                ],
            },
            indent=2,
        )
        + "\n"
    )
    (args.out / "payload-a.json").write_text(json.dumps(materialized[0]["request"], ensure_ascii=False) + "\n")
    (args.out / "payload-b.json").write_text(json.dumps(materialized[1]["request"], ensure_ascii=False) + "\n")

    sampler_stop = threading.Event()
    samples = []

    def sampler():
        while not sampler_stop.is_set():
            row = {"t": time.perf_counter()}
            for label, base in (("a", args.url_a), ("b", args.url_b)):
                try:
                    row[label] = get_json(base + "/status", timeout=2)
                except Exception as exc:
                    row[label] = {"error": repr(exc)}
            samples.append(row)
            sampler_stop.wait(0.2)

    st = threading.Thread(target=sampler, daemon=True)
    st.start()
    barrier = threading.Barrier(2)
    origin = time.perf_counter()
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            fa = pool.submit(stream_complete, args.url_a, materialized[0]["request"], barrier, origin)
            fb = pool.submit(stream_complete, args.url_b, materialized[1]["request"], barrier, origin)
            ra = fa.result()
            rb = fb.result()
    finally:
        sampler_stop.set()
        st.join(timeout=2)

    for result, item in zip((ra, rb), materialized):
        usage = result["usage"]
        actual_prompt = usage.get("prompt_tokens")
        actual_output = usage.get("completion_tokens")
        result["expected_prompt_tokens"] = item["prompt_tokens"]
        result["prompt_count_match"] = actual_prompt == item["prompt_tokens"]
        result["minimum_output_pass"] = isinstance(actual_output, int) and actual_output >= item["minimum_output_tokens"]
        result["nonempty_output"] = bool(result["text"].strip())
        result["text_sha256"] = sha256_bytes(result["text"].encode("utf-8"))

    decode_start = max(x["first_abs"] for x in (ra, rb) if x["first_abs"] is not None)
    decode_end = min(ra["end_abs"], rb["end_abs"])
    decode_overlap_s = max(0.0, decode_end - decode_start)
    both_busy_samples = 0
    both_answering_samples = 0
    if decode_overlap_s > 0:
        for row in samples:
            if decode_start <= row["t"] <= decode_end:
                a = row.get("a") or {}
                b = row.get("b") or {}
                if a.get("busy") and b.get("busy"):
                    both_busy_samples += 1
                if a.get("phase") == "answering" and b.get("phase") == "answering":
                    both_answering_samples += 1

    ma, la = newest_request(args.url_a)
    mb, lb = newest_request(args.url_b)
    after = {
        "health_a": get_json(args.url_a + "/health"),
        "health_b": get_json(args.url_b + "/health"),
        "metrics_a": ma,
        "metrics_b": mb,
    }
    (args.out / "after.json").write_text(json.dumps(after, indent=2) + "\n")
    (args.out / "status-samples.json").write_text(json.dumps(samples, indent=2) + "\n")

    submission_skew = abs(ra["submitted_s"] - rb["submitted_s"])
    batch_wall = max(ra["end_abs"], rb["end_abs"]) - origin
    summary = {
        "workload_id": manifest["workload_id"],
        "manifest_sha256": manifest_sha,
        "warmup_count": 0,
        "measured_repetitions": 1,
        "submission_skew_s": submission_skew,
        "batch_wall_s": batch_wall,
        "decode_overlap_s": decode_overlap_s,
        "both_busy_samples": both_busy_samples,
        "both_answering_samples": both_answering_samples,
        "requests": [],
    }

    for label, result, last in (("A", ra, la), ("B", rb, lb)):
        timings = result.get("timings") or {}
        usage = result.get("usage") or {}
        details = usage.get("prompt_tokens_details") or {}
        summary["requests"].append(
            {
                "label": label,
                "prompt_tokens": usage.get("prompt_tokens"),
                "expected_prompt_tokens": result.get("expected_prompt_tokens"),
                "output_tokens": usage.get("completion_tokens"),
                "finish_reason": result.get("finish_reason"),
                "wall_s": result.get("wall_s"),
                "ttft_s": result.get("ttft_s"),
                "prefill_tok_s": timings.get("prompt_per_second"),
                "decode_tok_s": timings.get("predicted_per_second"),
                "cache_n": timings.get("cache_n"),
                "cached_tokens": details.get("cached_tokens"),
                "expert_hit_rate": last.get("hit_rate"),
                "file_mb": last.get("file_mb"),
                "ram_blobs": last.get("ram_blobs"),
                "file_blobs": last.get("file_blobs"),
                "prompt_count_match": result.get("prompt_count_match"),
                "minimum_output_pass": result.get("minimum_output_pass"),
                "nonempty_output": result.get("nonempty_output"),
                "text_sha256": result.get("text_sha256"),
            }
        )

    summary["pass_mechanical"] = all(
        r["prompt_count_match"] and r["minimum_output_pass"] and r["nonempty_output"]
        for r in summary["requests"]
    )
    summary["active_overlap"] = decode_overlap_s > 0 and both_busy_samples > 0
    summary["post_health"] = bool(
        after["health_a"].get("loaded") and after["health_b"].get("loaded")
    )

    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    print("=== frozen C2 performance/v1 materialization ===")
    for x in materialized:
        print(
            f"{x['project_id']}: prompt={x['prompt_tokens']} reserve={x['reserved_output_tokens']} "
            f"total={x['total_budget_used']} util={x['utilization']:.5f} "
            f"sha={x['raw_prompt_sha256']}"
        )
    print()
    print("=== measured C2 batch ===")
    print(f"submission_skew_s={submission_skew:.6f}")
    print(f"batch_wall_s={batch_wall:.3f}")
    print(f"decode_overlap_s={decode_overlap_s:.3f}")
    print(f"both_busy_samples={both_busy_samples}")
    print(f"both_answering_samples={both_answering_samples}")
    for r in summary["requests"]:
        print(
            f"{r['label']}: prompt={r['prompt_tokens']} output={r['output_tokens']} "
            f"wall={r['wall_s']:.3f}s ttft={r['ttft_s']:.3f}s "
            f"prefill={r['prefill_tok_s']} tok/s decode={r['decode_tok_s']} tok/s "
            f"cache_n={r['cache_n']} cached_tokens={r['cached_tokens']} "
            f"expert_hit={r['expert_hit_rate']} file_mb={r['file_mb']} "
            f"min1024={r['minimum_output_pass']}"
        )
    print()
    print(f"mechanical_pass={summary['pass_mechanical']}")
    print(f"active_overlap={summary['active_overlap']}")
    print(f"post_health={summary['post_health']}")
    print(f"saved={args.out}")

    return 0 if summary["pass_mechanical"] and summary["active_overlap"] and summary["post_health"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
