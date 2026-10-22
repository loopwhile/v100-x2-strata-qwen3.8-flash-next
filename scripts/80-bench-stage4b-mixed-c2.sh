#!/usr/bin/env bash
set -euo pipefail

# Stage 4-B C2 128K Performance Benchmark Runner
# Upstream Strata v0.1.47 (Release 0.2.2) on dual independent V100s.

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="strata-v100-upstream:0.1.47"
IQ2XS_ROOT="/srv/models/strata-iq2xs"
IQ3XXS_ROOT="/srv/models/strata-iq3xxs"
A_NAME="strata-s4b-mixed-iq3xxs-agent-a"
B_NAME="strata-s4b-mixed-iq2xs-agent-b"
A_MODEL="qwen3.8-flash-next-iq3_xxs-s4b-mixed-a"
B_MODEL="qwen3.8-flash-next-iq2_xs-s4b-mixed-b"
A_URL="${STRATA_IQ2XS_AGENT_A_URL:-http://127.0.0.1:8080}"
B_URL="${STRATA_IQ2XS_AGENT_B_URL:-http://127.0.0.1:8081}"
MANIFEST="$ROOT/bench/workloads/v100-performance-v1.json"
EXPECTED_SHA="e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca"

[ -f "$MANIFEST" ] || {
  echo "ERROR: missing frozen workload: $MANIFEST" >&2
  exit 1
}

actual_sha="$(sha256sum "$MANIFEST" | awk '{print $1}')"
if [ "$actual_sha" != "$EXPECTED_SHA" ]; then
  echo "ERROR: frozen workload SHA256 mismatch." >&2
  echo "  expected: $EXPECTED_SHA" >&2
  echo "  actual  : $actual_sha" >&2
  exit 1
fi

for n in "$A_NAME" "$B_NAME"; do
  docker inspect "$n" >/dev/null 2>&1 || {
    echo "ERROR: required container is missing: $n" >&2
    exit 1
  }
done

docker image inspect "$IMAGE" >/dev/null 2>&1 || {
  echo "ERROR: Docker image not found: $IMAGE" >&2
  exit 1
}

echo "=== Frozen C2 performance contract (Stage 4-B MIXED IQ3_XXS A / IQ2_XS B) ==="
echo "Engine          : Upstream Strata v0.1.47 (v0.2.2)"
echo "Workload        : V100-PERFORMANCE-C2-128K-v1"
echo "Manifest SHA256 : $actual_sha"
echo "Agents          : $A_NAME ($A_MODEL), $B_NAME ($B_MODEL)"
echo "Context/request : 131072"
echo "Output reserve  : 4096"
echo "Minimum output  : 1024"
echo

[ "$(docker image inspect --format '{{.Id}}' "$IMAGE")" = "sha256:19c3b72a1097486eeae3fd9b964179a36a1c137615e5c93f6d6e70eacdab8e9d" ] || {
  echo "ERROR: Stage 4-B Docker image ID is unexpected." >&2
  exit 1
}
python3 - "$A_NAME" "$B_NAME" <<'PY'
import json,sys,subprocess
models=json.loads(subprocess.check_output(["docker","inspect",sys.argv[1],sys.argv[2]],text=True))
for c,gpu,cpus,port,mount in zip(models,("0","1"),("0-2,6-8","3-5,9-11"),("8080","8081"),("/iq3xxs","/iq2")):
    h=c["HostConfig"]
    if not c["State"]["Running"] or h["CpusetCpus"]!=cpus:
        raise SystemExit("ERROR: unexpected mixed container state/CPU affinity")
    ids=[d for r in h.get("DeviceRequests",[]) for d in r.get("DeviceIDs",[])]
    if ids != [gpu]: raise SystemExit(f"ERROR: wrong host GPU mapping: {ids}")
    bindings=h["PortBindings"]["8080/tcp"]
    if len(bindings)!=1 or bindings[0]["HostPort"]!=port: raise SystemExit("ERROR: wrong host port")
    if not any(m["Destination"]==mount and not m["RW"] for m in c["Mounts"]):
        raise SystemExit("ERROR: mixed model path must be read-only")
    if any(s.startswith("STRATA_SM70_TABLE=1") for s in c["Config"].get("Env",[])):
        raise SystemExit("ERROR: SM70_TABLE tuning not permitted for vanilla Stage 4-B")
PY

echo "=== Host before fresh-process restart ==="
free -h
echo
nvidia-smi --query-gpu=index,name,memory.used,memory.free,utilization.gpu,power.draw,temperature.gpu \
  --format=csv,noheader
echo

echo "Restarting ONLY the two Stage 4-B MIXED agents to clear per-process request/prefix state ..."
docker restart "$A_NAME" "$B_NAME" >/dev/null

wait_health() {
  local url="$1"
  local expected="$2"
  local label="$3"
  echo "Waiting for $label ($url, expected $expected) ..."
  for _ in $(seq 1 600); do
    if curl -fsS "$url/health" 2>/dev/null |
      python3 -c '
import json,sys
want=sys.argv[1]
try:
    h=json.load(sys.stdin)
except Exception:
    raise SystemExit(1)
raise SystemExit(0 if h.get("status")=="ok" and h.get("loaded") and h.get("model")==want else 1)
' "$expected"
    then
      echo "[ok] $label ready"
      return 0
    fi
    sleep 1
  done
  echo "ERROR: timed out waiting for $label" >&2
  return 1
}

wait_health "$A_URL" "$A_MODEL" "Agent A"
wait_health "$B_URL" "$B_MODEL" "Agent B"

# C2 uses one tokenizer for both project requests: fail closed if model tokenizers differ.
for f in vocab.json merges.txt token_type.json chat_template.jinja; do
  cmp -s "$IQ3XXS_ROOT/pack/iq3_xxs-native/tokenizer/$f" "$IQ2XS_ROOT/pack/iq2_xs-native/tokenizer/$f" || {
    echo "ERROR: mixed tokenizer mismatch: $f; cannot use shared calibration." >&2
    exit 1
  }
done
echo "[ok] IQ3_XXS/IQ2_XS tokenizer and chat template files are byte-identical."

# Health checks are not inference warmups. Assert that no request has run since restart.
for pair in "A $A_URL" "B $B_URL"; do
  set -- $pair
  label="$1"
  url="$2"
  kept="$(curl -fsS "$url/metrics" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("requests_kept", -1))')"
  if [ "$kept" != "0" ]; then
    echo "ERROR: Agent $label already has $kept completed request(s) after restart." >&2
    echo "       Refusing to call this a no-warmup measured run." >&2
    exit 1
  fi
done

RUN_LABEL="${1:-1}"
stamp="$(date +%Y%m%d-%H%M%S)"
OUT_HOST="$ROOT/results/c2-stage4b-mixed-v100-contract-$stamp-run$RUN_LABEL"
OUT_CONT="/work/results/c2-stage4b-mixed-v100-contract-$stamp-run$RUN_LABEL"
mkdir -p "$ROOT/results"

echo
echo "=== Starting C2 batch (Run #$RUN_LABEL) ==="
echo "Results: $OUT_HOST"
echo

set +e
docker run --rm \
  --network host \
  -e STRATA_DIR=/opt/strata \
  -v "$ROOT:/work" \
  -v "$IQ3XXS_ROOT:/iq3xxs:ro" \
  --entrypoint /opt/strata/.venv/bin/python \
  "$IMAGE" \
  /work/bench/c2_v100_contract.py \
    --url-a "$A_URL" \
    --url-b "$B_URL" \
    --expected-model-a "$A_MODEL" \
    --expected-model-b "$B_MODEL" \
    --config /work/artifacts/stage4-configs-20261021/mixed/strata-s4b-mixed-iq3xxs-agent-a.json \
    --manifest /work/bench/workloads/v100-performance-v1.json \
    --out "$OUT_CONT"
rc=$?
set -e

echo
echo "=== Host after measured batch ==="
free -h
echo
nvidia-smi --query-gpu=index,name,memory.used,memory.free,utilization.gpu,power.draw,temperature.gpu \
  --format=csv,noheader

echo
echo "Results directory: $OUT_HOST"
if [ -f "$OUT_HOST/summary.json" ]; then
  echo "Summary:"
  cat "$OUT_HOST/summary.json"
fi
echo

# Extra cold-run enforcement beyond c2_v100_contract.py's mechanical status.
if [ "$rc" -eq 0 ]; then
  python3 - "$OUT_HOST/summary.json" <<'PY'
import json,sys
with open(sys.argv[1]) as f: s=json.load(f)
assert s["pass_mechanical"] and s["active_overlap"] and s["post_health"]
assert s["warmup_count"]==0 and s["decode_overlap_s"]>0
for r,n in zip(s["requests"],(126967,126968)):
    assert r["prompt_tokens"]==n
    assert r["cache_n"]==0 and r["cached_tokens"]==0
    assert r["output_tokens"]>=1024
    print(f"[ok] {r['label']}: prefill={r['prefill_tok_s']} decode={r['decode_tok_s']} TTFT={r['ttft_s']:.2f}s")
print("[ok] MIXED C2 cold contract validated")
PY
fi
exit "$rc"
