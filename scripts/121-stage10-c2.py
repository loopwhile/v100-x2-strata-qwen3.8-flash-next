#!/usr/bin/env python3
"""P520: Stage 10 candidate execution runner (startup gate + fresh C2 batches).

Strict safety contract:
- Tesla V100 135-1245 MHz clock lock verified
- 150 W configured GPU power limits verified
- Single-GPU isolated agents on cpusets 0-2,6-8 and 3-5,9-11
- INT8 KV, 131072 context, mmap experts
- DFlash2 stock selector pack, no MTP fallback
- Three fresh-process 128K C2 batches per scored arm; clean container cleanup
- Full telemetry: GPU power/temp/clocks/VRAM, CPU, RAM, swap, page cache, IO
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

UPSTREAM_IMAGE = "sha256:dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d"
SOURCE_SHA = "712fec6b4297c9cfd32ab43daaa2979a9aa01edf"
ENGINE_SHA256 = "ccca488231f12da422be4a80b5c7f165b7593f6388907cac92d3c3f0d4229031"
PACK_SHA = "4a42b98220ea7880664002c8edda1563aecbae754b762a2e2f31b2b91ee93ecd"
PACK_NAME = "qwen3.8-flash-next-dflash2.q4_0-selq4.pack"
MANIFEST_SHA = "e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca"
HARNESS_SHA = "a8e42cc5a71421a7287618fd5be0332ae40f312426e4d243ce1c7619fdfc5246"
PROMPT_HASHES = [
    "882a3617750ab8dbcb61d3e8e1d42641555a6b1450d060d7bb22a4f1161670b6",
    "5a19042f67dd7702e843595467e1d6c2b96414f565b0fbfa8036590709dba557"
]
PORTS = {"a": 18086, "b": 18087}
CPUS = {"a": "0-2,6-8", "b": "3-5,9-11"}
BASE_ENV = {"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1"}
GPU_FIELDS = "timestamp,index,temperature.gpu,power.draw,power.limit,utilization.gpu,memory.used,clocks.sm"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def now():
    return dt.datetime.now().astimezone().isoformat()


def run(*args, timeout=60):
    return sp.check_output(args, text=True, stderr=sp.STDOUT, timeout=timeout).strip()


def save(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n")
    tmp.replace(path)


def api(s, route, body=None, timeout=5):
    url = f"http://127.0.0.1:{PORTS[s]}/{route}"
    req = urllib.request.Request(
        url,
        None if body is None else json.dumps(body).encode(),
        {} if body is None else {"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def snapshot(d, phase):
    (d / f"memory-{phase}.txt").write_text(run("free", "-b") + "\n")
    (d / f"vmstat-{phase}.txt").write_text(Path("/proc/vmstat").read_text())
    paths = sorted(Path("/srv/models/strata-iq3xxs/IQ3_XXS").glob("*.gguf"))
    paths += [Path("/srv/models/strata-iq3xxs/pack/iq3_xxs-native/dense.bin")]
    (d / f"cache-{phase}.json").write_text(run("fincore", "--json", "--bytes", *map(str, paths)) + "\n")


def verify_latest_clock_receipt(journal, ceiling=1245):
    for bus in ("00000000:65:00.0", "00000000:B3:00.0"):
        applied = [line for line in journal.splitlines() if "GPU clocks set to" in line and bus in line]
        assert applied and f"gpuClkMin 135, gpuClkMax {ceiling})" in applied[-1], (bus, applied)


def verify_idle(ceiling=1245):
    assert not run("docker", "ps", "-q"), "Running container found; no interruption authorized"
    assert not run("nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"), "GPU workload found"
    limits = run("nvidia-smi", "--query-gpu=power.limit", "--format=csv,noheader,nounits").splitlines()
    assert len(limits) == 2 and all(float(x) == 150 for x in limits), limits
    assert run("systemctl", "is-active", "v100-clock-lock.service") == "active"
    journal = run("journalctl", "-b", "-u", "v100-clock-lock.service", "--no-pager")
    verify_latest_clock_receipt(journal, ceiling)
    listening = run("ss", "-H", "-ltn")
    for line in listening.splitlines():
        address = line.split()[3]
        port = address.rsplit(":", 1)[-1]
        assert port not in {str(p) for p in PORTS.values()}, f"Listener on test port: {line}"


def sample_host():
    while True:
        memory = {
            k.rstrip(":"): int(v.split()[0]) * 1024
            for k, v in (line.split(maxsplit=1) for line in Path("/proc/meminfo").read_text().splitlines())
        }
        vm = {k: int(v) for k, v in (line.split() for line in Path("/proc/vmstat").read_text().splitlines())}
        cpu = {
            line.split()[0]: list(map(int, line.split()[1:]))
            for line in Path("/proc/stat").read_text().splitlines() if line.startswith("cpu")
        }
        print(json.dumps({
            "time": now(), "memory": memory, "cpu_ticks": cpu,
            "vmstat": {k: vm[k] for k in ("pgmajfault", "pswpin", "pswpout", "pgpgin", "pgpgout")}
        }), flush=True)
        time.sleep(1)


def stop_owned(cid, experiment_id):
    identity = json.loads(run("docker", "inspect", cid))[0]
    assert identity["Config"].get("Labels", {}).get("lab.stage10.run") == experiment_id, "Refuse foreign cleanup"
    run("docker", "stop", "-t", "20", cid, timeout=45)


def config_for(base, arm, draft_conf, spec, prefill, model):
    cfg = json.loads(json.dumps(base))
    expected = {
        "--max-context": "131072",
        "--kv": "int8",
        "--kv-resident": "32768",
        "--spec": str(spec),
        "--prefill": prefill,
        "--expert-cache": "auto",
        "--draft-conf": f"{draft_conf:g}"
    }
    assert "--mmap-experts" in cfg["args"]
    assert cfg["gpu"] == 0 and cfg["gpus_asked"]
    cfg["model_name"] = model
    cfg["drafting"] = "dflash2"

    # Replace native pack mount path with stage10 path
    pack_idx = cfg["args"].index("--pack")
    cfg["args"][pack_idx + 1] = "/stage10-data/packs/iq3_xxs-native"

    # Replace spec-min-p with dflash2 params
    if "--spec-min-p" in cfg["args"]:
        idx = cfg["args"].index("--spec-min-p")
        del cfg["args"][idx:idx + 2]

    # Update args in cfg
    for k, v in expected.items():
        if k in cfg["args"]:
            cfg["args"][cfg["args"].index(k) + 1] = v
        else:
            cfg["args"].extend([k, v])

    cfg["user_args"] = [item for flag, val in expected.items() for item in (flag, val)]
    return cfg, expected


def validate_drafter(effective, spec, draft_conf):
    assert "--mtp" not in effective, "MTP drafter found in DFlash2 arm"
    assert "--spec-min-p" not in effective
    expected_flags = {
        "--draft": "dflash2",
        "--draft-fallback": "none",
        "--draft-model": "/stage10-data/dflash2/" + PACK_NAME,
        "--spec": str(spec),
        "--draft-conf": f"{draft_conf:g}",
        "--mtp-draft-vocab": "/shared-mtp/rt/draft_vocab.bin"
    }
    for key, value in expected_flags.items():
        assert effective.count(key) == 1 and effective[effective.index(key) + 1] == value, (key, effective)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--arm", required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--scored-batches", type=int, default=3)
    p.add_argument("--spec", type=int, default=6)
    p.add_argument("--draft-conf", type=float, default=0.7)
    p.add_argument("--prefill", default="auto")
    p.add_argument("--extra-env", nargs="*", default=[])
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--sm-clock-ceiling", type=int, default=1245)
    args = p.parse_args()

    assert socket.gethostname() == "p520-llm", "Must run on p520-llm"
    root = Path.home() / "v100-x2-strata-qwen3.8-flash-next"
    assert root.is_dir()

    # Parse extra env
    env_overrides = dict(BASE_ENV)
    for pair in args.extra_env:
        k, v = pair.split("=", 1)
        env_overrides[k] = v

    draft_data_dir = root / "results/stage10-preparation/draft-data"
    assert (draft_data_dir / "dflash2" / PACK_NAME).stat().st_size == 339694592
    assert sha(draft_data_dir / "dflash2" / PACK_NAME) == PACK_SHA

    # Lock files
    locks = []
    for name in (".stage7-experiment.lock", ".stage8-experiment.lock", ".stage9-experiment.lock", ".stage10-experiment.lock"):
        lock = (root / "results" / name).open("a")
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        locks.append(lock)

    assert sha(root / "bench/c2_v100_contract.py") == HARNESS_SHA
    assert sha(root / "bench/workloads/v100-performance-v1.json") == MANIFEST_SHA

    # Verify idle state
    verify_idle(args.sm_clock_ceiling)

    # Assets stat check
    assets_file = root / "artifacts/stage8-results-20261107/assets.sha256"
    asset_stats = {}
    for line in assets_file.read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        p_asset = Path(name.strip())
        st = p_asset.stat()
        asset_stats[str(p_asset)] = {"sha256": digest, "size": st.st_size, "mtime_ns": st.st_mtime_ns}

    # Dry run check
    if args.dry_run:
        for side in "ab":
            base = json.loads((root / f"results/stage5-iq3xxs/agent-{side}.json").read_text())
            cfg, _ = config_for(base, args.arm, args.draft_conf, args.spec, args.prefill, f"qwen3.8-flash-next-iq3_xxs_s10_dry_{side}")
        print(json.dumps({
            "dry_run": "PASS",
            "arm": args.arm,
            "id": args.id,
            "spec": args.spec,
            "draft_conf": args.draft_conf,
            "prefill": args.prefill,
            "env": env_overrides,
            "scored_batches": args.scored_batches
        }))
        return

    exp_dir = root / f"results/stage10/S10-{args.arm}" / args.id
    assert not exp_dir.exists(), f"Experiment directory already exists: {exp_dir}"
    exp_dir.mkdir(parents=True, exist_ok=False)

    checkpoint = {
        "id": args.id,
        "arm": f"S10-{args.arm}",
        "phase": "prepared",
        "verdict": None,
        "host": socket.gethostname(),
        "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
        "pid": os.getpid(),
        "pid_start_ticks": Path(f"/proc/{os.getpid()}/stat").read_text().split()[21],
        "started": now(),
        "timeout_s": 3600,
        "image_id": UPSTREAM_IMAGE,
        "source_sha": SOURCE_SHA,
        "engine_sha256": ENGINE_SHA256,
        "runner_sha256": sha(Path(__file__)),
        "harness_sha256": HARNESS_SHA,
        "manifest_sha256": MANIFEST_SHA,
        "overrides": env_overrides,
        "draft_conf": args.draft_conf,
        "spec": args.spec,
        "prefill": args.prefill,
        "sm_clock_ceiling_mhz": args.sm_clock_ceiling,
        "batches": []
    }
    save(exp_dir / "progress.json", checkpoint)
    save(exp_dir / "assets.json", asset_stats)
    (exp_dir / "clock-service.txt").write_text(run("journalctl", "-b", "-u", "v100-clock-lock.service", "--no-pager"))
    (exp_dir / "rollback.txt").write_text("Stage 10 execution rollback: stop owned containers, preserve historical images/logs.\n")

    # Determine batch sequence
    if args.scored_batches == 0:
        phases = ["startup", "diagnostic-1"]
    else:
        phases = ["startup"] + [f"batch-{i+1}" for i in range(args.scored_batches)]

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
        raise TimeoutError("Runner deadline expired")

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    signal.signal(signal.SIGALRM, deadline_expired)
    signal.alarm(3600)

    try:
        for phase in phases:
            verify_idle(args.sm_clock_ceiling)
            assert Path("/proc/sys/kernel/random/boot_id").read_text().strip() == checkpoint["boot_id"]
            for name_a, meta_a in asset_stats.items():
                st_a = Path(name_a).stat()
                assert (st_a.st_size, st_a.st_mtime_ns) == (meta_a["size"], meta_a["mtime_ns"]), name_a

            current = exp_dir / phase
            current.mkdir()
            (current / "logs").mkdir()
            is_scored = phase.startswith("batch-")
            record = {"id": f"{args.id}-{phase}", "phase": "loading", "started": now(), "scored": is_scored}
            checkpoint["batches"].append(record)
            checkpoint.update(phase="running", current_phase=phase)
            save(exp_dir / "progress.json", checkpoint)
            snapshot(current, "before")

            # Telemetry collectors
            for filename, cmd in [
                ("gpu-telemetry.csv", ["nvidia-smi", f"--query-gpu={GPU_FIELDS}", "--format=csv,noheader,nounits", "-l", "1"]),
                ("host-telemetry.jsonl", [sys.executable, "-u", str(Path(__file__).resolve()), "--sample-host"]),
                ("vmstat.log", ["stdbuf", "-oL", "vmstat", "1"]),
                ("iostat.log", ["stdbuf", "-oL", "iostat", "-xz", "1"])
            ]:
                handle = (current / filename).open("w")
                handles.append(handle)
                collectors.append(sp.Popen(cmd, stdout=handle, stderr=sp.STDOUT))

            configs, models, servers = {}, {}, {}
            for s in "ab":
                base = json.loads((root / f"results/stage5-iq3xxs/agent-{s}.json").read_text())
                model = "qwen3.8-flash-next-iq3_xxs_s10_" + f"{args.id}_{phase}_{s}".replace("-", "_")
                cfg, expected = config_for(base, args.arm, args.draft_conf, args.spec, args.prefill, model)
                configs[s], models[s] = cfg, cfg["model_name"]
                save(current / f"agent-{s}.json", cfg)
                cname = f"strata-s10-{args.id}-{phase}-{s}"
                cmd = [
                    "docker", "run", "-d", "--pull", "never", "--name", cname, "--restart", "no",
                    "--cpuset-cpus", CPUS[s], "--gpus", f'"device={"ab".index(s)}"', "--network", "host",
                    "--label", f"lab.stage10.run={args.id}",
                    "-v", "/srv/models/strata-iq3xxs:/iq3xxs:ro",
                    "-v", "/srv/models/strata-data/mtp:/shared-mtp:ro",
                    "-v", f"{draft_data_dir}/dflash2:/stage10-data/dflash2:ro",
                    "-v", "/srv/models/strata-iq3xxs/pack/iq3_xxs-native:/stage10-data/packs/iq3_xxs-native:ro",
                    "-v", f"{current}/logs:/trial-logs",
                    "-v", f"{current}/agent-{s}.json:/opt/strata/config.json:ro"
                ]
                for k, v in env_overrides.items():
                    cmd.extend(["-e", f"{k}={v}"])
                cmd.extend([
                    "--entrypoint", "/opt/strata/.venv/bin/python", UPSTREAM_IMAGE,
                    "/opt/strata/serve/server.py", "--engine", "strata", "--config", "/opt/strata/config.json",
                    "--host", "127.0.0.1", "--port", str(PORTS[s])
                ])
                save(current / f"command-{s}.json", cmd)
                cid = run(*cmd)
                owned.append(cid)
                checkpoint.setdefault("owned_container_ids", []).append(cid)
                save(exp_dir / "progress.json", checkpoint)
                servers[s] = cid
                (current / f"container-{s}.id").write_text(cid + "\n")

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
                assert time.monotonic() < deadline, "Server readiness deadline exceeded"
                time.sleep(2)

            # Probe server processes and args
            for s in "ab":
                save(current / f"health-before-{s}.json", api(s, "health"))
                metrics = api(s, "metrics")
                save(current / f"metrics-before-{s}.json", metrics)
                assert metrics.get("requests_kept") == 0
                assert run("docker", "exec", servers[s], "sha256sum", "/opt/strata/engine/strata").split()[0] == ENGINE_SHA256
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
                validate_drafter(effective, args.spec, args.draft_conf)
                for k, v in env_overrides.items():
                    assert processes[0]["strata_env"].get(k) == v, f"Env mismatch for {k}: expected {v}, got {processes[0]['strata_env'].get(k)}"

            record.update(phase="startup_inference" if phase == "startup" else "benchmark", benchmark_started=now())
            save(exp_dir / "progress.json", checkpoint)
            print(f"{now()} {phase} START", flush=True)

            if phase == "startup":
                for s in "ab":
                    response = api(s, "v1/chat/completions", {
                        "model": models[s],
                        "messages": [{"role": "user", "content": "Write the integers 1 through 40, separated by spaces."}],
                        "max_tokens": 128,
                        "temperature": 0,
                        "reasoning_effort": "none"
                    }, timeout=180)
                    save(current / f"smoke-{s}.json", response)
                    assert response.get("choices") and response["choices"][0].get("message", {}).get("content"), response
                    save(current / f"models-{s}.json", api(s, "v1/models"))
            else:
                bench_cmd = [
                    "docker", "run", "-d", "--pull", "never",
                    "--name", f"strata-s10-{args.id}-{phase}-bench",
                    "--network", "host",
                    "--label", f"lab.stage10.run={args.id}",
                    "--user", f"{os.getuid()}:{os.getgid()}",
                    "-e", "STRATA_DIR=/opt/strata",
                    "-v", f"{root}:/work",
                    "-v", "/srv/models/strata-iq3xxs:/iq3xxs:ro",
                    "--entrypoint", "/opt/strata/.venv/bin/python", UPSTREAM_IMAGE,
                    "/work/bench/c2_v100_contract.py",
                    "--url-a", f"http://127.0.0.1:{PORTS['a']}",
                    "--url-b", f"http://127.0.0.1:{PORTS['b']}",
                    "--expected-model-a", models["a"],
                    "--expected-model-b", models["b"],
                    "--config", f"/work/{current.relative_to(root)}/agent-a.json",
                    "--manifest", "/work/bench/workloads/v100-performance-v1.json",
                    "--out", f"/work/{current.relative_to(root)}/c2"
                ]
                save(current / "benchmark-command.json", bench_cmd)
                bench = run(*bench_cmd)
                owned.append(bench)
                checkpoint.setdefault("owned_container_ids", []).append(bench)
                record["bench_container_id"] = bench
                save(exp_dir / "progress.json", checkpoint)
                rc = run("docker", "wait", bench, timeout=1200)
                (current / "docker-bench.log").write_text(run("docker", "logs", bench))
                (current / "benchmark-exit-code").write_text(rc + "\n")
                assert rc == "0", f"C2 benchmark exited with code {rc}"
                summary = json.loads((current / "c2/summary.json").read_text())
                workload = json.loads((current / "c2/workload.json").read_text())
                assert [x["raw_prompt_sha256"] for x in workload["items"]] == PROMPT_HASHES
                assert summary["pass_mechanical"] and summary["active_overlap"] and summary["post_health"]
                assert summary["warmup_count"] == 0
                assert [x["prompt_tokens"] for x in summary["requests"]] == [126967, 126968]
                for req in summary["requests"]:
                    assert req["output_tokens"] >= 1024 and req["finish_reason"] == "stop"
                    assert req["cache_n"] == req["cached_tokens"] == 0
                record["metrics"] = [
                    {k: req[k] for k in ("label", "prompt_tokens", "output_tokens", "prefill_tok_s", "decode_tok_s", "ttft_s")}
                    for req in summary["requests"]
                ]

            for s in "ab":
                h = api(s, "health")
                assert h.get("status") == "ok" and h.get("loaded")
                save(current / f"health-after-{s}.json", h)
                after_processes = json.loads(run("docker", "exec", servers[s], "/opt/strata/.venv/bin/python", "-c", probe))
                before_process = json.loads((current / f"engine-process-{s}.json").read_text())
                assert len(after_processes) == 1 and all(
                    after_processes[0][k] == before_process[k] for k in ("pid", "pid_start_ticks", "args")
                ), "Engine process mutated or restarted"
                metrics_after = api(s, "metrics")
                save(current / f"metrics-after-{s}.json", metrics_after)
                rows = metrics_after.get("requests", [])
                assert rows and rows[0].get("drafts_offered", 0) > 0, "DFlash2 must offer drafts"
                notes = (current / f"logs/agent-{s}.log").read_text(errors="replace")
                assert re.search(r"strata dflash2: \d+-token draft head", notes)
                assert "no MTP layer is loaded (--draft-fallback none)" in notes
                (current / f"docker-{s}.log").write_text(run("docker", "logs", servers[s]))

            if phase == "startup":
                record["verdict"] = "STARTUP_PASS_NOT_C2"
            elif phase.startswith("diagnostic"):
                record["verdict"] = "DIAGNOSTIC_PASS_NOT_SCORED"
            else:
                record["verdict"] = "PASS"

            record.update(phase="validated", inference_finished=now())
            save(exp_dir / "progress.json", checkpoint)
            cleanup()
            snapshot(current, "after")

            # Validate GPU telemetry
            samples = [line.split(",") for line in (current / "gpu-telemetry.csv").read_text().splitlines() if len(line.split(",")) == 8]
            assert samples, "No GPU telemetry found"
            assert all(any(row[1].strip() == str(i) for row in samples) for i in (0, 1))
            assert all(float(row[7].strip()) <= args.sm_clock_ceiling and float(row[4].strip()) == 150 for row in samples), "Clock/power violation"
            assert len((current / "host-telemetry.jsonl").read_text().splitlines()) >= 2, "Missing host telemetry"

            record.update(phase="results_saved", finished=now())
            save(exp_dir / "progress.json", checkpoint)
            (current / "verdict").write_text(record["verdict"] + "\n")
            print(f"{now()} {phase} {record['verdict']} {json.dumps(record.get('metrics', []))}", flush=True)

        verify_idle(args.sm_clock_ceiling)
        checkpoint.update(phase="results_saved", verdict="PASS", finished=now(), owned_containers_stopped=True)
        save(exp_dir / "progress.json", checkpoint)
        (exp_dir / "exit-code").write_text("0\n")
        (exp_dir / "verdict").write_text("PASS\n")
        print(f"Candidate {args.arm} ({args.id}) COMPLETE PASS", flush=True)

    except BaseException as exc:
        for cid in owned:
            try:
                if current:
                    (current / f"failure-{cid[:12]}.log").write_text(run("docker", "logs", cid))
            except Exception:
                pass
        checkpoint.update(
            phase="interrupted",
            verdict="FAIL_TIMEOUT" if isinstance(exc, (TimeoutError, sp.TimeoutExpired)) else "INCONCLUSIVE",
            error=repr(exc),
            finished=now()
        )
        if checkpoint["batches"] and checkpoint["batches"][-1]["phase"] != "results_saved":
            checkpoint["batches"][-1].update(phase="interrupted", verdict=checkpoint["verdict"], error=repr(exc))
        save(exp_dir / "progress.json", checkpoint)
        (exp_dir / "exit-code").write_text("1\n")
        raise
    finally:
        cleanup()
        signal.alarm(0)


if __name__ == "__main__":
    if sys.argv[1:] == ["--sample-host"]:
        sample_host()
    else:
        main()
