#!/usr/bin/env python3
"""Stage 11 preflight and offline calibration gate on P520 (S11-D4 on IQ3_S).

Validates IQ3_S model assets, DFlash2 pack integrity, image provenance, host idle state,
and offline C2 calibration without starting server or modifying host settings.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess as sp

UPSTREAM_IMAGE = "sha256:dd8913d85f1811af034b66f3817ec392a82abdd28082e98e8a44b1d826bfea3d"
ENGINE_SHA256 = "ccca488231f12da422be4a80b5c7f165b7593f6388907cac92d3c3f0d4229031"
SOURCE_SHA = "712fec6b4297c9cfd32ab43daaa2979a9aa01edf"
PACK_SHA = "4a42b98220ea7880664002c8edda1563aecbae754b762a2e2f31b2b91ee93ecd"
PACK_NAME = "qwen3.8-flash-next-dflash2.q4_0-selq4.pack"
PACK_BYTES = 339694592
BASE_PACK_NAME = "qwen3.8-flash-next-dflash2.q4_0.pack"
BASE_PACK_BYTES = 522458112
BASE_PACK_SHA = "cda40d62d0eb8f37ed6e272142641a1d2f0de4a32f9e14d0416e7a71534849f1"
MANIFEST_SHA = "e413acced27c1991d76ce2b2df195ff73ce2b4f45853b9676e5b9000ef8503ca"
HARNESS_SHA = "a8e42cc5a71421a7287618fd5be0332ae40f312426e4d243ce1c7619fdfc5246"
PORTS = {"a": 18088, "b": 18089}


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run(*args, timeout=60):
    return sp.check_output(args, text=True, stderr=sp.STDOUT, timeout=timeout).strip()


def verify_latest_clock_receipt(journal, ceiling=1245):
    for bus in ("00000000:65:00.0", "00000000:B3:00.0"):
        applied = [line for line in journal.splitlines() if "GPU clocks set to" in line and bus in line]
        assert applied and f"gpuClkMin 135, gpuClkMax {ceiling})" in applied[-1], (bus, applied)


def verify_idle(ceiling=1245):
    assert not run("docker", "ps", "-q"), "Running container found; aborting"
    assert not run("nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"), "GPU workload active"
    limits = run("nvidia-smi", "--query-gpu=power.limit", "--format=csv,noheader,nounits").splitlines()
    assert len(limits) == 2 and all(float(x) == 150 for x in limits), limits
    assert run("systemctl", "is-active", "v100-clock-lock.service") == "active"
    journal = run("journalctl", "-b", "-u", "v100-clock-lock.service", "--no-pager")
    verify_latest_clock_receipt(journal, ceiling)
    listening = run("ss", "-H", "-ltn")
    for line in listening.splitlines():
        address = line.split()[3]
        port = address.rsplit(":", 1)[-1]
        assert port not in {str(p) for p in PORTS.values()}, f"Listener on test port {port}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("/home/loopwhile/v100-x2-strata-qwen3.8-flash-next/results/stage11-preparation")
    )
    parser.add_argument("--verify-gguf-sha", action="store_true", help="Re-hash large IQ3_S GGUF shards")
    args = parser.parse_args()

    assert socket.gethostname() == "p520-llm", "Must run on p520-llm"
    root = Path(__file__).resolve().parents[1]
    prep_dir = args.out_dir
    prep_dir.mkdir(parents=True, exist_ok=True)

    print("1. Checking idle state and clock/power lock...", flush=True)
    verify_idle(1245)

    print("2. Verifying frozen harness and manifest...", flush=True)
    harness_path = root / "bench/c2_v100_contract.py"
    manifest_path = root / "bench/workloads/v100-performance-v1.json"
    assert sha(harness_path) == HARNESS_SHA, "Harness SHA mismatch"
    assert sha(manifest_path) == MANIFEST_SHA, "Manifest SHA mismatch"

    print("3. Verifying IQ3_S model & tokenizer assets...", flush=True)
    assets_file = root / "artifacts/stage11-preparation/iq3s-assets.sha256"
    assert assets_file.is_file(), f"iq3s-assets.sha256 missing: {assets_file}"
    assets_lines = [line for line in assets_file.read_text().splitlines() if line.strip()]
    assert len(assets_lines) == 12, f"Expected 12 assets, got {len(assets_lines)}"
    asset_records = []
    for line in assets_lines:
        expected_sha, filepath = line.split(maxsplit=1)
        p = Path(filepath.strip())
        assert p.is_file(), f"Asset missing: {p}"
        st = p.stat()
        if args.verify_gguf_sha or not p.name.endswith(".gguf"):
            actual = sha(p)
            assert actual == expected_sha, f"SHA mismatch for {p}: {actual} != {expected_sha}"
        asset_records.append({
            "path": str(p),
            "sha256": expected_sha,
            "size": st.st_size,
            "mtime_ns": st.st_mtime_ns
        })
    print(f"   All {len(asset_records)} IQ3_S assets exist and verified.", flush=True)

    print("4. Verifying DFlash2 stock selector pack...", flush=True)
    source_draft_dir = root / "results/stage10-preparation/draft-data/dflash2"
    target_draft_dir = prep_dir / "draft-data/dflash2"
    target_draft_dir.mkdir(parents=True, exist_ok=True)

    for item in ("draft_vocab.bin", BASE_PACK_NAME, PACK_NAME, PACK_NAME + ".ok"):
        src = source_draft_dir / item
        dst = target_draft_dir / item
        if not dst.exists() and src.exists():
            try:
                os.link(src, dst)
            except OSError:
                shutil.copy2(src, dst)

    base_pack_file = target_draft_dir / BASE_PACK_NAME
    assert base_pack_file.is_file(), f"Base DFlash2 pack missing (required by drafting.pack_ready): {base_pack_file}"
    assert base_pack_file.stat().st_size == BASE_PACK_BYTES, f"Base pack size {base_pack_file.stat().st_size} != {BASE_PACK_BYTES}"
    actual_base_sha = sha(base_pack_file)
    assert actual_base_sha == BASE_PACK_SHA, f"Base pack SHA mismatch: {actual_base_sha}"

    pack_file = target_draft_dir / PACK_NAME
    assert pack_file.is_file(), f"DFlash2 pack missing: {pack_file}"
    assert pack_file.stat().st_size == PACK_BYTES, f"Pack size {pack_file.stat().st_size} != {PACK_BYTES}"
    actual_pack_sha = sha(pack_file)
    assert actual_pack_sha == PACK_SHA, f"Pack SHA mismatch: {actual_pack_sha}"
    print(f"   DFlash2 packs verified: selq4={actual_pack_sha}, base={actual_base_sha}", flush=True)

    print("5. Verifying Docker image and engine binary...", flush=True)
    img_inspect = json.loads(run("docker", "image", "inspect", UPSTREAM_IMAGE))[0]
    assert img_inspect["Id"] == UPSTREAM_IMAGE
    assert img_inspect["Config"]["Labels"]["org.opencontainers.image.revision"] == SOURCE_SHA
    actual_engine_sha = run("docker", "run", "--rm", "--entrypoint", "sha256sum", UPSTREAM_IMAGE, "/opt/strata/engine/strata").split()[0]
    assert actual_engine_sha == ENGINE_SHA256, f"Engine binary SHA mismatch: {actual_engine_sha}"
    print(f"   Engine binary SHA verified: {actual_engine_sha}", flush=True)

    print("6. Verifying offline C2 calibration inside container (IQ3_S tokenizer)...", flush=True)
    calib_cmd = [
        "docker", "run", "--rm", "--network", "none",
        "-v", f"{root}:/work:ro",
        "-v", "/srv/models/strata-iq3s:/iq3s:ro",
        "-v", "/srv/models/strata-data/mtp:/shared-mtp:ro",
        "--entrypoint", "/opt/strata/.venv/bin/python",
        UPSTREAM_IMAGE, "-c",
        """
import importlib.util, json, pathlib
spec = importlib.util.spec_from_file_location('c2_frozen', '/work/bench/c2_v100_contract.py')
c2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c2)
base = json.loads(pathlib.Path('/work/artifacts/stage6-configs-20261028/iq3s/strata-s6-iq3s-agent-a.json').read_text())
cfg_path = pathlib.Path('/tmp/test-config.json')
cfg_path.write_text(json.dumps(base))
tok, template, frontend = c2.load_tokenizer_and_template(cfg_path)
manifest = json.loads(pathlib.Path('/work/bench/workloads/v100-performance-v1.json').read_text())
res = []
for task in manifest['requests']:
    row = c2.materialize_one(manifest, task, tok, template, frontend)
    res.append({'id': row['id'], 'prompt_tokens': row['prompt_tokens'], 'raw_prompt_sha256': row['raw_prompt_sha256']})
print(json.dumps(res))
"""
    ]
    calib_output = json.loads(run(*calib_cmd))
    expected_calib = [
        {"id": "project-a", "prompt_tokens": 126967, "raw_prompt_sha256": "882a3617750ab8dbcb61d3e8e1d42641555a6b1450d060d7bb22a4f1161670b6"},
        {"id": "project-b", "prompt_tokens": 126968, "raw_prompt_sha256": "5a19042f67dd7702e843595467e1d6c2b96414f565b0fbfa8036590709dba557"}
    ]
    assert calib_output == expected_calib, f"Calibration mismatch: {calib_output}"
    print("   Offline C2 calibration OK: 126967 and 126968 tokens.", flush=True)

    summary = {
        "timestamp": dt.datetime.now().astimezone().isoformat(),
        "host": socket.gethostname(),
        "verdict": "PREPARATION_PASS_NOT_C2",
        "quantization": "IQ3_S",
        "image_id": UPSTREAM_IMAGE,
        "engine_sha256": ENGINE_SHA256,
        "source_sha": SOURCE_SHA,
        "pack_name": PACK_NAME,
        "pack_bytes": PACK_BYTES,
        "pack_sha256": PACK_SHA,
        "harness_sha256": HARNESS_SHA,
        "manifest_sha256": MANIFEST_SHA,
        "assets_count": len(asset_records),
        "calibration": calib_output,
        "clock_ceiling_mhz": 1245,
        "power_limit_w": 150
    }
    (prep_dir / "preparation.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"Preparation complete. Summary saved to {prep_dir / 'preparation.json'}", flush=True)


if __name__ == "__main__":
    main()
