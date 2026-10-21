#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REF="${STRATA_UPSTREAM_REF:-011c9e600a93bbc9fd451c563501b5831c32bbca}"
IMAGE="${STRATA_DOCKER_IMAGE:-strata-v100-upstream:0.1.47}"

command -v docker >/dev/null || { echo "ERROR: docker not found" >&2; exit 1; }
docker info >/dev/null

echo "Building $IMAGE"
echo "Source: Niko1221/Strata@$REF (v0.2.2 / engine 0.1.47)"
echo "Base: nvidia/cuda:12.9.1-devel-ubuntu24.04"
echo "Target: Volta sm_70 / text-only / STRATA_EXPERIMENTAL_SM60=ON"
echo

docker build --pull \
  -f "$ROOT/Dockerfile.upstream-0.1.47" \
  --build-arg STRATA_UPSTREAM_REF="$REF" \
  --build-arg CUDA_ARCHITECTURES=70 \
  --build-arg BUILD_VISION=0 \
  -t "$IMAGE" \
  "$ROOT"

echo
echo "=== image receipt ==="

docker image inspect "$IMAGE" \
  --format 'ID={{.Id}} Created={{.Created}} Revision={{index .Config.Labels "org.opencontainers.image.revision"}}'

docker run --rm \
  --entrypoint /bin/bash \
  "$IMAGE" \
  -lc '
set -e
echo "--- CUDA ---"
nvcc --version | tail -n2
echo
echo "--- engine ---"
ls -lh /opt/strata/engine/strata
echo
echo "--- BUILD.json ---"
cat /opt/strata/engine/BUILD.json
echo
echo "--- source HEAD ---"
git -C /opt/strata rev-parse HEAD
echo
echo "--- source version ---"
/opt/strata/.venv/bin/python - <<PY
import setup
print("version:", setup.source_version())
PY
'

echo
echo "Built: $IMAGE"
echo "Expected engine: Strata 0.1.47 / CUDA 12.9.x / archs [70] / vision none"
