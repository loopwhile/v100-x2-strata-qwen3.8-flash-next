#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"

stop_one() {
  local name="$1"
  local file="$2"
  if [ ! -f "$file" ]; then
    echo "$name: no PID file"
    return 0
  fi
  local pid
  pid="$(cat "$file")"
  if kill -0 "$pid" 2>/dev/null; then
    echo "Stopping $name process group $pid ..."
    kill -- "-$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
    for _ in $(seq 1 20); do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.5
    done
    if kill -0 "$pid" 2>/dev/null; then
      echo "$name still alive; sending SIGKILL"
      kill -KILL -- "-$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null || true
    fi
  else
    echo "$name: PID $pid already stopped"
  fi
  rm -f "$file"
}

stop_one "Agent A" "$RESULTS_DIR/agent-a.pid"
stop_one "Agent B" "$RESULTS_DIR/agent-b.pid"

echo
ss -ltnp | grep -E ':8080\b|:8081\b' || true
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu,power.draw --format=csv,noheader
