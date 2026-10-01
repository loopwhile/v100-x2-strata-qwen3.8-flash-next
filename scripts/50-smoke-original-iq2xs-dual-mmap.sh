#!/usr/bin/env bash
set -euo pipefail

# Concurrent smoke test for the two independent original IQ2_XS mmap agents.
# Sends one small request to :8080 and :8081 at the same time, then prints
# per-agent timing/tier metrics plus host RAM/GPU state.

A_URL="${STRATA_IQ2XS_AGENT_A_URL:-http://127.0.0.1:8080}"
B_URL="${STRATA_IQ2XS_AGENT_B_URL:-http://127.0.0.1:8081}"

echo "=== preflight ==="
for u in "$A_URL" "$B_URL"; do
  curl -fsS "$u/health"
  echo
done
echo
free -h
echo
nvidia-smi --query-gpu=index,name,memory.used,memory.free,utilization.gpu,power.draw,temperature.gpu \
  --format=csv,noheader
echo

python3 - "$A_URL" "$B_URL" <<'PY'
import concurrent.futures
import json
import sys
import time
import urllib.request
import urllib.error

urls = sys.argv[1:]

def req(base):
    payload = {
        "model": "strata",
        "messages": [{"role": "user", "content": "Reply with exactly: READY"}],
        "temperature": 0,
        "max_tokens": 32,
        "reasoning_effort": "none",
    }
    request = urllib.request.Request(
        base.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=600) as r:
            body = json.loads(r.read().decode("utf-8"))
        err = None
    except Exception as e:
        body = None
        err = repr(e)
    return base, time.perf_counter() - t0, body, err

t0 = time.perf_counter()
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
    rows = list(ex.map(req, urls))
round_wall = time.perf_counter() - t0

print("=== concurrent completions ===")
print(f"round_wall_s = {round_wall:.3f}")
ok = True
for base, wall, body, err in rows:
    print()
    print(base)
    print("  wall_s =", round(wall, 3))
    print("  error  =", err)
    if err or not body:
        ok = False
        continue
    choice = (body.get("choices") or [{}])[0]
    content = ((choice.get("message") or {}).get("content"))
    usage = body.get("usage") or {}
    timings = body.get("timings") or {}
    print("  content        =", repr(content))
    print("  prompt_tokens  =", usage.get("prompt_tokens"))
    print("  output_tokens  =", usage.get("completion_tokens"))
    print("  prefill_tok_s  =", timings.get("prompt_per_second"))
    print("  decode_tok_s   =", timings.get("predicted_per_second"))
    if content != "READY":
        ok = False

if not ok:
    raise SystemExit(2)
PY

echo
echo "=== newest request metrics ==="
for pair in "A $A_URL" "B $B_URL"; do
  set -- $pair
  label="$1"
  url="$2"
  echo "Agent $label:"
  curl -fsS "$url/metrics" | python3 -c '
import json,sys
m=json.load(sys.stdin)
e=m.get("engine",{})
r=(m.get("requests") or [{}])[0]
print("  model          =", e.get("model"))
print("  expert_slots   =", e.get("expert_slots"))
print("  arena_mib      =", e.get("arena_mib"))
print("  vram_free_mib  =", e.get("vram_free_mib"))
print("  prompt         =", r.get("prompt_tokens"))
print("  output         =", r.get("output_tokens"))
print("  decode_tok_s   =", r.get("decode_tok_s"))
print("  hit_rate       =", r.get("hit_rate"))
print("  ram_blobs      =", r.get("ram_blobs"))
print("  file_blobs     =", r.get("file_blobs"))
print("  file_mb        =", r.get("file_mb"))
'
done

echo
echo "=== host after ==="
free -h
echo
nvidia-smi --query-gpu=index,name,memory.used,memory.free,utilization.gpu,power.draw,temperature.gpu \
  --format=csv,noheader
