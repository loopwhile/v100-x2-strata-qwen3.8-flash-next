#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import shutil

import setup

print("[v100-build] preparing pinned llama.cpp", flush=True)
llama = setup.get_llama_cpp()

nvcc, version = setup.find_nvcc()
print(f"[v100-build] nvcc={nvcc} version={version}", flush=True)
if not nvcc or not version or version[0] != 12:
    raise SystemExit(f"V100 image requires CUDA 12.x nvcc, found {nvcc} {version}")

bdir = setup.ROOT / "build"
print("[v100-build] compiling Strata for sm_70", flush=True)
setup.cmake_build(
    setup.ROOT,
    bdir,
    "strata",
    [
        "-DSTRATA_ENABLE_CUDA=ON",
        "-DSTRATA_EXPERIMENTAL_SM60=ON",
        "-DSTRATA_BUILD_TESTS=OFF",
        "-DCMAKE_CUDA_ARCHITECTURES=70",
        f"-DCMAKE_CUDA_COMPILER={nvcc}",
        f"-DSTRATA_GGML_DIR={llama}",
    ],
    None,
    "build-strata-v100.bat",
)

built = bdir / setup.EXE
print(f"[v100-build] expected binary: {built}", flush=True)
if not built.is_file():
    raise SystemExit(f"CMake returned success but {built} does not exist")

eng = setup.ROOT / "engine"
eng.mkdir(exist_ok=True)
dst = eng / setup.EXE
shutil.copy2(built, dst)
dst.chmod(0o755)

bindir = pathlib.Path(nvcc).parent
meta = {
    "source": "local",
    "version": setup.source_version(),
    "archs": [70],
    "vision": "none",
    "cuda_dirs": [
        str(d)
        for d in (bindir, bindir / "x64", bindir.parent / "lib64")
        if d.is_dir()
    ],
    "src": setup.source_hash(setup.ENGINE_SOURCES),
    "vision_src": None,
}
stamp = eng / "BUILD.json"
stamp.write_text(json.dumps(meta, indent=1), encoding="utf-8")

print("[v100-build] packaged engine:", flush=True)
print(dst, dst.stat().st_size, flush=True)
print(stamp.read_text(encoding="utf-8"), flush=True)
