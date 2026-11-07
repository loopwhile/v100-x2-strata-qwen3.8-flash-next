#!/usr/bin/env python3
"""ThinkPad: copy a finished Stage 8 arm via ssh p520 and verify every file hash."""
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
    p.add_argument("arm", choices=("D1", "C1", "C2", "C3", "M1", "M2", "M3"))
    p.add_argument("id")
    a = p.parse_args()
    assert re.fullmatch(a.arm.lower() + r"-\d{8}T\d{6}", a.id)
    root = Path(__file__).resolve().parents[1]
    remote = f"/home/loopwhile/v100-x2-strata-qwen3.8-flash-next/results/stage8/S8-{a.arm}/{a.id}"
    probe = """from pathlib import Path
import json,hashlib,sys
p=Path(sys.argv[1]);x=json.loads((p/'progress.json').read_text())
assert x['phase'] in ('results_saved','interrupted'), 'Runner still active'
stat=Path('/proc')/str(x['pid'])/'stat'
if stat.exists(): assert stat.read_text().split()[21]!=str(x['pid_start_ticks']), 'Runner cleanup still active'
print(json.dumps({str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(p.rglob('*')) if f.is_file()}))
"""
    manifest = json.loads(sp.check_output(["ssh", "p520", "python3 -c " + shlex.quote(probe) + " " + shlex.quote(remote)], text=True))
    target = root / "results/raw" / a.id
    if not target.exists():
        with tempfile.TemporaryDirectory(prefix=f"{a.id}-", dir=root / "results/raw") as tmp:
            proc = sp.Popen(["ssh", "p520", "tar -C " + shlex.quote(remote) + " -cf - ."], stdout=sp.PIPE)
            with tarfile.open(fileobj=proc.stdout, mode="r|") as archive:
                archive.extractall(tmp, filter="data")
            assert proc.wait() == 0
            local = {str(f.relative_to(tmp)): hashlib.sha256(f.read_bytes()).hexdigest() for f in Path(tmp).rglob("*") if f.is_file()}
            assert local == manifest, "Transferred data mismatch; source and temporary copy retained where possible"
            Path(tmp).rename(target)
    local = {str(f.relative_to(target)): hashlib.sha256(f.read_bytes()).hexdigest() for f in target.rglob("*") if f.is_file()}
    assert local == manifest, "Existing local evidence differs; refusing to overwrite"
    receipt = {"id": a.id, "arm": "S8-" + a.arm, "files": len(manifest), "all_match": True, "sha256": manifest}
    out = root / "results/raw" / f"{a.id}-sha256.json"
    if out.exists():
        assert json.loads(out.read_text()) == receipt
    else:
        out.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({k: receipt[k] for k in ("id", "arm", "files", "all_match")}))


if __name__ == "__main__":
    main()
