#!/usr/bin/env bash
set -euo pipefail

# Stage 5 Agent Startup Script
# Supports T1 (vanilla), T2 (SIMT), T3 (WMMA), T4 (combined), T5 (single-agent controls), T6/T7

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${STRATA_DOCKER_IMAGE:-strata-v100-upstream:0.1.47}"
A_NAME="strata-s5-agent-a"
B_NAME="strata-s5-agent-b"
MODE="${1:-both}" # both, a, or b

# Extra environment flags (e.g. STRATA_SELECT_SIMT=1, STRATA_PF_WMMA=1)
EXTRA_DOCKER_ENV=()
if [ -n "${STRATA_SELECT_SIMT:-}" ]; then
  EXTRA_DOCKER_ENV+=("-e" "STRATA_SELECT_SIMT=${STRATA_SELECT_SIMT}")
fi
if [ -n "${STRATA_PF_WMMA:-}" ]; then
  EXTRA_DOCKER_ENV+=("-e" "STRATA_PF_WMMA=${STRATA_PF_WMMA}")
fi
if [ -n "${STRATA_PF_WMMA2:-}" ]; then
  EXTRA_DOCKER_ENV+=("-e" "STRATA_PF_WMMA2=${STRATA_PF_WMMA2}")
fi
if [ -n "${STRATA_PREFILL_TIMING:-}" ]; then
  EXTRA_DOCKER_ENV+=("-e" "STRATA_PREFILL_TIMING=${STRATA_PREFILL_TIMING}")
fi

# Safety check: preserved serving agents must never be overwritten
for preserved in "strata-jmn-iq2xs-agent-a" "strata-jmn-iq2xs-agent-b"; do
  if docker ps --format '{{.Names}}' | grep -qw "$preserved"; then
    echo "ERROR: Preserved serving agent $preserved is currently RUNNING." >&2
    echo "       Stopping production agents requires explicit user approval." >&2
    exit 1
  fi
done

# Check image
docker image inspect "$IMAGE" >/dev/null 2>&1 || {
  echo "ERROR: Image $IMAGE does not exist." >&2
  exit 1
}

# Clean prior Stage 5 test containers if existed (to free ports)
for c in "$A_NAME" "$B_NAME"; do
  if docker ps -a --format '{{.Names}}' | grep -qw "$c"; then
    echo "Cleaning up prior test container: $c"
    docker rm -f "$c" >/dev/null
  fi
done

# Check ports
if [ "$MODE" = "both" ] || [ "$MODE" = "a" ]; then
  if ss -tlnp 2>/dev/null | grep -q ":8080 "; then
    echo "ERROR: Port 8080 is already in use on host." >&2
    exit 1
  fi
fi
if [ "$MODE" = "both" ] || [ "$MODE" = "b" ]; then
  if ss -tlnp 2>/dev/null | grep -q ":8081 "; then
    echo "ERROR: Port 8081 is already in use on host." >&2
    exit 1
  fi
fi

start_agent_a() {
  echo "Starting Stage 5 Agent A on Host GPU 0 (cpus: 0-2,6-8, port: 8080) ..."
  echo "  Image: $IMAGE"
  echo "  Flags: ${EXTRA_DOCKER_ENV[*]:-none}"
  docker run -d \
    --name "$A_NAME" \
    --cpuset-cpus "0-2,6-8" \
    --gpus '"device=0"' \
    -p 127.0.0.1:8080:8080 \
    -v /srv/models/strata-iq3s:/iq3s:ro \
    -v /srv/models/strata-iq3s/logs:/iq3s-logs \
    -v /srv/models/strata-data/mtp:/shared-mtp:ro \
    -v "$ROOT/artifacts/stage5-configs-20261027/iq3s/strata-s5-agent-a.json:/opt/strata/config.json:ro" \
    "${EXTRA_DOCKER_ENV[@]}" \
    --restart no \
    --entrypoint /opt/strata/.venv/bin/python \
    "$IMAGE" \
    /opt/strata/serve/server.py \
      --engine strata \
      --config /opt/strata/config.json \
      --host 0.0.0.0 \
      --port 8080
}

start_agent_b() {
  echo "Starting Stage 5 Agent B on Host GPU 1 (cpus: 3-5,9-11, port: 8081) ..."
  echo "  Image: $IMAGE"
  echo "  Flags: ${EXTRA_DOCKER_ENV[*]:-none}"
  docker run -d \
    --name "$B_NAME" \
    --cpuset-cpus "3-5,9-11" \
    --gpus '"device=1"' \
    -p 127.0.0.1:8081:8080 \
    -v /srv/models/strata-iq3s:/iq3s:ro \
    -v /srv/models/strata-iq3s/logs:/iq3s-logs \
    -v /srv/models/strata-data/mtp:/shared-mtp:ro \
    -v "$ROOT/artifacts/stage5-configs-20261027/iq3s/strata-s5-agent-b.json:/opt/strata/config.json:ro" \
    "${EXTRA_DOCKER_ENV[@]}" \
    --restart no \
    --entrypoint /opt/strata/.venv/bin/python \
    "$IMAGE" \
    /opt/strata/serve/server.py \
      --engine strata \
      --config /opt/strata/config.json \
      --host 0.0.0.0 \
      --port 8080
}

if [ "$MODE" = "both" ] || [ "$MODE" = "a" ]; then
  start_agent_a
fi
if [ "$MODE" = "both" ] || [ "$MODE" = "b" ]; then
  start_agent_b
fi

echo
echo "Waiting for health checks ..."
check_pairs=()
if [ "$MODE" = "both" ] || [ "$MODE" = "a" ]; then
  check_pairs+=("A http://127.0.0.1:8080 qwen3.8-flash-next-iq3_s-s5-a")
fi
if [ "$MODE" = "both" ] || [ "$MODE" = "b" ]; then
  check_pairs+=("B http://127.0.0.1:8081 qwen3.8-flash-next-iq3_s-s5-b")
fi

for pair in "${check_pairs[@]}"; do
  set -- $pair
  label="$1"
  url="$2"
  want="$3"
  echo "Waiting for Agent $label ($url) loaded as $want ..."
  ready=0
  for _ in $(seq 1 120); do
    if curl -fsS "$url/health" 2>/dev/null | python3 -c '
import json, sys
want = sys.argv[1]
try:
    h = json.load(sys.stdin)
except Exception:
    raise SystemExit(1)
raise SystemExit(0 if h.get("status") == "ok" and h.get("loaded") and h.get("model") == want else 1)
' "$want"; then
      echo "[ok] Agent $label ready."
      ready=1
      break
    fi
    sleep 1
  done
  if [ "$ready" -ne 1 ]; then
    echo "ERROR: Timed out waiting for Agent $label." >&2
    exit 1
  fi
done

echo "Stage 5 agents are UP and healthy."
