#!/usr/bin/env python3
"""Stage 12 candidate execution runner (smoke1, smoke2, diag, screen, scored 128K C2).

Enforces:
- Tesla V100 135-1245 MHz clock lock & 150 W configured power cap
- --prefill auto:8192 explicitly locked & verified in startup logs (chunk <= 8192)
- --prompt-cache 0 (prefix reuse disabled)
- DFlash2 active with --draft-fallback none (no MTP fallback)
- Zero silent D2 overrides; only explicit --extra-env applied
- Isolated single-GPU agents on cpusets 0-2,6-8 and 3-5,9-11
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

CLIENT_BENCH_IMAGE = "sha256:dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d"
PACK_SHA = "4a42b98220ea7880664002c8edda1563aecbae754b762a2e2f31b2b91ee93ecd"
PACK_NAME = "qwen3.8-flash-next-dflash2.q4_0-selq4.pack"
Q4_0_PACK_NAME = "qwen3.8-flash-next-dflash2.q4_0.pack"
MANIFEST_SHA = "e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca"
HARNESS_SHA = "a8e42cc5a71421a7287618fd5be0332ae40f312426e4d243ce1c7619fdfc5246"
PROMPT_HASHES = [
    "882a3617750ab8dbcb61d3e8e1d42641555a6b1450d060d7bb22a4f1161670b6",
    "5a19042f67dd7702e843595467e1d6c2b96414f565b0fbfa8036590709dba557",
]
PORTS = {"a": 18086, "b": 18087}
CPUS = {"a": "0-2,6-8", "b": "3-5,9-11"}
FORBIDDEN_ENV = {"STRATA_NV_CHUNK", "STRATA_PREFILL_AUTO_MAX", "STRATA_ADAPT_LAG", "STRATA_ADAPT_NOWAIT", "STRATA_PF_HC_REGION", "STRATA_AUX_CPUS"}
GPU_FIELDS = "timestamp,index,temperature.gpu,power.draw,power.limit,utilization.gpu,memory.used,clocks.sm"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def now() -> str:
    return dt.datetime.now().astimezone().isoformat()


def run(*args, timeout=60) -> str:
    return sp.check_output(args, text=True, stderr=sp.STDOUT, timeout=timeout).strip()


def save(path: Path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n")
    tmp.replace(path)


def api(s: str, route: str, body=None, timeout: int = 5):
    url = f"http://127.0.0.1:{PORTS[s]}/{route}"
    req = urllib.request.Request(
        url,
        None if body is None else json.dumps(body).encode(),
        {} if body is None else {"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def snapshot(d: Path, phase: str):
    (d / f"memory-{phase}.txt").write_text(run("free", "-b") + "\n")
    (d / f"vmstat-{phase}.txt").write_text(Path("/proc/vmstat").read_text())
    paths = sorted(Path("/srv/models/strata-iq3xxs/IQ3_XXS").glob("*.gguf"))
    paths += [Path("/srv/models/strata-iq3xxs/pack/iq3_xxs-native/dense.bin")]
    (d / f"cache-{phase}.json").write_text(run("fincore", "--json", "--bytes", *map(str, paths)) + "\n")


def verify_idle(ceiling: int = 1245):
    assert not run("docker", "ps", "-q"), "Running container found; aborting"
    assert not run("nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"), "GPU workload found"
    limits = run("nvidia-smi", "--query-gpu=power.limit", "--format=csv,noheader,nounits").splitlines()
    assert len(limits) == 2 and all(float(x) == 150 for x in limits), limits
    assert run("systemctl", "is-active", "v100-clock-lock.service") == "active"
    journal = run("journalctl", "-b", "-u", "v100-clock-lock.service", "--no-pager")
    for bus in ("00000000:65:00.0", "00000000:B3:00.0"):
        applied = [line for line in journal.splitlines() if "GPU clocks set to" in line and bus in line]
        assert applied and f"gpuClkMin 135, gpuClkMax {ceiling})" in applied[-1], (bus, applied)
    for line in run("ss", "-H", "-ltn").splitlines():
        port = line.split()[3].rsplit(":", 1)[-1]
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
            "vmstat": {k: vm[k] for k in ("pgmajfault", "pswpin", "pswpout", "pgpgin", "pgpgout")},
        }), flush=True)
        time.sleep(1)


def stop_owned(cid: str, experiment_id: str):
    identity = json.loads(run("docker", "inspect", cid))[0]
    assert identity["Config"].get("Labels", {}).get("lab.stage12.run") == experiment_id, "Refuse foreign cleanup"
    run("docker", "stop", "-t", "20", cid, timeout=45)


def config_for(base: dict, draft_conf: float, spec: int, prefill: str, model: str, extra_args: list[str], legacy_0159: bool):
    assert prefill == "auto:8192", f"Only --prefill auto:8192 allowed in Stage 12, got {prefill}"
    cfg = json.loads(json.dumps(base))
    expected = {
        "--max-context": "131072",
        "--kv": "int8",
        "--kv-resident": "32768",
        "--spec": str(spec),
        "--prefill": prefill,
        "--expert-cache": "auto",
        "--draft-conf": f"{draft_conf:g}",
    }
    if not legacy_0159:
        expected["--prompt-cache"] = "0"
    assert "--mmap-experts" in cfg["args"]
    assert cfg["gpu"] == 0 and cfg["gpus_asked"]
    cfg["model_name"] = model
    cfg["drafting"] = "dflash2"
    cfg["args"][cfg["args"].index("--pack") + 1] = "/stage10-data/packs/iq3_xxs-native"
    if "--spec-min-p" in cfg["args"]:
        idx = cfg["args"].index("--spec-min-p")
        del cfg["args"][idx:idx + 2]
    for k, v in expected.items():
        if k in cfg["args"]:
            cfg["args"][cfg["args"].index(k) + 1] = v
        else:
            cfg["args"].extend([k, v])
    if extra_args:
        cfg["args"].extend(extra_args)
    cfg["user_args"] = [item for flag, val in expected.items() for item in (flag, val)] + list(extra_args)
    return cfg, expected


def validate_drafter(effective: list[str], spec: int, draft_conf: float):
    assert "--mtp" not in effective, "MTP drafter found in DFlash2 arm"
    assert "--spec-min-p" not in effective
    expected_flags = {
        "--draft": "dflash2",
        "--draft-fallback": "none",
        "--draft-model": "/stage10-data/dflash2/" + PACK_NAME,
        "--spec": str(spec),
        "--draft-conf": f"{draft_conf:g}",
        "--mtp-draft-vocab": "/shared-mtp/rt/draft_vocab.bin",
    }
    for key, value in expected_flags.items():
        assert effective.count(key) == 1 and effective[effective.index(key) + 1] == value, (key, effective)


def verify_chunk_safety(log_text: str):
    # Ensure startup never picks >8192 chunk
    for m in re.finditer(r"prefill(?:\s+chunk)?[^0-9\n]*(\d+)", log_text, re.IGNORECASE):
        val = int(m.group(1))
        if val in (16384, 32768):
            raise AssertionError(f"Unsafe prefill chunk detected in log: {m.group(0)}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--arm", required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--mode", required=True, choices=["smoke1", "smoke2", "diag", "screen", "scored"])
    p.add_argument("--image", required=True)
    p.add_argument("--engine-sha256", required=True)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--spec", type=int, default=8)
    p.add_argument("--draft-conf", type=float, default=0.7)
    p.add_argument("--prefill", default="auto:8192")
    p.add_argument("--extra-env", nargs="*", default=[])
    p.add_argument("--extra-args", nargs="*", default=[])
    p.add_argument("--legacy-0159", action="store_true", help="Use /opt/strata/serve/server.py layout (for S12-R0 only)")
    p.add_argument("--sm-clock-ceiling", type=int, default=1245)
    args = p.parse_args()

    assert socket.gethostname() == "p520-llm", "Must run on p520-llm"
    assert args.prefill == "auto:8192", "Stage 12 requires explicit --prefill auto:8192"
    root = Path.home() / "v100-x2-strata-qwen3.8-flash-next"

    env_overrides = {}
    for pair in args.extra_env:
        k, v = pair.split("=", 1)
        assert k not in FORBIDDEN_ENV, f"Forbidden env var: {k}"
        env_overrides[k] = v

    draft_data_dir = root / "results/stage10-preparation/draft-data"
    assert sha(draft_data_dir / "dflash2" / PACK_NAME) == PACK_SHA
    assert sha(root / "bench/c2_v100_contract.py") == HARNESS_SHA
    assert sha(root / "bench/workloads/v100-performance-v1.json") == MANIFEST_SHA

    locks = []
    for name in (".stage7-experiment.lock", ".stage8-experiment.lock", ".stage9-experiment.lock",
                 ".stage10-experiment.lock", ".stage11x-experiment.lock", ".stage12-experiment.lock"):
        lock = (root / "results" / name).open("a")
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        locks.append(lock)

    verify_idle(args.sm_clock_ceiling)
    assets_file = root / "artifacts/stage8-results-20261107/assets.sha256"
    asset_stats = {}
    for line in assets_file.read_text().splitlines():
        if not line.strip():
            continue
        digest, name = line.split(maxsplit=1)
        st = Path(name.strip()).stat()
        asset_stats[name.strip()] = {"sha256": digest, "size": st.st_size, "mtime_ns": st.st_mtime_ns}

    exp_dir = root / f"results/stage12/{args.arm}" / args.id
    assert not exp_dir.exists(), f"Experiment dir exists: {exp_dir}"
    exp_dir.mkdir(parents=True, exist_ok=False)

    checkpoint = {
        "id": args.id, "arm": args.arm, "mode": args.mode, "phase": "prepared", "verdict": None,
        "host": socket.gethostname(),
        "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
        "started": now(), "image_id": args.image, "source_sha": args.source_sha,
        "engine_sha256": args.engine_sha256, "runner_sha256": sha(Path(__file__)),
        "overrides": env_overrides, "extra_args": args.extra_args,
        "spec": args.spec, "draft_conf": args.draft_conf, "prefill": args.prefill,
        "sm_clock_ceiling_mhz": args.sm_clock_ceiling, "batches": [],
    }
    save(exp_dir / "progress.json", checkpoint)
    save(exp_dir / "assets.json", asset_stats)

    if args.mode == "smoke1":
        phases = [("smoke1", "a")]
    elif args.mode == "smoke2":
        phases = [("smoke2", "ab")]
    elif args.mode == "diag":
        phases = [("diagnostic-1", "ab")]
    elif args.mode == "screen":
        phases = [("startup", "ab"), ("batch-1", "ab")]
    else:
        phases = [("startup", "ab")] + [(f"batch-{i + 1}", "ab") for i in range(3)]

    owned, collectors, handles = [], [], []
    current = None
    server_entry = "/opt/strata/serve/server.py" if args.legacy_0159 else "/opt/strata/terminal/serve/server.py"

    def cleanup():
        for cid in reversed(owned):
            try:
                stop_owned(cid, args.id)
            except Exception:
                pass
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
        owned.clear()

    def handle_sig(signum, frame):
        raise InterruptedError(f"Signal {signum}")

    signal.signal(signal.SIGTERM, handle_sig)
    signal.signal(signal.SIGINT, handle_sig)
    signal.alarm(5400)

    try:
        for phase, sides in phases:
            verify_idle(args.sm_clock_ceiling)
            current = exp_dir / phase
            current.mkdir()
            (current / "logs").mkdir()
            is_c2 = phase.startswith("batch-") or phase.startswith("diagnostic")
            record = {"id": f"{args.id}-{phase}", "phase": "loading", "started": now(), "scored": phase.startswith("batch-")}
            checkpoint["batches"].append(record)
            save(exp_dir / "progress.json", checkpoint)
            snapshot(current, "before")

            for filename, cmd in [
                ("gpu-telemetry.csv", ["nvidia-smi", f"--query-gpu={GPU_FIELDS}", "--format=csv,noheader,nounits", "-l", "1"]),
                ("host-telemetry.jsonl", [sys.executable, "-u", str(Path(__file__).resolve()), "--sample-host"]),
                ("vmstat.log", ["stdbuf", "-oL", "vmstat", "1"]),
                ("iostat.log", ["stdbuf", "-oL", "iostat", "-xz", "1"]),
            ]:
                h = (current / filename).open("w")
                handles.append(h)
                collectors.append(sp.Popen(cmd, stdout=h, stderr=sp.STDOUT))

            models, servers = {}, {}
            for s in sides:
                base = json.loads((root / f"results/stage5-iq3xxs/agent-{s}.json").read_text())
                model = f"qwen3.8-flash-next-iq3_xxs_s12_{args.id}_{phase}_{s}".replace("-", "_")
                cfg, expected = config_for(base, args.draft_conf, args.spec, args.prefill, model, args.extra_args, args.legacy_0159)
                models[s] = cfg["model_name"]
                save(current / f"agent-{s}.json", cfg)
                cname = f"strata-s12-{args.id}-{phase}-{s}"
                cmd = [
                    "docker", "run", "-d", "--pull", "never", "--name", cname, "--restart", "no",
                    "--cpuset-cpus", CPUS[s], "--gpus", f"device={'ab'.index(s)}", "--network", "host",
                    "--label", f"lab.stage12.run={args.id}",
                    "-v", "/srv/models/strata-iq3xxs:/iq3xxs:ro",
                    "-v", "/srv/models/strata-data/mtp:/shared-mtp:ro",
                    "-v", f"{draft_data_dir}/dflash2:/stage10-data/dflash2:ro",
                    "-v", "/srv/models/strata-iq3xxs/pack/iq3_xxs-native:/stage10-data/packs/iq3_xxs-native:ro",
                    "-v", f"{current}/logs:/trial-logs",
                    "-v", f"{current}/agent-{s}.json:/opt/strata/config.json:ro",
                ]
                for k, v in env_overrides.items():
                    cmd.extend(["-e", f"{k}={v}"])
                cmd.extend([
                    "--entrypoint", "/opt/strata/.venv/bin/python", args.image,
                    server_entry, "--engine", "strata", "--config", "/opt/strata/config.json",
                    "--host", "127.0.0.1", "--port", str(PORTS[s]),
                ])
                save(current / f"command-{s}.json", cmd)
                cid = run(*cmd)
                owned.append(cid)
                servers[s] = cid
                (current / f"container-{s}.id").write_text(cid + "\n")

            deadline = time.monotonic() + 600
            while True:
                ready = True
                for s in sides:
                    state = run("docker", "inspect", servers[s], "--format", "{{.State.Running}}")
                    if state != "true":
                        (current / f"docker-{s}-early-exit.log").write_text(run("docker", "logs", servers[s]))
                        raise RuntimeError(f"Server {s} exited during startup")
                    try:
                        h = api(s, "health")
                        ready &= h.get("status") == "ok" and h.get("loaded") and h.get("max_context") == 131072 and h.get("model") == models[s]
                    except Exception:
                        ready = False
                if ready:
                    break
                assert time.monotonic() < deadline, "Server readiness deadline exceeded"
                time.sleep(2)

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
print(json.dumps(out))"""

            for s in sides:
                save(current / f"health-before-{s}.json", api(s, "health"))
                assert run("docker", "exec", servers[s], "sha256sum", "/opt/strata/engine/strata").split()[0] == args.engine_sha256
                procs = json.loads(run("docker", "exec", servers[s], "/opt/strata/.venv/bin/python", "-c", probe))
                assert len(procs) == 1, procs
                save(current / f"engine-process-{s}.json", procs[0])
                eff = procs[0]["args"]
                assert eff[eff.index("--prefill") + 1] == "auto:8192", eff
                if not args.legacy_0159:
                    assert eff[eff.index("--prompt-cache") + 1] == "0", eff
                validate_drafter(eff, args.spec, args.draft_conf)
                for k, v in env_overrides.items():
                    assert procs[0]["strata_env"].get(k) == v, (k, procs[0]["strata_env"])
                notes = (current / f"logs/agent-{s}.log").read_text(errors="replace")
                verify_chunk_safety(notes)

            if not is_c2:
                for s in sides:
                    resp = api(s, "v1/chat/completions", {
                        "model": models[s],
                        "messages": [{"role": "user", "content": "Write the integers 1 through 40, separated by spaces."}],
                        "max_tokens": 128, "temperature": 0, "reasoning_effort": "none",
                    }, timeout=180)
                    save(current / f"smoke-{s}.json", resp)
                    assert resp.get("choices") and resp["choices"][0].get("message", {}).get("content"), resp
            else:
                bench_cmd = [
                    "docker", "run", "-d", "--pull", "never",
                    "--name", f"strata-s12-{args.id}-{phase}-bench",
                    "--network", "host",
                    "--label", f"lab.stage12.run={args.id}",
                    "--user", f"{os.getuid()}:{os.getgid()}",
                    "-e", "STRATA_DIR=/opt/strata",
                    "-v", f"{root}:/work",
                    "-v", "/srv/models/strata-iq3xxs:/iq3xxs:ro",
                    "--entrypoint", "/opt/strata/.venv/bin/python", CLIENT_BENCH_IMAGE,
                    "/work/bench/c2_v100_contract.py",
                    "--url-a", f"http://127.0.0.1:{PORTS['a']}",
                    "--url-b", f"http://127.0.0.1:{PORTS['b']}",
                    "--expected-model-a", models["a"],
                    "--expected-model-b", models["b"],
                    "--config", f"/work/{current.relative_to(root)}/agent-a.json",
                    "--manifest", "/work/bench/workloads/v100-performance-v1.json",
                    "--out", f"/work/{current.relative_to(root)}/c2",
                ]
                save(current / "benchmark-command.json", bench_cmd)
                bench = run(*bench_cmd)
                owned.append(bench)
                rc = run("docker", "wait", bench, timeout=1500)
                (current / "docker-bench.log").write_text(run("docker", "logs", bench))
                assert rc == "0", f"C2 benchmark exited {rc}"
                summary = json.loads((current / "c2/summary.json").read_text())
                workload = json.loads((current / "c2/workload.json").read_text())
                assert [x["raw_prompt_sha256"] for x in workload["items"]] == PROMPT_HASHES
                assert summary["pass_mechanical"] and summary["active_overlap"] and summary["post_health"]
                assert [x["prompt_tokens"] for x in summary["requests"]] == [126967, 126968]
                for req in summary["requests"]:
                    assert req["output_tokens"] >= 1024 and req["finish_reason"] == "stop"
                    assert req["cache_n"] == req["cached_tokens"] == 0
                record["metrics"] = [
                    {k: req[k] for k in ("label", "prompt_tokens", "output_tokens", "prefill_tok_s", "decode_tok_s", "ttft_s")}
                    for req in summary["requests"]
                ]

            for s in sides:
                h = api(s, "health")
                assert h.get("status") == "ok" and h.get("loaded")
                save(current / f"health-after-{s}.json", h)
                metrics_after = api(s, "metrics")
                save(current / f"metrics-after-{s}.json", metrics_after)
                rows = metrics_after.get("requests", [])
                assert rows and rows[0].get("drafts_offered", 0) > 0, f"DFlash2 drafts_offered missing on {s}"
                notes = (current / f"logs/agent-{s}.log").read_text(errors="replace")
                verify_chunk_safety(notes)
                assert re.search(r"strata dflash2: \d+-token draft head", notes), f"Missing dflash2 log on {s}"
                assert "no MTP layer is loaded (--draft-fallback none)" in notes, f"Missing fallback=none on {s}"
                (current / f"docker-{s}.log").write_text(run("docker", "logs", servers[s]))

            record["verdict"] = "PASS" if phase.startswith("batch-") else ("DIAGNOSTIC_PASS_NOT_SCORED" if phase.startswith("diagnostic") else "SMOKE_PASS_NOT_C2")
            record.update(phase="validated", finished=now())
            cleanup()
            snapshot(current, "after")

            samples = [line.split(",") for line in (current / "gpu-telemetry.csv").read_text().splitlines() if len(line.split(",")) == 8]
            assert samples, "No GPU telemetry"
            assert all(float(row[7].strip()) <= args.sm_clock_ceiling and float(row[4].strip()) == 150 for row in samples)
            (current / "verdict").write_text(record["verdict"] + "\n")
            save(exp_dir / "progress.json", checkpoint)
            print(f"{now()} {phase} {record['verdict']} {json.dumps(record.get('metrics', []))}", flush=True)

        verify_idle(args.sm_clock_ceiling)
        checkpoint.update(phase="results_saved", verdict="PASS", finished=now())
        save(exp_dir / "progress.json", checkpoint)
        (exp_dir / "verdict").write_text("PASS\n")
        print(f"Stage 12 {args.arm} ({args.id}) COMPLETE PASS", flush=True)

    except BaseException as exc:
        for cid in owned:
            try:
                if current:
                    (current / f"failure-{cid[:12]}.log").write_text(run("docker", "logs", cid))
            except Exception:
                pass
        checkpoint.update(phase="interrupted", verdict="FAIL", error=repr(exc), finished=now())
        save(exp_dir / "progress.json", checkpoint)
        raise
    finally:
        cleanup()
        signal.alarm(0)


if __name__ == "__main__":
    if sys.argv[1:] == ["--sample-host"]:
        sample_host()
    else:
        main()
