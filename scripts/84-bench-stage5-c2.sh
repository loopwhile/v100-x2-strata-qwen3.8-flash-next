#!/usr/bin/env bash
set -euo pipefail

# Stage 5 C2 128K Performance Benchmark Runner with Host Telemetry Capture
# Usage: ./84-bench-stage5-c2.sh <test_id> [run_number]
# Example: ./84-bench-stage5-c2.sh t1 1

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEST_ID="${1:-t1}"
RUN_LABEL="${2:-1}"

IMAGE="${STRATA_DOCKER_IMAGE:-strata-v100-upstream:0.1.47}"
IQ3S_ROOT="${IQ3S_ROOT:-/srv/models/strata-iq3s}"
A_NAME="${STRATA_AGENT_A_NAME:-strata-s5-agent-a}"
B_NAME="${STRATA_AGENT_B_NAME:-strata-s5-agent-b}"
A_MODEL="${STRATA_AGENT_A_MODEL:-qwen3.8-flash-next-iq3_s-s5-a}"
B_MODEL="${STRATA_AGENT_B_MODEL:-qwen3.8-flash-next-iq3_s-s5-b}"
A_URL="${STRATA_AGENT_A_URL:-http://127.0.0.1:8080}"
B_URL="${STRATA_AGENT_B_URL:-http://127.0.0.1:8081}"

MANIFEST="$ROOT/bench/workloads/v100-performance-v1.json"
EXPECTED_SHA="e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca"

[ -f "$MANIFEST" ] || { echo "ERROR: missing frozen workload: $MANIFEST" >&2; exit 1; }

actual_sha="$(sha256sum "$MANIFEST" | awk '{print $1}')"
if [ "$actual_sha" != "$EXPECTED_SHA" ]; then
  echo "ERROR: frozen workload SHA256 mismatch." >&2
  echo "  expected: $EXPECTED_SHA" >&2
  echo "  actual  : $actual_sha" >&2
  exit 1
fi

for n in "$A_NAME" "$B_NAME"; do
  docker inspect "$n" >/dev/null 2>&1 || {
    echo "ERROR: required container is missing: $n" >&2
    exit 1
  }
done

docker image inspect "$IMAGE" >/dev/null 2>&1 || {
  echo "ERROR: Docker image not found: $IMAGE" >&2
  exit 1
}

echo "=== Stage 5 Frozen C2 Benchmark ($TEST_ID Run #$RUN_LABEL) ==="
echo "Engine          : $IMAGE"
echo "Model           : Qwen3.8-Flash-Next IQ3_S"
echo "Workload        : V100-PERFORMANCE-C2-128K-v1"
echo "Manifest SHA256 : $actual_sha"
echo "Agents          : $A_NAME ($A_MODEL), $B_NAME ($B_MODEL)"
echo

echo "=== Host before fresh-process restart ==="
free -h
echo
nvidia-smi --query-gpu=index,name,memory.used,memory.free,utilization.gpu,power.draw,temperature.gpu \
  --format=csv,noheader
echo

echo "Restarting Stage 5 agents for fresh-process state ..."
docker restart "$A_NAME" "$B_NAME" >/dev/null

wait_health() {
  local url="$1"
  local expected="$2"
  local label="$3"
  echo "Waiting for $label ($url, expected $expected) ..."
  for _ in $(seq 1 600); do
    if curl -fsS "$url/health" 2>/dev/null |
      python3 -c '
import json,sys
want=sys.argv[1]
try:
    h=json.load(sys.stdin)
except Exception:
    raise SystemExit(1)
raise SystemExit(0 if h.get("status")=="ok" and h.get("loaded") and h.get("model")==want else 1)
' "$expected"
    then
      echo "[ok] $label ready"
      return 0
    fi
    sleep 1
  done
  echo "ERROR: timed out waiting for $label" >&2
  return 1
}

wait_health "$A_URL" "$A_MODEL" "Agent A"
wait_health "$B_URL" "$B_MODEL" "Agent B"

# Assert requests_kept == 0 (no warmup)
for pair in "A $A_URL" "B $B_URL"; do
  set -- $pair
  label="$1"
  url="$2"
  kept="$(curl -fsS "$url/metrics" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("requests_kept", -1))')"
  if [ "$kept" != "0" ]; then
    echo "ERROR: Agent $label has $kept completed request(s) after restart. Expected 0." >&2
    exit 1
  fi
done

stamp="$(date +%Y%m%d-%H%M%S)"
OUT_HOST="$ROOT/results/c2-stage5-${TEST_ID}-iq3s-$stamp-run${RUN_LABEL}"
OUT_CONT="/work/results/c2-stage5-${TEST_ID}-iq3s-$stamp-run${RUN_LABEL}"
mkdir -p "$ROOT/results"

TELEMETRY_TMP="/tmp/stage5-telemetry-$stamp"
mkdir -p "$TELEMETRY_TMP"

echo
echo "=== Starting Telemetry & Benchmark Execution ==="
echo "Output Directory: $OUT_HOST"
echo

# Telemetry background processes
grep -E "pgfault|pgmajfault|pgpgin|pgpgout|pswpin|pswpout" /proc/vmstat > "$TELEMETRY_TMP/vmstat-proc-before.txt"
vmstat 1 > "$TELEMETRY_TMP/telemetry-vmstat.log" 2>&1 &
PID_VMSTAT=$!
iostat -xz 1 > "$TELEMETRY_TMP/telemetry-iostat.log" 2>&1 &
PID_IOSTAT=$!
pidstat -r -u -d 1 > "$TELEMETRY_TMP/telemetry-pidstat.log" 2>&1 &
PID_PIDSTAT=$!
nvidia-smi --query-gpu=timestamp,index,temperature.gpu,power.draw,power.limit,utilization.gpu,memory.used,memory.total,clocks.sm --format=csv,noheader -l 1 > "$TELEMETRY_TMP/telemetry-gpu.log" 2>&1 &
PID_GPU=$!

cleanup_telemetry() {
  kill "$PID_VMSTAT" "$PID_IOSTAT" "$PID_PIDSTAT" "$PID_GPU" 2>/dev/null || true
  wait "$PID_VMSTAT" "$PID_IOSTAT" "$PID_PIDSTAT" "$PID_GPU" 2>/dev/null || true
  grep -E "pgfault|pgmajfault|pgpgin|pgpgout|pswpin|pswpout" /proc/vmstat > "$TELEMETRY_TMP/vmstat-proc-after.txt" 2>/dev/null || true
  if [ -d "$OUT_HOST" ]; then
    mv "$TELEMETRY_TMP"/* "$OUT_HOST/" 2>/dev/null || true
    rmdir "$TELEMETRY_TMP" 2>/dev/null || true
  fi
}
trap cleanup_telemetry EXIT

set +e
docker run --rm \
  --network host \
  -e STRATA_DIR=/opt/strata \
  -v "$ROOT:/work" \
  -v "$IQ3S_ROOT:/iq3s:ro" \
  --entrypoint /opt/strata/.venv/bin/python \
  "$IMAGE" \
  /work/bench/c2_v100_contract.py \
    --url-a "$A_URL" \
    --url-b "$B_URL" \
    --expected-model-a "$A_MODEL" \
    --expected-model-b "$B_MODEL" \
    --config /work/artifacts/stage5-configs-20261027/iq3s/strata-s5-agent-a.json \
    --manifest /work/bench/workloads/v100-performance-v1.json \
    --out "$OUT_CONT"
rc=$?
set -e

cleanup_telemetry
trap - EXIT

echo
echo "=== Host after measured batch ==="
free -h
echo
nvidia-smi --query-gpu=index,name,memory.used,memory.free,utilization.gpu,power.draw,temperature.gpu \
  --format=csv,noheader

echo
echo "=== C2 Benchmark Summary ==="
if [ -f "$OUT_HOST/summary.json" ]; then
  cat "$OUT_HOST/summary.json"
fi
echo
exit "$rc"
