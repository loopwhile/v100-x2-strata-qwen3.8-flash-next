#!/usr/bin/env bash
set -euo pipefail
for n in "${STRATA_AGENT_A_NAME:-strata-agent-a}" "${STRATA_AGENT_B_NAME:-strata-agent-b}"; do
  if docker ps -a --format '{{.Names}}' | grep -qx "$n"; then
    docker rm -f "$n"
  else
    echo "$n is not present"
  fi
done
