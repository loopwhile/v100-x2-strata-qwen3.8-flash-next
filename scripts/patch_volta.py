#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(path: Path, old: str, new: str, label: str, *, optional: bool = False) -> bool:
    text = path.read_text(encoding="utf-8-sig")
    if new in text:
        print(f"[ok] {label}: already applied")
        return False
    if old not in text:
        if optional:
            print(f"[skip] {label}: source already differs; no patch applied")
            return False
        raise SystemExit(f"[error] {label}: expected source text not found in {path}")
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    print(f"[patched] {label}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("strata", type=Path)
    args = ap.parse_args()
    root = args.strata.resolve()

    setup = root / "setup.py"
    device = root / "src/core/device.cu"
    cmake = root / "CMakeLists.txt"
    for p in (setup, device, cmake):
        if not p.exists():
            raise SystemExit(f"missing Strata source file: {p}")

    # setup.py currently filters cards below sm_75 before the local build path can run.
    replace_once(
        setup,
        '    if int(g["arch"]) < 75:\n',
        '    if int(g["arch"]) < 70:\n',
        "setup: admit Volta sm_70",
        optional=True,
    )

    # A V100 engine built from 0.1.30 still has a runtime guard below sm_75.
    # Upstream 0.1.31 may already make the experimental build flag honor Volta;
    # lowering only this guard to 70 is harmless for our dedicated V100 tree.
    replace_once(
        device,
        "    if (d.cc_major * 10 + d.cc_minor < 75) {\n",
        "    if (d.cc_major * 10 + d.cc_minor < 70) {\n",
        "runtime: admit Volta sm_70",
        optional=True,
    )

    # Current CMake already accepts pre-sm75 when STRATA_EXPERIMENTAL_SM60=ON.
    # Older snapshots may have an unconditional floor.
    replace_once(
        cmake,
        "    if(_base LESS 75)\n",
        "    if(_base LESS 70)\n",
        "cmake: lower unconditional architecture floor",
        optional=True,
    )

    # Force the existing experimental compatibility path into local CUDA builds.
    replace_once(
        setup,
        '["-DSTRATA_ENABLE_CUDA=ON", "-DSTRATA_BUILD_TESTS=OFF", f"-DCMAKE_CUDA_ARCHITECTURES={cuda_archs}",\n',
        '["-DSTRATA_ENABLE_CUDA=ON", "-DSTRATA_EXPERIMENTAL_SM60=ON", "-DSTRATA_BUILD_TESTS=OFF", f"-DCMAKE_CUDA_ARCHITECTURES={cuda_archs}",\n',
        "build: enable experimental pre-sm75 compatibility path",
        optional=True,
    )

    # CUDA 13 dropped Volta. setup.py normally picks the newest nvcc it finds.
    # In a machine containing a V100, ignore CUDA 13+ candidates and pick the
    # newest CUDA 12.x toolkit instead.
    old = '''            v = re.search(r"release (\\d+)\\.(\\d+)", out([c, "--version"]))
            if v and (best[1] is None or (int(v.group(1)), int(v.group(2))) > best[1]):
                best = (c, (int(v.group(1)), int(v.group(2))))
'''
    new = '''            v = re.search(r"release (\\d+)\\.(\\d+)", out([c, "--version"]))
            if v:
                vv = (int(v.group(1)), int(v.group(2)))
                if any(int(g["arch"]) == 70 for g in gpus()) and vv[0] >= 13:
                    continue
                if best[1] is None or vv > best[1]:
                    best = (c, vv)
'''
    replace_once(setup, old, new, "setup: prefer CUDA 12.x for Volta", optional=True)

    marker = root / ".volta-sm70-harness"
    marker.write_text(
        "Patched by loopwhile/v100-x2-strata-qwen3.8-flash-next\n",
        encoding="utf-8",
    )
    print(f"[ok] marker: {marker}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
