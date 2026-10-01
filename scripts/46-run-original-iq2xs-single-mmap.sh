#!/usr/bin/env bash
set -euo pipefail

# Stop (do not remove) the validated 2xV100 IQ2_XS server, then start a
# one-V100 GGUF-in-place mmap validation server on host GPU0.
#
# Existing model data and /srv/models are never modified.

IMAGE="${STRATA_DOCKER_IMAGE:-strata-v100:0.1.31}"
IQ2XS_ROOT="${IQ2XS_ROOT:-$HOME/models/strata-iq2xs}"
CFG_HOST="$IQ2XS_ROOT/config/strata-iq2xs-single-mmap.json"
CFG_CONT="/iq2/config/strata-iq2xs-single-mmap.json"
PACK="$IQ2XS_ROOT/pack/iq2_xs-native"
LOG_DIR="$IQ2XS_ROOT/logs"
MTP_HOST="${STRATA_MTP_DIR:-/srv/models/strata-data/mtp}"

MGPU_NAME="${STRATA_IQ2XS_MGPU_NAME:-strata-iq2xs-mgpu}"
NAME="${STRATA_IQ2XS_SINGLE_MMAP_NAME:-strata-iq2xs-single-mmap}"
HOST_PORT="${STRATA_IQ2XS_SINGLE_MMAP_PORT:-8080}"
HOST_GPU="${STRATA_IQ2XS_SINGLE_MMAP_GPU:-0}"

[ -f "$CFG_HOST" ] || {
  echo "ERROR: missing config: $CFG_HOST" >&2
  echo "       Run scripts/45-prepare-original-iq2xs-single-mmap.sh first." >&2
  exit 1
}

[ -f "$PACK/native_experts.txt" ] || {
  echo "ERROR: missing native expert map: $PACK/native_experts.txt" >&2
  exit 1
}

if [ -e "$PACK/experts.bin" ]; then
  echo "ERROR: $PACK/experts.bin exists." >&2
  echo "       Refusing to run the GGUF-in-place mmap validation." >&2
  exit 1
fi

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

echo "=== Before transition ==="
docker ps -a --filter "name=$MGPU_NAME" --filter "name=$NAME" \
  --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'
echo
free -h
echo
nvidia-smi --query-gpu=index,name,memory.used,memory.free --format=csv,noheader
echo

if docker ps --format '{{.Names}}' | grep -qx "$MGPU_NAME"; then
  echo "Stopping validated multi-GPU container (not removing): $MGPU_NAME"
  docker stop "$MGPU_NAME" >/dev/null
  echo "[ok] stopped $MGPU_NAME"
else
  echo "Multi-GPU container is not running: $MGPU_NAME"
fi

# Wait for the driver to release the previous engine's GPU allocations.
echo "Waiting for NVIDIA compute processes to exit ..."
for _ in $(seq 1 60); do
  if ! nvidia-smi --query-compute-apps=pid --format=csv,noheader,nounits 2>/dev/null | grep -Eq '^[0-9]+$'; then
    break
  fi
  sleep 1
done

if nvidia-smi --query-compute-apps=pid --format=csv,noheader,nounits 2>/dev/null | grep -Eq '^[0-9]+$'; then
  echo "ERROR: an NVIDIA compute process is still running after stopping $MGPU_NAME." >&2
  nvidia-smi >&2
  echo "The stopped multi-GPU container was not removed." >&2
  exit 1
fi

if ss -ltnH | awk '{print $4}' | grep -Eq "(^|:)${HOST_PORT}$"; then
  echo "ERROR: TCP port $HOST_PORT is still listening." >&2
  echo "       The stopped multi-GPU container was not removed." >&2
  exit 1
fi

echo
echo "=== Starting one-V100 mmap validation ==="
echo "Image      : $IMAGE"
echo "Container  : $NAME"
echo "Host GPU   : $HOST_GPU"
echo "Model root : $IQ2XS_ROOT"
echo "MTP        : $MTP_HOST (read-only)"
echo "API        : http://127.0.0.1:$HOST_PORT/v1"
echo "Context    : 131072"
echo "KV         : int8, resident window 32768"
echo "Experts    : GGUF-in-place mmap; NO experts.bin"
echo "Prompt attn: STRATA_PROMPT_ATTN_OLD=1"
echo

docker run -d \
  --name "$NAME" \
  --gpus "device=$HOST_GPU" \
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
docker ps -a --filter "name=$MGPU_NAME" --filter "name=$NAME" \
  --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'
echo
echo "Follow startup:"
echo "  docker logs -f $NAME"
echo
echo "Engine log:"
echo "  tail -f $LOG_DIR/strata-iq2xs-single-mmap.log"
echo
echo "To stop this validation without deleting it:"
echo "  docker stop $NAME"
echo
echo "To restore the validated multi-GPU server later:"
echo "  docker start $MGPU_NAME"
