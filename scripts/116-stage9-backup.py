#!/usr/bin/env python3
"""ThinkPad: hash-verified Stage 9 evidence backup, excluding draft weights."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess as sp
import tarfile
import tempfile


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('kind', choices=('P0', 'U1', 'D1', 'F1'))
    p.add_argument('id')
    a = p.parse_args()
    assert re.fullmatch(a.kind.lower() + r'-\d{8}T\d{6}', a.id)
    root = Path(__file__).resolve().parents[1]
    relative = f'stage9-preparation/{a.id}' if a.kind == 'P0' else f'stage9/S9-{a.kind}/{a.id}'
    remote = '/home/loopwhile/v100-x2-strata-qwen3.8-flash-next/results/' + relative
    probe = '''from pathlib import Path
import json,hashlib,sys
p=Path(sys.argv[1])
for checkpoint in p.rglob('progress.json'):
 if 'draft-data' in checkpoint.parts: continue
 x=json.loads(checkpoint.read_text())
 assert x['phase'] in ('results_saved','interrupted'), str(checkpoint)+' is not finished'
 if x.get('boot_id')==Path('/proc/sys/kernel/random/boot_id').read_text().strip() and 'pid' in x:
  stat=Path('/proc')/str(x['pid'])/'stat'
  if stat.exists(): assert stat.read_text().split()[21]!=str(x['pid_start_ticks']), 'Process cleanup still active'
print(json.dumps({str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(p.rglob('*')) if f.is_file() and not {'draft-data','__pycache__'} & set(f.relative_to(p).parts)}))
'''
    manifest = json.loads(sp.check_output(['ssh', 'p520', 'python3 -c ' + shlex.quote(probe) + ' ' + shlex.quote(remote)], text=True))
    parent = root / 'results' / ('stage9-preparation-backup' if a.kind == 'P0' else 'raw')
    parent.mkdir(parents=True, exist_ok=True)
    target = parent / a.id
    if not target.exists():
        # Keep any partial transfer for inspection; never replace a different target.
        temp = Path(tempfile.mkdtemp(prefix=a.id + '-partial-', dir=parent))
        # Send only the hash-manifest files, so draft weights cannot accidentally
        # be transferred through differing tar exclusion semantics.
        assert all(not Path(name).is_absolute() and '..' not in Path(name).parts for name in manifest)
        proc = sp.Popen(['ssh', 'p520', 'tar -C ' + shlex.quote(remote) + ' --null -T - -cf -'], stdin=sp.PIPE, stdout=sp.PIPE)
        proc.stdin.write(b''.join(name.encode() + b'\0' for name in sorted(manifest)))
        proc.stdin.close()
        with tarfile.open(fileobj=proc.stdout, mode='r|') as archive:
            archive.extractall(temp, filter='data')
        assert proc.wait() == 0
        found = {str(f.relative_to(temp)): hashlib.sha256(f.read_bytes()).hexdigest() for f in temp.rglob('*') if f.is_file()}
        assert found == manifest, f'Partial retained: {temp}'
        temp.rename(target)
    found = {str(f.relative_to(target)): hashlib.sha256(f.read_bytes()).hexdigest() for f in target.rglob('*') if f.is_file()}
    assert found == manifest, 'Existing backup differs; refusing overwrite'
    receipt = dict(id=a.id, kind=a.kind, files=len(manifest), all_match=True, sha256=manifest, excluded='draft-data weights and Python cache')
    dest = parent / (a.id + '-sha256.json')
    if dest.exists():
        assert json.loads(dest.read_text()) == receipt
    else:
        dest.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: receipt[k] for k in ('id', 'kind', 'files', 'all_match')}))


if __name__ == '__main__':
    main()
