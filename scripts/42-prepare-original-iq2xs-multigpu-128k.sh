#!/usr/bin/env bash
set -euo pipefail

# Prepare, but do not start, a 2x V100 / 128K config for the original
# Qwen3.8-Flash-Next IQ2_XS.
#
# This first validation intentionally uses normal (non-low-RAM) expert loading:
# the full expert arena is loaded into system RAM, while the two V100s share the
# GPU expert cache through Strata's layer split.  The later dual-agent test will
# use GGUF-in-place mmap instead.
#
# Existing Coder containers and /srv/models data are not modified.

IMAGE="${STRATA_DOCKER_IMAGE:-strata-v100:0.1.31}"
IQ2XS_ROOT="${IQ2XS_ROOT:-$HOME/models/strata-iq2xs}"
CONFIG_DIR="$IQ2XS_ROOT/config"
LOG_DIR="$IQ2XS_ROOT/logs"
CFG="$CONFIG_DIR/strata-iq2xs-multigpu.json"

SHARD1="$IQ2XS_ROOT/model/Qwen3.8-Flash-Next-GSQ-RCO-IQ2_XS-00001-of-00002.gguf"
SHARD2="$IQ2XS_ROOT/model/Qwen3.8-Flash-Next-GSQ-RCO-IQ2_XS-00002-of-00002.gguf"
PACK="$IQ2XS_ROOT/pack/iq2_xs-native"
MTP_HOST="${STRATA_MTP_DIR:-/srv/models/strata-data/mtp}"

for f in \
  "$SHARD1" \
  "$SHARD2" \
  "$PACK/dense.bin" \
  "$PACK/index.txt" \
  "$PACK/native_experts.txt" \
  "$PACK/tokenizer/vocab.json" \
  "$PACK/tokenizer/chat_template.jinja" \
  "$MTP_HOST/rt/experts.bin"
do
  [ -f "$f" ] || {
    echo "ERROR: required file is missing: $f" >&2
    exit 1
  }
done

if [ -e "$PACK/experts.bin" ]; then
  echo "ERROR: $PACK/experts.bin exists." >&2
  echo "       This config is meant to validate the no-experts.bin native pack." >&2
  exit 1
fi

docker image inspect "$IMAGE" >/dev/null 2>&1 || {
  echo "ERROR: Docker image not found: $IMAGE" >&2
  exit 1
}

mkdir -p "$CONFIG_DIR" "$LOG_DIR"

# Read the CUDA library directories from the exact image that will run Strata.
BUILD_JSON="$(docker run --rm --entrypoint cat "$IMAGE" /opt/strata/engine/BUILD.json)"
export BUILD_JSON CFG

python3 - <<'PY'
import json
import os
from pathlib import Path

build = json.loads(os.environ["BUILD_JSON"])
cfg_path = Path(os.environ["CFG"])

cuda_dirs = build.get("lib_dirs") or build.get("cuda_dirs") or []

cfg = {
    "exe": "/opt/strata/engine/strata",
    "args": [
        "--pack", "/iq2/pack/iq2_xs-native",
        "--native", "/iq2/model/Qwen3.8-Flash-Next-GSQ-RCO-IQ2_XS-00001-of-00002.gguf",
        "--ple-gguf", "/iq2/model/Qwen3.8-Flash-Next-GSQ-RCO-IQ2_XS-00002-of-00002.gguf",
        "--expert-profile", "/opt/strata/data/expert-profile.bin",
        "--expert-cache", "auto",
        "--prefill", "auto",
        "--spec", "4",
        "--spec-min-p", "0.5",
        "--mtp", "/shared-mtp/rt",
        "--max-context", "131072",
        "--kv", "int8",
        "--kv-resident", "32768",
    ],
    "cwd": "/opt/strata",
    "tokenizer": "/iq2/pack/iq2_xs-native/tokenizer",
    "model_name": "qwen3.8-flash-next-iq2_xs",
    "log": "/iq2-logs/strata-iq2xs-mgpu.log",
    "lib_dirs": cuda_dirs,
    "port": 8080,
    "gpu": [0, 1],
    "gpus_asked": True,
    "layer_split": "auto",
}

cfg_path.write_text(json.dumps(cfg, indent=1) + "\n", encoding="utf-8")
PY

chmod 0644 "$CFG"

echo "=== IQ2_XS multi-GPU config prepared ==="
echo "Config: $CFG"
echo

python3 - "$CFG" <<'PY'
import json
import sys

p = sys.argv[1]
c = json.load(open(p, encoding="utf-8"))
a = c["args"]

def value(k):
    return a[a.index(k) + 1] if k in a else "(absent)"

print("model_name       :", c.get("model_name"))
print("gpu              :", c.get("gpu"))
print("layer_split      :", c.get("layer_split"))
print("--max-context    :", value("--max-context"))
print("--kv             :", value("--kv"))
print("--kv-resident    :", value("--kv-resident"))
print("--pack           :", value("--pack"))
print("--native         :", value("--native"))
print("--ple-gguf       :", value("--ple-gguf"))
print("--mtp            :", value("--mtp"))
print("--mmap-experts   :", "--mmap-experts" in a)
print("--resident-experts:", "--resident-experts" in a)
PY

echo
echo "=== Host state (read-only) ==="
free -h
echo
nvidia-smi --query-gpu=index,name,memory.used,memory.free --format=csv,noheader
echo
echo "Existing Coder containers (not stopped or modified):"
docker ps -a --filter name=strata-agent-a --filter name=strata-agent-b \
  --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'
echo
echo "No server was started."
echo "No files under /srv/models were changed."
