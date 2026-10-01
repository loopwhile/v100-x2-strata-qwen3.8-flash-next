#!/usr/bin/env bash
set -euo pipefail

IMAGE="${STRATA_DOCKER_IMAGE:-strata-v100:0.1.31}"
DATA_DIR="${STRATA_DATA_DIR:-/srv/models/strata-data}"
MGPU_NAME="${STRATA_CONTAINER_NAME:-strata-v100-mgpu}"

if docker ps -a --format '{{.Names}}' | grep -qx "$MGPU_NAME"; then
  echo "Stopping/removing multi-GPU container first: $MGPU_NAME"
  docker rm -f "$MGPU_NAME" >/dev/null
fi

echo "Preparing one-GPU / low-RAM mmap Coder config using V100 #0."
echo "Existing model files in $DATA_DIR are reused."
echo
echo "Note: /data was originally populated by a root-running container."
echo "      All config writes are therefore done inside this helper container;"
echo "      no host chown/sudo is required."
echo

docker run --rm   --gpus "device=0"   --ulimit memlock=-1:-1   -v "$DATA_DIR:/data"   --entrypoint /bin/bash   "$IMAGE" -lc '
    set -euo pipefail

    mkdir -p /data/config

    # Preserve the working two-GPU config before setup rewrites the canonical
    # model config for the one-GPU mmap layout.
    if [ -f /data/config/strata-coder-iq1_m.json ]; then
      cp -f /data/config/strata-coder-iq1_m.json             /data/config/strata-coder-iq1_m-multigpu.json
      echo "[ok] preserved multi-GPU config"
    fi

    cd /opt/strata
    .venv/bin/python setup.py       --setup --yes       --family coder       --model IQ1_M       --context 131072       --kv int8       --vision no       --experimental-speed-projection off       --gpu 0       --low-ram mmap       --data-dir /data       --host 0.0.0.0       --port 8080       --no-start

    test -f /opt/strata/strata-coder-iq1_m.json
    cp -f /opt/strata/strata-coder-iq1_m.json           /data/config/strata-coder-iq1_m-single.json
    chmod 0644 /data/config/strata-coder-iq1_m-single.json
    [ ! -f /data/config/strata-coder-iq1_m-multigpu.json ] ||       chmod 0644 /data/config/strata-coder-iq1_m-multigpu.json

    echo
    echo "=== single-GPU config sanity ==="
    python3 - <<'"'"'PY'"'"'
import json
p="/data/config/strata-coder-iq1_m-single.json"
c=json.load(open(p))
a=c.get("args", [])
print("gpu:", c.get("gpu"))
print("layer_split:", c.get("layer_split"))
for k in ("--max-context","--kv","--kv-resident","--prefill","--expert-cache"):
    print(k, a[a.index(k)+1] if k in a and a.index(k)+1 < len(a) else "(absent)")
print("--mmap-experts", "--mmap-experts" in a)
print("--resident-experts", "--resident-experts" in a)
PY
  '

echo
echo "Prepared:"
echo "  $DATA_DIR/config/strata-coder-iq1_m-single.json"
echo
echo "Next: bash scripts/31-docker-run-dual-agents.sh"
