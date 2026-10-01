#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${STRATA_DOCKER_IMAGE:-strata-v100:0.1.31}"

command -v docker >/dev/null || { echo "ERROR: docker not found" >&2; exit 1; }
docker info >/dev/null

echo "Building $IMAGE"
echo "Base: nvidia/cuda:12.9.1-devel-ubuntu24.04"
echo "Target: Strata 0.1.31 / Volta sm_70 / text-only"
echo

docker build --pull -f "$ROOT/Dockerfile.v100" -t "$IMAGE" "$ROOT"

echo
echo "=== image receipt ==="
docker run --rm --entrypoint /bin/bash "$IMAGE" -lc '
  set -e
  echo "--- nvcc ---"
  nvcc --version | tail -n2
  echo "--- compiler ---"
  gcc --version | head -n1
  echo "--- Strata commit ---"
  git rev-parse HEAD
  echo "--- BUILD.json ---"
  cat engine/BUILD.json
'

echo
echo "Built: $IMAGE"
echo "Next: bash scripts/21-docker-run-multigpu-128k.sh"
