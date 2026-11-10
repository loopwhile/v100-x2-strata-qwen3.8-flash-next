#!/usr/bin/env python3
"""Run one frozen v100-llm-test-style C2 performance batch against a SINGLE Strata endpoint (Solo A or Solo B).

Preserves identical prompt materialization and measurement semantics as bench/c2_v100_contract.py,
enabling exact contention and shared-resource comparisons between solo and concurrent serving.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import keyword
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STRATA = Path("/opt/strata")
EXPECTED_MANIFEST_SHA256 = "e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca"
STRATA_CTX_SLACK = 8
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


def diversify_body(code: str, index: int) -> str:
    assigned: dict[str, str] = {}
    anon_counter = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal anon_counter
        name = match.group(0)
        if name in KEEP_IDENTIFIERS:
            return name
        if name not in assigned:
            anon_counter += 1
            assigned[name] = f"v{anon_counter}_t{index}"
        return assigned[name]

    return IDENTIFIER.sub(replace, code)


def render(spec: dict, units: int, pad: int = 0, diversify_identifiers: bool = False) -> str:
    parts = [spec["prefix"]]
    body = spec["repeated_section"]
    if diversify_identifiers:
        body = diversify_body(body, 1)
    parts.extend([body] * units)
    if pad:
        parts.append(spec["padding"] * pad)
    return "\n".join(parts)


def request_body(content: str, manifest: dict) -> dict:
    return {
        "messages": [{"role": "user", "content": content}],
        "max_tokens": manifest.get("output_tokens", 4096),
        "temperature": 0.0,
        "stream": True,
        "chat_template_kwargs": {"enable_thinking": False},
        "extra_body": {
            "reasoning_effort": "none",
            "thinking": {"type": "disabled"},
            "strata_tune": {"adaptive_route": False, "trace": False},
        },
    }


def post_template_count(body: dict, tok, template, openai_to_messages) -> int:
    messages = openai_to_messages(body["messages"])
    rendered = template.render(messages, enable_thinking=False)
    return len(tok.encode(rendered))


def materialize_one(manifest: dict, spec: dict, tok, template, openai_to_messages) -> dict:
    target = int(manifest["effective_target_tokens"])
    reserve = int(manifest.get("output_tokens", 4096))
    context = int(manifest.get("context_limit", 131072))
    minimum_total = int(manifest.get("minimum_total_tokens", 129000))
    diversify = bool(manifest.get("diversify_repeated_identifiers", False))

    def count_units(units: int) -> int:
        req = request_body(render(spec, units, diversify_identifiers=diversify), manifest)
        return post_template_count(req, tok, template, openai_to_messages)

    def count_text(text: str) -> int:
        req = request_body(text, manifest)
        return post_template_count(req, tok, template, openai_to_messages)

    lo, hi = 1, 4096
    best_units = 1
    while lo <= hi:
        mid = (lo + hi) // 2
        n = count_units(mid)
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
    if total + STRATA_CTX_SLACK > context or total < minimum_total:
        raise RuntimeError(
            f"bad calibrated budget: prompt={prompt_tokens} total={total} "
            f"strata_slack={STRATA_CTX_SLACK} context={context}"
        )

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
        "runtime_context_used": total + STRATA_CTX_SLACK,
        "runtime_context_slack": STRATA_CTX_SLACK,
        "utilization": total / context,
        "raw_prompt_sha256": raw_hash,
        "section_units": best_units,
        "padding_units": best_pad,
    }


def stream_complete(base: str, payload: dict, origin: float):
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
    try:
        response_ctx = urllib.request.urlopen(req, timeout=7200)
    except urllib.error.HTTPError as exc:
        body = exc.read(8192).decode("utf-8", "replace")
        raise RuntimeError(f"HTTP {exc.code} from {base}: {body}") from exc
    with response_ctx as response:
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


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--url", required=True, help="Strata base URL (e.g. http://127.0.0.1:18086)")
    p.add_argument("--side", required=True, choices=["a", "b"], help="Agent side: a (Project A) or b (Project B)")
    p.add_argument("--expected-model", required=True)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    manifest_bytes = args.manifest.read_bytes()
    manifest_sha = sha256_bytes(manifest_bytes)
    if manifest_sha != EXPECTED_MANIFEST_SHA256:
        raise SystemExit(f"manifest SHA256 mismatch: {manifest_sha} != {EXPECTED_MANIFEST_SHA256}")
    manifest = json.loads(manifest_bytes)

    h = get_json(args.url.rstrip("/") + "/health")
    if h.get("status") != "ok" or not h.get("loaded") or h.get("model") != args.expected_model:
        raise SystemExit(f"bad health for {args.url}: {h}")

    tok, template, openai_to_messages = load_tokenizer_and_template(args.config)
    spec_idx = 0 if args.side == "a" else 1
    item = materialize_one(manifest, manifest["requests"][spec_idx], tok, template, openai_to_messages)

    before = {
        "health": get_json(args.url.rstrip("/") + "/health"),
        "metrics": get_json(args.url.rstrip("/") + "/metrics", timeout=30),
    }
    (args.out / "before.json").write_text(json.dumps(before, indent=2) + "\n")
    (args.out / f"payload-{args.side}.json").write_text(json.dumps(item["request"], ensure_ascii=False) + "\n")

    origin = time.perf_counter()
    result = stream_complete(args.url, item["request"], origin)

    usage = result["usage"]
    actual_prompt = usage.get("prompt_tokens")
    actual_output = usage.get("completion_tokens")
    result["expected_prompt_tokens"] = item["prompt_tokens"]
    result["prompt_count_match"] = actual_prompt == item["prompt_tokens"]
    result["minimum_output_pass"] = isinstance(actual_output, int) and actual_output >= item["minimum_output_tokens"]
    result["nonempty_output"] = bool(result["text"].strip())
    result["text_sha256"] = sha256_bytes(result["text"].encode("utf-8"))

    (args.out / f"result-{args.side}.json").write_text(json.dumps(result, indent=2) + "\n")
    time.sleep(2)

    after = {
        "health": get_json(args.url.rstrip("/") + "/health"),
        "metrics": get_json(args.url.rstrip("/") + "/metrics", timeout=30),
    }
    (args.out / "after.json").write_text(json.dumps(after, indent=2) + "\n")

    label = args.side.upper()
    timings = result.get("timings") or {}
    last_records = after["metrics"].get("records") or []
    last = last_records[-1] if last_records else {}

    summary = {
        "workload_id": manifest["workload_id"],
        "manifest_sha256": manifest_sha,
        "side": args.side,
        "warmup_count": 0,
        "measured_repetitions": 1,
        "batch_wall_s": result["wall_s"],
        "requests": [
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
                "cached_tokens": (usage.get("prompt_tokens_details") or {}).get("cached_tokens"),
                "expert_hit_rate": last.get("hit_rate"),
                "file_mb": last.get("file_mb"),
                "ram_blobs": last.get("ram_blobs"),
                "file_blobs": last.get("file_blobs"),
                "prompt_count_match": result.get("prompt_count_match"),
                "minimum_output_pass": result.get("minimum_output_pass"),
                "nonempty_output": result.get("nonempty_output"),
                "text_sha256": result.get("text_sha256"),
            }
        ],
        "pass_mechanical": bool(result["prompt_count_match"] and result["minimum_output_pass"] and result["nonempty_output"]),
        "post_health": bool(after["health"].get("loaded")),
    }
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    r = summary["requests"][0]
    print(f"=== solo C2 {label} batch ===")
    print(
        f"{r['label']}: prompt={r['prompt_tokens']} output={r['output_tokens']} "
        f"wall={r['wall_s']:.3f}s ttft={r['ttft_s']:.3f}s "
        f"prefill={r['prefill_tok_s']} tok/s decode={r['decode_tok_s']} tok/s "
        f"expert_hit={r['expert_hit_rate']} file_mb={r['file_mb']} min1024={r['minimum_output_pass']}"
    )
    print(f"mechanical_pass={summary['pass_mechanical']}")
    print(f"post_health={summary['post_health']}")
    return 0 if summary["pass_mechanical"] and summary["post_health"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
