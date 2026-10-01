#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"

activate_cuda12

[ -d "$STRATA_DIR/.git" ] || {
  echo "ERROR: $STRATA_DIR not prepared. Run scripts/01-prepare-strata.sh first." >&2
  exit 1
}

FAMILY="${STRATA_FAMILY:-coder}"
MODEL="${STRATA_MODEL:-IQ1_M}"
CONTEXT="${STRATA_CONTEXT:-131072}"

case "$FAMILY:$MODEL" in
  coder:IQ1_M|qwen:Q2_0|qwen:IQ2_XS|qwen:IQ3_XXS|qwen:IQ3_S|swift:Q2_0|swift:IQ2_XS|swift:IQ3_XXS) ;;
  *)
    echo "ERROR: unsupported FAMILY:MODEL combination: $FAMILY:$MODEL" >&2
    exit 1
    ;;
esac

mkdir -p "$DATA_DIR" "$CONFIGS_DIR" "$RESULTS_DIR"

echo "=== target ==="
echo "Strata:      $STRATA_DIR"
echo "Data:        $DATA_DIR"
echo "GPU mode:    V100 #0 + V100 #1 layer split"
echo "Family:      $FAMILY"
echo "Model:       $MODEL"
echo "Context:     $CONTEXT"
echo "KV:          INT8"
echo "KV stream:   setup should enable --kv-resident 32768 at 128K"
echo "Low RAM:     off (one shared model across both GPUs)"
echo "Vision:      off"
echo

(
  cd "$STRATA_DIR"
  ./setup.sh     --setup     --family "$FAMILY"     --model "$MODEL"     --context "$CONTEXT"     --kv int8     --vision no     --experimental-speed-projection off     --gpus 0,1     --layer-split auto     --low-ram off     --build     --yes     --no-start     --data-dir "$DATA_DIR"
)

cfg="$(find "$STRATA_DIR" -maxdepth 1 -type f -name 'strata-*.json' -printf '%T@ %p\n' | sort -nr | awk 'NR==1{print $2}')"
[ -n "$cfg" ] || { echo "ERROR: generated Strata config not found" >&2; exit 1; }

slug="$(printf '%s-%s' "$FAMILY" "$MODEL" | tr '[:upper:]_' '[:lower:]-')"
saved="$CONFIGS_DIR/$slug-128k-multigpu.json"
cp "$cfg" "$saved"

echo
echo "Generated config: $cfg"
python3 - "$cfg" <<'PY'
import json, sys
p=sys.argv[1]
c=json.load(open(p))
print("model:", c.get("model_name"))
print("gpu:", c.get("gpu"))
print("layer_split:", c.get("layer_split"))
print("port:", c.get("port"))
args=c.get("args",[])
for k in ("--max-context","--kv","--kv-resident","--prefill","--expert-cache"):
    print(k, args[args.index(k)+1] if k in args and args.index(k)+1 < len(args) else "(absent)")
print("--mmap-experts", "--mmap-experts" in args)
print("--resident-experts", "--resident-experts" in args)
PY

echo
echo "Saved harness copy: $saved"
echo "Next: bash scripts/03-start-multigpu.sh"
