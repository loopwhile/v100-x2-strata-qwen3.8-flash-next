#!/usr/bin/env bash
set -euo pipefail

# Prepare a one-V100 / 128K / GGUF-in-place mmap config for original IQ2_XS.
# This only writes a new config file. It does not stop or start any container.

IQ2XS_ROOT="${IQ2XS_ROOT:-$HOME/models/strata-iq2xs}"
SRC="$IQ2XS_ROOT/config/strata-iq2xs-multigpu.json"
DST="$IQ2XS_ROOT/config/strata-iq2xs-single-mmap.json"
PACK="$IQ2XS_ROOT/pack/iq2_xs-native"

[ -f "$SRC" ] || {
  echo "ERROR: missing source config: $SRC" >&2
  exit 1
}

[ -f "$PACK/native_experts.txt" ] || {
  echo "ERROR: native pack is incomplete: $PACK/native_experts.txt missing" >&2
  exit 1
}

if [ -e "$PACK/experts.bin" ]; then
  echo "ERROR: $PACK/experts.bin exists." >&2
  echo "       Refusing to prepare the GGUF-in-place mmap config." >&2
  exit 1
fi

export SRC DST
python3 - <<'PY'
import json
import os
from pathlib import Path

src = Path(os.environ["SRC"])
dst = Path(os.environ["DST"])
cfg = json.loads(src.read_text(encoding="utf-8"))

args = list(cfg["args"])
for flag in ("--resident-experts",):
    while flag in args:
        args.remove(flag)
if "--mmap-experts" not in args:
    args.append("--mmap-experts")

cfg["args"] = args
cfg["gpu"] = 0
cfg["gpus_asked"] = True
cfg.pop("layer_split", None)
cfg.pop("split_skip_if_fits", None)
cfg["model_name"] = "qwen3.8-flash-next-iq2_xs-mmap"
cfg["log"] = "/iq2-logs/strata-iq2xs-single-mmap.log"
cfg["port"] = 8080

dst.write_text(json.dumps(cfg, indent=1) + "\n", encoding="utf-8")
PY

chmod 0644 "$DST"

echo "=== IQ2_XS single-V100 mmap config prepared ==="
echo "Config: $DST"
echo

python3 - "$DST" <<'PY'
import json
import sys

c = json.load(open(sys.argv[1], encoding="utf-8"))
a = c["args"]

def value(k):
    return a[a.index(k)+1] if k in a and a.index(k)+1 < len(a) else "(absent)"

print("model_name        :", c.get("model_name"))
print("gpu               :", c.get("gpu"))
print("layer_split       :", c.get("layer_split", "(absent)"))
print("--max-context     :", value("--max-context"))
print("--kv              :", value("--kv"))
print("--kv-resident     :", value("--kv-resident"))
print("--pack            :", value("--pack"))
print("--native          :", value("--native"))
print("--ple-gguf        :", value("--ple-gguf"))
print("--mmap-experts    :", "--mmap-experts" in a)
print("--resident-experts:", "--resident-experts" in a)
PY

echo
echo "Current multi-GPU container was not modified:"
docker ps -a --filter name=strata-iq2xs-mgpu   --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'
echo
echo "No container was stopped or started."
echo "No files under /srv/models were changed."
