#!/usr/bin/env bash
set -euo pipefail

# Download the original Qwen3.8-Flash-Next IQ2_XS GGUF shards into a
# host-local directory, independently from the existing Coder baseline.
#
# Default target:
#   ~/models/strata-iq2xs/model
#
# Override with:
#   IQ2XS_ROOT=/path/to/strata-iq2xs bash scripts/40-download-original-iq2xs.sh

MODEL_ROOT="${IQ2XS_ROOT:-$HOME/models/strata-iq2xs}"
MODEL_DIR="$MODEL_ROOT/model"

HF_REPO="ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF"
HF_REV="ed59f92082b1e93c0e96d60a8b11aab089b52f09"
QUANT="IQ2_XS"

FILES=(
  "Qwen3.8-Flash-Next-GSQ-RCO-IQ2_XS-00001-of-00002.gguf"
  "Qwen3.8-Flash-Next-GSQ-RCO-IQ2_XS-00002-of-00002.gguf"
)

# Conservative lower bounds. The publisher lists the two shards as
# approximately 39.2 GB and 28.8 GB respectively.
MIN_BYTES=(
  38000000000
  28000000000
)

command -v curl >/dev/null || {
  echo "ERROR: curl is required." >&2
  exit 1
}

command -v od >/dev/null || {
  echo "ERROR: od is required (coreutils)." >&2
  exit 1
}

mkdir -p "$MODEL_DIR"

echo "=== Original Qwen3.8-Flash-Next IQ2_XS download ==="
echo "Repository : $HF_REPO"
echo "Revision   : $HF_REV"
echo "Target     : $MODEL_DIR"
echo
echo "Current filesystem:"
df -hT "$MODEL_DIR"
echo

gguf_magic_ok() {
  local f="$1"
  [ -f "$f" ] || return 1
  local magic
  magic="$(dd if="$f" bs=4 count=1 status=none | od -An -tx1 | tr -d ' \n')"
  [ "$magic" = "47475546" ]
}

remote_size() {
  local url="$1"
  # Hugging Face normally exposes the backing object size through
  # x-linked-size. If it is absent, return nothing and use the conservative
  # local sanity check instead.
  curl -fsSIL --retry 5 --retry-delay 2 "$url" 2>/dev/null |
    tr -d '\r' |
    awk -F': *' 'tolower($1)=="x-linked-size" {print $2}' |
    tail -n1
}

validate_file() {
  local f="$1"
  local expected="$2"
  local minimum="$3"

  [ -f "$f" ] || {
    echo "ERROR: missing file: $f" >&2
    return 1
  }

  local actual
  actual="$(stat -c '%s' "$f")"

  if [ -n "$expected" ]; then
    if [ "$actual" -ne "$expected" ]; then
      echo "ERROR: size mismatch for $(basename "$f")" >&2
      echo "       expected: $expected bytes" >&2
      echo "       actual  : $actual bytes" >&2
      return 1
    fi
  elif [ "$actual" -lt "$minimum" ]; then
    echo "ERROR: file is unexpectedly small: $(basename "$f")" >&2
    echo "       actual : $actual bytes" >&2
    echo "       minimum: $minimum bytes" >&2
    return 1
  fi

  if ! gguf_magic_ok "$f"; then
    echo "ERROR: GGUF magic is invalid: $f" >&2
    return 1
  fi
}

download_one() {
  local idx="$1"
  local name="${FILES[$idx]}"
  local minimum="${MIN_BYTES[$idx]}"
  local dst="$MODEL_DIR/$name"
  local part="$dst.part"
  local url="https://huggingface.co/$HF_REPO/resolve/$HF_REV/$QUANT/$name?download=true"

  echo "=== $name ==="

  local expected
  expected="$(remote_size "$url" || true)"
  if [ -n "$expected" ]; then
    echo "Remote size: $expected bytes"
  else
    echo "Remote size header unavailable; conservative size validation will be used."
  fi

  if [ -f "$dst" ]; then
    if validate_file "$dst" "$expected" "$minimum"; then
      echo "[ok] already complete; skipping"
      echo
      return 0
    fi

    echo "ERROR: final file exists but failed validation." >&2
    echo "       It was not modified: $dst" >&2
    exit 1
  fi

  if [ -f "$part" ]; then
    echo "Resuming partial download: $(du -h "$part" | awk '{print $1}')"
  else
    echo "Starting download."
  fi

  # -C - resumes a .part file after interruption. Download directly into the
  # target filesystem so there is no second 68 GB cache/copy elsewhere.
  curl     --fail     --location     --retry 20     --retry-all-errors     --retry-delay 5     --continue-at -     --progress-bar     --output "$part"     "$url"

  validate_file "$part" "$expected" "$minimum"
  mv "$part" "$dst"
  echo "[ok] $(basename "$dst")"
  echo
}

download_one 0
download_one 1

echo "=== Download complete ==="
ls -lh "$MODEL_DIR"
echo
du -sh "$MODEL_DIR"
df -hT "$MODEL_DIR"
echo
echo "No files under /srv/models were changed."
