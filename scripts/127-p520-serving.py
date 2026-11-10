#!/usr/bin/env python3
"""Manage the stable P520 serving pair without touching historical containers."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import socket
import subprocess as sp
import time
import urllib.request

IMAGE = "sha256:dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d"
ENGINE_SHA = "ccca488231f12da422be4a80b5c7f165b7593f6388907cac92d3c3f0d4229031"
PACK_NAME = "qwen3.8-flash-next-dflash2.q4_0-selq4.pack"
PACK_SHA = "4a42b98220ea7880664002c8edda1563aecbae754b762a2e2f31b2b91ee93ecd"
ENV = {"STRATA_SELECT_SIMT": "1", "STRATA_SM70_TABLE": "1", "STRATA_PF_WMMA": "1"}
CPUS = {"a": "0-2,6-8", "b": "3-5,9-11"}
PORTS = {"a": 8080, "b": 8081}
LABEL = "p520.serving.recipe"
ROOT = Path.home() / "v100-x2-strata-qwen3.8-flash-next"
SERVING_ROOT = ROOT / "results/p520-serving"
ARCHIVE = ROOT / "results/stage10/S10-D4/d4-20261110T225518/batch-3"


def run(*args, timeout=60):
    return sp.check_output(args, text=True, stderr=sp.STDOUT, timeout=timeout).strip()


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def name(side):
    return f"p520-llm-{side}"


def canonical(side):
    # The unmodified server chooses DFlash2 from this Qwen model-name pattern.
    # API aliases provide independent, permanent names for clients.
    return f"qwen3.8-flash-next-iq3_xxs_p520_{side}"


def identity(side):
    item = json.loads(run("docker", "inspect", name(side)))[0]
    assert item["Config"].get("Labels", {}).get(LABEL) == "S10-D4", "Refuse foreign container"
    assert item["Image"] == IMAGE, "Unexpected image; inspect before managing"
    assert item["HostConfig"]["CpusetCpus"] == CPUS[side]
    assert item["HostConfig"]["NetworkMode"] == "host"
    devices = item["HostConfig"]["DeviceRequests"]
    assert len(devices) == 1 and devices[0]["DeviceIDs"] == [str("ab".index(side))]
    return item


def preflight(allow_owned=False):
    running = set(run("docker", "ps", "--format", "{{.Names}}").splitlines())
    allowed = {name(s) for s in "ab"} if allow_owned else set()
    assert not running - allowed, f"Other containers are running: {running - allowed}"
    allowed_pids = set()
    for s in "ab":
        if name(s) in running:
            identity(s)
            allowed_pids.update(run("docker", "top", name(s), "-eo", "pid").splitlines()[1:])
    gpu_pids = set(run("nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader").splitlines())
    assert not {x.strip() for x in gpu_pids} - {x.strip() for x in allowed_pids}, "Foreign GPU workload"
    limits = run("nvidia-smi", "--query-gpu=power.limit", "--format=csv,noheader,nounits").splitlines()
    assert len(limits) == 2 and all(float(x) == 150 for x in limits), limits
    assert run("systemctl", "is-active", "v100-clock-lock.service") == "active"
    journal = run("journalctl", "-b", "-u", "v100-clock-lock.service", "--no-pager")
    for bus in ("00000000:65:00.0", "00000000:B3:00.0"):
        entries = [x for x in journal.splitlines() if bus in x and "GPU clocks set to" in x]
        assert entries and "gpuClkMin 135, gpuClkMax 1245)" in entries[-1], "Clock policy differs; no change made"
    for s in "ab":
        if name(s) not in running:
            with socket.socket() as probe:
                probe.bind(("127.0.0.1", PORTS[s]))
    return {"running": sorted(running), "gpu_pids": sorted(gpu_pids), "clock_journal": journal}


def prepare():
    before = preflight()
    assert run("docker", "image", "inspect", IMAGE, "--format", "{{.Id}}") == IMAGE
    draft_dir = ROOT / "results/stage10-preparation/draft-data/dflash2"
    assert sha(draft_dir / PACK_NAME) == PACK_SHA
    release = SERVING_ROOT / "releases" / ("s10-d4-" + dt.datetime.now().strftime("%Y%m%dT%H%M%S"))
    release.mkdir(parents=True, exist_ok=False)
    (release / "logs").mkdir()
    save(release / "preflight.json", before)
    commands = {}
    for s in "ab":
        cfg = json.loads((ARCHIVE / f"agent-{s}.json").read_text())
        expected = {"--spec": "8", "--draft-conf": "0.7", "--prefill": "auto",
                    "--max-context": "131072", "--kv": "int8", "--kv-resident": "32768",
                    "--expert-cache": "auto", "--pack": "/stage10-data/packs/iq3_xxs-native"}
        for flag, value in expected.items():
            assert cfg["args"].count(flag) == 1 and cfg["args"][cfg["args"].index(flag) + 1] == value
        assert cfg["drafting"] == "dflash2" and "--mmap-experts" in cfg["args"]
        assert cfg["gpu"] == 0 and cfg["gpus_asked"]
        cfg["model_name"] = canonical(s)
        cfg["aliases"] = [name(s)]
        cfg["port"] = PORTS[s]
        save(release / f"agent-{s}.json", cfg)
        cmd = ["docker", "create", "--pull", "never", "--name", name(s),
               "--restart", "unless-stopped", "--cpuset-cpus", CPUS[s],
               "--gpus", f"device={'ab'.index(s)}", "--network", "host",
               "--label", f"{LABEL}=S10-D4", "--label", f"p520.serving.release={release.name}"]
        for source, target, mode in [
            ("/srv/models/strata-iq3xxs", "/iq3xxs", "ro"),
            ("/srv/models/strata-data/mtp", "/shared-mtp", "ro"),
            (draft_dir, "/stage10-data/dflash2", "ro"),
            ("/srv/models/strata-iq3xxs/pack/iq3_xxs-native", "/stage10-data/packs/iq3_xxs-native", "ro"),
            (release / "logs", "/trial-logs", "rw"),
            (release / f"agent-{s}.json", "/opt/strata/config.json", "ro")
        ]:
            assert Path(source).exists(), source
            cmd.extend(["--mount", f"type=bind,src={source},dst={target}" + (",readonly" if mode == "ro" else "")])
        for key, value in ENV.items():
            cmd.extend(["-e", f"{key}={value}"])
        cmd.extend(["--entrypoint", "/opt/strata/.venv/bin/python", IMAGE,
                    "/opt/strata/serve/server.py", "--engine", "strata", "--config", "/opt/strata/config.json",
                    "--host", "127.0.0.1", "--port", str(PORTS[s])])
        commands[s] = cmd
    save(release / "commands.json", commands)
    save(release / "release.json", {"recipe": "S10-D4", "image": IMAGE,
         "engine_sha256": ENGINE_SHA, "draft_sha256": PACK_SHA,
         "configs": {s: sha(release / f"agent-{s}.json") for s in "ab"}})
    (release / "rollback.txt").write_text(
        "Initial state: all serving stopped. Rollback to initial state:\n"
        "docker stop -t 30 p520-llm-a p520-llm-b\n"
        "Preserve new containers and this release. Historical containers remain untouched.\n")
    print(release)


def install(release):
    release = release.resolve()
    assert release.parent == SERVING_ROOT / "releases", "Release must be in the serving releases directory"
    preflight()
    existing = set(run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines())
    assert not existing & {name(s) for s in "ab"}, "Stable names already exist; archive before a reviewed upgrade"
    manifest = json.loads((release / "release.json").read_text())
    commands = json.loads((release / "commands.json").read_text())
    assert manifest["image"] == IMAGE
    for s in "ab":
        assert sha(release / f"agent-{s}.json") == manifest["configs"][s]
        assert commands[s][:6] == ["docker", "create", "--pull", "never", "--name", name(s)]
    for s in "ab":
        print(run(*commands[s]), flush=True)
        identity(s)
    print("Created both containers, stopped. Start with: docker start p520-llm-a p520-llm-b")


def api(side, route):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORTS[side]}/{route}", timeout=5) as response:
        return json.load(response)


def check():
    output = {}
    for s in "ab":
        item = identity(s)
        assert item["State"]["Running"], f"{name(s)} is stopped"
        health, models = api(s, "health"), api(s, "v1/models")
        assert health.get("status") == "ok" and health.get("loaded")
        assert health.get("model") == canonical(s) and health.get("max_context") == 131072
        assert name(s) in [x["id"] for x in models["data"]]
        assert run("docker", "exec", name(s), "sha256sum", "/opt/strata/engine/strata").split()[0] == ENGINE_SHA
        probe = """import json,pathlib
out=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdigit(): continue
 try:
  args=(p/'cmdline').read_bytes().decode().strip('\\0').split('\\0')
  if args[0]!='/opt/strata/engine/strata': continue
  env=dict(x.split('=',1) for x in (p/'environ').read_bytes().decode().split('\\0') if x.startswith('STRATA_'))
  out.append({'args':args,'env':env})
 except (FileNotFoundError,PermissionError,ProcessLookupError): pass
print(json.dumps(out))
"""
        processes = json.loads(run("docker", "exec", name(s), "/opt/strata/.venv/bin/python", "-c", probe))
        assert len(processes) == 1
        effective = processes[0]["args"]
        for flag, value in {"--spec": "8", "--draft-conf": "0.7", "--prefill": "auto",
                            "--draft": "dflash2", "--draft-fallback": "none",
                            "--draft-model": "/stage10-data/dflash2/" + PACK_NAME,
                            "--max-context": "131072", "--kv": "int8", "--kv-resident": "32768",
                            "--expert-cache": "auto"}.items():
            assert effective.count(flag) == 1 and effective[effective.index(flag) + 1] == value, (flag, effective)
        assert "--mtp" not in effective and "--spec-min-p" not in effective
        assert "--mmap-experts" in effective
        for key, value in ENV.items():
            assert processes[0]["env"].get(key) == value
        for key in ("STRATA_ADAPT_LAG", "STRATA_ADAPT_NOWAIT", "STRATA_PF_HC_REGION"):
            assert key not in processes[0]["env"], f"Unapproved D4 override: {key}"
        output[s] = {"health": health, "models": models, "engine": processes[0]}
    print(json.dumps(output, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "install", "start", "stop", "status", "check"])
    parser.add_argument("--release", type=Path)
    args = parser.parse_args()
    assert socket.gethostname() == "p520-llm", "Run through ssh p520"
    if args.action == "prepare":
        prepare()
    elif args.action == "install":
        assert args.release, "Pass --release from prepare output"
        install(args.release)
    elif args.action == "status":
        print(run("docker", "ps", "-a", "--filter", "name=^/p520-llm-[ab]$",
                  "--format", "table {{.Names}}\t{{.Image}}\t{{.Status}}"))
    elif args.action == "check":
        check()
    else:
        for s in "ab":
            identity(s)
        if args.action == "stop":
            print(run("docker", "stop", "-t", "30", *[name(s) for s in "ab"], timeout=90))
        else:
            preflight(allow_owned=True)
            print(run("docker", "start", *[name(s) for s in "ab"]))
            deadline = time.monotonic() + 600
            while True:
                try:
                    ready = all(api(s, "health").get("loaded") for s in "ab")
                except (OSError, ValueError):
                    ready = False
                assert all(identity(s)["State"]["Running"] for s in "ab"), "Server exited; inspect docker logs"
                if ready:
                    break
                if time.monotonic() >= deadline:
                    raise TimeoutError("Readiness timeout; inspect logs. Containers retained.")
                print("Waiting for both models to load...", flush=True)
                time.sleep(10)
            try:
                check()
            except (AssertionError, sp.CalledProcessError):
                # A loaded engine with wrong flags must never remain serving.
                run("docker", "stop", "-t", "30", *[name(s) for s in "ab"], timeout=90)
                raise


if __name__ == "__main__":
    main()
