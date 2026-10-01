#!/usr/bin/env bash
set -euo pipefail

IMAGE="${STRATA_DOCKER_IMAGE:-strata-v100:0.1.31}"
DATA_DIR="${STRATA_DATA_DIR:-/srv/models/strata-data}"
NAME="${STRATA_CONTAINER_NAME:-strata-v100-mgpu}"
HOST_PORT="${STRATA_HOST_PORT:-8080}"

mkdir -p "$DATA_DIR"

if docker ps -a --format '{{.Names}}' | grep -qx "$NAME"; then
  echo "Removing previous container: $NAME"
  docker rm -f "$NAME" >/dev/null
fi

echo "Starting $NAME"
echo "  GPUs:       all (Strata layer split 0,1)"
echo "  Model:      Coder IQ1_M"
echo "  Context:    131072"
echo "  KV:         INT8"
echo "  Low RAM:    off"
echo "  Volta PF:   STRATA_PROMPT_ATTN_OLD=1 (force pre-sm75 fallback)"
echo "  Data:       $DATA_DIR"
echo "  API:        http://127.0.0.1:$HOST_PORT/v1"
echo

docker run -d   --name "$NAME"   --gpus all   --ulimit memlock=-1:-1   -p "127.0.0.1:${HOST_PORT}:8080"   -v "$DATA_DIR:/data"   -e FAMILY=coder   -e MODEL=IQ1_M   -e CONTEXT=131072   -e KV=int8   -e VISION=no   -e GPUS=0,1   -e LAYER_SPLIT=auto   -e LOW_RAM=off   -e HOST=0.0.0.0   -e PORT=8080   -e STRATA_PROMPT_ATTN_OLD=1   "$IMAGE" >/dev/null

echo "Container started. First run downloads/prepares the model and can take a while."
echo
echo "Follow setup/load progress:"
echo "  docker logs -f $NAME"
echo
echo "When it prints ready, run:"
echo "  bash scripts/04-smoke-api.sh http://127.0.0.1:$HOST_PORT"
echo "  bash scripts/23-docker-bench-multigpu.sh"
