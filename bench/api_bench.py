#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STRATA = Path(os.environ.get("STRATA_DIR", ROOT / ".work" / "Strata"))


def load_tokenizer(config_path: Path):
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    tpath = Path(cfg["tokenizer"])
    sys.path.insert(0, str(STRATA / "tools"))
    import strata_tokenizer as ST  # type: ignore

    vocab = json.loads((tpath / "vocab.json").read_text(encoding="utf-8"))
    tokens = [None] * len(vocab)
    for token, index in vocab.items():
        tokens[index] = token
    merges = (tpath / "merges.txt").read_text(encoding="utf-8").split("\n")
    types = json.loads((tpath / "token_type.json").read_text(encoding="utf-8"))
    return ST.Tokenizer(tokens, merges, types)


def make_prompt(tok, target: int) -> tuple[str, int]:
    unit = (
        "The expedition recorded observations of the landscape, atmosphere, rocks, "
        "software systems, measurements, and distant stars. "
        "Keep every detail available for later retrieval.\n"
    )
    suffix = (
        "\nNow summarize the engineering implications in five concise bullet points. "
        "Do not discuss how this benchmark prompt was constructed."
    )
    unit_tokens = len(tok.encode(unit))
    suffix_tokens = len(tok.encode(suffix))
    n = max(1, (target - suffix_tokens) // max(1, unit_tokens))
    text = unit * n + suffix

    # Tighten without ever going above the requested user-content token target.
    count = len(tok.encode(text))
    while count > target and n > 1:
        n -= 1
        text = unit * n + suffix
        count = len(tok.encode(text))
    while True:
        candidate = unit * (n + 1) + suffix
        c = len(tok.encode(candidate))
        if c > target:
            break
        n += 1
        text, count = candidate, c
    return text, count


def get_json(url: str):
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}


def request_one(base: str, prompt: str, max_tokens: int):
    payload = {
        "model": "strata",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_tokens,
        "reasoning_effort": "none",
    }
    req = urllib.request.Request(
        base.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=7200) as r:
            body = json.loads(r.read().decode("utf-8"))
        error = None
    except Exception as e:
        body = None
        error = repr(e)
    elapsed = time.perf_counter() - started
    status = get_json(base.rstrip("/") + "/status")
    return {
        "base_url": base,
        "wall_s": round(elapsed, 3),
        "response": body,
        "error": error,
        "status": status,
    }


def gpu_snapshot():
    cmd = [
        "nvidia-smi",
        "--query-gpu=index,name,memory.used,memory.total,utilization.gpu,power.draw,temperature.gpu",
        "--format=csv,noheader,nounits",
    ]
    try:
        return subprocess.check_output(cmd, text=True, timeout=10).strip().splitlines()
    except Exception as e:
        return [f"nvidia-smi failed: {e}"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", action="append", required=True, help="Base server URL; repeat for multiple servers")
    ap.add_argument("--config", type=Path, default=ROOT / "configs" / "coder-128k-multigpu.json")
    ap.add_argument("--targets", nargs="+", type=int, default=[32000, 64000, 125000],
                    help="Target USER-CONTENT token counts; chat-template overhead is additional")
    ap.add_argument("--max-tokens", type=int, default=256)
    ap.add_argument("--parallel", action="store_true", help="Launch all URLs simultaneously for each target")
    args = ap.parse_args()

    if not args.config.exists():
        raise SystemExit(f"config not found: {args.config}")
    if not STRATA.exists():
        raise SystemExit(f"Strata source not found: {STRATA}")

    tok = load_tokenizer(args.config)
    all_results = {
        "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "config": str(args.config),
        "urls": args.url,
        "parallel": args.parallel,
        "max_tokens": args.max_tokens,
        "runs": [],
    }

    for target in args.targets:
        print(f"\nPreparing target user prompt: {target:,} tokens", flush=True)
        prompt, actual = make_prompt(tok, target)
        print(f"Actual user-content tokens: {actual:,}", flush=True)

        if args.parallel and len(args.url) > 1:
            round_started = time.perf_counter()
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(args.url)) as ex:
                futs = [ex.submit(request_one, u, prompt, args.max_tokens) for u in args.url]
                results = [f.result() for f in futs]
            round_wall = time.perf_counter() - round_started
        else:
            round_started = time.perf_counter()
            results = [request_one(u, prompt, args.max_tokens) for u in args.url]
            round_wall = time.perf_counter() - round_started

        entry = {
            "target_user_tokens": target,
            "actual_user_tokens": actual,
            "round_wall_s": round(round_wall, 3),
            "gpu_after": gpu_snapshot(),
            "servers": results,
        }
        all_results["runs"].append(entry)

        print(f"Round wall: {round_wall:.1f}s")
        for r in results:
            usage = (r.get("response") or {}).get("usage") or {}
            print(
                f"  {r['base_url']}: wall={r['wall_s']}s "
                f"prompt={usage.get('prompt_tokens')} completion={usage.get('completion_tokens')} "
                f"error={r['error']}"
            )
            st = r.get("status") or {}
            if isinstance(st, dict):
                for k in ("phase", "tokens_per_s", "prompt_tokens_per_s", "generated", "elapsed_s"):
                    if k in st:
                        print(f"    status.{k}={st[k]}")

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = ROOT / "results" / f"api-bench-{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(all_results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
