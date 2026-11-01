#!/usr/bin/env bash
set -Eeuo pipefail
# Execute only on P520, from an isolated build context copied from ThinkPad.
ARM="${1:?15 or 16 required}"
ATTEMPT="${2:-1}"
[[ "$ATTEMPT" =~ ^[1-9][0-9]*$ ]] || exit 2
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
case "$ARM" in
  15) FILE=Dockerfile.stage7-v100-wmma2; IMAGE=strata-v100-upstream:0.1.54-v100-wmma2-s7-20261101 ;;
  16) FILE=Dockerfile.stage7-v100-wmma2-lean; IMAGE=strata-v100-upstream:0.1.54-v100-wmma2-lean-s7-20261101 ;;
  *) exit 2 ;;
esac
if [[ "${3:-full}" == resume15 && "$ARM" == 15 ]]; then FILE=Dockerfile.stage7-v100-wmma2-finish; fi
RESULTS="$HOME/v100-x2-strata-qwen3.8-flash-next/results"
DIR="$RESULTS/stage7-iq3xxs-v100-port/build$ARM"
if [[ "$ATTEMPT" != 1 ]]; then DIR="$DIR-attempt$ATTEMPT"; fi
exec 9>"$RESULTS/.stage7-experiment.lock"
flock -n 9 || { echo 'Stage 7 lock held' >&2; exit 1; }
test -z "$(docker ps -q)" || { echo 'running containers' >&2; exit 1; }
test -z "$(nvidia-smi --query-compute-apps=pid --format=csv,noheader)" || exit 1
test -f "$ROOT/$FILE"
test ! -e "$DIR" || { echo 'build receipt already exists' >&2; exit 1; }
if docker image inspect "$IMAGE" >/dev/null 2>&1; then echo 'image already exists' >&2; exit 1; fi
mkdir -p "$DIR"
trap 'printf "%s\n" "$?" > "$DIR/exit-code"' EXIT
printf 'arm=%s\nstart=%s\ncontext=%s\n' "$ARM" "$(date -Is)" "$ROOT" > "$DIR/receipt"
sha256sum "$ROOT/$FILE" "$ROOT"/docker/patches/*.patch > "$DIR/input-sha256.txt"
docker build -f "$ROOT/$FILE" -t "$IMAGE" "$ROOT" > "$DIR/build.log" 2>&1
docker image inspect "$IMAGE" --format '{{.Id}}' > "$DIR/image-id"
docker image inspect "$IMAGE" --format '{{json .Config.Labels}}' > "$DIR/labels.json"
docker run --name "strata-s7-port-build-receipt-$ARM-$ATTEMPT" --entrypoint /bin/bash "$IMAGE" -lc '
set -euo pipefail
nvcc --version
git rev-parse HEAD
git diff --stat
sha256sum engine/strata
cat engine/BUILD.json
grep -E "CMAKE_CUDA_(ARCHITECTURES|COMPILER):|STRATA_EXPERIMENTAL_SM60:" build/CMakeCache.txt
cuobjdump --list-elf engine/strata | awk "/sm_70/ {n++; if(n<=5) print} END {if(!n) exit 1}"
.venv/bin/python -c "import setup; assert setup.source_version() == '\''0.1.54'\''; print(setup.source_version())"
' > "$DIR/image-receipt.txt" 2>&1
printf 'BUILD_PASS_PARITY_AND_SMOKE_PENDING\n' > "$DIR/verdict"
