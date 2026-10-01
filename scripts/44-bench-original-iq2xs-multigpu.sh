#!/usr/bin/env bash
set -euo pipefail

# Long-context benchmark for the original Qwen3.8-Flash-Next IQ2_XS
# 2x V100 single-server configuration.
#
# Run one target at a time so RAM/VRAM/engine health can be checked between
# increasingly large prompts:
#   bash scripts/44-bench-original-iq2xs-multigpu.sh 32000
#   bash scripts/44-bench-original-iq2xs-multigpu.sh 64000
#   bash scripts/44-bench-original-iq2xs-multigpu.sh 125000

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${STRATA_DOCKER_IMAGE:-strata-v100:0.1.31}"
IQ2XS_ROOT="${IQ2XS_ROOT:-$HOME/models/strata-iq2xs}"
CFG="/iq2/config/strata-iq2xs-multigpu.json"
HOST_PORT="${STRATA_IQ2XS_MGPU_PORT:-8080}"
TARGET="${1:-32000}"
MAX_TOKENS="${STRATA_BENCH_MAX_TOKENS:-256}"

case "$TARGET" in
  32000|64000|125000) ;;
  *)
    echo "ERROR: target must be one of: 32000 64000 125000" >&2
    exit 1
    ;;
esac

[ -f "$IQ2XS_ROOT/config/strata-iq2xs-multigpu.json" ] || {
  echo "ERROR: IQ2_XS config is missing." >&2
  exit 1
}

curl -fsS "http://127.0.0.1:$HOST_PORT/health" >/dev/null || {
  echo "ERROR: IQ2_XS server is not healthy on port $HOST_PORT." >&2
  exit 1
}

echo "=== IQ2_XS long-context benchmark ==="
echo "Target user tokens : $TARGET"
echo "Max output tokens  : $MAX_TOKENS"
echo "API                : http://127.0.0.1:$HOST_PORT"
echo

echo "--- before ---"
free -h
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
    --url "http://127.0.0.1:$HOST_PORT" \
    --targets "$TARGET" \
    --max-tokens "$MAX_TOKENS"

echo
echo "--- health after ---"
curl -fsS "http://127.0.0.1:$HOST_PORT/health"
echo
echo
echo "--- metrics summary after ---"
curl -fsS "http://127.0.0.1:$HOST_PORT/metrics" |
python3 -c '
import json, sys
m=json.load(sys.stdin)
e=m.get("engine",{})
r=(m.get("requests") or [{}])[0]
h=m.get("hardware",{})
print("engine.version      =", e.get("version"))
print("engine.context      =", e.get("context"))
print("engine.kv           =", e.get("kv"))
print("engine.kv_resident  =", e.get("kv_resident"))
print("engine.expert_slots =", e.get("expert_slots"))
print("engine.vram_free_mib=", e.get("vram_free_mib"))
print("request.prompt      =", r.get("prompt_tokens"))
print("request.output      =", r.get("output_tokens"))
print("request.prompt_ms   =", r.get("prompt_ms"))
print("request.decode_ms   =", r.get("decode_ms"))
print("request.decode_tok_s=", r.get("decode_tok_s"))
print("request.hit_rate    =", r.get("hit_rate"))
print("request.ram_blobs   =", r.get("ram_blobs"))
print("request.file_blobs  =", r.get("file_blobs"))
print("request.file_mb     =", r.get("file_mb"))
print("hardware.ram_used   =", h.get("ram_used"))
'
echo

echo "--- host after ---"
free -h
nvidia-smi --query-gpu=index,name,memory.used,memory.free,utilization.gpu,power.draw,temperature.gpu \
  --format=csv,noheader
