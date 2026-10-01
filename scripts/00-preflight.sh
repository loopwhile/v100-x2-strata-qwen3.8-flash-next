#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"

ts="$(date +%Y%m%d-%H%M%S)"
out="$RESULTS_DIR/preflight-$ts.txt"

{
  echo "=== date ==="
  date -Is
  echo

  echo "=== OS ==="
  uname -a
  cat /etc/os-release 2>/dev/null || true
  echo

  echo "=== CPU ==="
  lscpu
  echo

  echo "=== memory ==="
  free -h
  grep -E 'MemTotal|MemAvailable|SwapTotal|SwapFree' /proc/meminfo
  echo

  echo "=== storage ==="
  df -hT
  echo
  lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL
  echo

  echo "=== NVIDIA GPUs ==="
  nvidia-smi
  echo
  nvidia-smi --query-gpu=index,name,pci.bus_id,memory.total,compute_cap,driver_version,power.limit --format=csv,noheader
  echo

  echo "=== NVIDIA topology ==="
  nvidia-smi topo -m || true
  echo

  echo "=== PCIe ==="
  lspci -nn | grep -i -E 'nvidia|vga|3d controller' || true
  echo

  echo "=== CUDA toolkits ==="
  command -v nvcc || true
  nvcc --version 2>/dev/null || true
  for d in /usr/local/cuda* /opt/cuda*; do
    [ -e "$d" ] || continue
    echo "-- $d"
    [ -x "$d/bin/nvcc" ] && "$d/bin/nvcc" --version | tail -n2
  done
  echo

  echo "=== compilers ==="
  gcc --version | head -n1 || true
  g++ --version | head -n1 || true
  for c in gcc-14 g++-14 gcc-13 g++-13 gcc-12 g++-12; do
    command -v "$c" >/dev/null 2>&1 && "$c" --version | head -n1
  done
  cmake --version | head -n1 || true
  ninja --version || true
  python3 --version
  git --version
  echo

  echo "=== NUMA / CPU topology ==="
  command -v numactl >/dev/null && numactl --hardware || true
  lscpu -e=CPU,CORE,SOCKET,NODE,ONLINE,MAXMHZ,MINMHZ
  echo

  echo "=== kernel locked-memory limit ==="
  ulimit -l
} | tee "$out"

echo
echo "Saved: $out"

mapfile -t gpu_rows < <(nvidia-smi --query-gpu=name,memory.total,compute_cap --format=csv,noheader,nounits 2>/dev/null || true)
v100_count=0
for row in "${gpu_rows[@]}"; do
  if [[ "$row" == *"V100"* && "$row" == *", 7.0" ]]; then
    v100_count=$((v100_count + 1))
  fi
done

if [ "$v100_count" -lt 2 ]; then
  echo "WARNING: expected two V100 sm_70 GPUs, found $v100_count matching device(s)." >&2
fi

if nvcc12="$(find_cuda12_nvcc 2>/dev/null)"; then
  echo "CUDA 12.x nvcc: $nvcc12"
else
  echo "WARNING: no CUDA 12.x nvcc found. Do not build Strata for V100 with CUDA 13." >&2
fi

gcc_major="$(g++ -dumpfullversion -dumpversion 2>/dev/null | cut -d. -f1 || true)"
if [ -n "$gcc_major" ] && [ "$gcc_major" -gt 14 ]; then
  if ! command -v g++-14 >/dev/null 2>&1 && ! command -v g++-13 >/dev/null 2>&1 && ! command -v g++-12 >/dev/null 2>&1; then
    echo "WARNING: default G++ is $gcc_major; CUDA 12.9 supports GCC through 14.x and no compatible g++ 12-14 was found." >&2
  fi
fi

memlock="$(ulimit -l)"
if [ "$memlock" != "unlimited" ]; then
  echo "WARNING: memlock is $memlock KB, not unlimited. Strata's Linux expert arena/KV streaming uses large pinned/locked host memory." >&2
  echo "         Run scripts/00-install-host-prereqs.sh, reconnect SSH, and verify 'ulimit -l' => unlimited." >&2
fi
