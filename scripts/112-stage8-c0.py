#!/usr/bin/env python3
"""P520: bounded Stage 8 C0 single-change runner (preserves scripts 107/111 unchanged).

Scope: S8-C0 only — S8-C1 (c1-20261107T141343) configuration with ONLY
`--pool-workers 3` removed (leaving default automatic 2 pool workers on 0.1.57
with SIMT=1, SM70_TABLE=1, PF_WMMA=1). Does NOT reuse or overwrite closed U1/C1
IDs. No retries, combinations, promotion, serving interruption or hardware
changes. Run under an outer timeout; all evidence survives an SSH disconnect.
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
import time
import urllib.request

SOURCE = "c3b3f5035506f3e966f1b4b7b188aeaabae92f1d"
MANIFEST_SHA = "e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca"
HARNESS_SHA = "a8e42cc5a71421a7287618fd5be0332ae40f312426e4d243ce1c7619fdfc5246"
PORTS = {"a": 18086, "b": 18087}
CPUS = {"a": "0-2,6-8", "b": "3-5,9-11"}
ENV = {"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1"}
GPU_FIELDS = "timestamp,index,temperature.gpu,power.draw,power.limit,utilization.gpu,memory.used,clocks.sm"
FORBIDDEN_EXTRA_ARGS = {"--pool-workers", "--resident-budget-gib", "--adapt-async", "--expert-cache-per-layer"}


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


def wait_for_log(log_path, needle, timeout=15.0):
    deadline = time.monotonic() + timeout
    last = ""
    while True:
        last = log_path.read_text(errors="replace") if log_path.exists() else ""
        if needle in last:
            return last
        assert time.monotonic() < deadline, f"Expected log substring {needle!r} missing in {log_path}"
        time.sleep(0.2)


def snapshot(d, phase):
    (d / f"memory-{phase}.txt").write_text(run("free", "-b") + "\n")
    (d / f"vmstat-{phase}.txt").write_text(Path("/proc/vmstat").read_text())
    paths = sorted(Path("/srv/models/strata-iq3xxs/IQ3_XXS").glob("*.gguf"))
    paths += [Path("/srv/models/strata-iq3xxs/pack/iq3_xxs-native/dense.bin")]
    (d / f"cache-{phase}.json").write_text(run("fincore", "--json", "--bytes", *map(str, paths)) + "\n")


def idle():
    assert not run("docker", "ps", "-q"), "Running container found; no interruption authorized"
    assert not run("nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"), "GPU workload found"
    limits = run("nvidia-smi", "--query-gpu=power.limit", "--format=csv,noheader,nounits").splitlines()
    assert len(limits) == 2 and all(float(x) == 150 for x in limits), limits
    assert run("systemctl", "is-active", "v100-clock-lock.service") == "active"
    journal = run("journalctl", "-b", "-u", "v100-clock-lock.service", "--no-pager")
    for bus in ("00000000:65:00.0", "00000000:B3:00.0"):
        assert any("gpuClkMax 1110)" in line and bus in line for line in journal.splitlines()), journal
    listening = run("ss", "-H", "-ltn")
    for line in listening.splitlines():
        address = line.split()[3]
        assert address.rsplit(":", 1)[-1] not in {str(p) for p in PORTS.values()}, f"Listener on test port: {line}"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--id", required=True)
    p.add_argument("--arm", choices=("C0",), required=True)
    p.add_argument("--reference-receipt", required=True, type=Path, help="Completed S8-C1 progress receipt")
    p.add_argument("--image", required=True, help="Immutable sha256 image ID")
    p.add_argument("--engine-sha256", required=True)
    p.add_argument("--assets", required=True, type=Path)
    args = p.parse_args()
    assert re.fullmatch(r"c0-\d{8}T\d{6}", args.id)
    arm = "S8-C0"
    overrides = {}
    flags = []
    env = dict(ENV)
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", args.image)
    assert re.fullmatch(r"[0-9a-f]{64}", args.engine_sha256)
    assert socket.gethostname() == "p520-llm"
    root = Path.home() / "v100-x2-strata-qwen3.8-flash-next"
    assert args.reference_receipt.resolve().is_relative_to(root / "results/stage8/S8-C1")
    reference = json.loads(args.reference_receipt.read_text())
    assert reference["arm"] == "S8-C1" and reference["verdict"] == "PASS"
    assert reference["image_id"] == args.image
    assert reference["overrides"] == {"--pool-workers": "3"}
    assert reference.get("extra_flags", []) == []
    assert reference.get("runtime_env") == env
    assert len([b for b in reference["batches"] if b["scored"] and b.get("verdict") == "PASS"]) == 3

    locks = []
    for name in (".stage7-experiment.lock", ".stage8-experiment.lock"):
        lock = (root / "results" / name).open("a")
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        locks.append(lock)
    assert sha(root / "bench/c2_v100_contract.py") == HARNESS_SHA
    assert sha(root / "bench/workloads/v100-performance-v1.json") == MANIFEST_SHA
    image = json.loads(run("docker", "image", "inspect", args.image))[0]
    assert image["Id"] == args.image
    assert image["Config"]["Labels"]["org.opencontainers.image.revision"] == SOURCE
    image_env = dict(x.split("=", 1) for x in image["Config"]["Env"] if x.startswith("STRATA_"))
    assert image_env == {"STRATA_EXECV": "1"}, image_env
    idle()
    assets = args.assets.read_text()
    assert len(assets.splitlines()) >= 15
    asset_stats = {}
    for line in assets.splitlines():
        digest, name = line.split(maxsplit=1)
        assert re.fullmatch(r"[0-9a-f]{64}", digest)
        path = Path(name.strip())
        assert str(path).startswith(("/srv/models/strata-iq3xxs/", "/srv/models/strata-data/mtp/rt/"))
        st = path.stat()
        asset_stats[str(path)] = {"sha256": digest, "size": st.st_size, "mtime_ns": st.st_mtime_ns}
    d = root / "results/stage8" / arm / args.id
    d.mkdir(parents=True, exist_ok=False)
    checkpoint = {"id": args.id, "arm": arm, "phase": "prepared", "verdict": None,
                  "host": socket.gethostname(), "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
                  "pid": os.getpid(), "pid_start_ticks": Path(f"/proc/{os.getpid()}/stat").read_text().split()[21],
                  "started": now(), "timeout_s": 3600, "image_id": args.image, "source_sha": SOURCE,
                  "engine_sha256": args.engine_sha256, "runner_sha256": sha(Path(__file__)),
                  "harness_sha256": HARNESS_SHA, "manifest_sha256": MANIFEST_SHA,
                  "scope": "S8-C0 startup then exactly THREE fresh-process concurrent 128K C2; no retry; S8-C1 with ONLY --pool-workers 3 removed",
                  "overrides": overrides, "extra_flags": flags, "runtime_env": env,
                  "reference_id": reference["id"],
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
                run("docker", "stop", "-t", "20", cid, timeout=45)
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
        owned.clear()
        collectors.clear()
        handles.clear()
        if errors:
            raise RuntimeError(f"Owned container cleanup failed: {errors}")

    def interrupted(signum, frame):
        raise TimeoutError(f"Runner signal {signum}")

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        for phase in ("startup", "batch-1", "batch-2", "batch-3"):
            idle()
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
                                  ("vmstat.log", ["stdbuf", "-oL", "vmstat", "1"]),
                                  ("iostat.log", ["stdbuf", "-oL", "iostat", "-xz", "1"])]:
                handle = (current / filename).open("w")
                handles.append(handle)
                collectors.append(sp.Popen(cmd, stdout=handle, stderr=sp.STDOUT))
            configs, models, servers = {}, {}, {}
            for s in "ab":
                cfg = json.loads((root / f"results/stage5-iq3xxs/agent-{s}.json").read_text())
                expected = {"--max-context": "131072", "--kv": "int8", "--kv-resident": "32768", "--spec": "4", "--spec-min-p": "0.5", "--prefill": "auto", "--expert-cache": "auto"}
                for flag, val in expected.items():
                    assert cfg["args"][cfg["args"].index(flag) + 1] == val
                assert "--mmap-experts" in cfg["args"]
                assert not cfg.get("env") and not cfg.get("user_args")
                assert not (FORBIDDEN_EXTRA_ARGS & set(cfg["args"])), cfg["args"]
                cfg["model_name"] = f"qwen3.8-flash-next-iq3_xxs-s8-{args.id}-{phase}-{s}"
                cfg["drafting"] = "mtp"
                cfg["user_args"] = [item for flag, val in expected.items() for item in (flag, val)]
                configs[s], models[s] = cfg, cfg["model_name"]
                save(current / f"agent-{s}.json", cfg)
                name = f"strata-s8-{args.id}-{phase}-{s}"
                cmd = ["docker", "run", "-d", "--pull", "never", "--name", name, "--restart", "no", "--cpuset-cpus", CPUS[s],
                       "--gpus", f'"device={"ab".index(s)}"', "-p", f"127.0.0.1:{PORTS[s]}:8080",
                       "-v", "/srv/models/strata-iq3xxs:/iq3xxs:ro", "-v", "/srv/models/strata-data/mtp:/shared-mtp:ro",
                       "-v", f"{current}/logs:/trial-logs", "-v", f"{current}/agent-{s}.json:/opt/strata/config.json:ro"]
                for k, v in env.items():
                    cmd.extend(["-e", f"{k}={v}"])
                cmd.extend(["--entrypoint", "/opt/strata/.venv/bin/python", args.image, "/opt/strata/serve/server.py",
                            "--engine", "strata", "--config", "/opt/strata/config.json", "--host", "0.0.0.0", "--port", "8080"])
                save(current / f"command-{s}.json", cmd)
                cid = run(*cmd)
                owned.append(cid)
                servers[s] = cid
                (current / f"container-{s}.id").write_text(cid + "\n")
                c = json.loads(run("docker", "inspect", cid))[0]
                assert c["Image"] == args.image and c["HostConfig"]["CpusetCpus"] == CPUS[s]
                assert c["HostConfig"]["DeviceRequests"][0]["DeviceIDs"] == [str("ab".index(s))]
                assert c["HostConfig"]["PortBindings"]["8080/tcp"] == [{"HostIp": "127.0.0.1", "HostPort": str(PORTS[s])}]
                save(current / f"inspect-{s}.json", {"id": cid, "image": c["Image"], "pid": c["State"]["Pid"], "started": c["State"]["StartedAt"],
                                                     "cpus": CPUS[s], "gpus": c["HostConfig"]["DeviceRequests"], "mounts": c["Mounts"], "overrides": env})
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
  out.append({'pid':int(p.name),'args':cmd,'strata_env':env})
 except (FileNotFoundError,PermissionError,ProcessLookupError): pass
print(json.dumps(out))
"""
                processes = json.loads(run("docker", "exec", servers[s], "/opt/strata/.venv/bin/python", "-c", probe))
                assert len(processes) == 1, processes
                save(current / f"engine-process-{s}.json", processes[0])
                effective = processes[0]["args"]
                for flag, val in expected.items():
                    assert effective[effective.index(flag) + 1] == val, (flag, effective)
                assert "--mmap-experts" in effective and "--mtp" in effective and "--draft" not in effective
                assert not (FORBIDDEN_EXTRA_ARGS & set(effective)), effective
                assert all(processes[0]["strata_env"].get(k) == v for k, v in env.items())
                log_text = wait_for_log(current / f"logs/agent-{s}.log", "2 pool workers on logical processors")
                assert "3 CPU expert workers are configured" not in log_text, log_text
                wait_for_log(current / f"logs/agent-{s}.log", "MTP windows up to 4 tokens")

            record.update(phase="startup_inference" if phase == "startup" else "benchmark", benchmark_started=now())
            save(d / "progress.json", checkpoint)
            print(f"{now()} {phase} START", flush=True)
            if phase == "startup":
                for s in "ab":
                    response = api(s, "v1/chat/completions", {"model": models[s], "messages": [{"role": "user", "content": "Reply with READY."}], "max_tokens": 64, "temperature": 0, "reasoning_effort": "none"}, timeout=180)
                    save(current / f"smoke-{s}.json", response)
                    assert response.get("choices") and response["choices"][0].get("message", {}).get("content"), response
                    save(current / f"models-{s}.json", api(s, "v1/models"))
            else:
                cmd = ["docker", "run", "-d", "--pull", "never", "--name", f"strata-s8-{args.id}-{phase}-bench", "--network", "host", "--user", f"{os.getuid()}:{os.getgid()}",
                       "-e", "STRATA_DIR=/opt/strata", "-v", f"{root}:/work", "-v", "/srv/models/strata-iq3xxs:/iq3xxs:ro", "--entrypoint", "/opt/strata/.venv/bin/python", args.image,
                       "/work/bench/c2_v100_contract.py", "--url-a", f"http://127.0.0.1:{PORTS['a']}", "--url-b", f"http://127.0.0.1:{PORTS['b']}",
                       "--expected-model-a", models["a"], "--expected-model-b", models["b"], "--config", f"/work/{current.relative_to(root)}/agent-a.json",
                       "--manifest", "/work/bench/workloads/v100-performance-v1.json", "--out", f"/work/{current.relative_to(root)}/c2"]
                save(current / "benchmark-command.json", cmd)
                bench = run(*cmd)
                owned.append(bench)
                record["bench_container_id"] = bench
                save(d / "progress.json", checkpoint)
                rc = run("docker", "wait", bench, timeout=1200)
                (current / "docker-bench.log").write_text(run("docker", "logs", bench))
                (current / "benchmark-exit-code").write_text(rc + "\n")
                assert rc == "0", f"C2 exit {rc}"
                summary = json.loads((current / "c2/summary.json").read_text())
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
                save(current / f"metrics-after-{s}.json", api(s, "metrics"))
                (current / f"docker-{s}.log").write_text(run("docker", "logs", servers[s]))
            record.update(phase="results_saved", verdict="STARTUP_PASS_NOT_C2" if phase == "startup" else "PASS", finished=now())
            save(d / "progress.json", checkpoint)
            cleanup()
            snapshot(current, "after")
            samples = [line.split(",") for line in (current / "gpu-telemetry.csv").read_text().splitlines() if len(line.split(",")) == 8]
            assert samples, "No GPU telemetry"
            assert all(float(row[7].strip()) <= 1110 and float(row[4].strip()) == 150 for row in samples), "Clock/power cap mismatch"
            (current / "verdict").write_text(record["verdict"] + "\n")
            print(f"{now()} {phase} {record['verdict']} {json.dumps(record.get('metrics', []))}", flush=True)
        idle()
        checkpoint.update(phase="results_saved", verdict="PASS", finished=now(), owned_containers_stopped=True)
        save(d / "progress.json", checkpoint)
        (d / "exit-code").write_text("0\n")
        (d / "verdict").write_text(checkpoint["verdict"] + "\n")
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


if __name__ == "__main__":
    main()
