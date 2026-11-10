#!/usr/bin/env python3
"""P520: bounded, separately pinned Stage 9 image build; retain every log."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import socket
import subprocess as sp

PINS = {
    'upstream': ('Niko1221/Strata', '712fec6b4297c9cfd32ab43daaa2979a9aa01edf', '0.1.59'),
    'fork': ('jmnargi/Strata-V100', '8b4c09bd3d9213b2d47880826c6e818c3140664d', '0.1.45.7'),
}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', choices=PINS)
    p.add_argument('--out', required=True, type=Path)
    a = p.parse_args()
    assert socket.gethostname() == 'p520-llm'
    repo, revision, version = PINS[a.source]
    tag = f'strata-stage9-{a.source}:{version}-{revision[:7]}'
    assert sp.run(['docker', 'image', 'inspect', tag], capture_output=True).returncode != 0, 'Existing image is protected'
    a.out.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    cmd = ['docker', 'build', '-f', str(root / 'Dockerfile.stage9-v100'), '-t', tag,
           '--build-arg', f'STRATA_REPO={repo}', '--build-arg', f'STRATA_REF={revision}',
           '--build-arg', f'STRATA_VERSION={version}', str(root)]
    record = dict(source=a.source, revision=revision, version=version, tag=tag,
                  started=dt.datetime.now().astimezone().isoformat(), command=cmd,
                  pid=os.getpid(), boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                  pid_start_ticks=Path(f'/proc/{os.getpid()}/stat').read_text().split()[21],
                  timeout_s=7200, phase='running')
    progress = a.out / 'progress.json'
    progress.write_text(json.dumps(record, indent=2) + '\n')
    try:
        with (a.out / 'build.log').open('w') as log:
            rc = sp.run(cmd, stdout=log, stderr=sp.STDOUT, timeout=7000).returncode
        assert rc == 0, f'Build failed: {rc}'
        info = json.loads(sp.check_output(['docker', 'image', 'inspect', tag], text=True))[0]
        record['image_id'] = info['Id']
        probe = 'cat engine/BUILD.json; sha256sum engine/strata; nvcc --version; cuobjdump --list-elf engine/strata'
        receipt = sp.check_output(['docker', 'run', '--rm', '--network', 'none', '--entrypoint', '/bin/bash', info['Id'], '-euc', probe], text=True)
        (a.out / 'provenance.txt').write_text(receipt)
        record.update(phase='results_saved', verdict='BUILD_PASS_NOT_C2')
        (a.out / 'exit-code').write_text('0\n')
    except BaseException as exc:
        record.update(phase='interrupted', verdict='INCONCLUSIVE', error=repr(exc))
        (a.out / 'exit-code').write_text('1\n')
        raise
    finally:
        record['finished'] = dt.datetime.now().astimezone().isoformat()
        temp = progress.with_suffix('.tmp')
        temp.write_text(json.dumps(record, indent=2) + '\n')
        temp.replace(progress)


if __name__ == '__main__':
    main()
