#!/usr/bin/env bash
set -euo pipefail
# Explicit, controlled reset for Stage 6 experiment container definitions only.
# Does NOT use docker rm -f and NEVER touches Stage 2-5, production, model, or results.
if [[ "${1:-}" != "--confirm-stage6-only" ]]; then
  echo "Usage: bash $0 --confirm-stage6-only" >&2
  echo "First stop Stage 6 agents with scripts/89-stop-stage6-agents.sh." >&2
  exit 2
fi
for name in strata-s6-iq3s-agent-a strata-s6-iq3s-agent-b; do
  if ! docker container inspect "$name" >/dev/null 2>&1; then
    echo "Absent: $name"
    continue
  fi
  if [[ "$(docker inspect --format '{{.State.Running}}' "$name")" == true ]]; then
    echo "ERROR: $name is running; stop it explicitly first. Nothing removed." >&2
    exit 1
  fi
done
for name in strata-s6-iq3s-agent-a strata-s6-iq3s-agent-b; do
  if docker container inspect "$name" >/dev/null 2>&1; then
    docker rm "$name"
  fi
done
echo "Removed Stage 6 container objects only; preserved logs/models/images and all other containers."
