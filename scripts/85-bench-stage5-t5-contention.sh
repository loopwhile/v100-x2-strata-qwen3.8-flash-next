#!/usr/bin/env bash
set -euo pipefail

# Stage 5 T5 Resource Contention Controls
# Measures:
# 1. Agent A alone on GPU 0 (aff 0-2,6-8)
# 2. Agent B alone on GPU 1 (aff 3-5,9-11)
# 3. Concurrent A+B control
# Correlates CPU scheduling, RAM/page cache, NVMe I/O, and PCIe contention.

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${STRATA_DOCKER_IMAGE:-strata-v100-upstream:0.1.47}"
IQ3S_ROOT="${IQ3S_ROOT:-/srv/models/strata-iq3s}"

echo "=== Stage 5 T5 Contention Control Benchmark ==="

run_single() {
  local agent="$1" # a or b
  local port=8080
  local gpu=0
  local url="http://127.0.0.1:8080"
  local model="qwen3.8-flash-next-iq3_s-s5-a"
  if [ "$agent" = "b" ]; then
    port=8081
    gpu=1
    url="http://127.0.0.1:8081"
    model="qwen3.8-flash-next-iq3_s-s5-b"
  fi

  echo
  echo "--- Running Single Agent $agent (GPU $gpu, Port $port) ---"
  bash "$ROOT/scripts/83-stop-stage5-agents.sh"
  bash "$ROOT/scripts/82-start-stage5-agents.sh" "$agent"

  stamp="$(date +%Y%m%d-%H%M%S)"
  out_host="$ROOT/results/c2-stage5-t5-single-${agent}-$stamp"
  out_cont="/work/results/c2-stage5-t5-single-${agent}-$stamp"
  mkdir -p "$ROOT/results"

  telemetry_tmp="/tmp/stage5-t5-telemetry-$stamp"
  mkdir -p "$telemetry_tmp"

  # Start telemetry
  vmstat 1 > "$telemetry_tmp/telemetry-vmstat.log" 2>&1 &
  pid_vmstat=$!
  iostat -xz 1 > "$telemetry_tmp/telemetry-iostat.log" 2>&1 &
  pid_iostat=$!
  pidstat -r -u -d 1 > "$telemetry_tmp/telemetry-pidstat.log" 2>&1 &
  pid_pidstat=$!

  docker run --rm \
    --network host \
    -e STRATA_DIR=/opt/strata \
    -v "$ROOT:/work" \
    -v "$IQ3S_ROOT:/iq3s:ro" \
    --entrypoint /opt/strata/.venv/bin/python \
    "$IMAGE" \
    /work/bench/c2_single_agent.py \
      --url "$url" \
      --expected-model "$model" \
      --agent "$agent" \
      --config "/work/artifacts/stage5-configs-20261027/iq3s/strata-s5-agent-${agent}.json" \
      --out "$out_cont"

  kill "$pid_vmstat" "$pid_iostat" "$pid_pidstat" 2>/dev/null || true
  wait "$pid_vmstat" "$pid_iostat" "$pid_pidstat" 2>/dev/null || true
  if [ -d "$out_host" ]; then
    mv "$telemetry_tmp"/* "$out_host/" 2>/dev/null || true
    rmdir "$telemetry_tmp" 2>/dev/null || true
  fi

  bash "$ROOT/scripts/83-stop-stage5-agents.sh"
}

# Run Agent A alone
run_single a

# Run Agent B alone
run_single b

# Run concurrent A+B
echo
echo "--- Running Concurrent Agent A + B Control ---"
bash "$ROOT/scripts/83-stop-stage5-agents.sh"
bash "$ROOT/scripts/82-start-stage5-agents.sh" both
bash "$ROOT/scripts/84-bench-stage5-c2.sh" t5 concurrent
bash "$ROOT/scripts/83-stop-stage5-agents.sh"

echo
echo "T5 contention controls completed."
