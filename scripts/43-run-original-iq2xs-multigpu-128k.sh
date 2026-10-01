#!/usr/bin/env bash
set -euo pipefail

# Start the original Qwen3.8-Flash-Next IQ2_XS as one Strata server
# split across both V100s. Uses the config prepared by script 42.
#
# This does not modify /srv/models. The existing Coder data is mounted
# read-only only for the already-prepared MTP draft layer.

IMAGE="${STRATA_DOCKER_IMAGE:-strata-v100:0.1.31}"
IQ2XS_ROOT="${IQ2XS_ROOT:-$HOME/models/strata-iq2xs}"
CFG_HOST="$IQ2XS_ROOT/config/strata-iq2xs-multigpu.json"
CFG_CONT="/iq2/config/strata-iq2xs-multigpu.json"
LOG_DIR="$IQ2XS_ROOT/logs"
MTP_HOST="${STRATA_MTP_DIR:-/srv/models/strata-data/mtp}"
NAME="${STRATA_IQ2XS_MGPU_NAME:-strata-iq2xs-mgpu}"
HOST_PORT="${STRATA_IQ2XS_MGPU_PORT:-8080}"

[ -f "$CFG_HOST" ] || {
  echo "ERROR: missing config: $CFG_HOST" >&2
  echo "       Run scripts/42-prepare-original-iq2xs-multigpu-128k.sh first." >&2
  exit 1
}

[ -f "$MTP_HOST/rt/experts.bin" ] || {
  echo "ERROR: missing shared MTP: $MTP_HOST/rt/experts.bin" >&2
  exit 1
}

docker image inspect "$IMAGE" >/dev/null 2>&1 || {
  echo "ERROR: Docker image not found: $IMAGE" >&2
  exit 1
}

mkdir -p "$LOG_DIR"

if docker ps -a --format '{{.Names}}' | grep -qx "$NAME"; then
  echo "ERROR: container already exists: $NAME" >&2
  echo "       Refusing to remove it automatically." >&2
  echo "       Inspect it first with: docker ps -a --filter name=$NAME" >&2
  exit 1
fi

if ss -ltnH | awk '{print $4}' | grep -Eq "(^|:)${HOST_PORT}$"; then
  echo "ERROR: TCP port $HOST_PORT is already listening." >&2
  echo "       Choose another with STRATA_IQ2XS_MGPU_PORT=<port>." >&2
  exit 1
fi

echo "=== Preflight ==="
echo "Image      : $IMAGE"
echo "Container  : $NAME"
echo "Model root : $IQ2XS_ROOT"
echo "MTP        : $MTP_HOST (read-only)"
echo "API        : http://127.0.0.1:$HOST_PORT/v1"
echo "GPUs       : 0,1"
echo "Context    : 131072"
echo "KV         : int8, resident window 32768"
echo "Prompt attn: STRATA_PROMPT_ATTN_OLD=1"
echo

free -h
echo
nvidia-smi --query-gpu=index,name,memory.used,memory.free --format=csv,noheader
echo

# Refuse to start on top of any running GPU workload. A few MiB from the
# driver is normal; nvidia-smi's process list is the decisive check here.
if nvidia-smi --query-compute-apps=pid --format=csv,noheader,nounits 2>/dev/null | grep -Eq '^[0-9]+$'; then
  echo "ERROR: an NVIDIA compute process is already running." >&2
  nvidia-smi >&2
  exit 1
fi

docker run -d \
  --name "$NAME" \
  --gpus all \
  --ulimit memlock=-1:-1 \
  -p "127.0.0.1:$HOST_PORT:8080" \
  -v "$IQ2XS_ROOT:/iq2:ro" \
  -v "$LOG_DIR:/iq2-logs" \
  -v "$MTP_HOST:/shared-mtp:ro" \
  -e STRATA_PROMPT_ATTN_OLD=1 \
  --entrypoint /opt/strata/.venv/bin/python \
  "$IMAGE" \
  /opt/strata/serve/server.py \
    --engine strata \
    --config "$CFG_CONT" \
    --host 0.0.0.0 \
    --port 8080 >/dev/null

echo "Started: $NAME"
echo
docker ps --filter "name=$NAME"
echo
echo "Follow startup:"
echo "  docker logs -f $NAME"
echo
echo "Engine log:"
echo "  tail -f $LOG_DIR/strata-iq2xs-mgpu.log"
echo
echo "When the server reports ready, check:"
echo "  curl -fsS http://127.0.0.1:$HOST_PORT/health"
echo
echo "To stop without deleting the container:"
echo "  docker stop $NAME"
