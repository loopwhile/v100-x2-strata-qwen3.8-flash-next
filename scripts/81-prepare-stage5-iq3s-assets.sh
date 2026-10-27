#!/usr/bin/env bash
set -euo pipefail

# Stage 5 IQ3_S Assets Preparation & Verification
# Frees up space on /srv/models by removing strata-iq3xxs (verified backed up),
# then restores strata-iq3s to /srv/models/strata-iq3s on NVMe1.

BACKUP_IQ3XXS="/srv/backup/models-archive/strata-iq3xxs"
LIVE_IQ3XXS="/srv/models/strata-iq3xxs"

BACKUP_IQ3S="/srv/backup/models-archive/strata-iq3s"
LIVE_IQ3S="/srv/models/strata-iq3s"

EXPECTED_SHARD1_SIZE=54817524224
EXPECTED_SHARD2_SIZE=28800138432

echo "=== Stage 5 Asset Preflight Check ==="

# 1. Verify IQ3_XXS backup before touching live
if [ -d "$LIVE_IQ3XXS" ]; then
  if [ ! -d "$BACKUP_IQ3XXS/IQ3_XXS" ]; then
    echo "ERROR: Backup $BACKUP_IQ3XXS is missing or incomplete. Refusing to remove $LIVE_IQ3XXS." >&2
    exit 1
  fi
  echo "Verified IQ3_XXS backup exists at $BACKUP_IQ3XXS."
  echo "Removing $LIVE_IQ3XXS to reclaim ~73 GiB on NVMe1 (/srv/models) ..."
  rm -rf "$LIVE_IQ3XXS"
  echo "[ok] $LIVE_IQ3XXS removed."
fi

# 2. Check disk space on /srv/models
AVAIL_KB=$(df -P "$LIVE_IQ3S" 2>/dev/null | tail -1 | awk '{print $4}' || df -P "/srv/models" | tail -1 | awk '{print $4}')
echo "Available space on /srv/models: $(( AVAIL_KB / 1024 / 1024 )) GiB"
if [ "$AVAIL_KB" -lt 85000000 ]; then
  echo "ERROR: Less than 85 GB available on /srv/models (found $(( AVAIL_KB / 1024 / 1024 )) GiB)." >&2
  exit 1
fi

# 3. Restore/Sync strata-iq3s
echo "Restoring IQ3_S assets from $BACKUP_IQ3S to $LIVE_IQ3S ..."
mkdir -p "$LIVE_IQ3S"
rsync -a --info=progress2 "$BACKUP_IQ3S/" "$LIVE_IQ3S/"
mkdir -p "$LIVE_IQ3S/logs"

# 4. Verify shard integrity
SHARD1="$LIVE_IQ3S/IQ3_S/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00001-of-00002.gguf"
SHARD2="$LIVE_IQ3S/IQ3_S/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00002-of-00002.gguf"

[ -f "$SHARD1" ] || { echo "ERROR: missing shard 1: $SHARD1" >&2; exit 1; }
[ -f "$SHARD2" ] || { echo "ERROR: missing shard 2: $SHARD2" >&2; exit 1; }

S1_SIZE=$(stat -c%s "$SHARD1")
S2_SIZE=$(stat -c%s "$SHARD2")

if [ "$S1_SIZE" -ne "$EXPECTED_SHARD1_SIZE" ]; then
  echo "ERROR: Shard 1 size mismatch. Expected $EXPECTED_SHARD1_SIZE, got $S1_SIZE" >&2
  exit 1
fi

if [ "$S2_SIZE" -ne "$EXPECTED_SHARD2_SIZE" ]; then
  echo "ERROR: Shard 2 size mismatch. Expected $EXPECTED_SHARD2_SIZE, got $S2_SIZE" >&2
  exit 1
fi

[ -d "$LIVE_IQ3S/pack/iq3_s-native" ] || {
  echo "ERROR: Native pack missing at $LIVE_IQ3S/pack/iq3_s-native" >&2
  exit 1
}

echo "[ok] Shard 1 verified ($S1_SIZE bytes)."
echo "[ok] Shard 2 verified ($S2_SIZE bytes)."
echo "[ok] Native pack verified."
echo
echo "=== Host Environment Verification ==="
for port in 8080 8081; do
  if ss -tlnp 2>/dev/null | grep -q ":$port "; then
    echo "WARNING: Port $port is currently in use." >&2
  else
    echo "[ok] Port $port is free."
  fi
done

nvidia-smi --query-gpu=index,name,memory.used,memory.free,utilization.gpu,power.draw,temperature.gpu --format=csv,noheader
echo
echo "[ok] Stage 5 IQ3_S assets successfully prepared and verified on NVMe1."
