#!/usr/bin/env bash
set -euo pipefail

A_NAME="${STRATA_IQ3S_AGENT_A_NAME:-strata-s4b-iq3s-agent-a}"
B_NAME="${STRATA_IQ3S_AGENT_B_NAME:-strata-s4b-iq3s-agent-b}"

echo "Stopping Stage 4-B IQ3_S disposable agents ($A_NAME, $B_NAME) ..."

for c in "$A_NAME" "$B_NAME"; do
  if docker ps -a --format '{{.Names}}' | grep -qw "$c"; then
    echo "Stopping container $c ..."
    docker stop "$c" >/dev/null 2>&1 || true
    echo "Removing container $c ..."
    docker rm -f "$c" >/dev/null 2>&1 || true
  fi
done

echo "Stage 4-B IQ3_S containers stopped and cleaned up."
