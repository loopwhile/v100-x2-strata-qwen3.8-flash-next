#!/usr/bin/env bash
set -euo pipefail

# One measured C2 run using the frozen v100-llm-test performance/v1 contract.
#
# Differences from the earlier diagnostic 32K/64K/125K sweep:
# - fresh Strata processes via docker restart
# - no inference warmup
# - two distinct Project A/B prompts
# - exact live Strata tokenizer/chat-template calibration
# - 131072 context budget per request
# - 4096 output reserve / minimum 1024 actual output
# - one common-barrier C2 batch, exactly once
# - records prefix-cache reuse separately from Strata expert-cache hit rate

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${STRATA_DOCKER_IMAGE:-strata-v100:0.1.31}"
IQ2XS_ROOT="${IQ2XS_ROOT:-$HOME/models/strata-iq2xs}"
A_NAME="${STRATA_IQ2XS_AGENT_A_NAME:-strata-iq2xs-agent-a}"
B_NAME="${STRATA_IQ2XS_AGENT_B_NAME:-strata-iq2xs-agent-b}"
A_URL="${STRATA_IQ2XS_AGENT_A_URL:-http://127.0.0.1:8080}"
B_URL="${STRATA_IQ2XS_AGENT_B_URL:-http://127.0.0.1:8081}"
MANIFEST="$ROOT/bench/workloads/v100-performance-v1.json"
EXPECTED_SHA="e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca"

[ -f "$MANIFEST" ] || {
  echo "ERROR: missing frozen workload: $MANIFEST" >&2
  exit 1
}

actual_sha="$(sha256sum "$MANIFEST" | awk '{print $1}')"
if [ "$actual_sha" != "$EXPECTED_SHA" ]; then
  echo "ERROR: frozen workload SHA256 mismatch." >&2
  echo "  expected: $EXPECTED_SHA" >&2
  echo "  actual  : $actual_sha" >&2
  exit 1
fi

for n in "$A_NAME" "$B_NAME"; do
  docker inspect "$n" >/dev/null 2>&1 || {
    echo "ERROR: required container is missing: $n" >&2
    exit 1
  }
done

docker image inspect "$IMAGE" >/dev/null 2>&1 || {
  echo "ERROR: Docker image not found: $IMAGE" >&2
  exit 1
}

echo "=== Frozen C2 performance contract ==="
echo "Workload        : V100-PERFORMANCE-C2-128K-v1"
echo "Manifest SHA256 : $actual_sha"
echo "Context/request : 131072"
echo "Output reserve  : 4096"
echo "Minimum output  : 1024"
echo "Projects        : independent A + B"
echo "Measured runs   : 1"
echo "Full-size warmup: 0"
echo

echo "=== Host before fresh-process restart ==="
free -h
echo
nvidia-smi --query-gpu=index,name,memory.used,memory.free,utilization.gpu,power.draw,temperature.gpu \
  --format=csv,noheader
echo

echo "Restarting both validated dual-mmap agents to clear per-process request/prefix state ..."
docker restart "$A_NAME" "$B_NAME" >/dev/null

wait_health() {
  local url="$1"
  local expected="$2"
  local label="$3"
  echo "Waiting for $label ..."
  for _ in $(seq 1 600); do
    if curl -fsS "$url/health" 2>/dev/null |
      python3 -c '
import json,sys
want=sys.argv[1]
try:
    h=json.load(sys.stdin)
except Exception:
    raise SystemExit(1)
raise SystemExit(0 if h.get("status")=="ok" and h.get("loaded") and h.get("model")==want else 1)
' "$expected"
    then
      echo "[ok] $label ready"
      return 0
    fi
    sleep 1
  done
  echo "ERROR: timed out waiting for $label" >&2
  return 1
}

wait_health "$A_URL" "qwen3.8-flash-next-iq2_xs-mmap-a" "Agent A"
wait_health "$B_URL" "qwen3.8-flash-next-iq2_xs-mmap-b" "Agent B"

# Health checks are not inference warmups. Assert that no request has run since restart.
for pair in "A $A_URL" "B $B_URL"; do
  set -- $pair
  label="$1"
  url="$2"
  kept="$(curl -fsS "$url/metrics" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("requests_kept", -1))')"
  if [ "$kept" != "0" ]; then
    echo "ERROR: Agent $label already has $kept completed request(s) after restart." >&2
    echo "       Refusing to call this a no-warmup measured run." >&2
    exit 1
  fi
done

stamp="$(date +%Y%m%d-%H%M%S)"
OUT_HOST="$ROOT/results/c2-v100-contract-$stamp"
OUT_CONT="/work/results/c2-v100-contract-$stamp"

echo
echo "=== Starting exactly one measured C2 batch ==="
echo "Results: $OUT_HOST"
echo

set +e
docker run --rm \
  --network host \
  -e STRATA_DIR=/opt/strata \
  -v "$ROOT:/work" \
  -v "$IQ2XS_ROOT:/iq2:ro" \
  --entrypoint /opt/strata/.venv/bin/python \
  "$IMAGE" \
  /work/bench/c2_v100_contract.py \
    --url-a "$A_URL" \
    --url-b "$B_URL" \
    --config /iq2/config/strata-iq2xs-agent-a.json \
    --manifest /work/bench/workloads/v100-performance-v1.json \
    --out "$OUT_CONT"
rc=$?
set -e

echo
echo "=== Host after measured batch ==="
free -h
echo
nvidia-smi --query-gpu=index,name,memory.used,memory.free,utilization.gpu,power.draw,temperature.gpu \
  --format=csv,noheader

echo
echo "Results directory:"
echo "  $OUT_HOST"
echo "Summary:"
echo "  cat $OUT_HOST/summary.json"
echo
echo "No retry was performed."
exit "$rc"
