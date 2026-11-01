#!/usr/bin/env bash
set -euo pipefail
# Run on P520; creates a new, isolated pair for a single compatibility smoke.
ROOT="$HOME/v100-x2-strata-qwen3.8-flash-next"
DIR="$ROOT/results/stage7-iq3xxs-smoke"
IMAGE=strata-v100-upstream:0.1.54
MANIFEST="$ROOT/bench/workloads/v100-performance-v1.json"
test ! -e "$DIR" || { echo 'Smoke directory already exists; refusing to overwrite' >&2; exit 1; }
test -z "$(docker ps -q)" || { echo 'Running containers found; refusing to start' >&2; exit 1; }
test -z "$(nvidia-smi --query-compute-apps=pid --format=csv,noheader)" || { echo 'GPU workload found' >&2; exit 1; }
for port in 18084 18085; do
  if ss -H -tln | awk '{print $4}' | grep -Eq ":${port}$"; then echo "Port $port in use" >&2; exit 1; fi
done
for s in a b; do
  if docker inspect "strata-s7xxs-smoke-$s" >/dev/null 2>&1; then echo 'Smoke container exists' >&2; exit 1; fi
done
test "$(sha256sum "$MANIFEST" | cut -d' ' -f1)" = e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca
docker image inspect "$IMAGE" >/dev/null
test -d /srv/models/strata-iq3xxs/pack/iq3_xxs-native
test -d /srv/models/strata-data/mtp/rt
mkdir -p "$DIR/logs"
python3 - "$ROOT" "$DIR" <<'PY'
import json, pathlib, sys
root, dest = map(pathlib.Path, sys.argv[1:])
for s in 'ab':
    config = json.loads((root / 'results/stage5-iq3xxs' / f'agent-{s}.json').read_text())
    config['model_name'] = f'qwen3.8-flash-next-iq3_xxs-s7smoke-{s}'
    (dest / f'agent-{s}.json').write_text(json.dumps(config, indent=2) + '\n')
PY
sha256sum "$DIR"/agent-*.json > "$DIR/config-sha256.txt"
docker image inspect "$IMAGE" --format '{{.Id}}' > "$DIR/image-id.txt"
created=()
cleanup_on_failure() {
  rc=$?
  if (( rc != 0 )); then
    for name in "${created[@]}"; do docker stop -t 20 "$name" >/dev/null 2>&1 || :; done
  fi
}
trap cleanup_on_failure EXIT
for spec in 'a 0 0-2,6-8 18084' 'b 1 3-5,9-11 18085'; do
  read -r s gpu cpus port <<< "$spec"
  name="strata-s7xxs-smoke-$s"
  docker run -d --name "$name" --cpuset-cpus "$cpus" --gpus "\"device=$gpu\"" \
    -p "127.0.0.1:$port:8080" -v /srv/models/strata-iq3xxs:/iq3xxs:ro \
    -v "$DIR/logs:/trial-logs" -v /srv/models/strata-data/mtp:/shared-mtp:ro \
    -v "$DIR/agent-$s.json:/opt/strata/config.json:ro" --restart no \
    --entrypoint /opt/strata/.venv/bin/python "$IMAGE" \
    /opt/strata/serve/server.py --engine strata --config /opt/strata/config.json --host 0.0.0.0 --port 8080 > "$DIR/container-$s.id"
  created+=("$name")
done
