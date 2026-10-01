#!/usr/bin/env bash
set -euo pipefail

# Concurrent long-context benchmark for two independent original IQ2_XS
# GGUF-in-place mmap agents:
#   Agent A: 127.0.0.1:8080
#   Agent B: 127.0.0.1:8081
#
# Run one target at a time. Start with 32K:
#   bash scripts/51-bench-original-iq2xs-dual-mmap.sh 32000

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${STRATA_DOCKER_IMAGE:-strata-v100:0.1.31}"
IQ2XS_ROOT="${IQ2XS_ROOT:-$HOME/models/strata-iq2xs}"
CFG="/iq2/config/strata-iq2xs-agent-a.json"
A_URL="${STRATA_IQ2XS_AGENT_A_URL:-http://127.0.0.1:8080}"
B_URL="${STRATA_IQ2XS_AGENT_B_URL:-http://127.0.0.1:8081}"
TARGET="${1:-32000}"
MAX_TOKENS="${STRATA_BENCH_MAX_TOKENS:-256}"

case "$TARGET" in
  32000|64000|125000) ;;
  *)
    echo "ERROR: target must be one of: 32000 64000 125000" >&2
    exit 1
    ;;
esac

[ -f "$IQ2XS_ROOT/config/strata-iq2xs-agent-a.json" ] || {
  echo "ERROR: Agent A config is missing." >&2
  exit 1
}
[ -f "$IQ2XS_ROOT/config/strata-iq2xs-agent-b.json" ] || {
  echo "ERROR: Agent B config is missing." >&2
  exit 1
}
if [ -e "$IQ2XS_ROOT/pack/iq2_xs-native/experts.bin" ]; then
  echo "ERROR: experts.bin exists; this is no longer the intended GGUF-in-place test." >&2
  exit 1
fi

check_health() {
  local url="$1" expected="$2"
  curl -fsS "$url/health" |
    python3 -c '
import json,sys
want=sys.argv[1]
h=json.load(sys.stdin)
if h.get("status") != "ok" or not h.get("loaded"):
    raise SystemExit("server is not healthy/loaded")
if h.get("model") != want:
    raise SystemExit("wrong model: " + str(h.get("model")) + " != " + want)
print(h)
' "$expected"
}

echo "=== preflight ==="
check_health "$A_URL" "qwen3.8-flash-next-iq2_xs-mmap-a"
check_health "$B_URL" "qwen3.8-flash-next-iq2_xs-mmap-b"
echo

echo "=== IQ2_XS dual mmap benchmark ==="
echo "Target user tokens : $TARGET x 2 concurrently"
echo "Max output tokens  : $MAX_TOKENS per agent"
echo "Agent A            : $A_URL"
echo "Agent B            : $B_URL"
echo

echo "--- before ---"
free -h
echo
nvidia-smi --query-gpu=index,name,memory.used,memory.free,utilization.gpu,power.draw,temperature.gpu \
  --format=csv,noheader
echo

docker run --rm \
  --gpus all \
  --network host \
  -e STRATA_DIR=/opt/strata \
  -v "$ROOT:/work" \
  -v "$IQ2XS_ROOT:/iq2:ro" \
  --entrypoint /opt/strata/.venv/bin/python \
  "$IMAGE" \
  /work/bench/api_bench.py \
    --config "$CFG" \
    --url "$A_URL" \
    --url "$B_URL" \
    --targets "$TARGET" \
    --max-tokens "$MAX_TOKENS" \
    --parallel

echo
echo "--- health after ---"
check_health "$A_URL" "qwen3.8-flash-next-iq2_xs-mmap-a"
check_health "$B_URL" "qwen3.8-flash-next-iq2_xs-mmap-b"

echo
echo "--- newest request / tier summaries ---"
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
h=m.get("hardware",{})
print("  model             =", e.get("model"))
print("  context           =", e.get("context"))
print("  kv                =", e.get("kv"))
print("  kv_resident       =", e.get("kv_resident"))
print("  expert_slots      =", e.get("expert_slots"))
print("  arena_mib         =", e.get("arena_mib"))
print("  vram_free_mib     =", e.get("vram_free_mib"))
print("  prompt            =", r.get("prompt_tokens"))
print("  output            =", r.get("output_tokens"))
print("  prompt_ms         =", r.get("prompt_ms"))
print("  decode_ms         =", r.get("decode_ms"))
print("  decode_tok_s      =", r.get("decode_tok_s"))
print("  hit_rate          =", r.get("hit_rate"))
print("  ram_blobs         =", r.get("ram_blobs"))
print("  file_blobs        =", r.get("file_blobs"))
print("  file_mb           =", r.get("file_mb"))
print("  disk_read_mb      =", h.get("disk_read_mb"))
print("  ram_used          =", h.get("ram_used"))
'
done

echo
echo "--- host after ---"
free -h
echo
nvidia-smi --query-gpu=index,name,memory.used,memory.free,utilization.gpu,power.draw,temperature.gpu \
  --format=csv,noheader
