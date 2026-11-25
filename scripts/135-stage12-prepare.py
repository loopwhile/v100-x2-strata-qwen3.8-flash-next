#!/usr/bin/env python3
"""Stage 12 preflight on P520: verifies idle GPUs, 150 W caps, 135-1245 MHz lock, IQ3_XXS + DFlash2 + C2 assets."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess as sp

PACK_SHA = "4a42b98220ea7880664002c8edda1563aecbae754b762a2e2f31b2b91ee93ecd"
PACK_NAME = "qwen3.8-flash-next-dflash2.q4_0-selq4.pack"
BASE_PACK_NAME = "qwen3.8-flash-next-dflash2.q4_0.pack"
BASE_PACK_SHA = "cda40d62d0eb8f37ed6e272142641a1d2f0de4a32f9e14d0416e7a71534849f1"
MANIFEST_SHA = "e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca"
HARNESS_SHA = "a8e42cc5a71421a7287618fd5be0332ae40f312426e4d243ce1c7619fdfc5246"
PORTS = (18086, 18087)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run(*args, timeout=60) -> str:
    return sp.check_output(args, text=True, stderr=sp.STDOUT, timeout=timeout).strip()


def verify_idle(ceiling: int = 1245):
    assert not run("docker", "ps", "-q"), "Running container found; aborting"
    assert not run("nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"), "GPU workload active"
    limits = run("nvidia-smi", "--query-gpu=power.limit", "--format=csv,noheader,nounits").splitlines()
    assert len(limits) == 2 and all(float(x) == 150 for x in limits), limits
    assert run("systemctl", "is-active", "v100-clock-lock.service") == "active"
    journal = run("journalctl", "-b", "-u", "v100-clock-lock.service", "--no-pager")
    for bus in ("00000000:65:00.0", "00000000:B3:00.0"):
        applied = [line for line in journal.splitlines() if "GPU clocks set to" in line and bus in line]
        assert applied and f"gpuClkMin 135, gpuClkMax {ceiling})" in applied[-1], (bus, applied)
    listening = run("ss", "-H", "-ltn")
    for line in listening.splitlines():
        port = line.split()[3].rsplit(":", 1)[-1]
        assert port not in {str(p) for p in PORTS}, f"Listener on test port {port}"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--verify-gguf-sha", action="store_true")
    args = p.parse_args()

    assert socket.gethostname() == "p520-llm", "Must run on p520-llm"
    root = Path(__file__).resolve().parents[1]
    prep_dir = root / "results/stage12-preparation"
    prep_dir.mkdir(parents=True, exist_ok=True)

    verify_idle(1245)
    assert sha(root / "bench/c2_v100_contract.py") == HARNESS_SHA
    assert sha(root / "bench/workloads/v100-performance-v1.json") == MANIFEST_SHA

    assets_file = root / "artifacts/stage8-results-20261107/assets.sha256"
    records = []
    for line in assets_file.read_text().splitlines():
        if not line.strip():
            continue
        expected_sha, fp = line.split(maxsplit=1)
        path = Path(fp.strip())
        assert path.is_file(), f"Missing asset: {path}"
        if args.verify_gguf_sha or not path.name.endswith(".gguf"):
            assert sha(path) == expected_sha, f"SHA mismatch: {path}"
        st = path.stat()
        records.append({"path": str(path), "sha256": expected_sha, "size": st.st_size, "mtime_ns": st.st_mtime_ns})

    dflash_dir = root / "results/stage10-preparation/draft-data/dflash2"
    assert sha(dflash_dir / PACK_NAME) == PACK_SHA
    assert sha(dflash_dir / BASE_PACK_NAME) == BASE_PACK_SHA

    p520_a = json.loads(run("docker", "inspect", "p520-llm-a", "--format", "{{.State.Status}}")) if False else run("docker", "inspect", "p520-llm-a", "--format", "{{.State.Status}}")
    p520_b = run("docker", "inspect", "p520-llm-b", "--format", "{{.State.Status}}")
    assert p520_a == "exited" and p520_b == "exited", (p520_a, p520_b)

    summary = {
        "timestamp": dt.datetime.now().astimezone().isoformat(),
        "host": socket.gethostname(),
        "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
        "verdict": "PREPARATION_PASS_NOT_C2",
        "quantization": "IQ3_XXS",
        "assets_count": len(records),
        "dflash2_pack_sha256": PACK_SHA,
        "harness_sha256": HARNESS_SHA,
        "manifest_sha256": MANIFEST_SHA,
        "clock_ceiling_mhz": 1245,
        "power_limit_w": 150,
        "serving_containers_state": {"p520-llm-a": p520_a, "p520-llm-b": p520_b},
        "disk_free_bytes": os.statvfs("/").f_bavail * os.statvfs("/").f_frsize,
    }
    (prep_dir / "preparation.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
