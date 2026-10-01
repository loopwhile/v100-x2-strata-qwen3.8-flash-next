#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"

activate_cuda12

mkdir -p "$(dirname "$STRATA_DIR")"

if [ -d "$STRATA_DIR/.git" ]; then
  echo "Refreshing disposable upstream tree: $STRATA_DIR"
  git -C "$STRATA_DIR" fetch origin
  git -C "$STRATA_DIR" reset --hard origin/main
  git -C "$STRATA_DIR" clean -fdx
else
  rm -rf "$STRATA_DIR"
  git clone https://github.com/Niko1221/Strata.git "$STRATA_DIR"
fi

echo "Upstream commit:"
git -C "$STRATA_DIR" log -1 --oneline

python3 "$HARNESS_ROOT/scripts/patch_volta.py" "$STRATA_DIR"

echo
echo "Patched diff:"
git -C "$STRATA_DIR" diff -- CMakeLists.txt setup.py src/core/device.cu || true

mkdir -p "$RESULTS_DIR"
{
  echo "upstream=$(git -C "$STRATA_DIR" rev-parse HEAD)"
  echo "nvcc=$CUDA12_NVCC"
  "$CUDA12_NVCC" --version | tail -n2
} > "$RESULTS_DIR/strata-source.txt"

echo
echo "Running Strata hardware check (no model download)..."
(
  cd "$STRATA_DIR"
  ./setup.sh --check --yes
)

echo
echo "Prepared: $STRATA_DIR"
echo "Next: bash scripts/02-setup-coder-128k-multigpu.sh"
