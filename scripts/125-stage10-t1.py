#!/usr/bin/env python3
"""P520: Stage 10 RAM contention benchmark runner (S10-T1).

Executes:
1. Condition A (Solo A): GPU0 + Agent A 단독 (3 fresh 128K C2 batches)
2. Condition B (Solo B): GPU1 + Agent B 단독 (3 fresh 128K C2 batches)
3. Condition C (Concurrent): GPU0 + GPU1 동시 (3 fresh 128K C2 batches)

Total 9 C2 batches under frozen S10-D4 recipe (spec 8, conf 0.7, prefill auto).
Collects:
- Per-batch Prefill, Decode, TTFT
- Continuous GPU thermals, power, clocks (nvidia-smi)
- Host RAM usage, major page faults, swap activity (vmstat, meminfo)
- Disk / NVMe I/O throughput (iostat)
- CPU memory controller bandwidth (pcm-memory, if permissions available)
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


def config_for(base, spec, draft_conf, prefill, model):
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

    pack_idx = cfg["args"].index("--pack")
    cfg["args"][pack_idx + 1] = "/stage10-data/packs/iq3_xxs-native"

    if "--spec-min-p" in cfg["args"]:
        idx = cfg["args"].index("--spec-min-p")
        del cfg["args"][idx:idx + 2]

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
    p.add_argument("--id", required=True, help="Experiment ID (e.g. t1-20261110T234500)")
    p.add_argument("--condition", choices=["all", "a", "b", "c"], default="all",
                   help="Run condition: a (Solo A), b (Solo B), c (Concurrent), or all (all three conditions)")
    p.add_argument("--spec", type=int, default=8)
    p.add_argument("--draft-conf", type=float, default=0.7)
    p.add_argument("--prefill", default="auto")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--sm-clock-ceiling", type=int, default=1245)
    args = p.parse_args()

    assert socket.gethostname() == "p520-llm", "Must run on p520-llm"
    root = Path.home() / "v100-x2-strata-qwen3.8-flash-next"
    assert root.is_dir()

    draft_data_dir = root / "results/stage10-preparation/draft-data"
    assert (draft_data_dir / "dflash2" / PACK_NAME).stat().st_size == 339694592
    assert sha(draft_data_dir / "dflash2" / PACK_NAME) == PACK_SHA

    # Dry run
    if args.dry_run:
        print(json.dumps({
            "dry_run": "PASS", "arm": "S10-T1", "id": args.id,
            "condition": args.condition, "spec": args.spec,
            "draft_conf": args.draft_conf, "prefill": args.prefill
        }))
        return

    exp_dir = root / "results/stage10/S10-T1" / args.id
    assert not exp_dir.exists(), f"Directory exists: {exp_dir}"
    exp_dir.mkdir(parents=True, exist_ok=False)

    checkpoint = {
        "id": args.id, "arm": "S10-T1", "phase": "prepared", "verdict": None,
        "host": socket.gethostname(),
        "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
        "pid": os.getpid(),
        "pid_start_ticks": Path(f"/proc/{os.getpid()}/stat").read_text().split()[21],
        "started": now(), "timeout_s": 7200,
        "image_id": UPSTREAM_IMAGE, "source_sha": SOURCE_SHA, "engine_sha256": ENGINE_SHA256,
        "runner_sha256": sha(Path(__file__)),
        "harness_sha256": HARNESS_SHA, "manifest_sha256": MANIFEST_SHA,
        "spec": args.spec, "draft_conf": args.draft_conf, "prefill": args.prefill,
        "conditions_run": args.condition,
        "batches": []
    }
    save(exp_dir / "progress.json", checkpoint)

    # Lock files
    locks = []
    for name in (".stage7-experiment.lock", ".stage8-experiment.lock", ".stage9-experiment.lock", ".stage10-experiment.lock"):
        lock = (root / "results" / name).open("a")
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        locks.append(lock)

    verify_idle(args.sm_clock_ceiling)

    # Build sequence of phases
    phases = []
    if args.condition in ("all", "a"):
        phases.extend(["solo-a-startup", "solo-a-batch-1", "solo-a-batch-2", "solo-a-batch-3"])
    if args.condition in ("all", "b"):
        phases.extend(["solo-b-startup", "solo-b-batch-1", "solo-b-batch-2", "solo-b-batch-3"])
    if args.condition in ("all", "c"):
        phases.extend(["concurrent-startup", "concurrent-batch-1", "concurrent-batch-2", "concurrent-batch-3"])

    owned = []
    try:
        for phase in phases:
            verify_idle(args.sm_clock_ceiling)
            current = exp_dir / phase
            current.mkdir()
            (current / "logs").mkdir()

            is_scored = "batch" in phase
            is_solo_a = phase.startswith("solo-a")
            is_solo_b = phase.startswith("solo-b")
            is_concurrent = phase.startswith("concurrent")

            active_sides = "a" if is_solo_a else ("b" if is_solo_b else "ab")
            record = {"id": f"{args.id}-{phase}", "phase": "loading", "started": now(), "scored": is_scored, "sides": active_sides}
            checkpoint["batches"].append(record)
            checkpoint.update(phase="running", current_phase=phase)
            save(exp_dir / "progress.json", checkpoint)
            snapshot(current, "before")

            collectors = []
            handles = []
            for filename, cmd in [
                ("gpu-telemetry.csv", ["nvidia-smi", f"--query-gpu={GPU_FIELDS}", "--format=csv,noheader,nounits", "-l", "1"]),
                ("host-telemetry.jsonl", [sys.executable, "-u", str(Path(__file__).resolve()), "--sample-host"]),
                ("vmstat.log", ["stdbuf", "-oL", "vmstat", "1"]),
                ("iostat.log", ["stdbuf", "-oL", "iostat", "-xz", "1"])
            ]:
                handle = (current / filename).open("w")
                handles.append(handle)
                collectors.append(sp.Popen(cmd, stdout=handle, stderr=sp.STDOUT))

            # PCM memory bandwidth logger (if accessible)
            pcm_handle = (current / "pcm-memory.log").open("w")
            handles.append(pcm_handle)
            pcm_proc = sp.Popen(["/usr/sbin/pcm-memory", "1", "-csv=" + str(current / "pcm-memory.csv")],
                                stdout=pcm_handle, stderr=sp.STDOUT, env=dict(os.environ, PCM_NO_MSR="1"))
            collectors.append(pcm_proc)

            configs, models, servers = {}, {}, {}
            for s in active_sides:
                base = json.loads((root / f"results/stage5-iq3xxs/agent-{s}.json").read_text())
                model = f"qwen3.8-flash-next-iq3_xxs_s10_{args.id}_{phase}_{s}".replace("-", "_")
                cfg, expected = config_for(base, args.spec, args.draft_conf, args.prefill, model)
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
                for k, v in BASE_ENV.items():
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
                for s in active_sides:
                    try:
                        h = api(s, "health")
                        if h.get("status") != "ok" or not h.get("loaded"):
                            ready = False
                    except Exception:
                        ready = False
                if ready:
                    break
                assert time.monotonic() < deadline, f"Timeout waiting for server {active_sides}"
                for s in active_sides:
                    assert run("docker", "inspect", servers[s], "--format", "{{.State.Running}}") == "true", f"Server exited {s}"
                time.sleep(2)

            for s in active_sides:
                save(current / f"health-before-{s}.json", api(s, "health"))
                metrics = api(s, "metrics")
                save(current / f"metrics-before-{s}.json", metrics)
                assert metrics.get("requests_kept") == 0
                assert run("docker", "exec", servers[s], "sha256sum", "/opt/strata/engine/strata").split()[0] == ENGINE_SHA256

            record.update(phase="startup_inference" if "startup" in phase else "benchmark", benchmark_started=now())
            save(exp_dir / "progress.json", checkpoint)
            print(f"{now()} {phase} START ({active_sides})", flush=True)

            if "startup" in phase:
                for s in active_sides:
                    response = api(s, "v1/chat/completions", {
                        "model": models[s],
                        "messages": [{"role": "user", "content": "Write the integers 1 through 40, separated by spaces."}],
                        "max_tokens": 128, "temperature": 0, "reasoning_effort": "none"
                    }, timeout=180)
                    save(current / f"smoke-{s}.json", response)
                    assert response.get("choices") and response["choices"][0].get("message", {}).get("content"), response
            else:
                if is_concurrent:
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
                else:
                    target_side = active_sides
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
                        "/work/bench/c2_v100_solo_contract.py",
                        "--url", f"http://127.0.0.1:{PORTS[target_side]}",
                        "--side", target_side,
                        "--expected-model", models[target_side],
                        "--config", f"/work/{current.relative_to(root)}/agent-{target_side}.json",
                        "--manifest", "/work/bench/workloads/v100-performance-v1.json",
                        "--out", f"/work/{current.relative_to(root)}/c2"
                    ]
                save(current / "benchmark-command.json", bench_cmd)
                bench = run(*bench_cmd)
                owned.append(bench)
                checkpoint.setdefault("owned_container_ids", []).append(bench)
                save(exp_dir / "progress.json", checkpoint)
                rc = run("docker", "wait", bench, timeout=1200)
                (current / "docker-bench.log").write_text(run("docker", "logs", bench))
                assert rc == "0", f"Benchmark failed with code {rc}"

            record.update(phase="unloading", inference_finished=now())
            save(exp_dir / "progress.json", checkpoint)

            for s in active_sides:
                save(current / f"health-after-{s}.json", api(s, "health"))
                save(current / f"metrics-after-{s}.json", api(s, "metrics"))

            for proc in collectors:
                proc.send_signal(signal.SIGINT)
                try:
                    proc.wait(timeout=5)
                except sp.TimeoutExpired:
                    proc.kill()
            for h in handles:
                h.close()

            for s in active_sides:
                (current / f"docker-{s}.log").write_text(run("docker", "logs", servers[s]))
                stop_owned(servers[s], args.id)
                owned.remove(servers[s])
            if "startup" not in phase:
                stop_owned(bench, args.id)
                owned.remove(bench)

            snapshot(current, "after")
            v = "STARTUP_PASS_NOT_C2" if "startup" in phase else "PASS"
            record.update(phase="results_saved", verdict=v, finished=now())
            if is_scored:
                summary = json.loads((current / "c2/summary.json").read_text())
                metrics_list = []
                for req in summary["requests"]:
                    metrics_list.append({
                        "label": req["label"],
                        "prompt_tokens": req["prompt_tokens"],
                        "output_tokens": req["output_tokens"],
                        "prefill_tok_s": req["prefill_tok_s"],
                        "decode_tok_s": req["decode_tok_s"],
                        "ttft_s": req["ttft_s"]
                    })
                record["metrics"] = metrics_list
                print(f"{now()} {phase} {v} {json.dumps(metrics_list)}", flush=True)
            else:
                print(f"{now()} {phase} {v}", flush=True)
            save(exp_dir / "progress.json", checkpoint)

        checkpoint.update(phase="results_saved", verdict="PASS", finished=now(), owned_containers_stopped=True)
        save(exp_dir / "progress.json", checkpoint)
        print(f"S10-T1 ({args.id}) COMPLETE PASS", flush=True)

    finally:
        for cid in list(owned):
            try:
                run("docker", "stop", "-t", "10", cid)
            except Exception:
                pass


if __name__ == "__main__":
    main()
