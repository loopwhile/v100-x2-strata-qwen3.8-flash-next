#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"

activate_cuda12
[ -d "$STRATA_DIR/.git" ] || { echo "ERROR: prepare Strata first." >&2; exit 1; }

mkdir -p "$CONFIGS_DIR" "$RESULTS_DIR" "$DATA_DIR"

# Preserve the one-server/two-GPU baseline config before setup rewrites the Coder config.
if [ -f "$CONFIGS_DIR/coder-128k-multigpu.json" ]; then
  cp "$CONFIGS_DIR/coder-128k-multigpu.json" "$CONFIGS_DIR/coder-128k-multigpu.saved.json"
fi

echo "Preparing low-RAM/mmap Coder pack for independent servers."
echo "This reuses the already downloaded model and writes experts.bin if it does not exist."
echo

(
  cd "$STRATA_DIR"
  ./setup.sh     --setup     --family coder     --model IQ1_M     --context 131072     --kv int8     --vision no     --experimental-speed-projection off     --gpu 0     --low-ram mmap     --build     --yes     --no-start     --data-dir "$DATA_DIR"
)

cfg="$(find "$STRATA_DIR" -maxdepth 1 -type f -name 'strata-*coder*iq1_m*.json' | head -n1)"
if [ -z "$cfg" ]; then
  cfg="$(find "$STRATA_DIR" -maxdepth 1 -type f -name 'strata-*.json' -printf '%T@ %p\n' | sort -nr | awk 'NR==1{print $2}')"
fi
[ -n "$cfg" ] || { echo "ERROR: generated Strata config not found" >&2; exit 1; }

cp "$cfg" "$CONFIGS_DIR/coder-128k-agent-base.json"

python3 - "$cfg" "$CONFIGS_DIR" "$RESULTS_DIR" <<'PY'
import copy, json, sys
from pathlib import Path

src = Path(sys.argv[1])
outdir = Path(sys.argv[2])
results = Path(sys.argv[3])
base = json.loads(src.read_text(encoding="utf-8"))

args = base.get("args", [])
if "--mmap-experts" not in args:
    raise SystemExit("expected --mmap-experts in low-RAM base config")
if "--max-context" not in args or args[args.index("--max-context")+1] != "131072":
    raise SystemExit("expected --max-context 131072")
if "--kv" not in args or args[args.index("--kv")+1] != "int8":
    raise SystemExit("expected --kv int8")
if "--kv-resident" not in args:
    raise SystemExit("expected KV streaming (--kv-resident) for the 128K configuration")

for name, gpu, port in (("agent-a", 0, 8080), ("agent-b", 1, 8081)):
    cfg = copy.deepcopy(base)
    cfg["gpu"] = gpu
    cfg["gpus_asked"] = True
    cfg.pop("layer_split", None)
    cfg["port"] = port
    cfg["log"] = str(results / f"{name}-engine.log")
    p = outdir / f"{name}.json"
    p.write_text(json.dumps(cfg, indent=1), encoding="utf-8")
    print(f"wrote {p}: GPU {gpu}, port {port}")

print("base args:")
for k in ("--max-context", "--kv", "--kv-resident", "--prefill", "--expert-cache"):
    print(k, args[args.index(k)+1] if k in args else "(absent)")
print("--mmap-experts", "--mmap-experts" in args)
PY

echo
echo "Dual-agent configs are ready:"
echo "  $CONFIGS_DIR/agent-a.json -> GPU0 :8080"
echo "  $CONFIGS_DIR/agent-b.json -> GPU1 :8081"
echo
echo "Next: bash scripts/11-start-dual-agents.sh"
