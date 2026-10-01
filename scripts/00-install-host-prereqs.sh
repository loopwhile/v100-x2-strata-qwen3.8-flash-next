#!/usr/bin/env bash
set -euo pipefail

cat <<'EOF'
This native-host prerequisite path is retired.

The P520 already has:
- a working NVIDIA 580 driver
- Docker
- NVIDIA Container Toolkit
- verified GPU passthrough for both V100s

Use the isolated Docker workflow instead:

  git pull
  bash scripts/20-docker-build-v100.sh

No host CUDA toolkit or permanent host memlock change is required.
EOF

exit 0
