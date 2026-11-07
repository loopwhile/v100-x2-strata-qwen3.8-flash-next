#!/usr/bin/env bash
set -Eeuo pipefail
# Invoke on P520 through ssh p520; never overwrite an existing image tag.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE=strata-stage8-upstream:0.1.57-c3b3f50
test "$(hostname)" = p520-llm
if docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "Image already exists; preserve it: $IMAGE" >&2
  exit 1
fi
CONTEXT="$(mktemp -d /tmp/strata-stage8-build.XXXXXX)"
mkdir "$CONTEXT/docker"
cp "$ROOT/Dockerfile.stage8-0.1.57" "$CONTEXT/"
cp "$ROOT/docker/build_upstream_0157_v100_engine.py" "$CONTEXT/docker/"
echo "Retained minimal build context: $CONTEXT"
docker build -f "$CONTEXT/Dockerfile.stage8-0.1.57" -t "$IMAGE" "$CONTEXT"
docker image inspect "$IMAGE" --format '{{.Id}} {{index .Config.Labels "org.opencontainers.image.revision"}}'
# No GPU access: packaging/provenance only.
docker run --rm --entrypoint /bin/bash "$IMAGE" -c '
set -Eeuo pipefail
test "$(git rev-parse HEAD)" = c3b3f5035506f3e966f1b4b7b188aeaabae92f1d
cat engine/BUILD.json
sha256sum engine/strata
nvcc --version
cuobjdump --list-elf engine/strata
'
