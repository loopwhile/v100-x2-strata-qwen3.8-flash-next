#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${STRATA_DOCKER_IMAGE:-strata-v100-upstream:0.1.47}"
A_NAME="strata-s4c-iq3s-agent-a"
B_NAME="strata-s4c-iq3s-agent-b"

# Safety checks: ensure live production agents are not overwritten
for old in "strata-jmn-iq2xs-agent-a" "strata-jmn-iq2xs-agent-b"; do
  if docker ps --format '{{.Names}}' | grep -qw "$old"; then
    echo "ERROR: Preserved serving agent $old is currently RUNNING." >&2
    echo "       Stopping production agents requires explicit user approval." >&2
    exit 1
  fi
done

# Ensure ports 8080 and 8081 are free
for p in 8080 8081; do
  if ss -tlnp 2>/dev/null | grep -q ":$p "; then
    echo "ERROR: Port $p is already in use on host." >&2
    exit 1
  fi
done

# Check image existence
docker image inspect "$IMAGE" >/dev/null 2>&1 || {
  echo "ERROR: Image $IMAGE does not exist." >&2
  exit 1
}

# Remove prior containers if existed
for c in "$A_NAME" "$B_NAME"; do
  if docker ps -a --format '{{.Names}}' | grep -qw "$c"; then
    echo "Cleaning up prior container: $c"
    docker rm -f "$c" >/dev/null
  fi
done

echo "Starting Stage 4-C IQ3_S Agent A on Host GPU 0 (cpus: 0-2,6-8, port: 8080, STRATA_SM70_TABLE=1) ..."
docker run -d \
  --name "$A_NAME" \
  --cpuset-cpus "0-2,6-8" \
  --gpus '"device=0"' \
  -e STRATA_SM70_TABLE=1 \
  -p 127.0.0.1:8080:8080 \
  -v /srv/models/strata-iq3s:/iq3s:ro \
  -v /srv/models/strata-iq3s/logs:/iq3s-logs \
  -v /srv/models/strata-data/mtp:/shared-mtp:ro \
  -v "$ROOT/artifacts/stage4-configs-20261021/iq3s/strata-s4c-iq3s-agent-a.json:/opt/strata/config.json:ro" \
  --restart no \
  --entrypoint /opt/strata/.venv/bin/python \
  "$IMAGE" \
  /opt/strata/serve/server.py \
    --engine strata \
    --config /opt/strata/config.json \
    --host 0.0.0.0 \
    --port 8080

echo "Starting Stage 4-C IQ3_S Agent B on Host GPU 1 (cpus: 3-5,9-11, port: 8081, STRATA_SM70_TABLE=1) ..."
docker run -d \
  --name "$B_NAME" \
  --cpuset-cpus "3-5,9-11" \
  --gpus '"device=1"' \
  -e STRATA_SM70_TABLE=1 \
  -p 127.0.0.1:8081:8080 \
  -v /srv/models/strata-iq3s:/iq3s:ro \
  -v /srv/models/strata-iq3s/logs:/iq3s-logs \
  -v /srv/models/strata-data/mtp:/shared-mtp:ro \
  -v "$ROOT/artifacts/stage4-configs-20261021/iq3s/strata-s4c-iq3s-agent-b.json:/opt/strata/config.json:ro" \
  --restart no \
  --entrypoint /opt/strata/.venv/bin/python \
  "$IMAGE" \
  /opt/strata/serve/server.py \
    --engine strata \
    --config /opt/strata/config.json \
    --host 0.0.0.0 \
    --port 8080

echo
echo "Stage 4-C IQ3_S containers launched. Waiting for health checks ..."
for pair in "A http://127.0.0.1:8080 qwen3.8-flash-next-iq3_s-s4c-a" "B http://127.0.0.1:8081 qwen3.8-flash-next-iq3_s-s4c-b"; do
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
    echo "ERROR: Timeout waiting for Agent $label" >&2
    docker logs "$([ "$label" = "A" ] && echo "$A_NAME" || echo "$B_NAME")" | tail -n 30 >&2
    exit 1
  fi
done

echo "Both Stage 4-C IQ3_S agents healthy and ready."
