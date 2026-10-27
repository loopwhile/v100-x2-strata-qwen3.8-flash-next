#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REF="${STRATA_V100_REF:-2c9b1dd7bda3102c4a8e65fbe56c45f5c6882926}"
IMAGE="${STRATA_DOCKER_IMAGE:-strata-v100-jmnargi:2c9b1dd}"

command -v docker >/dev/null || { echo "ERROR: docker not found" >&2; exit 1; }
docker info >/dev/null

echo "Building $IMAGE"
echo "Source: jmnargi/Strata-V100@$REF (Stage 5 T7 — PR #74 IQ3_S WMMA2 + PR #80 V100 prefill scheduler)"
echo "Base: nvidia/cuda:12.9.1-devel-ubuntu24.04"
echo "Target: Volta sm_70 / text-only / STRATA_EXPERIMENTAL_SM60=ON"
echo

docker build --pull \
  -f "$ROOT/Dockerfile.jmnargi-v100-stage5" \
  --build-arg STRATA_V100_REF="$REF" \
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
sha256sum /opt/strata/engine/strata
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
echo "=== Restoring GGUF shard 1 into Active(file) page cache post-build ==="
if [ -f /srv/models/strata-iq3s/IQ3_S/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00001-of-00002.gguf ]; then
  cat /srv/models/strata-iq3s/IQ3_S/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00001-of-00002.gguf \
      /srv/models/strata-iq3s/pack/iq3_s-native/dense.bin > /dev/null
  cat /srv/models/strata-iq3s/IQ3_S/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00001-of-00002.gguf \
      /srv/models/strata-iq3s/pack/iq3_s-native/dense.bin > /dev/null
  command -v fincore >/dev/null && fincore /srv/models/strata-iq3s/IQ3_S/*.gguf /srv/models/strata-iq3s/pack/iq3_s-native/dense.bin || true
fi
