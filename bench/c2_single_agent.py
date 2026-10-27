#!/usr/bin/env python3
"""
Single-agent C2 benchmark runner for Stage 5 T5 resource contention controls.
Runs Agent A alone or Agent B alone against the frozen C2 prompt, with identical
request constraints and no concurrent peer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
STRATA = Path(os.environ.get("STRATA_DIR", "/opt/strata"))
EXPECTED_MANIFEST_SHA256 = (
    "e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca"
)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def get_json(url: str, timeout: float = 10.0):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def load_tokenizer_and_template(config_path: Path):
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    tpath = Path(cfg["tokenizer"])
    sys.path[:0] = [str(STRATA), str(STRATA / "tools")]
    from strata_tokenizer import Tokenizer  # type: ignore
    from serve.frontend import ChatTemplate, openai_to_messages  # type: ignore

    tok = Tokenizer(str(tpath))
    template = ChatTemplate.from_file(str(tpath / "chat_template.json"))
    return tok, template, openai_to_messages


def stream_complete(url: str, payload: dict, origin: float) -> dict:
    req_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url + "/v1/chat/completions",
        data=req_bytes,
        headers={"Content-Type": "application/json"},
    )
    t0 = time.perf_counter()
    first_token_time = None
    chunks = []
    finish_reason = None
    usage = {}

    with urllib.request.urlopen(req, timeout=1200) as resp:
        for raw in resp:
            line = raw.decode("utf-8").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                msg = json.loads(data)
            except Exception:
                continue
            if first_token_time is None:
                first_token_time = time.perf_counter()
            choice = (msg.get("choices") or [{}])[0]
            delta = choice.get("delta") or {}
            content = delta.get("content")
            if content:
                chunks.append(content)
            if choice.get("finish_reason"):
                finish_reason = choice["finish_reason"]
            if msg.get("usage"):
                usage = msg["usage"]

    t1 = time.perf_counter()
    full_text = "".join(chunks)
    ttft = (first_token_time - t0) if first_token_time else None
    wall = t1 - t0
    prompt_tokens = usage.get("prompt_tokens")
    output_tokens = usage.get("completion_tokens") or len(chunks)
    prefill_tok_s = (prompt_tokens / ttft) if (ttft and prompt_tokens) else None
    gen_time = (t1 - first_token_time) if first_token_time else None
    decode_tok_s = (output_tokens / gen_time) if (gen_time and output_tokens) else None

    return {
        "wall_s": wall,
        "ttft_s": ttft,
        "prefill_tok_s": round(prefill_tok_s, 2) if prefill_tok_s else None,
        "decode_tok_s": round(decode_tok_s, 2) if decode_tok_s else None,
        "finish_reason": finish_reason,
        "usage": usage,
        "text": full_text,
        "start_abs": t0,
        "first_abs": first_token_time,
        "end_abs": t1,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8080")
    ap.add_argument("--expected-model", default="qwen3.8-flash-next-iq3_s-s5-a")
    ap.add_argument("--agent", choices=["a", "b"], default="a")
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, default=ROOT / "bench/workloads/v100-performance-v1.json")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=False)

    manifest_bytes = args.manifest.read_bytes()
    manifest_sha = sha256_bytes(manifest_bytes)
    if manifest_sha != EXPECTED_MANIFEST_SHA256:
        raise SystemExit(f"manifest SHA256 mismatch: {manifest_sha} != {EXPECTED_MANIFEST_SHA256}")
    manifest = json.loads(manifest_bytes)

    h = get_json(args.url + "/health")
    if h.get("status") != "ok" or not h.get("loaded") or h.get("model") != args.expected_model:
        raise SystemExit(f"bad health for {args.url}: {h}")

    tok, template, openai_to_messages = load_tokenizer_and_template(args.config)
    spec_idx = 0 if args.agent == "a" else 1
    spec = manifest["requests"][spec_idx]

    # Materialize request
    from bench.c2_v100_contract import materialize_one
    item = materialize_one(manifest, spec, tok, template, openai_to_messages)

    before = {
        "health": get_json(args.url + "/health"),
        "metrics": get_json(args.url + "/metrics", timeout=30),
    }
    (args.out / "before.json").write_text(json.dumps(before, indent=2) + "\n")
    (args.out / "payload.json").write_text(json.dumps(item["request"], ensure_ascii=False) + "\n")

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

    after = {
        "health": get_json(args.url + "/health"),
        "metrics": get_json(args.url + "/metrics", timeout=30),
    }
    (args.out / "after.json").write_text(json.dumps(after, indent=2) + "\n")

    status_snap = get_json(args.url + "/status")
    status_item = (status_snap.get("items") or [{}])[0]
    metrics_diff = (after["metrics"].get("requests_kept") or 0) - (before["metrics"].get("requests_kept") or 0)

    summary = {
        "workload_id": manifest["workload_id"],
        "manifest_sha256": manifest_sha,
        "agent": args.agent,
        "prompt_tokens": actual_prompt,
        "output_tokens": actual_output,
        "finish_reason": result["finish_reason"],
        "wall_s": result["wall_s"],
        "ttft_s": result["ttft_s"],
        "prefill_tok_s": result["prefill_tok_s"],
        "decode_tok_s": result["decode_tok_s"],
        "cache_n": status_item.get("cache_n", 0),
        "cached_tokens": status_item.get("cached_tokens", 0),
        "expert_hit_rate": status_item.get("expert_hit_rate", 0.0),
        "file_mb": status_item.get("file_mb", 0.0),
        "prompt_count_match": result["prompt_count_match"],
        "minimum_output_pass": result["minimum_output_pass"],
        "nonempty_output": result["nonempty_output"],
        "text_sha256": result["text_sha256"],
        "pass_mechanical": bool(result["prompt_count_match"] and result["minimum_output_pass"] and result["finish_reason"] == "stop"),
        "post_health": bool(after["health"].get("status") == "ok"),
    }

    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if (summary["pass_mechanical"] and summary["post_health"]) else 1


if __name__ == "__main__":
    sys.exit(main())
