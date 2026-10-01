#!/usr/bin/env bash
set -euo pipefail

# Prepare two independent one-V100 / 128K / GGUF-in-place mmap configs
# for original Qwen3.8-Flash-Next IQ2_XS.
#
# Each future container sees exactly one physical GPU, so both configs use
# gpu=0 inside their own CUDA namespace. This script does not stop/start
# containers and does not modify model data.

IQ2XS_ROOT="${IQ2XS_ROOT:-$HOME/models/strata-iq2xs}"
SRC="$IQ2XS_ROOT/config/strata-iq2xs-single-mmap.json"
CFG_A="$IQ2XS_ROOT/config/strata-iq2xs-agent-a.json"
CFG_B="$IQ2XS_ROOT/config/strata-iq2xs-agent-b.json"
PACK="$IQ2XS_ROOT/pack/iq2_xs-native"

[ -f "$SRC" ] || {
  echo "ERROR: missing single-mmap config: $SRC" >&2
  exit 1
}

[ -f "$PACK/native_experts.txt" ] || {
  echo "ERROR: native pack is incomplete: $PACK/native_experts.txt missing" >&2
  exit 1
}

if [ -e "$PACK/experts.bin" ]; then
  echo "ERROR: $PACK/experts.bin exists." >&2
  echo "       Refusing to prepare GGUF-in-place dual-agent configs." >&2
  exit 1
fi

export SRC CFG_A CFG_B
python3 - <<'PY'
import json
import os
from pathlib import Path

src = Path(os.environ["SRC"])
base = json.loads(src.read_text(encoding="utf-8"))

def make(dst_s: str, name: str, log: str):
    c = json.loads(json.dumps(base))
    args = list(c["args"])
    if "--mmap-experts" not in args:
        args.append("--mmap-experts")
    while "--resident-experts" in args:
        args.remove("--resident-experts")
    c["args"] = args

    # Each container will expose only one physical GPU. Inside the container
    # that card is CUDA device 0, regardless of whether it is host GPU0 or GPU1.
    c["gpu"] = 0
    c["gpus_asked"] = True
    c.pop("layer_split", None)
    c.pop("split_skip_if_fits", None)

    c["model_name"] = name
    c["log"] = log
    c["port"] = 8080

    Path(dst_s).write_text(json.dumps(c, indent=1) + "\n", encoding="utf-8")

make(
    os.environ["CFG_A"],
    "qwen3.8-flash-next-iq2_xs-mmap-a",
    "/iq2-logs/strata-iq2xs-agent-a.log",
)
make(
    os.environ["CFG_B"],
    "qwen3.8-flash-next-iq2_xs-mmap-b",
    "/iq2-logs/strata-iq2xs-agent-b.log",
)
PY

chmod 0644 "$CFG_A" "$CFG_B"

echo "=== IQ2_XS dual mmap configs prepared ==="
echo

python3 - "$CFG_A" "$CFG_B" <<'PY'
import json
import sys

for p in sys.argv[1:]:
    c = json.load(open(p, encoding="utf-8"))
    a = c["args"]

    def value(k):
        return a[a.index(k)+1] if k in a and a.index(k)+1 < len(a) else "(absent)"

    print(p)
    print("  model_name         :", c.get("model_name"))
    print("  gpu                :", c.get("gpu"))
    print("  layer_split        :", c.get("layer_split", "(absent)"))
    print("  log                :", c.get("log"))
    print("  --max-context      :", value("--max-context"))
    print("  --kv               :", value("--kv"))
    print("  --kv-resident      :", value("--kv-resident"))
    print("  --mmap-experts     :", "--mmap-experts" in a)
    print("  --resident-experts :", "--resident-experts" in a)
    print()
PY

echo "=== Current containers (not modified) ==="
docker ps -a   --filter name=strata-iq2xs-single-mmap   --filter name=strata-iq2xs-agent-a   --filter name=strata-iq2xs-agent-b   --filter name=strata-iq2xs-mgpu   --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'

echo
echo "=== Current host memory / GPUs ==="
free -h
echo
nvidia-smi --query-gpu=index,name,memory.used,memory.free --format=csv,noheader
echo
echo "No container was stopped or started."
echo "No files under /srv/models were changed."
