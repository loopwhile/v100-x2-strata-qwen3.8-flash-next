#!/usr/bin/env bash
set -euo pipefail

IMAGE="${STRATA_DOCKER_IMAGE:-strata-v100:0.1.31}"
DATA_DIR="${STRATA_DATA_DIR:-/srv/models/strata-data}"
CFG="/data/config/strata-coder-iq1_m-single.json"
HOST_CFG="$DATA_DIR/config/strata-coder-iq1_m-single.json"
A_NAME="${STRATA_AGENT_A_NAME:-strata-agent-a}"
B_NAME="${STRATA_AGENT_B_NAME:-strata-agent-b}"
CPUSET_A="${STRATA_CPUSET_A:-0-2,6-8}"
CPUSET_B="${STRATA_CPUSET_B:-3-5,9-11}"

[ -f "$HOST_CFG" ] || {
  echo "ERROR: $HOST_CFG missing. Run scripts/30-docker-prepare-dual-agents.sh first." >&2
  exit 1
}

for n in "$A_NAME" "$B_NAME"; do
  if docker ps -a --format '{{.Names}}' | grep -qx "$n"; then
    docker rm -f "$n" >/dev/null
  fi
done

start_agent() {
  local name="$1" host_gpu="$2" host_port="$3" cpuset="$4"
  docker run -d     --name "$name"     --gpus "device=$host_gpu"     --cpuset-cpus "$cpuset"     --ulimit memlock=-1:-1     -p "127.0.0.1:${host_port}:8080"     -v "$DATA_DIR:/data:ro"     -e STRATA_PROMPT_ATTN_OLD=1     --entrypoint /opt/strata/.venv/bin/python     "$IMAGE"     /opt/strata/serve/server.py       --engine strata       --config "$CFG"       --host 0.0.0.0       --port 8080       --gpu 0 >/dev/null
}

echo "Starting Agent A: host GPU0 -> :8080, CPUs $CPUSET_A"
start_agent "$A_NAME" 0 8080 "$CPUSET_A"

echo "Starting Agent B: host GPU1 -> :8081, CPUs $CPUSET_B"
start_agent "$B_NAME" 1 8081 "$CPUSET_B"

echo
echo "Containers:"
docker ps --filter "name=$A_NAME" --filter "name=$B_NAME"

echo
echo "Follow logs:"
echo "  docker logs -f $A_NAME"
echo "  docker logs -f $B_NAME"
echo
echo "When both are ready:"
echo "  bash scripts/33-docker-bench-dual-agents.sh"
