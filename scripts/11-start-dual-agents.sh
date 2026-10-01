#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"

activate_cuda12

PY="$STRATA_DIR/.venv/bin/python"
SERVER="$STRATA_DIR/serve/server.py"
A="$CONFIGS_DIR/agent-a.json"
B="$CONFIGS_DIR/agent-b.json"

[ -x "$PY" ] || { echo "ERROR: Strata venv python missing: $PY" >&2; exit 1; }
[ -f "$A" ] || { echo "ERROR: $A missing. Run scripts/10-setup-dual-agents.sh first." >&2; exit 1; }
[ -f "$B" ] || { echo "ERROR: $B missing. Run scripts/10-setup-dual-agents.sh first." >&2; exit 1; }

mkdir -p "$RESULTS_DIR"

if ss -ltn | grep -qE ':8080\b|:8081\b'; then
  echo "ERROR: port 8080 or 8081 is already listening. Stop the previous server first." >&2
  ss -ltnp | grep -E ':8080\b|:8081\b' || true
  exit 1
fi

wait_health() {
  local url="$1"
  local name="$2"
  local i
  for i in $(seq 1 180); do
    if curl -fsS "$url/health" >/dev/null 2>&1; then
      echo "$name healthy: $url"
      return 0
    fi
    sleep 1
  done
  echo "ERROR: $name did not become healthy in 180 seconds" >&2
  return 1
}

echo "Starting Agent A on V100 #0 / port 8080 ..."
setsid nohup "$PY" "$SERVER" --engine strata --config "$A" --port 8080   >"$RESULTS_DIR/agent-a-server.log" 2>&1 < /dev/null &
pid_a=$!
echo "$pid_a" > "$RESULTS_DIR/agent-a.pid"

if ! wait_health http://127.0.0.1:8080 "Agent A"; then
  tail -n 100 "$RESULTS_DIR/agent-a-server.log" || true
  exit 1
fi

echo "Starting Agent B on V100 #1 / port 8081 ..."
setsid nohup "$PY" "$SERVER" --engine strata --config "$B" --port 8081   >"$RESULTS_DIR/agent-b-server.log" 2>&1 < /dev/null &
pid_b=$!
echo "$pid_b" > "$RESULTS_DIR/agent-b.pid"

if ! wait_health http://127.0.0.1:8081 "Agent B"; then
  tail -n 100 "$RESULTS_DIR/agent-b-server.log" || true
  exit 1
fi

echo
echo "Both independent Strata servers are running."
echo "  Agent A: http://127.0.0.1:8080/v1  PID $pid_a"
echo "  Agent B: http://127.0.0.1:8081/v1  PID $pid_b"
echo
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu,power.draw --format=csv,noheader

echo
echo "Smoke test:"
echo "  bash scripts/04-smoke-api.sh http://127.0.0.1:8080"
echo "  bash scripts/04-smoke-api.sh http://127.0.0.1:8081"
echo
echo "Parallel long-context benchmark:"
echo "  python3 bench/api_bench.py --config configs/agent-a.json --url http://127.0.0.1:8080 --url http://127.0.0.1:8081 --targets 32000 64000 125000 --parallel"
