#!/usr/bin/env bash
set -euo pipefail

HARNESS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STRATA_DIR="${STRATA_DIR:-$HARNESS_ROOT/.work/Strata}"

if [ -n "${STRATA_DATA_DIR:-}" ]; then
  DATA_DIR="$STRATA_DATA_DIR"
elif [ -d /srv/models ] && [ -w /srv/models ]; then
  DATA_DIR=/srv/models/strata-data
else
  DATA_DIR="$HOME/strata-data"
fi

RESULTS_DIR="$HARNESS_ROOT/results"
CONFIGS_DIR="$HARNESS_ROOT/configs"
mkdir -p "$RESULTS_DIR" "$CONFIGS_DIR"

find_cuda12_nvcc() {
  local c v
  for c in     "${CUDA12_NVCC:-}"     /usr/local/cuda-12.9/bin/nvcc     /usr/local/cuda-12-9/bin/nvcc     /usr/local/cuda-12.8/bin/nvcc     /usr/local/cuda-12-8/bin/nvcc     /opt/cuda-12.9/bin/nvcc     /opt/cuda-12-9/bin/nvcc     /opt/cuda-12.8/bin/nvcc     /opt/cuda-12-8/bin/nvcc     "$(command -v nvcc 2>/dev/null || true)"
  do
    [ -n "$c" ] || continue
    [ -x "$c" ] || continue
    v="$("$c" --version 2>/dev/null | sed -n 's/.*release \([0-9][0-9]*\)\.\([0-9][0-9]*\).*/\1.\2/p' | head -n1)"
    case "$v" in
      12.*) printf '%s\n' "$c"; return 0 ;;
    esac
  done
  return 1
}

activate_cuda12() {
  local nvcc
  nvcc="$(find_cuda12_nvcc)" || {
    echo "ERROR: CUDA 12.x nvcc not found. V100/sm_70 cannot be compiled with CUDA 13." >&2
    echo "Set CUDA12_NVCC=/path/to/cuda-12.x/bin/nvcc after installing a CUDA 12.x toolkit." >&2
    return 1
  }
  export CUDA12_NVCC="$nvcc"
  export CUDA_PATH="$(cd "$(dirname "$nvcc")/.." && pwd)"
  export PATH="$CUDA_PATH/bin:$PATH"
  export CUDACXX="$nvcc"
  echo "CUDA toolkit: $("$nvcc" --version | tail -n1)"
}
