#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"

BASE="${1:-http://127.0.0.1:8080}"
ts="$(date +%Y%m%d-%H%M%S)"
out="$RESULTS_DIR/smoke-$ts.txt"

{
  echo "=== health ==="
  curl -fsS "$BASE/health" || true
  echo
  echo

  echo "=== models ==="
  curl -fsS "$BASE/v1/models" || true
  echo
  echo

  echo "=== status before ==="
  curl -fsS "$BASE/status" || true
  echo
  echo

  echo "=== completion ==="
  curl -fsS "$BASE/v1/chat/completions" \
    -H 'Content-Type: application/json' \
    -d '{"model":"strata","messages":[{"role":"user","content":"Reply with exactly: READY"}],"temperature":0,"max_tokens":32,"reasoning_effort":"none"}'
  echo
  echo

  echo "=== status after ==="
  curl -fsS "$BASE/status" || true
  echo
  echo

  echo "=== metrics ==="
  curl -fsS "$BASE/metrics" || true
  echo
  echo

  echo "=== nvidia-smi ==="
  nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu,power.draw,temperature.gpu --format=csv,noheader
} | tee "$out"

echo
echo "Saved: $out"
