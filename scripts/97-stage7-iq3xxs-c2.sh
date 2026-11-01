#!/usr/bin/env bash
set -Eeuo pipefail
# One bounded, fresh-process Stage 7 C2 batch. Launch under timeout; never retry an ID.
ROOT="$HOME/v100-x2-strata-qwen3.8-flash-next"
ID="${1:?batch id required}"
case "$ID" in compat-[123]|xxs-[1-6]-[1-3]) ;; *) echo 'invalid batch id' >&2; exit 2;; esac
IMAGE=strata-v100-upstream:0.1.54
IMAGE_ID=sha256:2095eed79b0038ef23d602a0490bf0d89c63ad8e84ace8654c5016b2a51d2246
DIR="$ROOT/results/stage7-iq3xxs/$ID"
MANIFEST="$ROOT/bench/workloads/v100-performance-v1.json"
exec 9>"$ROOT/results/.stage7-experiment.lock"
flock -n 9 || { echo 'another Stage 7 experiment holds lock' >&2; exit 1; }
test ! -e "$DIR" || { echo 'existing batch directory; refusing' >&2; exit 1; }
test -z "$(docker ps -q)" || { echo 'running container found' >&2; exit 1; }
test -z "$(nvidia-smi --query-compute-apps=pid --format=csv,noheader)" || { echo 'GPU workload found' >&2; exit 1; }
test "$(docker image inspect "$IMAGE" --format '{{.Id}}')" = "$IMAGE_ID"
test "$(sha256sum "$MANIFEST" | cut -d' ' -f1)" = e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca
for port in 18084 18085; do if ss -H -tln | awk '{print $4}' | grep -Eq ":${port}$"; then echo "port in use $port" >&2; exit 1; fi; done
for suffix in a b bench; do if docker inspect "strata-s7-$ID-$suffix" >/dev/null 2>&1; then echo 'existing container name' >&2; exit 1; fi; done
mkdir -p "$DIR/logs"
printf 'id=%s\nhost=%s\nboot_id=%s\npid=%s\npid_start_ticks=%s\nstart=%s\ntimeout_s=1800\nimage_id=%s\n' "$ID" "$(hostname)" "$(cat /proc/sys/kernel/random/boot_id)" "$$" "$(awk '{print $22}' /proc/$$/stat)" "$(date -Is)" "$IMAGE_ID" > "$DIR/receipt"
printf 'phase=prepared\n' > "$DIR/progress"
sha256sum "$MANIFEST" > "$DIR/manifest-sha256.txt"
flags=()
case "$ID" in xxs-2-*|xxs-4-*|xxs-6-*) flags+=(-e STRATA_SELECT_SIMT=1);; esac
case "$ID" in xxs-3-*|xxs-4-*|xxs-6-*) flags+=(-e STRATA_PF_WMMA=1);; esac
case "$ID" in xxs-5-*|xxs-6-*) flags+=(-e STRATA_STAGER_SSD=0);; esac
printf '%s\n' "${flags[@]}" > "$DIR/overrides.txt"
python3 - "$ROOT" "$DIR" "$ID" <<'PY'
import json,pathlib,sys
root,d,id=map(pathlib.Path,sys.argv[1:])
for s in 'ab':
 c=json.loads((root/'results/stage5-iq3xxs'/f'agent-{s}.json').read_text())
 c['model_name']=f'qwen3.8-flash-next-iq3_xxs-s7-{id}-{s}'
 (d/f'agent-{s}.json').write_text(json.dumps(c,indent=2)+'\n')
PY
sha256sum "$DIR"/agent-*.json > "$DIR/config-sha256.txt"
PIDS=()
finish() {
 rc=$?; trap - EXIT
 for p in "${PIDS[@]}"; do kill "$p" 2>/dev/null || :; done
 for p in "${PIDS[@]}"; do wait "$p" 2>/dev/null || :; done
 for s in bench a b; do
   if test -s "$DIR/container-$s.id"; then
     c=$(cat "$DIR/container-$s.id")
     docker logs "$c" > "$DIR/docker-$s.log" 2>&1 || :
     docker stop -t 20 "$c" >/dev/null 2>&1 || :
   fi
 done
 grep -E 'pgfault|pgmajfault|pgpgin|pgpgout|pswpin|pswpout' /proc/vmstat > "$DIR/vmstat-after.txt" || :
 free -b > "$DIR/memory-after.txt" || :
 fincore --json --bytes /srv/models/strata-iq3xxs/IQ3_XXS/*.gguf /srv/models/strata-iq3xxs/pack/iq3_xxs-native/dense.bin > "$DIR/cache-after.json" 2> "$DIR/cache-after.err" || :
 printf '%s\n' "$rc" > "$DIR/exit-code"
 printf 'phase=finished\nexit_code=%s\nfinished=%s\n' "$rc" "$(date -Is)" > "$DIR/progress.tmp"; mv "$DIR/progress.tmp" "$DIR/progress"
 exit "$rc"
}
trap finish EXIT
trap 'exit 124' TERM INT
free -b > "$DIR/memory-before.txt"
fincore --json --bytes /srv/models/strata-iq3xxs/IQ3_XXS/*.gguf /srv/models/strata-iq3xxs/pack/iq3_xxs-native/dense.bin > "$DIR/cache-before.json" 2> "$DIR/cache-before.err" || :
grep -E 'pgfault|pgmajfault|pgpgin|pgpgout|pswpin|pswpout' /proc/vmstat > "$DIR/vmstat-before.txt"
nvidia-smi --query-gpu=timestamp,index,temperature.gpu,power.draw,power.limit,utilization.gpu,memory.used,clocks.sm --format=csv,noheader -l 1 > "$DIR/gpu-telemetry.csv" 2>&1 & PIDS+=("$!")
stdbuf -oL vmstat 1 > "$DIR/vmstat.log" 2>&1 & PIDS+=("$!")
stdbuf -oL iostat -xz 1 > "$DIR/iostat.log" 2>&1 & PIDS+=("$!")
for spec in 'a 0 0-2,6-8 18084' 'b 1 3-5,9-11 18085'; do
 read -r s gpu cpus port <<< "$spec"
 docker run -d --name "strata-s7-$ID-$s" --cpuset-cpus "$cpus" --gpus "\"device=$gpu\"" \
   -p "127.0.0.1:$port:8080" -v /srv/models/strata-iq3xxs:/iq3xxs:ro \
   -v "$DIR/logs:/trial-logs" -v /srv/models/strata-data/mtp:/shared-mtp:ro \
   -v "$DIR/agent-$s.json:/opt/strata/config.json:ro" "${flags[@]}" --restart no \
   --entrypoint /opt/strata/.venv/bin/python "$IMAGE" /opt/strata/serve/server.py \
   --engine strata --config /opt/strata/config.json --host 0.0.0.0 --port 8080 > "$DIR/container-$s.id"
done
for s in a b; do docker inspect "$(cat "$DIR/container-$s.id")" --format '{{.Id}} {{.Image}} {{.HostConfig.CpusetCpus}} {{json .HostConfig.DeviceRequests}}' > "$DIR/container-$s.inspect"; done
printf 'phase=loading\n' > "$DIR/progress"
for spec in 'a 18084' 'b 18085'; do
 read -r s port <<< "$spec"; ok=0
 for _ in $(seq 1 600); do
  if curl -fsS --max-time 2 "http://127.0.0.1:$port/health" > "$DIR/health-$s.tmp" 2>/dev/null && python3 - "$DIR/health-$s.tmp" "$ID" "$s" <<'PY'
import json,sys
h=json.load(open(sys.argv[1])); id,s=sys.argv[2:]
assert h.get('status')=='ok' and h.get('loaded') and h.get('max_context')==131072 and h.get('model')==f'qwen3.8-flash-next-iq3_xxs-s7-{id}-{s}'
PY
  then mv "$DIR/health-$s.tmp" "$DIR/health-$s.json"; ok=1; break; fi
  test "$(docker inspect "$(cat "$DIR/container-$s.id")" --format '{{.State.Running}}')" = true || break
  sleep 1
 done
 test "$ok" = 1 || { echo "health failed $s" >&2; exit 1; }
 curl -fsS --max-time 5 "http://127.0.0.1:$port/metrics" > "$DIR/metrics-before-$s.json"
 python3 - "$DIR/metrics-before-$s.json" <<'PY'
import json,sys
assert json.load(open(sys.argv[1])).get('requests_kept') == 0
PY
done
printf 'phase=benchmark\n' > "$DIR/progress"
docker run -d --name "strata-s7-$ID-bench" --network host --user "$(id -u):$(id -g)" \
 -e STRATA_DIR=/opt/strata -v "$ROOT:/work" -v /srv/models/strata-iq3xxs:/iq3xxs:ro \
 --entrypoint /opt/strata/.venv/bin/python "$IMAGE" /work/bench/c2_v100_contract.py \
 --url-a http://127.0.0.1:18084 --url-b http://127.0.0.1:18085 \
 --expected-model-a "qwen3.8-flash-next-iq3_xxs-s7-$ID-a" --expected-model-b "qwen3.8-flash-next-iq3_xxs-s7-$ID-b" \
 --config "/work/results/stage7-iq3xxs/$ID/agent-a.json" \
 --manifest /work/bench/workloads/v100-performance-v1.json --out "/work/results/stage7-iq3xxs/$ID/c2" > "$DIR/container-bench.id"
bench_rc=$(docker wait "$(cat "$DIR/container-bench.id")")
test "$bench_rc" = 0 || { echo "C2 runner exit $bench_rc" >&2; exit 1; }
python3 - "$DIR/c2/summary.json" <<'PY'
import json,sys
s=json.load(open(sys.argv[1])); assert s['pass_mechanical'] and s['active_overlap'] and s['post_health']
r=s['requests']; assert [x['prompt_tokens'] for x in r]==[126967,126968], r
for x in r:
 assert x['cache_n']==0 and x['cached_tokens']==0 and x['finish_reason']=='stop', x
 assert x['output_tokens']>=1024 and x['prefill_tok_s'] and x['decode_tok_s'], x
PY
printf 'PASS\n' > "$DIR/verdict"
