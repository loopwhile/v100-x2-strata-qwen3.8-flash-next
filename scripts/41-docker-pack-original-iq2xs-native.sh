#!/usr/bin/env bash
set -euo pipefail

# Build a native Strata pack for the original Qwen3.8-Flash-Next IQ2_XS
# without experts.bin. Strata 0.1.31 can mmap expert slices directly from
# the GGUF shards when native_experts.txt exists and experts.bin does not.
#
# Existing Coder data under /srv/models is not touched.

IMAGE="${STRATA_DOCKER_IMAGE:-strata-v100:0.1.31}"
IQ2XS_ROOT="${IQ2XS_ROOT:-$HOME/models/strata-iq2xs}"
MODEL_DIR="$IQ2XS_ROOT/model"
PACK_DIR="$IQ2XS_ROOT/pack/iq2_xs-native"

SHARD1="$MODEL_DIR/Qwen3.8-Flash-Next-GSQ-RCO-IQ2_XS-00001-of-00002.gguf"
SHARD2="$MODEL_DIR/Qwen3.8-Flash-Next-GSQ-RCO-IQ2_XS-00002-of-00002.gguf"

for f in "$SHARD1" "$SHARD2"; do
  [ -f "$f" ] || {
    echo "ERROR: missing model shard: $f" >&2
    exit 1
  }
done

if find "$MODEL_DIR" -maxdepth 1 -type f -name '*.part' -print -quit | grep -q .; then
  echo "ERROR: partial download file still exists under $MODEL_DIR" >&2
  find "$MODEL_DIR" -maxdepth 1 -type f -name '*.part' -ls >&2
  exit 1
fi

mkdir -p "$PACK_DIR"

# This workflow intentionally uses GGUF-in-place expert reads.
# Refuse to continue if an experts.bin is already present because the engine
# would prefer that file and silently defeat the purpose of this test.
if [ -e "$PACK_DIR/experts.bin" ] || [ -e "$PACK_DIR/experts.bin.tmp" ]; then
  echo "ERROR: experts.bin (or experts.bin.tmp) exists in $PACK_DIR" >&2
  echo "       Not modifying it automatically." >&2
  exit 1
fi

echo "=== Build native IQ2_XS pack (NO experts.bin) ==="
echo "Image : $IMAGE"
echo "Model : $MODEL_DIR"
echo "Pack  : $PACK_DIR"
echo
echo "Model shards:"
ls -lh "$SHARD1" "$SHARD2"
echo
echo "Filesystem before:"
df -hT "$IQ2XS_ROOT"
echo

docker image inspect "$IMAGE" >/dev/null 2>&1 || {
  echo "ERROR: Docker image not found: $IMAGE" >&2
  exit 1
}

docker run --rm \
  --network none \
  --user "$(id -u):$(id -g)" \
  -e HOME=/tmp \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -v "$IQ2XS_ROOT:/iq2" \
  --entrypoint /opt/strata/.venv/bin/python \
  "$IMAGE" \
  /opt/strata/tools/iq_pack.py \
    --gguf /iq2/model/Qwen3.8-Flash-Next-GSQ-RCO-IQ2_XS-00001-of-00002.gguf \
    --out /iq2/pack/iq2_xs-native

echo
echo "=== Pack verification ==="

for f in \
  "$PACK_DIR/dense.bin" \
  "$PACK_DIR/index.txt" \
  "$PACK_DIR/native_experts.txt" \
  "$PACK_DIR/tokenizer/vocab.json" \
  "$PACK_DIR/tokenizer/chat_template.jinja"
do
  [ -f "$f" ] || {
    echo "ERROR: expected pack artifact is missing: $f" >&2
    exit 1
  }
done

if [ -e "$PACK_DIR/experts.bin" ]; then
  echo "ERROR: experts.bin was created unexpectedly." >&2
  exit 1
fi

echo "[ok] native pack complete"
echo "[ok] experts.bin is absent; expert data will remain in the GGUF shards"
echo

echo "Pack files:"
du -ah "$PACK_DIR" | sort -h | tail -n 30
echo
echo "Pack total:"
du -sh "$PACK_DIR"
echo
echo "Filesystem after:"
df -hT "$IQ2XS_ROOT"
echo
echo "No files under /srv/models were changed."
