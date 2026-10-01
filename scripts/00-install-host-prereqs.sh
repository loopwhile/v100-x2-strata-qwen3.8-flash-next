#!/usr/bin/env bash
set -euo pipefail

# Host prerequisites for the P520 Volta test.
# This script intentionally DOES NOT install or replace the NVIDIA driver.
# It installs a CUDA-12-compatible host compiler, the CUDA 12.9.1 toolkit only,
# and raises the login user's memlock limit for Strata's pinned host arenas.

CUDA_RUNFILE="cuda_12.9.1_575.57.08_linux.run"
CUDA_URL="https://developer.download.nvidia.com/compute/cuda/12.9.1/local_installers/$CUDA_RUNFILE"
CUDA_SHA256="0f6d806ddd87230d2adbe8a6006a9d20144fdbda9de2d6acc677daa5d036417da"
CUDA_DST="${HOME}/${CUDA_RUNFILE}"
LOGIN_USER="${SUDO_USER:-$USER}"

echo "Target user: $LOGIN_USER"
echo
echo "1/3 Installing GCC/G++ 14 (CUDA 12.9 supports GCC through 14.x)..."
sudo apt-get update
sudo apt-get install -y gcc-14 g++-14

echo
echo "2/3 Installing CUDA Toolkit 12.9.1 only (NO NVIDIA driver change)..."
if [ ! -f "$CUDA_DST" ]; then
  wget -O "$CUDA_DST" "$CUDA_URL"
fi
echo "$CUDA_SHA256  $CUDA_DST" | sha256sum -c -
sudo sh "$CUDA_DST"   --silent   --toolkit   --override   --toolkitpath=/usr/local/cuda-12.9

echo
echo "3/3 Raising memlock for Strata pinned RAM/KV..."
sudo tee /etc/security/limits.d/99-strata-memlock.conf >/dev/null <<EOF
$LOGIN_USER soft memlock unlimited
$LOGIN_USER hard memlock unlimited
EOF

echo
echo "Installed versions:"
/usr/local/cuda-12.9/bin/nvcc --version | tail -n2
gcc-14 --version | head -n1
g++-14 --version | head -n1

echo
echo "IMPORTANT: log out of SSH completely and reconnect so the memlock limit is applied."
echo "After reconnect:"
echo "  ulimit -l"
echo "must print:"
echo "  unlimited"
echo
echo "Then rerun:"
echo "  bash scripts/00-preflight.sh"
