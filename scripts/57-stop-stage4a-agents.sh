#!/usr/bin/env bash
set -euo pipefail

A_NAME="strata-s4a-iq2xs-agent-a"
B_NAME="strata-s4a-iq2xs-agent-b"

echo "Stopping Stage 4-A disposable agents ($A_NAME, $B_NAME) ..."
for c in "$A_NAME" "$B_NAME"; do
  if docker ps -a --format '{{.Names}}' | grep -qw "$c"; then
    echo "Stopping container $c ..."
    docker stop -t 30 "$c" >/dev/null 2>&1 || true
    echo "Removing container $c ..."
    docker rm -f "$c" >/dev/null 2>&1 || true
  fi
done

echo "Stage 4-A containers stopped and cleaned up."
