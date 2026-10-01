#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"

activate_cuda12
[ -d "$STRATA_DIR" ] || { echo "ERROR: missing $STRATA_DIR" >&2; exit 1; }

echo "Starting the saved Coder config on both V100s."
echo "API: http://127.0.0.1:8080/v1"
echo "Press Ctrl-C to stop."
echo

cd "$STRATA_DIR"
exec ./setup.sh --gpus 0,1 --layer-split auto --port 8080 --yes
