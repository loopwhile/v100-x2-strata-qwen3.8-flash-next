#!/usr/bin/env python3
"""Stage 12 Semantic Quality Suite (anchor recall, coding exec, JSON schema, stop/determinism, garble/NaN)."""
import argparse
import hashlib
import json
import re
import subprocess as sp
import sys
import tempfile
import urllib.request
from pathlib import Path


def chat(url: str, model: str, messages: list[dict], max_tokens: int = 512, stop=None, temperature: float = 0.0):
    body = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 1,
        "seed": 520,
        "reasoning_effort": "none",
    }
    if stop:
        body["stop"] = stop
    req = urllib.request.Request(
        f"{url.rstrip('/')}/v1/chat/completions",
        json.dumps(body).encode("utf-8"),
        {"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)


def check_garbled(text: str) -> tuple[bool, str]:
    if not text or not text.strip():
        return False, "empty_output"
    if "\ufffd" in text or re.search(r"\bNaN\b|\binf\b", text):
        return False, "replacement_or_nan_token"
    tokens = text.split()
    if len(tokens) >= 40:
        grams = [tuple(tokens[i:i + 6]) for i in range(len(tokens) - 5)]
        if grams and (len(grams) - len(set(grams))) / len(grams) > 0.55:
            return False, "excessive_6gram_repetition"
    return True, "ok"


def run_suite(url: str, model: str) -> dict:
    results = []

    # 1. Long-context needle / anchor recall (~16K-20K chars filler + 3 anchors)
    filler = ("The quick verification log records routine telemetry for dual Volta node maintenance.\n" * 60)
    prompt_lc = (
        "Read the full log carefully and answer ONLY with the three values separated by commas.\n"
        "ANCHOR_ALPHA = VOLTA-7913\n" + filler * 4 +
        "ANCHOR_BETA = TITAN-4428\n" + filler * 4 +
        "ANCHOR_GAMMA = STRATA-9051\n" + filler * 3 +
        "\nQuestion: What are ANCHOR_ALPHA, ANCHOR_BETA, ANCHOR_GAMMA in order?"
    )
    r1 = chat(url, model, [{"role": "user", "content": prompt_lc}], max_tokens=128)
    t1 = r1["choices"][0]["message"]["content"]
    g1_ok, g1_msg = check_garbled(t1)
    p1 = g1_ok and all(k in t1 for k in ("VOLTA-7913", "TITAN-4428", "STRATA-9051"))
    results.append({"test": "long_context_anchor_recall", "pass": p1, "garble": g1_msg, "output": t1[:300]})

    # 2. Coding task + live execution test
    prompt_code = (
        "Write ONLY a Python function `def merge_intervals(intervals):` inside a ```python code block "
        "that takes a list of [start, end] integer pairs (possibly unsorted or overlapping) and returns "
        "a sorted list of merged non-overlapping [start, end] lists. Handle empty input."
    )
    r2 = chat(url, model, [{"role": "user", "content": prompt_code}], max_tokens=512)
    t2 = r2["choices"][0]["message"]["content"]
    g2_ok, g2_msg = check_garbled(t2)
    m = re.search(r"```(?:python)?\s*(.*?)```", t2, re.DOTALL)
    code = m.group(1) if m else t2
    code_pass = False
    code_err = ""
    if g2_ok and "def merge_intervals" in code:
        harness = code + "\n" + "\n".join([
            "assert merge_intervals([]) == []",
            "assert merge_intervals([[5,7],[1,3],[2,6],[8,10],[15,18]]) == [[1,7],[8,10],[15,18]]",
            "assert merge_intervals([[1,4],[4,5]]) == [[1,5]]",
            "print('CODE_OK')",
        ])
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
            tf.write(harness)
            tf_path = Path(tf.name)
        try:
            proc = sp.run([sys.executable, str(tf_path)], capture_output=True, text=True, timeout=10)
            code_pass = proc.returncode == 0 and "CODE_OK" in proc.stdout
            code_err = proc.stderr[:200] if not code_pass else ""
        finally:
            tf_path.unlink(missing_ok=True)
    results.append({"test": "coding_exec_merge_intervals", "pass": code_pass, "garble": g2_msg, "err": code_err})

    # 3. JSON schema / structured output
    prompt_json = (
        'Output ONLY valid JSON (no markdown fences) matching schema: '
        '{"gpu_count": 2, "arch": "sm_70", "kv_type": "int8", "tags": ["v100", "dflash2"]}.'
    )
    r3 = chat(url, model, [{"role": "user", "content": prompt_json}], max_tokens=128)
    t3 = r3["choices"][0]["message"]["content"].strip()
    g3_ok, g3_msg = check_garbled(t3)
    json_pass = False
    try:
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", t3, flags=re.DOTALL).strip()
        obj = json.loads(cleaned)
        json_pass = (
            g3_ok and isinstance(obj, dict)
            and obj.get("gpu_count") == 2
            and obj.get("arch") == "sm_70"
            and obj.get("kv_type") == "int8"
            and isinstance(obj.get("tags"), list)
        )
    except Exception as exc:
        g3_msg = repr(exc)
    results.append({"test": "json_schema_parse", "pass": json_pass, "detail": g3_msg, "output": t3[:200]})

    # 4. Stop sequence & greedy determinism (2 runs must match)
    prompt_det = "List integers 1 to 20 separated by commas: 1, 2, "
    r4a = chat(url, model, [{"role": "user", "content": prompt_det}], max_tokens=128, stop=["10"])
    r4b = chat(url, model, [{"role": "user", "content": prompt_det}], max_tokens=128, stop=["10"])
    t4a = r4a["choices"][0]["message"]["content"]
    t4b = r4b["choices"][0]["message"]["content"]
    det_pass = (
        t4a == t4b
        and "10" not in t4a
        and "9" in t4a
        and r4a["choices"][0].get("finish_reason") == "stop"
    )
    results.append({
        "test": "determinism_and_stop",
        "pass": det_pass,
        "hash_a": hashlib.sha256(t4a.encode()).hexdigest()[:12],
        "hash_b": hashlib.sha256(t4b.encode()).hexdigest()[:12],
        "finish_reason": r4a["choices"][0].get("finish_reason"),
    })

    return {
        "url": url,
        "model": model,
        "passed": sum(1 for r in results if r["pass"]),
        "total": len(results),
        "all_pass": all(r["pass"] for r in results),
        "checks": results,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--url-a", required=True)
    p.add_argument("--model-a", required=True)
    p.add_argument("--url-b", required=True)
    p.add_argument("--model-b", required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    out = {
        "agent_a": run_suite(args.url_a, args.model_a),
        "agent_b": run_suite(args.url_b, args.model_b),
    }
    out["all_pass"] = out["agent_a"]["all_pass"] and out["agent_b"]["all_pass"]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"all_pass": out["all_pass"], "a": f"{out['agent_a']['passed']}/{out['agent_a']['total']}", "b": f"{out['agent_b']['passed']}/{out['agent_b']['total']}"}))
    assert out["all_pass"], f"Quality suite failed: {json.dumps(out, indent=2)}"


if __name__ == "__main__":
    main()
