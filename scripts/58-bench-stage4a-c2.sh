#!/usr/bin/env bash
set -euo pipefail

# Stage 4-A C2 128K Performance Benchmark Runner
# Upstream Strata v0.1.44.1 on dual independent V100s.

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${STRATA_DOCKER_IMAGE:-strata-v100-upstream:0.1.44.1}"
IQ2XS_ROOT="${IQ2XS_ROOT:-/srv/models/strata-iq2xs}"
A_NAME="${STRATA_IQ2XS_AGENT_A_NAME:-strata-s4a-iq2xs-agent-a}"
B_NAME="${STRATA_IQ2XS_AGENT_B_NAME:-strata-s4a-iq2xs-agent-b}"
A_MODEL="${STRATA_IQ2XS_AGENT_A_MODEL:-qwen3.8-flash-next-iq2_xs-s4a-a}"
B_MODEL="${STRATA_IQ2XS_AGENT_B_MODEL:-qwen3.8-flash-next-iq2_xs-s4a-b}"
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

echo "=== Frozen C2 performance contract (Stage 4-A) ==="
echo "Engine          : Upstream Strata v0.1.44.1"
echo "Workload        : V100-PERFORMANCE-C2-128K-v1"
echo "Manifest SHA256 : $actual_sha"
echo "Agents          : $A_NAME ($A_MODEL), $B_NAME ($B_MODEL)"
echo "Context/request : 131072"
echo "Output reserve  : 4096"
echo "Minimum output  : 1024"
echo

echo "=== Host before fresh-process restart ==="
free -h
echo
nvidia-smi --query-gpu=index,name,memory.used,memory.free,utilization.gpu,power.draw,temperature.gpu \
  --format=csv,noheader
echo

echo "Restarting both Stage 4-A agents to clear per-process request/prefix state ..."
docker restart "$A_NAME" "$B_NAME" >/dev/null

wait_health() {
  local url="$1"
  local expected="$2"
  local label="$3"
  echo "Waiting for $label ($url, expected $expected) ..."
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

wait_health "$A_URL" "$A_MODEL" "Agent A"
wait_health "$B_URL" "$B_MODEL" "Agent B"

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

RUN_LABEL="${1:-1}"
stamp="$(date +%Y%m%d-%H%M%S)"
OUT_HOST="$ROOT/results/c2-stage4a-v100-contract-$stamp-run$RUN_LABEL"
OUT_CONT="/work/results/c2-stage4a-v100-contract-$stamp-run$RUN_LABEL"
mkdir -p "$ROOT/results"

echo
echo "=== Starting C2 batch (Run #$RUN_LABEL) ==="
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
    --expected-model-a "$A_MODEL" \
    --expected-model-b "$B_MODEL" \
    --config /iq2/config/strata-jmn-iq2xs-agent-a.json \
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
echo "Results directory: $OUT_HOST"
if [ -f "$OUT_HOST/summary.json" ]; then
  echo "Summary:"
  cat "$OUT_HOST/summary.json"
fi
echo
exit "$rc"
