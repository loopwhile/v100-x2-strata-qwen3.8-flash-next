#!/usr/bin/env python3
"""Build pinned Stage 12 Strata engine (0.1.66/0.1.67) + Gate A parity targets, CUDA12/sm70."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess as sp

ROOT = Path("/opt/strata")
ENGINE_SRC = ROOT / "engine"
BUILD_DIR = ROOT / "build-stage12"

DESIRED_TARGETS = [
    "strata",
    # CPU / Quant parity & determinism
    "native_arithmetic_parity",
    "native_arithmetic_parity_avx",
    "native_arithmetic_parity_mt1",
    "native_arithmetic_parity_no512",
    "native_arithmetic_parity_ggml",
    "pool_determinism",
    "pool_determinism_dep_off",
    "iq_avx2_parity",
    "iq_avx1_parity",
    "q8k_quant_parity",
    "q2_bitplane_parity",
    "quant_selftest",
    "quant_parity",
    "type_geometry_oracle",
    # GPU / Prefill / Qwen / Safety parity
    "native_expert_parity",
    "native_multi_parity",
    "native_grouped_parity",
    "native_i8_parity",
    "pf_wmma_parity",
    "gr_write_norm_parity",
    "qsa_prompt_attn_parity",
    "qsa_merge_daily_parity",
    "dflash2_parity",
    "dflash2_q4_parity",
    "file_expert_source_test",
    "nv_defaults_test",
    "tail_skip_default_test",
    "lookup_default_test",
    "adapt_async_default_test",
    "cgroup_mem_test",
    "cgroup_cpu_test",
]


def parse_engine_version(cmake_path: Path) -> str:
    text = cmake_path.read_text(encoding="utf-8")
    m = re.search(r"project\s*\(\s*strata\s+VERSION\s+([0-9]+\.[0-9]+\.[0-9]+)", text)
    assert m, f"Could not parse version from {cmake_path}"
    return m.group(1)


def find_nvcc():
    nvcc = shutil.which("nvcc") or "/usr/local/cuda/bin/nvcc"
    assert Path(nvcc).is_file(), f"nvcc missing: {nvcc}"
    out = sp.check_output([nvcc, "--version"], text=True)
    m = re.search(r"release\s+(\d+)\.(\d+)", out)
    assert m, out
    major, minor = int(m.group(1)), int(m.group(2))
    assert major == 12, f"CUDA 12.x required for sm_70, got {major}.{minor}"
    return nvcc, (major, minor)


def main():
    revision = sp.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert revision == os.environ["STRATA_EXPECTED_REF"], (revision, os.environ["STRATA_EXPECTED_REF"])
    version = parse_engine_version(ENGINE_SRC / "CMakeLists.txt")
    assert version == os.environ["STRATA_EXPECTED_VERSION"], (version, os.environ["STRATA_EXPECTED_VERSION"])
    nvcc, toolkit = find_nvcc()

    cmake_bin = str(ROOT / ".venv/bin/cmake")
    ninja_bin = str(ROOT / ".venv/bin/ninja")
    python_bin = str(ROOT / ".venv/bin/python")
    assert Path(cmake_bin).is_file() and Path(ninja_bin).is_file()

    defs = [
        "-DSTRATA_ENABLE_CUDA=ON",
        "-DSTRATA_EXPERIMENTAL_SM60=ON",
        "-DCMAKE_CUDA_ARCHITECTURES=70",
        "-DSTRATA_BUILD_TESTS=ON",
        f"-DCMAKE_CUDA_COMPILER={nvcc}",
        f"-DPython3_EXECUTABLE={python_bin}",
    ]
    configure_cmd = [
        cmake_bin, "-S", str(ENGINE_SRC), "-B", str(BUILD_DIR), "-G", "Ninja",
        f"-DCMAKE_MAKE_PROGRAM={ninja_bin}", "-DCMAKE_BUILD_TYPE=Release", *defs
    ]
    print(json.dumps(configure_cmd), flush=True)
    sp.run(configure_cmd, cwd=ROOT, check=True)

    available_raw = sp.check_output([ninja_bin, "-C", str(BUILD_DIR), "-t", "targets", "all"], text=True)
    available = {line.split(":", 1)[0].strip() for line in available_raw.splitlines() if ":" in line}
    selected = [t for t in DESIRED_TARGETS if t in available]
    missing = [t for t in DESIRED_TARGETS if t not in available]
    assert "strata" in selected, "strata target missing"
    print(json.dumps({"selected_targets": selected, "missing_targets": missing}), flush=True)

    build_cmd = [cmake_bin, "--build", str(BUILD_DIR), "--target", *selected, "-j", "6"]
    print(json.dumps(build_cmd), flush=True)
    sp.run(build_cmd, cwd=ROOT, check=True)

    engine_dir = ROOT / "engine-bin"
    # Keep upstream engine/ source tree intact and expose runtime binary at /opt/strata/engine/strata
    # or check if /opt/strata/engine/strata collides with engine/ dir: no, engine/ has no file named 'strata'.
    runtime_dir = ROOT / "engine"
    for name in ("strata", "libstrata_kq.so"):
        src = BUILD_DIR / name
        if name == "strata":
            assert src.is_file(), f"Built binary missing: {src}"
        if src.is_file():
            shutil.copy2(src, runtime_dir / name)
    binary = runtime_dir / "strata"
    binary.chmod(0o755)
    assert not (runtime_dir / "libstrata_kq.so").exists(), "MMQ library must not exist"

    patch_name = os.environ.get("STRATA_STAGE12_PATCH", "")
    patch_sha = None
    if patch_name:
        p = Path("/opt/strata-patches") / patch_name
        patch_sha = hashlib.sha256(p.read_bytes()).hexdigest()

    metadata = {
        "source": "local",
        "version": version,
        "archs": [70],
        "toolkit": list(toolkit),
        "cuda_compiler": nvcc,
        "git_revision": revision,
        "patch": patch_name or None,
        "patch_sha256": patch_sha,
        "selected_targets": selected,
        "missing_targets": missing,
        "build_commands": [configure_cmd, build_cmd],
        "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
    }
    (runtime_dir / "BUILD.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2), flush=True)


if __name__ == "__main__":
    main()
