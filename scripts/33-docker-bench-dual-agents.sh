#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${STRATA_DOCKER_IMAGE:-strata-v100:0.1.31}"
DATA_DIR="${STRATA_DATA_DIR:-/srv/models/strata-data}"
CFG="/data/config/strata-coder-iq1_m-single.json"

[ -f "$DATA_DIR/config/strata-coder-iq1_m-single.json" ] || {
  echo "ERROR: dual-agent config missing" >&2
  exit 1
}

docker run --rm   --network host   -e STRATA_DIR=/opt/strata   -v "$ROOT:/work"   -v "$DATA_DIR:/data:ro"   --entrypoint /opt/strata/.venv/bin/python   "$IMAGE"   /work/bench/api_bench.py     --config "$CFG"     --url http://127.0.0.1:8080     --url http://127.0.0.1:8081     --targets 32000 64000 125000     --parallel
