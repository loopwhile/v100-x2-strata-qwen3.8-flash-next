#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${STRATA_DOCKER_IMAGE:-strata-v100:0.1.31}"
DATA_DIR="${STRATA_DATA_DIR:-/srv/models/strata-data}"
HOST_PORT="${STRATA_HOST_PORT:-8080}"
CFG="/data/config/strata-coder-iq1_m.json"

[ -f "$DATA_DIR/config/strata-coder-iq1_m.json" ] || {
  echo "ERROR: multi-GPU config not found under $DATA_DIR/config" >&2
  exit 1
}

docker run --rm   --gpus all   --network host   -e STRATA_DIR=/opt/strata   -v "$ROOT:/work"   -v "$DATA_DIR:/data:ro"   --entrypoint /opt/strata/.venv/bin/python   "$IMAGE"   /work/bench/api_bench.py     --config "$CFG"     --url "http://127.0.0.1:$HOST_PORT"     --targets 32000 64000 125000
