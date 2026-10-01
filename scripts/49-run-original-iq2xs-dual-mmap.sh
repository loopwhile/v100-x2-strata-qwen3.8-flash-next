#!/usr/bin/env bash
set -euo pipefail

# Transition from the validated single-V100 mmap server to two independent
# original IQ2_XS mmap agents:
#   host GPU0 -> 127.0.0.1:8080, CPUs 0-2,6-8
#   host GPU1 -> 127.0.0.1:8081, CPUs 3-5,9-11
#
# Existing validated containers are stopped/preserved, never removed.
# Model/pack/MTP data is mounted read-only.

IMAGE="${STRATA_DOCKER_IMAGE:-strata-v100:0.1.31}"
IQ2XS_ROOT="${IQ2XS_ROOT:-$HOME/models/strata-iq2xs}"
LOG_DIR="$IQ2XS_ROOT/logs"
MTP_HOST="${STRATA_MTP_DIR:-/srv/models/strata-data/mtp}"

SINGLE_NAME="${STRATA_IQ2XS_SINGLE_MMAP_NAME:-strata-iq2xs-single-mmap}"
MGPU_NAME="${STRATA_IQ2XS_MGPU_NAME:-strata-iq2xs-mgpu}"
A_NAME="${STRATA_IQ2XS_AGENT_A_NAME:-strata-iq2xs-agent-a}"
B_NAME="${STRATA_IQ2XS_AGENT_B_NAME:-strata-iq2xs-agent-b}"

A_PORT="${STRATA_IQ2XS_AGENT_A_PORT:-8080}"
B_PORT="${STRATA_IQ2XS_AGENT_B_PORT:-8081}"
CPUSET_A="${STRATA_CPUSET_A:-0-2,6-8}"
CPUSET_B="${STRATA_CPUSET_B:-3-5,9-11}"

CFG_A_HOST="$IQ2XS_ROOT/config/strata-iq2xs-agent-a.json"
CFG_B_HOST="$IQ2XS_ROOT/config/strata-iq2xs-agent-b.json"
CFG_A_CONT="/iq2/config/strata-iq2xs-agent-a.json"
CFG_B_CONT="/iq2/config/strata-iq2xs-agent-b.json"
PACK="$IQ2XS_ROOT/pack/iq2_xs-native"

for f in \
  "$CFG_A_HOST" \
  "$CFG_B_HOST" \
  "$PACK/native_experts.txt" \
  "$MTP_HOST/rt/experts.bin"
do
  [ -f "$f" ] || {
    echo "ERROR: required file is missing: $f" >&2
    exit 1
  }
done

if [ -e "$PACK/experts.bin" ]; then
  echo "ERROR: $PACK/experts.bin exists." >&2
  echo "       Refusing to run the GGUF-in-place dual mmap validation." >&2
  exit 1
fi

docker image inspect "$IMAGE" >/dev/null 2>&1 || {
  echo "ERROR: Docker image not found: $IMAGE" >&2
  exit 1
}

mkdir -p "$LOG_DIR"

for n in "$A_NAME" "$B_NAME"; do
  if docker ps -a --format '{{.Names}}' | grep -qx "$n"; then
    echo "ERROR: container already exists: $n" >&2
    echo "       Refusing to remove or replace it automatically." >&2
    echo "       Inspect it first with: docker ps -a --filter name=$n" >&2
    exit 1
  fi
done

echo "=== Before transition ==="
docker ps -a \
  --filter "name=$SINGLE_NAME" \
  --filter "name=$MGPU_NAME" \
  --filter "name=$A_NAME" \
  --filter "name=$B_NAME" \
  --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'
echo
free -h
echo
nvidia-smi --query-gpu=index,name,memory.used,memory.free --format=csv,noheader
echo

if docker ps --format '{{.Names}}' | grep -qx "$SINGLE_NAME"; then
  echo "Stopping validated single-mmap container (not removing): $SINGLE_NAME"
  docker stop "$SINGLE_NAME" >/dev/null
  echo "[ok] stopped $SINGLE_NAME"
else
  echo "Single-mmap container is not running: $SINGLE_NAME"
fi

# The earlier validated multi-GPU server should remain stopped. Never start,
# remove or rewrite it here.
if docker ps --format '{{.Names}}' | grep -qx "$MGPU_NAME"; then
  echo "ERROR: $MGPU_NAME is unexpectedly running." >&2
  echo "       Stop it manually before the dual-agent test." >&2
  exit 1
fi

echo "Waiting for previous NVIDIA compute processes to exit ..."
for _ in $(seq 1 60); do
  if ! nvidia-smi --query-compute-apps=pid --format=csv,noheader,nounits 2>/dev/null | grep -Eq '^[0-9]+$'; then
    break
  fi
  sleep 1
done

if nvidia-smi --query-compute-apps=pid --format=csv,noheader,nounits 2>/dev/null | grep -Eq '^[0-9]+$'; then
  echo "ERROR: an NVIDIA compute process is still running before dual-agent start." >&2
  nvidia-smi >&2
  exit 1
fi

for p in "$A_PORT" "$B_PORT"; do
  if ss -ltnH | awk '{print $4}' | grep -Eq "(^|:)${p}$"; then
    echo "ERROR: TCP port $p is already listening." >&2
    exit 1
  fi
done

start_agent() {
  local name="$1"
  local host_gpu="$2"
  local host_port="$3"
  local cpuset="$4"
  local cfg_cont="$5"

  docker run -d \
    --name "$name" \
    --gpus "device=$host_gpu" \
    --cpuset-cpus "$cpuset" \
    --ulimit memlock=-1:-1 \
    -p "127.0.0.1:$host_port:8080" \
    -v "$IQ2XS_ROOT:/iq2:ro" \
    -v "$LOG_DIR:/iq2-logs" \
    -v "$MTP_HOST:/shared-mtp:ro" \
    -e STRATA_PROMPT_ATTN_OLD=1 \
    --entrypoint /opt/strata/.venv/bin/python \
    "$IMAGE" \
    /opt/strata/serve/server.py \
      --engine strata \
      --config "$cfg_cont" \
      --host 0.0.0.0 \
      --port 8080 >/dev/null
}

wait_ready() {
  local name="$1"
  local port="$2"
  local expected_model="$3"

  echo "Waiting for $name on 127.0.0.1:$port ..."
  for _ in $(seq 1 600); do
    if ! docker ps --format '{{.Names}}' | grep -qx "$name"; then
      echo "ERROR: $name exited during startup." >&2
      docker logs --tail 120 "$name" >&2 || true
      return 1
    fi

    if curl -fsS "http://127.0.0.1:$port/health" 2>/dev/null |
      python3 -c '
import json,sys
want=sys.argv[1]
try:
    h=json.load(sys.stdin)
except Exception:
    raise SystemExit(1)
raise SystemExit(0 if h.get("status")=="ok" and h.get("loaded") and h.get("model")==want else 1)
' "$expected_model"
    then
      echo "[ok] $name ready"
      return 0
    fi
    sleep 1
  done

  echo "ERROR: timed out waiting for $name." >&2
  docker logs --tail 120 "$name" >&2 || true
  return 1
}

echo
echo "=== Starting Agent A ==="
echo "host GPU0 -> :$A_PORT, CPUs $CPUSET_A"
start_agent "$A_NAME" 0 "$A_PORT" "$CPUSET_A" "$CFG_A_CONT"
wait_ready "$A_NAME" "$A_PORT" "qwen3.8-flash-next-iq2_xs-mmap-a"

echo
echo "=== Starting Agent B ==="
echo "host GPU1 -> :$B_PORT, CPUs $CPUSET_B"
start_agent "$B_NAME" 1 "$B_PORT" "$CPUSET_B" "$CFG_B_CONT"
wait_ready "$B_NAME" "$B_PORT" "qwen3.8-flash-next-iq2_xs-mmap-b"

echo
echo "=== Dual IQ2_XS mmap agents ready ==="
docker ps \
  --filter "name=$A_NAME" \
  --filter "name=$B_NAME" \
  --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

echo
free -h
echo
nvidia-smi --query-gpu=index,name,memory.used,memory.free,utilization.gpu,power.draw,temperature.gpu \
  --format=csv,noheader

echo
echo "Health:"
curl -fsS "http://127.0.0.1:$A_PORT/health"
echo
curl -fsS "http://127.0.0.1:$B_PORT/health"
echo

echo
echo "Logs:"
echo "  docker logs -f $A_NAME"
echo "  docker logs -f $B_NAME"
echo
echo "Stop without deleting:"
echo "  docker stop $A_NAME $B_NAME"
echo
echo "Validated older containers remain preserved:"
echo "  $SINGLE_NAME"
echo "  $MGPU_NAME"
echo
echo "No files under /srv/models were changed."
