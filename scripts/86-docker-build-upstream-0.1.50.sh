#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REF="${STRATA_UPSTREAM_REF:-4b9e05a2a806a3fe24f7b2560d98626c37dade35}"
IMAGE="${STRATA_DOCKER_IMAGE:-strata-v100-upstream:0.1.50}"

command -v docker >/dev/null || { echo "ERROR: docker not found" >&2; exit 1; }
docker info >/dev/null

echo "Building $IMAGE"
echo "Source: Niko1221/Strata@$REF (v0.2.6 / engine 0.1.50)"
echo "Base: nvidia/cuda:12.9.1-devel-ubuntu24.04"
echo "Target: Volta sm_70 / text-only / STRATA_EXPERIMENTAL_SM60=ON"
echo

docker build --pull \
  -f "$ROOT/Dockerfile.upstream-0.1.50" \
  --build-arg STRATA_UPSTREAM_REF="$REF" \
  --build-arg CUDA_ARCHITECTURES=70 \
  --build-arg BUILD_VISION=0 \
  -t "$IMAGE" \
  "$ROOT"

echo
echo "=== Image receipt ==="
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
echo "--- Engine ---"
ls -lh /opt/strata/engine/strata
echo
echo "--- BUILD.json ---"
cat /opt/strata/engine/BUILD.json
echo
echo "--- Source HEAD ---"
git -C /opt/strata rev-parse HEAD
echo
echo "--- Source version ---"
/opt/strata/.venv/bin/python - <<PY
import setup
print("version:", setup.source_version())
PY
'

echo
echo "Successfully built: $IMAGE"
