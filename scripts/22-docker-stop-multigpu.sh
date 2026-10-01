#!/usr/bin/env bash
set -euo pipefail
NAME="${STRATA_CONTAINER_NAME:-strata-v100-mgpu}"
if docker ps -a --format '{{.Names}}' | grep -qx "$NAME"; then
  docker rm -f "$NAME"
else
  echo "$NAME is not present"
fi
