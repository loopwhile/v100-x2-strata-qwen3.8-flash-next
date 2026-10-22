#!/usr/bin/env bash
set -euo pipefail

# Host GPU0/A = IQ3_XXS; host GPU1/B = IQ2_XS; no SM70_TABLE tuning.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="strata-v100-upstream:0.1.47"
A_NAME="strata-s4b-mixed-iq3xxs-agent-a"
B_NAME="strata-s4b-mixed-iq2xs-agent-b"

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

# Reject unrelated image revisions even if the Docker tag was reused.
EXPECTED_ID="sha256:19c3b72a1097486eeae3fd9b964179a36a1c137615e5c93f6d6e70eacdab8e9d"
# Check required existing models/packs (never download or repack).
for f in \
 /srv/models/strata-iq3xxs/pack/iq3_xxs-native/tokenizer/vocab.json \
 /srv/models/strata-iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf \
 /srv/models/strata-iq3xxs/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf \
 /srv/models/strata-iq2xs/pack/iq2_xs-native/tokenizer/vocab.json \
 /srv/models/strata-iq2xs/model/Qwen3.8-Flash-Next-GSQ-RCO-IQ2_XS-00001-of-00002.gguf \
 /srv/models/strata-iq2xs/model/Qwen3.8-Flash-Next-GSQ-RCO-IQ2_XS-00002-of-00002.gguf \
 /srv/models/strata-data/mtp/rt \
 "$ROOT/artifacts/stage4-configs-20261021/mixed/strata-s4b-mixed-iq3xxs-agent-a.json" "$ROOT/artifacts/stage4-configs-20261021/mixed/strata-s4b-mixed-iq2xs-agent-b.json"; do
  [ -e "$f" ] || { echo "ERROR: missing required frozen asset $f" >&2; exit 1; }
done

# Check image existence
docker image inspect "$IMAGE" >/dev/null 2>&1 || {
  echo "ERROR: Image $IMAGE does not exist. Run scripts/59-docker-build-upstream-0.1.47.sh first." >&2
  exit 1
}

# Never remove prior containers: allow explicit reuse with docker start after inspection.
for c in "$A_NAME" "$B_NAME"; do
  if docker container inspect "$c" >/dev/null 2>&1; then
    echo "ERROR: $c already exists; will NOT replace it. Inspect, or docker start the stopped container." >&2
    exit 1
  fi
done

mkdir -p "$ROOT/results/stage4b-mixed/logs"
ACTUAL_ID="$(docker image inspect --format '{{.Id}}' "$IMAGE")"
[ "$ACTUAL_ID" = "$EXPECTED_ID" ] || { echo "ERROR: unexpected image ID: $ACTUAL_ID" >&2; exit 1; }
if [ "${1:-}" = "--preflight" ]; then
  echo "[ok] Mixed A/B model assets, config files and pinned Stage 4-B image verified."
  echo "No running containers, power settings or SSH tunnel were changed."
  exit 0
fi
echo "Starting Stage 4-B MIXED IQ3_XXS Agent A on Host GPU 0 (cpus: 0-2,6-8, port: 8080) ..."
docker run -d \
  --name "$A_NAME" \
  --cpuset-cpus "0-2,6-8" \
  --gpus '"device=0"' \
  -p 127.0.0.1:8080:8080 \
  -v /srv/models/strata-iq3xxs:/iq3xxs:ro \
  -v "$ROOT/results/stage4b-mixed/logs:/mixed-logs" \
  -v /srv/models/strata-data/mtp:/shared-mtp:ro \
  -v "$ROOT/artifacts/stage4-configs-20261021/mixed/strata-s4b-mixed-iq3xxs-agent-a.json:/opt/strata/config.json:ro" \
  --restart no \
  --entrypoint /opt/strata/.venv/bin/python \
  "$IMAGE" \
  /opt/strata/serve/server.py \
    --engine strata \
    --config /opt/strata/config.json \
    --host 0.0.0.0 \
    --port 8080

echo "Starting Stage 4-B MIXED IQ2_XS Agent B on Host GPU 1 (cpus: 3-5,9-11, port: 8081) ..."
docker run -d \
  --name "$B_NAME" \
  --cpuset-cpus "3-5,9-11" \
  --gpus '"device=1"' \
  -p 127.0.0.1:8081:8080 \
  -v /srv/models/strata-iq2xs:/iq2:ro \
  -v "$ROOT/results/stage4b-mixed/logs:/mixed-logs" \
  -v /srv/models/strata-data/mtp:/shared-mtp:ro \
  -v "$ROOT/artifacts/stage4-configs-20261021/mixed/strata-s4b-mixed-iq2xs-agent-b.json:/opt/strata/config.json:ro" \
  --restart no \
  --entrypoint /opt/strata/.venv/bin/python \
  "$IMAGE" \
  /opt/strata/serve/server.py \
    --engine strata \
    --config /opt/strata/config.json \
    --host 0.0.0.0 \
    --port 8080

echo
echo "Stage 4-B containers launched. Waiting for health checks ..."
for pair in "A http://127.0.0.1:8080 qwen3.8-flash-next-iq3_xxs-s4b-mixed-a" "B http://127.0.0.1:8081 qwen3.8-flash-next-iq2_xs-s4b-mixed-b"; do
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

echo "Stage 4-B MIXED agents healthy. ThinkPad tunnel: A=18080 IQ3_XXS; B=18081 IQ2_XS."
