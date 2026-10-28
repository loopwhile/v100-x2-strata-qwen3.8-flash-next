#!/usr/bin/env bash
set -euo pipefail
# Read-only status; no restart, model load or destructive side effects.
docker ps -a --filter "name=^/strata-s6-iq3s-agent-a$" --filter "name=^/strata-s6-iq3s-agent-b$" \
  --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
for entry in "A|18082|strata-s6-iq3s-agent-a" "B|18083|strata-s6-iq3s-agent-b"; do
  IFS='|' read -r label port name <<<"$entry"
  if [[ "$(docker inspect --format '{{.State.Running}}' "$name" 2>/dev/null || true)" != true ]]; then
    echo "Agent $label: not running"
    continue
  fi
  echo "Agent $label: $(docker inspect --format '{{.HostConfig.CpusetCpus}}' "$name") CPUs"
  echo "Agent $label: GPU device request: $(docker inspect --format '{{json .HostConfig.DeviceRequests}}' "$name")"
  curl --connect-timeout 2 --max-time 4 -fsS "http://127.0.0.1:$port/health" || echo "Agent $label: not yet healthy"
  printf '\n'
done
