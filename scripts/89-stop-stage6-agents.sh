#!/usr/bin/env bash
set -euo pipefail
# Stops ONLY Stage 6 experiment containers. Keeps containers, images, model files and logs.
for name in strata-s6-iq3s-agent-a strata-s6-iq3s-agent-b; do
  if docker container inspect "$name" >/dev/null 2>&1; then
    if [[ "$(docker inspect --format '{{.State.Running}}' "$name")" == true ]]; then
      echo "Stopping $name ..."
      docker stop --time 20 "$name"
    else
      echo "Already stopped: $name"
    fi
  else
    echo "Not present: $name"
  fi
done
