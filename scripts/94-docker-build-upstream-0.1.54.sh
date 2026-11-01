#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REF="${STRATA_UPSTREAM_REF:-870aedd9e1ebe1c91f94da93b59af17729f6c5c0}"
IMAGE="${STRATA_DOCKER_IMAGE:-strata-v100-upstream:0.1.54}"

command -v docker >/dev/null || { echo "ERROR: docker not found" >&2; exit 1; }
docker info >/dev/null

echo "Building $IMAGE"
echo "Source: Niko1221/Strata@$REF (v0.2.8 / engine 0.1.54)"
echo "Base: nvidia/cuda:12.9.1-devel-ubuntu24.04"
echo "Target: Volta sm_70 / text-only / STRATA_EXPERIMENTAL_SM60=ON"
echo

if docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "ERROR: image tag already exists: $IMAGE" >&2
  exit 1
fi

docker build --pull \
  -f "$ROOT/Dockerfile.upstream-0.1.54" \
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
