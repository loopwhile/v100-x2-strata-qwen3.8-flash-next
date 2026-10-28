#!/usr/bin/env bash
set -euo pipefail

# Stage 6: create NEW independent IQ3_S containers from the pinned Stage 5 T7-Fixed image.
# This NEVER starts, stops, deletes or upgrades existing Stage 2-5/production containers.
# Must run on P520 only, during an explicitly approved window with BOTH V100s idle.
# Usage: bash scripts/88-start-stage6-agents.sh [both|a|b]

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-both}"
IMAGE="strata-v100-jmnargi:2c9b1dd"
A_NAME="strata-s6-iq3s-agent-a"
B_NAME="strata-s6-iq3s-agent-b"
CONFIG_DIR="$ROOT/artifacts/stage6-configs-20261028/iq3s"
ARM_DIR=""
if [[ -n "${STRATA_S6_ARM_DIR:-}" ]]; then
  ARM_DIR="$(realpath "${STRATA_S6_ARM_DIR}")"
  case "$ARM_DIR" in
    "$ROOT"/results/stage6/arms/s6-*) CONFIG_DIR="$ARM_DIR" ;;
    *) echo "ERROR: candidate arm must be inside $ROOT/results/stage6/arms/s6-*" >&2; exit 1 ;;
  esac
  test -f "$ARM_DIR/experimental-flags.env" || {
    echo "ERROR: missing candidate experimental-flags.env" >&2; exit 1;
  }
  test -f "$ARM_DIR/arm.json" || { echo "ERROR: missing arm.json" >&2; exit 1; }
fi
LOG_DIR="$ROOT/results/stage6/logs"

case "$MODE" in both|a|b) ;; *) echo "Usage: $0 [both|a|b]" >&2; exit 2;; esac

command -v docker >/dev/null || { echo "ERROR: docker is unavailable" >&2; exit 1; }
command -v nvidia-smi >/dev/null || { echo "ERROR: nvidia-smi is unavailable" >&2; exit 1; }
command -v ss >/dev/null || { echo "ERROR: ss is unavailable" >&2; exit 1; }

docker image inspect "$IMAGE" >/dev/null 2>&1 || {
  echo "ERROR: missing $IMAGE. Do not auto-build or pull; see docs/STAGE6_PREP.md" >&2
  exit 1
}

EXPECTED_IMAGE_ID="sha256:5b62fa861bbdb346f81b0b3edf88ee21396fb4e59795a14b2b092dfa2e4aa156"
actual_image_id="$(docker image inspect --format '{{.Id}}' "$IMAGE")"
if [[ "$actual_image_id" != "$EXPECTED_IMAGE_ID" ]]; then
  echo "ERROR: $IMAGE resolves to unexpected image ID: $actual_image_id" >&2
  echo "Expected pinned Stage 5 T7-Fixed image: $EXPECTED_IMAGE_ID" >&2
  exit 1
fi

# In all modes reject ANY existing Stage 6 names to prevent overwriting historic test arms.
for name in "$A_NAME" "$B_NAME"; do
  if docker container inspect "$name" >/dev/null 2>&1; then
    echo "ERROR: $name already exists. Inspect/stop it first; NO automatic recreate." >&2
    exit 1
  fi
done

# Conservative guard: no older Strata containers may be running during GPU reuse.
if docker ps --format '{{.Names}}' | grep -Eq '^strata-'; then
  echo "ERROR: existing Strata container(s) are running:" >&2
  docker ps --format '  {{.Names}} ({{.Image}})'
  echo "Do not stop production without user approval." >&2
  exit 1
fi

# Also reject non-Strata processes using NVIDIA compute. Checks both GPUs conservatively.
if ! running_pids="$(nvidia-smi --query-compute-apps=pid --format=csv,noheader)"; then
  echo "ERROR: GPU process query failed; refusing to start." >&2
  exit 1
fi
if printf '%s\n' "$running_pids" | grep -Eq '^[[:space:]]*[0-9]+[[:space:]]*$'; then
  echo "ERROR: active NVIDIA compute process(es); Stage 6 would contend for GPUs:" >&2
  printf '%s\n' "$running_pids" >&2
  exit 1
fi

# Stage 6 deliberately avoids P520's production ports 8080 and 8081.
for port in 18082 18083; do
  if ss -ltnH | awk '{print $4}' | grep -Eq "[:.]$port$"; then
    echo "ERROR: host port $port is occupied; refusing to start." >&2
    exit 1
  fi
done

for f in "$CONFIG_DIR/strata-s6-iq3s-agent-a.json" "$CONFIG_DIR/strata-s6-iq3s-agent-b.json"; do
  test -f "$f" || { echo "ERROR: missing config $f" >&2; exit 1; }
done
for f in \
  /srv/models/strata-iq3s/IQ3_S/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00001-of-00002.gguf \
  /srv/models/strata-iq3s/IQ3_S/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00002-of-00002.gguf; do
  test -f "$f" || { echo "ERROR: missing IQ3_S shard $f" >&2; exit 1; }
done
test -d /srv/models/strata-iq3s/pack/iq3_s-native || { echo "ERROR: missing native IQ3_S pack" >&2; exit 1; }
test -d /srv/models/strata-data/mtp || { echo "ERROR: missing shared MTP" >&2; exit 1; }

# Exactly Stage 5 T7-Fixed baseline: no speculative auto tuning and no SM70_PERF bundle.
BASE_ENV=(
  -e STRATA_SM70_PERF=0
  -e STRATA_SELECT_SIMT=1
  -e STRATA_PF_WMMA=1
  -e STRATA_PF_WMMA2=1
  -e STRATA_STAGER_SSD=0
)

# Optional Stage 6 research flags must be passed deliberately; both agents receive the same flags.
# Do not include diagnostic profiler flags in scored C2 measurements.
OPTIONAL_FLAGS=(
  STRATA_DECODE_TIMING STRATA_VERIFY_PROFILE
  STRATA_SIDE_MIXER STRATA_GU_SWIGLU STRATA_GR_UP75 STRATA_ATTN_DAILY
  STRATA_GR_NORM_FAST STRATA_ARGMAX_ROWS_SM70 STRATA_Q8_GATHER_WIDE
  STRATA_GDN_REC_WARP STRATA_SM70_TABLE STRATA_EXPDEC STRATA_ADAPT_OVERLAP
  STRATA_FUSE_DECODE STRATA_QSA_ROWS STRATA_QIL STRATA_B6_MMVQ_ROWS
  STRATA_GR_DOWN_TG
)
EXTRA_ENV=()
for flag in "${OPTIONAL_FLAGS[@]}"; do
  if [[ -v $flag ]]; then
    value="${!flag}"
    [[ -n "$value" ]] || { echo "ERROR: empty experimental env $flag" >&2; exit 1; }
    EXTRA_ENV+=(-e "$flag=$value")
  fi
done

# Candidate flags are read as DATA, not sourced/executed as a shell program.
if [[ -n "$ARM_DIR" ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -n "$line" ]] || continue
    [[ "$line" == *"="* ]] || { echo "ERROR: malformed candidate env line" >&2; exit 1; }
    key="${line%%=*}"
    value="${line#*=}"
    if [[ ! " ${OPTIONAL_FLAGS[*]} " == *" $key "* ]] || [[ ! "$value" =~ ^[0-9]+$ ]]; then
      echo "ERROR: invalid/unapproved candidate flag: $key" >&2
      exit 1
    fi
    if [[ -v $key ]]; then
      echo "ERROR: duplicate candidate flag from shell environment: $key" >&2
      exit 1
    fi
    EXTRA_ENV+=(-e "$key=$value")
  done < "$ARM_DIR/experimental-flags.env"
  echo "Stage 6 candidate arm directory: $ARM_DIR"
fi

mkdir -p "$LOG_DIR"
start_agent() {
  local label="$1" device="$2" cpus="$3" hostport="$4" name="$5"
  echo "Creating Stage 6 Agent $label (GPU $device, CPU $cpus, host 127.0.0.1:$hostport)"
  docker run -d \
    --name "$name" \
    --cpuset-cpus "$cpus" \
    --gpus "\"device=$device\"" \
    --restart no \
    -p "127.0.0.1:$hostport:8080" \
    -v /srv/models/strata-iq3s:/iq3s:ro \
    -v /srv/models/strata-data/mtp:/shared-mtp:ro \
    -v "$LOG_DIR:/stage6-logs" \
    -v "$CONFIG_DIR/$name.json:/opt/strata/config.json:ro" \
    "${BASE_ENV[@]}" "${EXTRA_ENV[@]}" \
    --entrypoint /opt/strata/.venv/bin/python \
    "$IMAGE" \
    /opt/strata/serve/server.py \
      --engine strata --config /opt/strata/config.json --host 0.0.0.0 --port 8080
}

if [[ "$MODE" == both || "$MODE" == a ]]; then
  start_agent A 0 "0-2,6-8" 18082 "$A_NAME"
fi
if [[ "$MODE" == both || "$MODE" == b ]]; then
  start_agent B 1 "3-5,9-11" 18083 "$B_NAME"
fi

echo "Containers created. They can take time to load the model."
echo "Check: bash scripts/90-status-stage6-agents.sh"
echo "Stop:  bash scripts/89-stop-stage6-agents.sh"
echo "Existing production ports/tunnels have NOT been changed."
