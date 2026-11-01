#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$HOME/v100-x2-strata-qwen3.8-flash-next"
DIR="$ROOT/results/stage7-iq3xxs-smoke"
STARTER="${1:?path to stage7 smoke starter required}"
for s in a b; do
  if docker inspect "strata-s7xxs-smoke-$s" >/dev/null 2>&1; then echo 'existing smoke container; refusing' >&2; exit 1; fi
done
test ! -e "$DIR" || { echo 'existing smoke directory; refusing' >&2; exit 1; }
exec 9>"$ROOT/results/.stage7-experiment.lock"
flock -n 9 || { echo 'Stage 7 lock held' >&2; exit 1; }
mkdir -p "$DIR"
printf 'phase=prepared\nexperiment=stage7-iq3xxs-smoke\nboot_id=%s\npid=%s\npid_start_ticks=%s\nstart=%s\ntimeout_s=1200\n' "$(cat /proc/sys/kernel/random/boot_id)" "$$" "$(awk '{print $22}' /proc/$$/stat)" "$(date -Is)" > "$DIR/receipt"
cp "$DIR/receipt" "$DIR/progress"
# The starter creates this directory; preserve this receipt outside it until creation.
mv "$DIR" "${DIR}.prepared"
owned=0
finish() {
  rc=$?
  trap - EXIT
  if (( owned )); then
    for s in a b; do
      c="strata-s7xxs-smoke-$s"
      if test -s "$DIR/container-$s.id" && test "$(docker inspect "$c" --format '{{.Id}}' 2>/dev/null)" = "$(cat "$DIR/container-$s.id")"; then
        docker logs "$c" > "$DIR/docker-$s.log" 2>&1 || :
        docker stop -t 20 "$c" >/dev/null 2>&1 || :
      fi
    done
  fi
  target="$DIR"; test -d "$target" || target="${DIR}.prepared"
  printf '%s\n' "$rc" > "$target/exit-code"
  printf 'phase=finished\nexit_code=%s\nfinished=%s\n' "$rc" "$(date -Is)" > "$target/progress"
}
trap finish EXIT
trap 'exit 124' TERM INT
# Starter checks no GPU users, verifies ports and uses only stage7-owned names.
owned=1
bash "$STARTER"
cp "${DIR}.prepared/receipt" "$DIR/receipt"
printf "phase=running\n" > "$DIR/progress"
for spec in 'a 18084' 'b 18085'; do
  read -r s port <<< "$spec"
  ok=0
  for _ in $(seq 1 600); do
    if curl -fsS --max-time 2 "http://127.0.0.1:$port/health" > "$DIR/health-$s.json.tmp" 2>/dev/null && \
      python3 - "$DIR/health-$s.json.tmp" "$s" <<'PY'
import json,sys
h=json.load(open(sys.argv[1])); s=sys.argv[2]
assert h.get('status')=='ok' and h.get('loaded') and h.get('model')==f'qwen3.8-flash-next-iq3_xxs-s7smoke-{s}'
assert h.get('max_context') == 131072, h
PY
    then mv "$DIR/health-$s.json.tmp" "$DIR/health-$s.json"; ok=1; break; fi
    test "$(docker inspect "strata-s7xxs-smoke-$s" --format '{{.State.Running}}')" = true || break
    sleep 1
  done
  test "$ok" = 1 || { echo "Agent $s did not reach expected health" >&2; exit 1; }
  curl -fsS --max-time 10 "http://127.0.0.1:$port/v1/models" > "$DIR/models-$s.json"
  python3 - "$port" "$s" "$DIR" <<'PY'
import json, pathlib, sys, urllib.request
port,s,d=sys.argv[1:]
body={'model':f'qwen3.8-flash-next-iq3_xxs-s7smoke-{s}','messages':[{'role':'user','content':'Reply with exactly: READY'}], 'max_tokens':32,'temperature':0}
r=urllib.request.Request(f'http://127.0.0.1:{port}/v1/chat/completions',json.dumps(body).encode(),{'Content-Type':'application/json'})
with urllib.request.urlopen(r,timeout=180) as res: data=json.load(res)
(pathlib.Path(d)/f'chat-{s}.json').write_text(json.dumps(data,indent=2)+'\n')
assert data.get('choices') and data['choices'][0].get('message',{}).get('content'), data
PY
  curl -fsS --max-time 5 "http://127.0.0.1:$port/health" > "$DIR/post-health-$s.json"
done
printf 'short_smoke=PASS\n128k_compatibility=NOT_YET_TESTED\n' > "$DIR/verdict"
