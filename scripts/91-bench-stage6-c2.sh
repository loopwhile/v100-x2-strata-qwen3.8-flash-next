#!/usr/bin/env bash
set -euo pipefail
# Stage 6 frozen C2; restarts ONLY the two Stage 6 containers.
# No profile env in scored runs. This script is NOT a routine production command.
# Usage: bash scripts/91-bench-stage6-c2.sh <test-id> <run-number>
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_ID="${1:-s6-baseline}"
RUN_NO="${2:-1}"
[[ "$TEST_ID" =~ ^[a-zA-Z0-9_-]+$ && "$RUN_NO" =~ ^[0-9]+$ ]] || {
  echo "ERROR: test-id must be alphanumeric/hyphen/underscore; run-number numeric" >&2
  exit 2
}

IMAGE="strata-v100-jmnargi:2c9b1dd"
A="strata-s6-iq3s-agent-a"
B="strata-s6-iq3s-agent-b"
A_URL="http://127.0.0.1:18082"
B_URL="http://127.0.0.1:18083"
A_MODEL="qwen3.8-flash-next-iq3_s-s6-a"
B_MODEL="qwen3.8-flash-next-iq3_s-s6-b"
EXPECTED_SHA="e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca"
MANIFEST="$ROOT/bench/workloads/v100-performance-v1.json"
CONFIG="$ROOT/artifacts/stage6-configs-20261028/iq3s/strata-s6-iq3s-agent-a.json"
[[ -f "$MANIFEST" && -f "$CONFIG" ]] || { echo "ERROR: frozen manifest/config missing" >&2; exit 1; }
echo "$EXPECTED_SHA  $MANIFEST" | sha256sum --check --status || {
 echo "ERROR: frozen C2 manifest SHA256 mismatch" >&2; exit 1;
}
docker image inspect "$IMAGE" >/dev/null || exit 1
EXPECTED_IMAGE_ID="sha256:5b62fa861bbdb346f81b0b3edf88ee21396fb4e59795a14b2b092dfa2e4aa156"
actual_image_id="$(docker image inspect --format '{{.Id}}' "$IMAGE")"
if [[ "$actual_image_id" != "$EXPECTED_IMAGE_ID" ]]; then
  echo "ERROR: $IMAGE resolves to unexpected image ID: $actual_image_id" >&2
  echo "Expected pinned Stage 5 T7-Fixed image: $EXPECTED_IMAGE_ID" >&2
  exit 1
fi

for name in "$A" "$B"; do
  [[ "$(docker inspect --format '{{.Config.Image}}' "$name" 2>/dev/null || true)" == "$IMAGE" ]] || {
    echo "ERROR: unexpected/missing Stage 6 container $name or image" >&2; exit 1;
  }
  [[ "$(docker inspect --format '{{.State.Running}}' "$name")" == true ]] || {
    echo "ERROR: Stage 6 container is stopped: $name" >&2; exit 1;
  }
done

# Scored runs must not include diagnostics that change scheduling and timing.
for name in "$A" "$B"; do
  if docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$name" \
      | grep -Eq '^STRATA_(DECODE_TIMING|VERIFY_PROFILE)='; then
    echo "ERROR: $name has timing profiler flags set. Recreate it without them for scored C2." >&2
    exit 1
  fi
done

stamp="$(date +%Y%m%d-%H%M%S)"
OUT="$ROOT/results/c2-stage6-${TEST_ID}-iq3s-${stamp}-run${RUN_NO}"
OUT_CONT="/work/results/$(basename "$OUT")"
mkdir -p "$ROOT/results"
echo "Stage 6 dual-agent C2: $TEST_ID / run $RUN_NO"
echo "Image: $IMAGE"
echo "Output: $OUT"
echo "Restarting ONLY Stage 6 A+B for fresh-process state ..."
docker restart "$A" "$B" >/dev/null

wait_loaded() {
  local url="$1" expected="$2" name="$3"
  for _ in $(seq 1 600); do
    if curl --connect-timeout 2 --max-time 3 -fsS "$url/health" 2>/dev/null \
      | python3 -c '
import json,sys
try: h=json.load(sys.stdin)
except Exception: sys.exit(1)
sys.exit(0 if h.get("status")=="ok" and h.get("loaded")==True
              and h.get("model")==sys.argv[1] and h.get("max_context")==131072 else 1)
' "$expected"; then
      echo "$name ready"
      return 0
    fi
    sleep 2
  done
  echo "ERROR: $name not healthy/loaded with 128K context" >&2
  return 1
}
wait_loaded "$A_URL" "$A_MODEL" "$A"
wait_loaded "$B_URL" "$B_MODEL" "$B"

for url in "$A_URL" "$B_URL"; do
  count="$(curl -fsS "$url/metrics" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("requests_kept",-1))')"
  [[ "$count" == 0 ]] || { echo "ERROR: requests_kept=$count at $url" >&2; exit 1; }
done

# The C2 harness creates OUT itself and requires that it does not yet exist.
# Save pre-run provenance separately, then move it into the results directory.
receipt_dir="$(mktemp -d "$ROOT/results/.stage6-receipt-XXXXXXXX")"
docker inspect "$A" "$B" > "$receipt_dir/stage6-containers-inspect.json"
docker image inspect "$IMAGE" > "$receipt_dir/stage6-image-inspect.json"
{ date --iso-8601=seconds; nvidia-smi --query-gpu=index,name,power.limit,memory.used,memory.free,temperature.gpu --format=csv; free -h; } > "$receipt_dir/host-before.txt"

set +e
docker run --rm --network host \
  --user "$(id -u):$(id -g)" \
  -e STRATA_DIR=/opt/strata \
  -v "$ROOT:/work" \
  -v /srv/models/strata-iq3s:/iq3s:ro \
  --entrypoint /opt/strata/.venv/bin/python \
  "$IMAGE" /work/bench/c2_v100_contract.py \
    --url-a "$A_URL" --url-b "$B_URL" \
    --expected-model-a "$A_MODEL" --expected-model-b "$B_MODEL" \
    --config /work/artifacts/stage6-configs-20261028/iq3s/strata-s6-iq3s-agent-a.json \
    --manifest /work/bench/workloads/v100-performance-v1.json \
    --out "$OUT_CONT"
rc=$?
set -e
mkdir -p "$OUT"
mv "$receipt_dir"/* "$OUT/"
rmdir "$receipt_dir"
{ date --iso-8601=seconds; nvidia-smi --query-gpu=index,name,power.draw,power.limit,memory.used,temperature.gpu --format=csv; free -h; } > "$OUT/host-after.txt"
if [[ -f "$OUT/summary.json" ]]; then
  cat "$OUT/summary.json"
fi
echo "Stage 6 C2 exit code: $rc; results: $OUT"
exit "$rc"
