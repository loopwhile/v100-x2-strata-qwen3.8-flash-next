#!/usr/bin/env python3
"""Build pinned Stage 9 Qwen sources only, CUDA12/sm70, no runtime acquisition."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess as sp

import setup


root = Path('/opt/strata')
revision = sp.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
assert revision == os.environ['STRATA_EXPECTED_REF']
version = setup.source_version()
assert version == os.environ['STRATA_EXPECTED_VERSION'], version
nvcc, toolkit = setup.find_nvcc()
assert nvcc and toolkit and toolkit[0] == 12, (nvcc, toolkit)
defs = ['-DSTRATA_ENABLE_CUDA=ON', '-DSTRATA_BUILD_TESTS=OFF',
        '-DSTRATA_EXPERIMENTAL_SM60=ON', '-DCMAKE_CUDA_ARCHITECTURES=70',
        f'-DCMAKE_CUDA_COMPILER={nvcc}']
vendored = root / 'third_party/strata-ggml/ggml/CMakeLists.txt'
if not vendored.is_file():
    # The pinned fork still uses the old GGML tree. Never invoke this for 0.1.59.
    assert version == '0.1.45.7'
    defs.append(f'-DSTRATA_GGML_DIR={setup.get_llama_cpp()}')
bdir = root / 'build-stage9'
commands = [['.venv/bin/cmake', '-S', '.', '-B', str(bdir), '-G', 'Ninja',
             f'-DCMAKE_MAKE_PROGRAM={root / ".venv/bin/ninja"}',
             '-DCMAKE_BUILD_TYPE=Release', *defs],
            ['.venv/bin/cmake', '--build', str(bdir), '--target', 'strata', '-j', '6']]
for cmd in commands:
    print(json.dumps(cmd), flush=True)
    sp.run(cmd, cwd=root, check=True)
engine = root / 'engine'
engine.mkdir(exist_ok=True)
for name in ('strata', 'libstrata_kq.so'):
    source = bdir / name
    if name == 'strata':
        assert source.is_file()
    if source.is_file():
        shutil.copy2(source, engine / name)
binary = engine / 'strata'
binary.chmod(0o755)
metadata = dict(source='local', version=version, archs=[70], vision='none', toolkit=12,
                cuda_dirs=[str(Path(nvcc).parent), str(Path(nvcc).parent.parent / 'lib64')],
                src=setup.source_hash(setup.ENGINE_SOURCES), vision_src=None,
                git_revision=revision, vendored_ggml=vendored.is_file(), build_commands=commands,
                binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest())
(engine / 'BUILD.json').write_text(json.dumps(metadata, indent=2) + '\n')
print(json.dumps(metadata, indent=2), flush=True)
# Keep CMakeCache/compile rules in the image as auditable build provenance.
