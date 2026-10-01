#!/usr/bin/env bash
set -euo pipefail

NAME="${STRATA_CONTAINER_NAME:-strata-v100-mgpu}"
DATA_DIR="${STRATA_DATA_DIR:-/srv/models/strata-data}"
OUT="$(cd "$(dirname "$0")/.." && pwd)/results/diagnose-$(date +%Y%m%d-%H%M%S).txt"

{
  echo "=== date ==="
  date -Is
  echo

  echo "=== container state ==="
  docker inspect "$NAME" --format 'name={{.Name}} status={{.State.Status}} running={{.State.Running}} exit={{.State.ExitCode}} oom={{.State.OOMKilled}} started={{.State.StartedAt}}' 2>&1 || true
  echo

  echo "=== health / metrics ==="
  curl -fsS http://127.0.0.1:8080/health 2>&1 || true
  echo
  curl -fsS http://127.0.0.1:8080/metrics 2>&1 || true
  echo
  echo

  echo "=== docker logs (tail 300) ==="
  docker logs --tail 300 "$NAME" 2>&1 || true
  echo

  echo "=== configs ==="
  find "$DATA_DIR/config" -maxdepth 1 -type f -print 2>/dev/null || true
  for f in "$DATA_DIR"/config/*.json; do
    [ -f "$f" ] || continue
    echo "--- $f"
    cat "$f"
    echo
  done
  echo

  echo "=== in-container engine log ==="
  docker exec "$NAME" sh -lc 'tail -n 300 /opt/strata/strata-coder-iq1_m.log' 2>&1 || true
  echo

  echo "=== possible engine logs ==="
  find "$DATA_DIR" -maxdepth 4 -type f \( -name '*.log' -o -name '*engine*' \) -print 2>/dev/null || true
  while IFS= read -r f; do
    echo "--- tail: $f"
    tail -n 200 "$f" 2>/dev/null || true
  done < <(find "$DATA_DIR" -maxdepth 4 -type f -name '*.log' -print 2>/dev/null)
  echo

  echo "=== GPU ==="
  nvidia-smi
  echo

  echo "=== RAM ==="
  free -h
  echo

  echo "=== kernel OOM / GPU faults (best effort) ==="
  dmesg 2>/dev/null | grep -i -E 'out of memory|killed process|nvrm|xid' | tail -n 100 || true
} | tee "$OUT"

echo
echo "Saved: $OUT"
