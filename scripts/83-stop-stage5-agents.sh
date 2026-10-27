#!/usr/bin/env bash
set -euo pipefail

# Safely stop only Stage 5 test containers
for name in "strata-s5-agent-a" "strata-s5-agent-b"; do
  if docker ps -a --format '{{.Names}}' | grep -qw "$name"; then
    echo "Stopping test container: $name"
    docker stop -t 10 "$name" >/dev/null 2>&1 || true
    docker rm -f "$name" >/dev/null 2>&1 || true
    echo "[ok] $name stopped and removed."
  fi
done

echo "Stage 5 test containers stopped."
