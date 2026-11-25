#!/usr/bin/env python3
"""ThinkPad: hash-verified Stage 12 evidence backup from P520, excluding draft weights."""
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
    p.add_argument("arm", help="Candidate arm e.g. S12-U0, S12-U1, S12-P0, S12-D1, S12-F1")
    p.add_argument("id", help="Run ID e.g. u0-20261125T151000")
    a = p.parse_args()
    assert re.fullmatch(r"S12-[A-Z0-9]+", a.arm), f"Invalid arm: {a.arm}"
    assert re.fullmatch(r"[a-z0-9]+-\d{8}T\d{6}", a.id), f"Invalid ID: {a.id}"

    root = Path(__file__).resolve().parents[1]
    remote = f"/home/loopwhile/v100-x2-strata-qwen3.8-flash-next/results/stage12/{a.arm}/{a.id}"

    probe = """from pathlib import Path
import json,hashlib,sys
p=Path(sys.argv[1])
for checkpoint in p.rglob('progress.json'):
 if 'draft-data' in checkpoint.parts: continue
 x=json.loads(checkpoint.read_text())
 assert x['phase'] in ('results_saved','interrupted'), str(checkpoint)+' is not finished'
print(json.dumps({str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(p.rglob('*')) if f.is_file() and not {'draft-data','__pycache__'} & set(f.relative_to(p).parts)}))
"""
    manifest = json.loads(sp.check_output(["ssh", "p520", "python3 -c " + shlex.quote(probe) + " " + shlex.quote(remote)], text=True))
    parent = root / "results/raw"
    parent.mkdir(parents=True, exist_ok=True)
    target = parent / a.id

    if not target.exists():
        temp = Path(tempfile.mkdtemp(prefix=a.id + "-partial-", dir=parent))
        assert all(not Path(name).is_absolute() and ".." not in Path(name).parts for name in manifest)
        proc = sp.Popen(["ssh", "p520", "tar -C " + shlex.quote(remote) + " --null -T - -cf -"], stdin=sp.PIPE, stdout=sp.PIPE)
        proc.stdin.write(b"".join(name.encode() + b"\0" for name in sorted(manifest)))
        proc.stdin.close()
        with tarfile.open(fileobj=proc.stdout, mode="r|") as archive:
            archive.extractall(temp, filter="data")
        assert proc.wait() == 0
        found = {str(f.relative_to(temp)): hashlib.sha256(f.read_bytes()).hexdigest() for f in temp.rglob("*") if f.is_file()}
        assert found == manifest, f"Partial retained: {temp}"
        temp.rename(target)

    found = {str(f.relative_to(target)): hashlib.sha256(f.read_bytes()).hexdigest() for f in target.rglob("*") if f.is_file() and f.name != "sha256-manifest.txt"}
    assert found == manifest, "Existing backup differs; refusing overwrite"

    manifest_txt = target / "sha256-manifest.txt"
    manifest_txt.write_text("\n".join(f"{digest}  {relpath}" for relpath, digest in sorted(manifest.items())) + "\n")

    receipt = dict(id=a.id, arm=a.arm, files=len(manifest), all_match=True, sha256=manifest)
    dest = parent / (a.id + "-sha256.json")
    dest.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({k: receipt[k] for k in ("id", "arm", "files", "all_match")}))


if __name__ == "__main__":
    main()
