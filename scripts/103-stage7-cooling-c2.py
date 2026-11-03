#!/usr/bin/env python3
"""Three user-authorized cooling measurements on the existing XXS-14 servers.

Run on P520 through SSH. Historical experiment IDs and runners are untouched.
Restarts only the explicitly named serving pair, leaves it serving afterwards,
and runs the original frozen C2 harness once per fresh-process batch. No retries.
"""
import argparse
import concurrent.futures
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

IMAGE = "sha256:2095eed79b0038ef23d602a0490bf0d89c63ad8e84ace8654c5016b2a51d2246"
MANIFEST_SHA = "e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca"
HARNESS_SHA = "a8e42cc5a71421a7287618fd5be0332ae40f312426e4d243ce1c7619fdfc5246"
NAMES = {s: f"strata-s7-xxs14-serve-{s}" for s in "ab"}
PORTS = dict(a=8080, b=8081)
CPUS = dict(a="0-2,6-8", b="3-5,9-11")
GPU_FIELDS = "timestamp,index,temperature.gpu,power.draw,power.limit,utilization.gpu,memory.used,clocks.sm"


def now():
    return dt.datetime.now().astimezone().isoformat()


def command(*args, timeout=60):
    return sp.check_output(args, text=True, stderr=sp.STDOUT, timeout=timeout).strip()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.replace(path)


def api(s, route):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORTS[s]}/{route}", timeout=5) as r:
        return json.load(r)


def inspect(s):
    return json.loads(command("docker", "inspect", NAMES[s]))[0]


def snapshot(d, when):
    (d / f"memory-{when}.txt").write_text(command("free", "-b") + "\n")
    (d / f"vmstat-{when}.txt").write_text(Path("/proc/vmstat").read_text())
    paths = sorted(Path("/srv/models/strata-iq3xxs/IQ3_XXS").glob("*.gguf"))
    paths += [Path("/srv/models/strata-iq3xxs/pack/iq3_xxs-native/dense.bin")]
    (d / f"cache-{when}.json").write_text(command("fincore", "--json", "--bytes", *map(str, paths)) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True)
    args = parser.parse_args()
    assert re.fullmatch(r"cooling-\d{8}T\d{6}", args.id), "Unique cooling ID required"
    assert socket.gethostname() == "p520-llm"
    root = Path.home() / "v100-x2-strata-qwen3.8-flash-next"
    lock = (root / "results/.stage7-experiment.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert sha(root / "bench/workloads/v100-performance-v1.json") == MANIFEST_SHA
    assert sha(root / "bench/c2_v100_contract.py") == HARNESS_SHA
    assert command("docker", "image", "inspect", IMAGE, "--format", "{{.Id}}") == IMAGE
    assert set(command("docker", "ps", "--format", "{{.Names}}").splitlines()) == set(NAMES.values())
    configs, models, config_paths, source_logs, original_ids = {}, {}, {}, {}, {}
    safe_inspects = {}
    for s in "ab":
        c = inspect(s)
        assert c["Image"] == IMAGE and c["State"]["Running"]
        assert c["HostConfig"]["CpusetCpus"] == CPUS[s]
        assert c["HostConfig"]["DeviceRequests"][0]["DeviceIDs"] == [str("ab".index(s))]
        env = dict(x.split("=", 1) for x in c["Config"]["Env"] if x.startswith("STRATA_"))
        assert env == {"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1", "STRATA_EXECV": "1"}, env
        assert c["HostConfig"]["PortBindings"]["8080/tcp"] == [{"HostIp": "127.0.0.1", "HostPort": str(PORTS[s])}]
        mounts = {m["Destination"]: m for m in c["Mounts"]}
        for dest in ("/iq3xxs", "/shared-mtp", "/opt/strata/config.json"):
            assert not mounts[dest]["RW"]
        config_paths[s] = Path(mounts["/opt/strata/config.json"]["Source"])
        configs[s] = json.loads(config_paths[s].read_text())
        for flag, value in {"--max-context": "131072", "--kv": "int8", "--kv-resident": "32768", "--spec": "4", "--spec-min-p": "0.5"}.items():
            assert configs[s]["args"][configs[s]["args"].index(flag) + 1] == value
        assert "--mmap-experts" in configs[s]["args"]
        models[s] = configs[s]["model_name"]
        source_logs[s] = Path(mounts["/trial-logs"]["Source"]) / f"agent-{s}.log"
        original_ids[s] = c["Id"]
        safe_inspects[s] = {"id": c["Id"], "image": c["Image"], "cpus": CPUS[s], "gpus": c["HostConfig"]["DeviceRequests"], "mounts": c["Mounts"], "strata_env": env, "restart_policy": c["HostConfig"]["RestartPolicy"]}
        assert api(s, "health")["loaded"]
        assert not api(s, "status").get("busy"), "Active request; refusing to interrupt"
    assert configs["a"]["args"] == configs["b"]["args"]
    gpu_pids = set(command("nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader").splitlines())
    owned = set()
    for s in "ab":
        owned.update(command("docker", "top", original_ids[s], "-eo", "pid").splitlines()[1:])
    assert gpu_pids <= {x.strip() for x in owned}, "Unknown GPU workload"
    limits = command("nvidia-smi", "--query-gpu=power.limit", "--format=csv,noheader,nounits").splitlines()
    assert len(limits) == 2 and all(float(x) == 150 for x in limits), limits
    d = root / "results/stage7-cooling" / args.id
    d.mkdir(parents=True, exist_ok=False)
    checkpoint = {"id": args.id, "phase": "prepared", "verdict": None, "host": socket.gethostname(), "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(), "pid": os.getpid(), "pid_start_ticks": Path(f"/proc/{os.getpid()}/stat").read_text().split()[21], "started": now(), "timeout_s": 2400, "scope": "Exactly three fresh-process 128K dual-agent C2 cooling measurements; no retries, warmup or noise measurements; preserve power/clocks/tunnel; leave current servers running", "image_id": IMAGE, "runner_sha256": sha(Path(__file__)), "manifest_sha256": MANIFEST_SHA, "harness_sha256": HARNESS_SHA, "serving": safe_inspects, "batches": []}
    save(d / "progress.json", checkpoint)
    for s in "ab":
        save(d / f"agent-{s}.json", configs[s])
    save(d / "config-sha256.json", {s: sha(config_paths[s]) for s in "ab"})
    (d / "gpu-before.csv").write_text(command("nvidia-smi", f"--query-gpu={GPU_FIELDS}", "--format=csv,noheader") + "\n")
    (d / "rollback.txt").write_text("Serving container identities/configs/ports are preserved; successful run leaves both serving.\nRecovery if either is stopped: docker start strata-s7-xxs14-serve-a strata-s7-xxs14-serve-b\nDo not restart an active request or resume completed batch IDs.\n")
    processes, handles = [], []
    bench_id = None
    batch_dir = None

    def stop_collectors():
        for proc in processes:
            if proc.poll() is None:
                proc.terminate()
        for proc in processes:
            try:
                proc.wait(timeout=5)
            except sp.TimeoutExpired:
                proc.kill()
                proc.wait()
        for handle in handles:
            handle.close()
        processes.clear()
        handles.clear()

    def interrupted(signum, frame):
        raise TimeoutError(f"Runner received signal {signum}")

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        for index in range(1, 4):
            batch_dir = d / f"batch-{index}"
            batch_dir.mkdir(exist_ok=False)
            record = {"index": index, "id": f"{args.id}-{index}", "phase": "prepared", "started": now()}
            checkpoint["batches"].append(record)
            checkpoint.update(phase="running", current_batch=index)
            save(d / "progress.json", checkpoint)
            log_starts = {}
            for s in "ab":
                assert inspect(s)["Id"] == original_ids[s]
                assert sha(config_paths[s]) == json.loads((d / "config-sha256.json").read_text())[s]
                assert not api(s, "status").get("busy"), "Active request before restart"
                stat = source_logs[s].stat()
                log_starts[s] = (stat.st_ino, stat.st_size)
            snapshot(batch_dir, "before")
            for filename, cmd in [("gpu-telemetry.csv", ["nvidia-smi", f"--query-gpu={GPU_FIELDS}", "--format=csv,noheader", "-l", "1"]), ("vmstat.log", ["stdbuf", "-oL", "vmstat", "1"]), ("iostat.log", ["stdbuf", "-oL", "iostat", "-xz", "1"])]:
                handle = (batch_dir / filename).open("w")
                handles.append(handle)
                processes.append(sp.Popen(cmd, stdout=handle, stderr=sp.STDOUT))
            print(f"{now()} BATCH {index}/3 restarting serving pair", flush=True)
            record["phase"] = "loading"
            save(d / "progress.json", checkpoint)
            record["before_processes"] = {s: {"pid": inspect(s)["State"]["Pid"], "started_at": inspect(s)["State"]["StartedAt"]} for s in "ab"}
            command("docker", "restart", "-t", "20", *(original_ids[s] for s in "ab"), timeout=120)
            deadline = time.monotonic() + 600
            while True:
                ready = True
                for s in "ab":
                    assert inspect(s)["State"]["Running"], f"Server {s} exited"
                    try:
                        h = api(s, "health")
                        ready &= h.get("status") == "ok" and h.get("loaded") and h.get("max_context") == 131072 and h.get("model") == models[s]
                    except Exception:
                        ready = False
                if ready:
                    break
                assert time.monotonic() < deadline, "Server loading deadline"
                time.sleep(2)
            record["processes"] = {}
            for s in "ab":
                c = inspect(s)
                record["processes"][s] = {"container_id": c["Id"], "pid": c["State"]["Pid"], "started_at": c["State"]["StartedAt"]}
                assert c["State"]["StartedAt"] != record["before_processes"][s]["started_at"]
                assert api(s, "metrics").get("requests_kept") == 0
                save(batch_dir / f"health-before-{s}.json", api(s, "health"))
            if index == 1:
                engine_sha = command("docker", "exec", original_ids["a"], "sha256sum", "/opt/strata/engine/strata").split()[0]
                assert engine_sha == "e98d7c6316500dfce9c05784557b3f20f6a340bdc853aaa49d479697f6247b4e"
                checkpoint["engine_sha256"] = engine_sha
            record.update(phase="benchmark", benchmark_started=now())
            save(d / "progress.json", checkpoint)
            print(f"{now()} BATCH {index}/3 C2 START", flush=True)
            cmd = ["docker", "run", "-d", "--pull", "never", "--name", f"strata-s7-{args.id}-{index}-bench", "--network", "host", "--user", f"{os.getuid()}:{os.getgid()}", "-e", "STRATA_DIR=/opt/strata", "-v", f"{root}:/work", "-v", "/srv/models/strata-iq3xxs:/iq3xxs:ro", "--entrypoint", "/opt/strata/.venv/bin/python", IMAGE, "/work/bench/c2_v100_contract.py", "--url-a", "http://127.0.0.1:8080", "--url-b", "http://127.0.0.1:8081", "--expected-model-a", models["a"], "--expected-model-b", models["b"], "--config", f"/work/{d.relative_to(root)}/agent-a.json", "--manifest", "/work/bench/workloads/v100-performance-v1.json", "--out", f"/work/{batch_dir.relative_to(root)}/c2"]
            save(batch_dir / "benchmark-command.json", cmd)
            bench_id = command(*cmd)
            record["bench_container_id"] = bench_id
            save(d / "progress.json", checkpoint)
            bench_rc = command("docker", "wait", bench_id, timeout=1200)
            record["benchmark_finished"] = now()
            (batch_dir / "docker-bench.log").write_text(command("docker", "logs", bench_id))
            (batch_dir / "benchmark-exit-code").write_text(bench_rc + "\n")
            bench_id = None
            stop_collectors()
            snapshot(batch_dir, "after")
            for s in "ab":
                (batch_dir / f"docker-{s}.log").write_text(command("docker", "logs", "--since", record["started"], original_ids[s]))
                data = source_logs[s].read_bytes()
                inode, offset = log_starts[s]
                if source_logs[s].stat().st_ino == inode and len(data) >= offset:
                    data = data[offset:]
                (batch_dir / f"engine-{s}.log").write_bytes(data)
                save(batch_dir / f"health-after-{s}.json", api(s, "health"))
                save(batch_dir / f"metrics-after-{s}.json", api(s, "metrics"))
            summary = json.loads((batch_dir / "c2/summary.json").read_text())
            assert bench_rc == "0", f"Benchmark failed: {bench_rc}"
            assert summary["pass_mechanical"] and summary["active_overlap"] and summary["post_health"]
            assert summary["warmup_count"] == 0
            assert [x["prompt_tokens"] for x in summary["requests"]] == [126967, 126968]
            for req in summary["requests"]:
                assert req["output_tokens"] >= 1024 and req["finish_reason"] == "stop"
                assert req["cache_n"] == req["cached_tokens"] == 0
            record.update(phase="results_saved", verdict="PASS", finished=now())
            (batch_dir / "verdict").write_text("PASS\n")
            save(d / "progress.json", checkpoint)
            print(f"{now()} BATCH {index}/3 PASS " + json.dumps({r["label"]: {k: r[k] for k in ["prefill_tok_s", "decode_tok_s", "output_tokens", "ttft_s"]} for r in summary["requests"]}), flush=True)
        save(d / "final-health.json", {s: api(s, "health") for s in "ab"})
        checkpoint.update(phase="results_saved", verdict="PASS", finished=now(), serving_left_running=True)
        (d / "exit-code").write_text("0\n")
        (d / "verdict").write_text("PASS\n")
        save(d / "progress.json", checkpoint)
        print(f"{now()} COMPLETE 3/3 PASS; serving pair left running", flush=True)
    except BaseException as exc:
        checkpoint.update(phase="interrupted", verdict="FAIL_TIMEOUT" if isinstance(exc, (TimeoutError, sp.TimeoutExpired)) else "INCONCLUSIVE", error=repr(exc), finished=now())
        if bench_id:
            sp.run(["docker", "stop", "-t", "20", bench_id], timeout=30, check=False)
        stop_collectors()
        (d / "exit-code").write_text("1\n")
        save(d / "progress.json", checkpoint)
        raise


if __name__ == "__main__":
    main()
