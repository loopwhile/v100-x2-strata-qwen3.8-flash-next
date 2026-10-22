#!/usr/bin/env bash
set -euo pipefail
# Stop ONLY the new mixed trial containers. Never delete any containers.
for c in strata-s4b-mixed-iq3xxs-agent-a strata-s4b-mixed-iq2xs-agent-b; do
  if docker container inspect "$c" >/dev/null 2>&1; then
    echo "Stopping mixed container $c (preserving it for reuse) ..."
    docker stop -t 30 "$c" >/dev/null
  else
    echo "$c does not exist; skip."
  fi
done
echo "Both mixed containers are stopped/preserved; historical agents unaffected."
