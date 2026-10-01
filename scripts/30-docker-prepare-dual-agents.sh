#!/usr/bin/env bash
set -euo pipefail

IMAGE="${STRATA_DOCKER_IMAGE:-strata-v100:0.1.31}"
DATA_DIR="${STRATA_DATA_DIR:-/srv/models/strata-data}"
MGPU_NAME="${STRATA_CONTAINER_NAME:-strata-v100-mgpu}"

mkdir -p "$DATA_DIR/config"

if docker ps -a --format '{{.Names}}' | grep -qx "$MGPU_NAME"; then
  echo "Stopping/removing multi-GPU container first: $MGPU_NAME"
  docker rm -f "$MGPU_NAME" >/dev/null
fi

# Preserve the multi-GPU config before the single-GPU setup writes the model's
# canonical config name again.
if [ -f "$DATA_DIR/config/strata-coder-iq1_m.json" ]; then
  cp -f "$DATA_DIR/config/strata-coder-iq1_m.json"         "$DATA_DIR/config/strata-coder-iq1_m-multigpu.json"
fi

echo "Preparing one-GPU / low-RAM mmap Coder config using V100 #0."
echo "Existing model files in $DATA_DIR are reused."
echo

docker run --rm   --gpus "device=0"   --ulimit memlock=-1:-1   -v "$DATA_DIR:/data"   --entrypoint /bin/bash   "$IMAGE" -lc '
    set -e
    cd /opt/strata
    .venv/bin/python setup.py       --setup --yes       --family coder       --model IQ1_M       --context 131072       --kv int8       --vision no       --experimental-speed-projection off       --gpu 0       --low-ram mmap       --data-dir /data       --host 0.0.0.0       --port 8080       --no-start
    mkdir -p /data/config
    cp -f /opt/strata/strata-coder-iq1_m.json           /data/config/strata-coder-iq1_m-single.json
  '

echo
echo "Prepared:"
echo "  $DATA_DIR/config/strata-coder-iq1_m-single.json"
echo
echo "Next: bash scripts/31-docker-run-dual-agents.sh"
