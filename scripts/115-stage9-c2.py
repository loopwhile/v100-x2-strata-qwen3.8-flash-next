#!/usr/bin/env python3
"""P520: one Stage 9 candidate startup gate followed by exactly three fresh-process C2 batches.

No baseline rerun, retries, promotion, serving interruption or hardware changes.
Run under an outer timeout; all evidence survives an SSH client disconnect.
"""
import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess as sp
import sys
import time
import urllib.request

SOURCES = {"U1": "712fec6b4297c9cfd32ab43daaa2979a9aa01edf", "D1": "712fec6b4297c9cfd32ab43daaa2979a9aa01edf", "F1": "8b4c09bd3d9213b2d47880826c6e818c3140664d"}
PACK_SHA = "4a42b98220ea7880664002c8edda1563aecbae754b762a2e2f31b2b91ee93ecd"
PACK_NAME = "qwen3.8-flash-next-dflash2.q4_0-selq4.pack"
MANIFEST_SHA = "e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca"
HARNESS_SHA = "a8e42cc5a71421a7287618fd5be0332ae40f312426e4d243ce1c7619fdfc5246"
PROMPT_HASHES = ['882a3617750ab8dbcb61d3e8e1d42641555a6b1450d060d7bb22a4f1161670b6',
                 '5a19042f67dd7702e843595467e1d6c2b96414f565b0fbfa8036590709dba557']
PORTS = {"a": 18086, "b": 18087}
CPUS = {"a": "0-2,6-8", "b": "3-5,9-11"}
ENV = {"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1"}
GPU_FIELDS = "timestamp,index,temperature.gpu,power.draw,power.limit,utilization.gpu,memory.used,clocks.sm"


def validate_drafter(effective, arm, confidence):
    if arm == 'D1':
        assert '--mtp' not in effective and '--spec-min-p' not in effective
        for key, value in {'--draft': 'dflash2', '--draft-fallback': 'none',
                           '--draft-model': '/stage9-data/dflash2/' + PACK_NAME,
                           '--spec': '6', '--draft-conf': f'{confidence:g}',
                           '--mtp-draft-vocab': '/shared-mtp/rt/draft_vocab.bin'}.items():
            assert effective.count(key) == 1 and effective[effective.index(key) + 1] == value, (key, effective)
    else:
        assert '--mtp' in effective and '--draft' not in effective


def config_for(base, arm, confidence, model):
    cfg = json.loads(json.dumps(base))
    expected = {'--max-context': '131072', '--kv': 'int8', '--kv-resident': '32768',
                '--spec': '4', '--spec-min-p': '0.5', '--prefill': 'auto', '--expert-cache': 'auto'}
    for flag, value in expected.items():
        assert cfg['args'].count(flag) == 1 and cfg['args'][cfg['args'].index(flag) + 1] == value, (flag, cfg)
    assert '--mmap-experts' in cfg['args'] and not cfg.get('env') and not cfg.get('user_args')
    assert cfg['gpu'] == 0 and cfg['gpus_asked']
    cfg['model_name'] = model
    cfg['drafting'] = 'dflash2' if arm == 'D1' else 'mtp'
    if arm == 'D1':
        assert cfg['args'][cfg['args'].index('--pack') + 1] == '/iq3xxs/pack/iq3_xxs-native'
        cfg['args'][cfg['args'].index('--pack') + 1] = '/stage9-data/packs/iq3_xxs-native'
        # Keep --mtp only in input args so upstream can locate the original vocab.
        # drafting.apply removes it; the effective child must never load the MTP.
        i = cfg['args'].index('--spec-min-p')
        del cfg['args'][i:i + 2]
        del expected['--spec-min-p']
        expected.update({'--spec': '6', '--draft-conf': f'{confidence:g}'})
    cfg['user_args'] = [item for flag, value in expected.items() for item in (flag, value)]
    return cfg, expected


def sample_host():
    while True:
        memory = {k.rstrip(':'): int(v.split()[0]) * 1024 for k, v in
                  (line.split(maxsplit=1) for line in Path('/proc/meminfo').read_text().splitlines())}
        vm = {k: int(v) for k, v in (line.split() for line in Path('/proc/vmstat').read_text().splitlines())}
        cpu = {line.split()[0]: list(map(int, line.split()[1:])) for line in
               Path('/proc/stat').read_text().splitlines() if line.startswith('cpu')}
        print(json.dumps({'time': now(), 'memory': memory, 'cpu_ticks': cpu,
                          'vmstat': {k: vm[k] for k in ('pgmajfault', 'pswpin', 'pswpout', 'pgpgin', 'pgpgout')}}), flush=True)
        time.sleep(1)


def stop_owned(cid, experiment_id):
    identity = json.loads(run('docker', 'inspect', cid))[0]
    assert identity['Config'].get('Labels', {}).get('lab.stage9.run') == experiment_id, 'Refuse foreign cleanup'
    run('docker', 'stop', '-t', '20', cid, timeout=45)


def now():
    return dt.datetime.now().astimezone().isoformat()


def run(*args, timeout=60):
    return sp.check_output(args, text=True, stderr=sp.STDOUT, timeout=timeout).strip()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n")
    tmp.replace(path)


def api(s, route, body=None, timeout=5):
    url = f"http://127.0.0.1:{PORTS[s]}/{route}"
    req = urllib.request.Request(url, None if body is None else json.dumps(body).encode(),
                                 {} if body is None else {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def snapshot(d, phase):
    (d / f"memory-{phase}.txt").write_text(run("free", "-b") + "\n")
    (d / f"vmstat-{phase}.txt").write_text(Path("/proc/vmstat").read_text())
    paths = sorted(Path("/srv/models/strata-iq3xxs/IQ3_XXS").glob("*.gguf"))
    paths += [Path("/srv/models/strata-iq3xxs/pack/iq3_xxs-native/dense.bin")]
    (d / f"cache-{phase}.json").write_text(run("fincore", "--json", "--bytes", *map(str, paths)) + "\n")


def verify_latest_clock_receipt(journal, ceiling):
    for bus in ('00000000:65:00.0', '00000000:B3:00.0'):
        applied = [line for line in journal.splitlines() if 'GPU clocks set to' in line and bus in line]
        assert applied and f'gpuClkMin 135, gpuClkMax {ceiling})' in applied[-1], (bus, applied)


def idle(ceiling):
    assert not run("docker", "ps", "-q"), "Running container found; no interruption authorized"
    assert not run("nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"), "GPU workload found"
    limits = run("nvidia-smi", "--query-gpu=power.limit", "--format=csv,noheader,nounits").splitlines()
    assert len(limits) == 2 and all(float(x) == 150 for x in limits), limits
    assert run("systemctl", "is-active", "v100-clock-lock.service") == "active"
    journal = run("journalctl", "-b", "-u", "v100-clock-lock.service", "--no-pager")
    # A service can be restarted later in the same boot. An older matching
    # line must never hide a newer applied range.
    verify_latest_clock_receipt(journal, ceiling)
    # A bind probe without SO_REUSEADDR falsely rejects the previous phase's
    # TIME_WAIT connections. Check actual listeners, as Docker does at publish.
    listening = run("ss", "-H", "-ltn")
    for line in listening.splitlines():
        address = line.split()[3]
        assert address.rsplit(":", 1)[-1] not in {str(p) for p in PORTS.values()}, f"Listener on test port: {line}"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--arm", required=True, choices=SOURCES)
    p.add_argument("--draft-data", type=Path)
    p.add_argument("--draft-conf", type=float)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument('--sm-clock-ceiling', type=int, choices=(1110, 1245), default=1110)
    p.add_argument('--previous-preparation-id', help='Explicitly reviewed, zero-scored clock-gate preparation only')
    p.add_argument("--id", required=True)
    p.add_argument("--image", required=True, help="Immutable sha256 image ID")
    p.add_argument("--engine-sha256", required=True)
    p.add_argument("--assets", required=True, type=Path)
    args = p.parse_args()
    assert re.fullmatch(args.arm.lower() + r"-\d{8}T\d{6}", args.id)
    source = SOURCES[args.arm]
    overrides = dict(ENV)
    if args.arm == "F1": overrides["STRATA_PF_WMMA2"] = "0"
    if args.arm == "D1":
        assert args.draft_data and args.draft_conf is not None
        assert args.draft_conf in (0.35, 0.5, 0.7, 0.8)
        assert sha(args.draft_data / "dflash2" / PACK_NAME) == PACK_SHA
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", args.image)
    assert re.fullmatch(r"[0-9a-f]{64}", args.engine_sha256)
    assert socket.gethostname() == "p520-llm"
    root = Path.home() / "v100-x2-strata-qwen3.8-flash-next"
    locks = []
    for name in (".stage7-experiment.lock", ".stage8-experiment.lock", ".stage9-experiment.lock"):
        lock = (root / "results" / name).open("a")
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        locks.append(lock)
    assert sha(root / "bench/c2_v100_contract.py") == HARNESS_SHA
    assert sha(root / "bench/workloads/v100-performance-v1.json") == MANIFEST_SHA
    image = json.loads(run("docker", "image", "inspect", args.image))[0]
    assert image["Id"] == args.image
    assert image["Config"]["Labels"]["org.opencontainers.image.revision"] == source
    image_env = dict(x.split("=", 1) for x in image["Config"]["Env"] if x.startswith("STRATA_"))
    assert image_env == {"STRATA_EXECV": "1"}, image_env
    idle(args.sm_clock_ceiling)
    assets = args.assets.read_text()
    assert len(assets.splitlines()) >= 15
    # The completed preparation hash receipt identifies the unchanged files. Size/mtime
    # captured here detect accidental mutations during this campaign, without re-reading
    # 75 GB before every batch. Full SHA verification is a preparation operation.
    asset_stats = {}
    for line in assets.splitlines():
        digest, name = line.split(maxsplit=1)
        assert re.fullmatch(r"[0-9a-f]{64}", digest)
        path = Path(name.strip())
        assert str(path).startswith(("/srv/models/strata-iq3xxs/", "/srv/models/strata-data/mtp/rt/"))
        st = path.stat()
        asset_stats[str(path)] = {"sha256": digest, "size": st.st_size, "mtime_ns": st.st_mtime_ns}
    d = root / f"results/stage9/S9-{args.arm}" / args.id
    assert not d.exists(), "Experiment IDs are immutable"
    previous = list(d.parent.glob("*/progress.json"))
    if previous:
        assert args.previous_preparation_id and args.sm_clock_ceiling == 1245
        assert len(previous) == 1 and previous[0].parent.name == args.previous_preparation_id
        old = json.loads(previous[0].read_text())
        assert old['phase'] == 'interrupted' and old['verdict'] == 'INCONCLUSIVE'
        assert old.get('error') == "AssertionError('Clock/power cap mismatch')"
        assert old['image_id'] == args.image and not any(x['scored'] for x in old['batches']), 'No scored retry permitted'
    else:
        assert not args.previous_preparation_id
    if args.dry_run:
        for side in "ab":
            cfg = json.loads((root / f"results/stage5-iq3xxs/agent-{side}.json").read_text())
            config_for(cfg, args.arm, args.draft_conf, f"dry-{side}")
        print(json.dumps({"dry_run": "PASS", "arm": args.arm, "source": source, "image": args.image, "ports": PORTS, "overrides": overrides, 'sm_clock_ceiling': args.sm_clock_ceiling}))
        return
    d.mkdir(parents=True, exist_ok=False)
    checkpoint = {"id": args.id, "arm": "S9-" + args.arm, "phase": "prepared", "verdict": None,
                  "host": socket.gethostname(), "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
                  "pid": os.getpid(), "pid_start_ticks": Path(f"/proc/{os.getpid()}/stat").read_text().split()[21],
                  "started": now(), "timeout_s": 3600, "image_id": args.image, "source_sha": source,
                  "engine_sha256": args.engine_sha256, "runner_sha256": sha(Path(__file__)),
                  "harness_sha256": HARNESS_SHA, "manifest_sha256": MANIFEST_SHA,
                  "overrides": overrides, "draft_conf": args.draft_conf,
                  'sm_clock_ceiling_mhz': args.sm_clock_ceiling, 'previous_preparation_id': args.previous_preparation_id,
                  "scope": "Stage 9 selected candidate startup/short inference, then exactly 3 fresh-process dual 128K C2; no retry; stop owned containers; original serving state empty",
                  "batches": []}
    save(d / "progress.json", checkpoint)
    save(d / "assets.json", asset_stats)
    (d / "assets.sha256").write_text(assets)
    (d / "clock-service.txt").write_text(run("journalctl", "-b", "-u", "v100-clock-lock.service", "--no-pager"))
    (d / "rollback.txt").write_text("Initial serving state: empty. Stop only this run's recorded container IDs; preserve all containers/images/logs. No promotion. Existing strata-s7-xxs14-serve-a/b stay stopped. No tunnel/power/clock operation.\n")
    owned, collectors, handles = [], [], []
    current = None

    def cleanup():
        errors = []
        for cid in reversed(owned):
            try:
                stop_owned(cid, args.id)
            except Exception as exc:
                errors.append({"container": cid, "error": repr(exc)})
        for proc in collectors:
            if proc.poll() is None:
                proc.terminate()
            try:
                proc.wait(timeout=5)
            except sp.TimeoutExpired:
                proc.kill()
                proc.wait()
        for h in handles:
            h.close()
        collectors.clear()
        handles.clear()
        if errors:
            raise RuntimeError(f"Owned container cleanup failed: {errors}")
        owned.clear()

    def interrupted(signum, frame):
        raise InterruptedError(f"Runner signal {signum}")

    def deadline_expired(signum, frame):
        raise TimeoutError("Runner 3600s deadline")

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    signal.signal(signal.SIGALRM, deadline_expired)
    signal.alarm(3600)
    try:
        for phase in ("startup", "batch-1", "batch-2", "batch-3"):
            idle(args.sm_clock_ceiling)
            assert Path("/proc/sys/kernel/random/boot_id").read_text().strip() == checkpoint["boot_id"]
            for name, meta in asset_stats.items():
                st = Path(name).stat()
                assert (st.st_size, st.st_mtime_ns) == (meta["size"], meta["mtime_ns"]), name
            current = d / phase
            current.mkdir()
            (current / "logs").mkdir()
            record = {"id": f"{args.id}-{phase}", "phase": "loading", "started": now(), "scored": phase != "startup"}
            checkpoint["batches"].append(record)
            checkpoint.update(phase="running", current_phase=phase)
            save(d / "progress.json", checkpoint)
            snapshot(current, "before")
            for filename, cmd in [("gpu-telemetry.csv", ["nvidia-smi", f"--query-gpu={GPU_FIELDS}", "--format=csv,noheader,nounits", "-l", "1"]),
                                  ("host-telemetry.jsonl", [sys.executable, '-u', str(Path(__file__).resolve()), '--sample-host']),
                                  ("vmstat.log", ["stdbuf", "-oL", "vmstat", "1"]),
                                  ("iostat.log", ["stdbuf", "-oL", "iostat", "-xz", "1"])]:
                handle = (current / filename).open("w")
                handles.append(handle)
                collectors.append(sp.Popen(cmd, stdout=handle, stderr=sp.STDOUT))
            configs, models, servers = {}, {}, {}
            for s in "ab":
                base = json.loads((root / f"results/stage5-iq3xxs/agent-{s}.json").read_text())
                model = 'qwen3.8-flash-next-iq3_xxs_s9_' + f'{args.id}_{phase}_{s}'.replace('-', '_')
                cfg, expected = config_for(base, args.arm, args.draft_conf, model)
                configs[s], models[s] = cfg, cfg["model_name"]
                save(current / f"agent-{s}.json", cfg)
                name = f"strata-s9-{args.id}-{phase}-{s}"
                cmd = ["docker", "run", "-d", "--pull", "never", "--name", name, "--restart", "no", "--cpuset-cpus", CPUS[s],
                       "--gpus", f'"device={"ab".index(s)}"', "--network", "host",
                       "--label", f"lab.stage9.run={args.id}",
                       "-v", "/srv/models/strata-iq3xxs:/iq3xxs:ro", "-v", "/srv/models/strata-data/mtp:/shared-mtp:ro",
                       "-v", f"{current}/logs:/trial-logs", "-v", f"{current}/agent-{s}.json:/opt/strata/config.json:ro"]
                for k, v in overrides.items():
                    cmd.extend(["-e", f"{k}={v}"])
                if args.arm == "D1":
                    # The original model mount stays read-only and unchanged. A separate
                    # pack alias lets upstream locate the new drafter outside that tree.
                    cmd.extend(["-v", f"{args.draft_data}/dflash2:/stage9-data/dflash2:ro",
                                '-v', '/srv/models/strata-iq3xxs/pack/iq3_xxs-native:/stage9-data/packs/iq3_xxs-native:ro'])
                cmd.extend(["--entrypoint", "/opt/strata/.venv/bin/python", args.image, "/opt/strata/serve/server.py",
                            "--engine", "strata", "--config", "/opt/strata/config.json", "--host", "127.0.0.1", "--port", str(PORTS[s])])
                save(current / f"command-{s}.json", cmd)
                cid = run(*cmd)
                owned.append(cid)
                checkpoint.setdefault("owned_container_ids", []).append(cid)
                save(d / "progress.json", checkpoint)
                servers[s] = cid
                (current / f"container-{s}.id").write_text(cid + "\n")
                c = json.loads(run("docker", "inspect", cid))[0]
                assert c["Image"] == args.image and c["HostConfig"]["CpusetCpus"] == CPUS[s]
                assert c["HostConfig"]["DeviceRequests"][0]["DeviceIDs"] == [str("ab".index(s))]
                assert c["HostConfig"]["NetworkMode"] == "host"
                assert not c["HostConfig"]["PortBindings"]
                save(current / f"inspect-{s}.json", {"id": cid, "image": c["Image"], "pid": c["State"]["Pid"], "started": c["State"]["StartedAt"],
                                                     "cpus": CPUS[s], "gpus": c["HostConfig"]["DeviceRequests"], "mounts": c["Mounts"], "overrides": overrides})
            assert configs["a"]["args"] == configs["b"]["args"]
            save(current / "config-sha256.json", {s: sha(current / f"agent-{s}.json") for s in "ab"})
            deadline = time.monotonic() + 600
            while True:
                ready = True
                for s in "ab":
                    assert run("docker", "inspect", servers[s], "--format", "{{.State.Running}}") == "true", f"Server exited {s}"
                    try:
                        h = api(s, "health")
                        ready &= h.get("status") == "ok" and h.get("loaded") and h.get("max_context") == 131072 and h.get("model") == models[s]
                    except Exception:
                        ready = False
                if ready:
                    break
                assert time.monotonic() < deadline, "Server readiness deadline"
                time.sleep(2)
            for s in "ab":
                save(current / f"health-before-{s}.json", api(s, "health"))
                metrics = api(s, "metrics")
                save(current / f"metrics-before-{s}.json", metrics)
                assert metrics.get("requests_kept") == 0
                assert run("docker", "exec", servers[s], "sha256sum", "/opt/strata/engine/strata").split()[0] == args.engine_sha256
                probe = """import json,pathlib
out=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdigit(): continue
 try:
  cmd=(p/'cmdline').read_bytes().decode().strip('\\0').split('\\0')
  if cmd[0]!='/opt/strata/engine/strata': continue
  env=dict(x.split('=',1) for x in (p/'environ').read_bytes().decode().split('\\0') if x.startswith('STRATA_'))
  out.append({'pid':int(p.name),'pid_start_ticks':(p/'stat').read_text().split()[21],'args':cmd,'strata_env':env})
 except (FileNotFoundError,PermissionError,ProcessLookupError): pass
print(json.dumps(out))
"""
                processes = json.loads(run("docker", "exec", servers[s], "/opt/strata/.venv/bin/python", "-c", probe))
                assert len(processes) == 1, processes
                save(current / f"engine-process-{s}.json", processes[0])
                effective = processes[0]["args"]
                for flag, val in expected.items():
                    assert effective[effective.index(flag) + 1] == val, (flag, effective)
                validate_drafter(effective, args.arm, args.draft_conf)
                assert all(processes[0]["strata_env"].get(k) == v for k, v in overrides.items())
            record.update(phase="startup_inference" if phase == "startup" else "benchmark", benchmark_started=now())
            save(d / "progress.json", checkpoint)
            print(f"{now()} {phase} START", flush=True)
            if phase == "startup":
                for s in "ab":
                    response = api(s, "v1/chat/completions", {"model": models[s], "messages": [{"role": "user", "content": "Write the integers 1 through 40, separated by spaces."}], "max_tokens": 128, "temperature": 0, "reasoning_effort": "none"}, timeout=180)
                    save(current / f"smoke-{s}.json", response)
                    assert response.get("choices") and response["choices"][0].get("message", {}).get("content"), response
                    save(current / f"models-{s}.json", api(s, "v1/models"))
            else:
                cmd = ["docker", "run", "-d", "--pull", "never", "--name", f"strata-s9-{args.id}-{phase}-bench", "--network", "host", "--label", f"lab.stage9.run={args.id}", "--user", f"{os.getuid()}:{os.getgid()}",
                       "-e", "STRATA_DIR=/opt/strata", "-v", f"{root}:/work", "-v", "/srv/models/strata-iq3xxs:/iq3xxs:ro", "--entrypoint", "/opt/strata/.venv/bin/python", args.image,
                       "/work/bench/c2_v100_contract.py", "--url-a", f"http://127.0.0.1:{PORTS['a']}", "--url-b", f"http://127.0.0.1:{PORTS['b']}",
                       "--expected-model-a", models["a"], "--expected-model-b", models["b"], "--config", f"/work/{current.relative_to(root)}/agent-a.json",
                       "--manifest", "/work/bench/workloads/v100-performance-v1.json", "--out", f"/work/{current.relative_to(root)}/c2"]
                save(current / "benchmark-command.json", cmd)
                bench = run(*cmd)
                owned.append(bench)
                checkpoint.setdefault("owned_container_ids", []).append(bench)
                record["bench_container_id"] = bench
                save(d / "progress.json", checkpoint)
                rc = run("docker", "wait", bench, timeout=1200)
                (current / "docker-bench.log").write_text(run("docker", "logs", bench))
                (current / "benchmark-exit-code").write_text(rc + "\n")
                assert rc == "0", f"C2 exit {rc}"
                summary = json.loads((current / "c2/summary.json").read_text())
                workload = json.loads((current / 'c2/workload.json').read_text())
                assert [x['raw_prompt_sha256'] for x in workload['items']] == PROMPT_HASHES
                assert summary["pass_mechanical"] and summary["active_overlap"] and summary["post_health"]
                assert summary["warmup_count"] == 0
                assert [x["prompt_tokens"] for x in summary["requests"]] == [126967, 126968]
                for req in summary["requests"]:
                    assert req["output_tokens"] >= 1024 and req["finish_reason"] == "stop"
                    assert req["cache_n"] == req["cached_tokens"] == 0
                record["metrics"] = [{k: req[k] for k in ("label", "prompt_tokens", "output_tokens", "prefill_tok_s", "decode_tok_s", "ttft_s")} for req in summary["requests"]]
            for s in "ab":
                h = api(s, "health")
                assert h.get("status") == "ok" and h.get("loaded")
                save(current / f"health-after-{s}.json", h)
                after_processes = json.loads(run('docker', 'exec', servers[s], '/opt/strata/.venv/bin/python', '-c', probe))
                before_process = json.loads((current / f'engine-process-{s}.json').read_text())
                save(current / f'engine-process-after-{s}.json', after_processes)
                assert len(after_processes) == 1 and all(after_processes[0][k] == before_process[k]
                    for k in ('pid', 'pid_start_ticks', 'args')), 'Engine restarted during this phase; no hidden retry allowed'
                metrics_after = api(s, "metrics")
                save(current / f"metrics-after-{s}.json", metrics_after)
                if args.arm == 'D1':
                    rows = metrics_after.get('requests', [])
                    assert rows and rows[0].get('drafts_offered', 0) > 0, 'DFlash2 must actually propose drafts'
                    notes = (current / f'logs/agent-{s}.log').read_text(errors='replace')
                    assert re.search(r'strata dflash2: \d+-token draft head', notes)
                    assert 'no MTP layer is loaded (--draft-fallback none)' in notes
                    assert 'selector codebooks: Q4_0 rows' in notes
                (current / f"docker-{s}.log").write_text(run("docker", "logs", servers[s]))
            record.update(phase="validated", verdict="STARTUP_PASS_NOT_C2" if phase == "startup" else "PASS", inference_finished=now())
            save(d / "progress.json", checkpoint)
            cleanup()
            snapshot(current, "after")
            # Reject any departure from the frozen cap; startup is part of the gate.
            samples = [line.split(",") for line in (current / "gpu-telemetry.csv").read_text().splitlines() if len(line.split(",")) == 8]
            assert samples, "No GPU telemetry"
            assert all(any(row[1].strip() == str(i) for row in samples) for i in (0, 1))
            assert all(float(row[7].strip()) <= args.sm_clock_ceiling and float(row[4].strip()) == 150 for row in samples), "Clock/power cap mismatch"
            assert len((current / 'host-telemetry.jsonl').read_text().splitlines()) >= 2, 'Missing host lifetime telemetry'
            record.update(phase="results_saved", finished=now())
            save(d / "progress.json", checkpoint)
            (current / "verdict").write_text(record["verdict"] + "\n")
            print(f"{now()} {phase} {record['verdict']} {json.dumps(record.get('metrics', []))}", flush=True)
        idle(args.sm_clock_ceiling)
        checkpoint.update(phase="results_saved", verdict="PASS", finished=now(), owned_containers_stopped=True)
        save(d / "progress.json", checkpoint)
        (d / "exit-code").write_text("0\n")
        (d / "verdict").write_text("PASS\n")
    except BaseException as exc:
        for cid in owned:
            try:
                if current:
                    (current / f"failure-{cid[:12]}.log").write_text(run("docker", "logs", cid))
            except Exception:
                pass
        checkpoint.update(phase="interrupted", verdict="FAIL_TIMEOUT" if isinstance(exc, (TimeoutError, sp.TimeoutExpired)) else "INCONCLUSIVE", error=repr(exc), finished=now())
        if checkpoint["batches"] and checkpoint["batches"][-1]["phase"] != "results_saved":
            checkpoint["batches"][-1].update(phase="interrupted", verdict=checkpoint["verdict"], error=repr(exc))
        save(d / "progress.json", checkpoint)
        (d / "exit-code").write_text("1\n")
        raise
    finally:
        cleanup()
        signal.alarm(0)


if __name__ == "__main__":
    if sys.argv[1:] == ['--sample-host']:
        sample_host()
    else:
        main()
