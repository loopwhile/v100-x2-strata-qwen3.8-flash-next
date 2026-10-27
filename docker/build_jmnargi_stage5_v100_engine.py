#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import pathlib
import shutil

import setup

print("[jmnargi-stage5-v100] preparing pinned llama.cpp", flush=True)
llama = setup.get_llama_cpp()

nvcc, version = setup.find_nvcc()
print(f"[jmnargi-stage5-v100] nvcc={nvcc} version={version}", flush=True)

if not nvcc or not version or version[0] != 12:
    raise SystemExit(
        f"V100 build requires CUDA 12.x nvcc, found {nvcc} {version}"
    )

arch = os.environ.get("CUDA_ARCHITECTURES", "70").strip().strip('"').replace(",", ";")
if arch != "70":
    raise SystemExit(f"expected CUDA_ARCHITECTURES=70, got {arch!r}")

if os.environ.get("BUILD_VISION", "0") != "0":
    raise SystemExit("Stage 5 T7 image is text-only; BUILD_VISION must be 0")

bdir = setup.ROOT / "build"

print("[jmnargi-stage5-v100] compiling jmnargi/Strata-V100 for sm_70 with STRATA_EXPERIMENTAL_SM60=ON", flush=True)
setup.cmake_build(
    setup.ROOT,
    bdir,
    "strata",
    [
        "-DSTRATA_ENABLE_CUDA=ON",
        "-DSTRATA_BUILD_TESTS=OFF",
        "-DSTRATA_EXPERIMENTAL_SM60=ON",
        f"-DCMAKE_CUDA_ARCHITECTURES={arch}",
        f"-DCMAKE_CUDA_COMPILER={nvcc}",
        f"-DSTRATA_GGML_DIR={llama}",
    ],
    None,
    "build-strata-v100.bat",
)

built = bdir / setup.EXE
print(f"[jmnargi-stage5-v100] expected binary: {built}", flush=True)

if not built.is_file():
    raise SystemExit(
        f"CMake returned success but engine binary does not exist: {built}"
    )

eng = setup.ROOT / "engine"
eng.mkdir(exist_ok=True)

dst = eng / setup.EXE
shutil.copy2(built, dst)
dst.chmod(0o755)

if getattr(setup, "KQ_LIB", None) and (bdir / setup.KQ_LIB).exists():
    shutil.copy2(bdir / setup.KQ_LIB, eng / setup.KQ_LIB)
    print(f"[jmnargi-stage5-v100] copied {setup.KQ_LIB}", flush=True)

bindir = pathlib.Path(nvcc).parent
meta = {
    "source": "local",
    "version": setup.source_version(),
    "archs": [70],
    "vision": "none",
    "cuda_dirs": [
        str(d)
        for d in (
            bindir,
            bindir / "x64",
            bindir.parent / "lib64",
        )
        if d.is_dir()
    ],
    "src": setup.source_hash(setup.ENGINE_SOURCES),
    "vision_src": None,
}

stamp = eng / "BUILD.json"
stamp.write_text(
    json.dumps(meta, indent=1),
    encoding="utf-8",
)
print(f"[jmnargi-stage5-v100] wrote {stamp}: {meta}", flush=True)
