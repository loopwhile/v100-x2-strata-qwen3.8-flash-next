#!/usr/bin/env python3
"""ThinkPad: validate preparation, dry-run, then launch one authorized Stage 9 arm.

Never launch all candidates as a queue; review and back up each arm first.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess as sp


def remote(code, *args):
    return sp.check_output(['ssh', 'p520', 'python3 -c ' + shlex.quote(code) + ' ' + ' '.join(map(shlex.quote, args))], text=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('arm', choices=('U1', 'D1', 'F1'))
    p.add_argument('--preparation', required=True)
    p.add_argument('--previous-preparation-id')
    a = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    contract = json.loads((root / 'bench/stage9-candidates.json').read_text())
    assert contract['authorized_gpu_execution'], 'No current authorized campaign'
    assert re.fullmatch(r'/home/loopwhile/v100-x2-strata-qwen3\.8-flash-next/results/stage9-preparation/p0-\d{8}T\d{6}', a.preparation)
    probe = '''from pathlib import Path
import json,subprocess as s,sys,hashlib
p=Path(sys.argv[1]);arm=sys.argv[2];source='fork' if arm=='F1' else 'upstream'
x=json.loads((p/(source+'-build/progress.json')).read_text());assert x['phase']=='results_saved' and x['verdict']=='BUILD_PASS_NOT_C2'
assets=(p/'asset-verification.log').read_text().splitlines();assert len(assets)==15 and all(t.endswith(': OK') for t in assets),assets
assert (p/'preflight-v2/offline-c2-calibration.json').is_file()
preflight=json.loads((p/'preflight-v2/confidence-policy.json').read_text())
if arm=='D1':
 assert json.loads((p/'preflight-v2/preparation.json').read_text())['verdict']=='PREPARATION_PASS_NOT_C2'
 assert s.check_output(['docker','inspect','strata-s9-p0-draft-preparation-v2','--format','{{.State.ExitCode}} {{.State.Running}}'],text=True).strip()=='0 false'
if arm=='F1':
 assert (p/'fork-offline/offline-c2-calibration.json').is_file()
 assert s.check_output(['docker','inspect','strata-s9-p0-fork-offline','--format','{{.State.ExitCode}} {{.State.Running}}'],text=True).strip()=='0 false'
meta=json.loads((p/(source+'-image.json')).read_text());assert meta['git_revision']==x['revision'] and meta['archs']==[70] and meta['toolkit']==12
runner=p/'execution-tools-v3-clock1245/scripts/115-stage9-c2.py'
print(json.dumps({'image':x['image_id'],'engine_sha256':meta['binary_sha256'],'source':x['revision'],'draft_conf':preflight['draft_conf'],'runner':str(runner),'runner_sha256':hashlib.sha256(runner.read_bytes()).hexdigest()}))
'''
    evidence = json.loads(remote(probe, a.preparation, a.arm))
    assert evidence['runner_sha256'] == hashlib.sha256((root / 'scripts/115-stage9-c2.py').read_bytes()).hexdigest()
    experiment = a.arm.lower() + '-' + dt.datetime.now().strftime('%Y%m%dT%H%M%S')
    command = ['python3', evidence['runner'], '--arm', a.arm, '--id', experiment, '--image', evidence['image'],
               '--engine-sha256', evidence['engine_sha256'], '--assets', a.preparation + '/artifacts/stage8-results-20261107/assets.sha256',
               '--sm-clock-ceiling', str(contract['shared']['sm_clock_ceiling_mhz'])]
    if a.previous_preparation_id:
        command += ['--previous-preparation-id', a.previous_preparation_id]
    if a.arm == 'D1':
        command += ['--draft-data', a.preparation + '/preflight-v2/draft-data', '--draft-conf', f"{evidence['draft_conf']:g}"]
    dry = remote("import subprocess as s,sys; s.run(sys.argv[1:]+['--dry-run'],check=True)", *command)
    print(dry, end='')
    artifact = f'/home/loopwhile/v100-x2-strata-qwen3.8-flash-next/results/stage9/S9-{a.arm}/{experiment}'
    state = root / 'state/current.md'
    text = state.read_text()
    current = f'''# Current operation — Stage 9 S9-{a.arm} launch (2026-11-10 KST)

User-authorized P0 → U1 → D1 → F1, max 3 scored C2 per eligible arm, 9 total. No retries/baseline/tuning/promotion/Git publication.

- Active task **S9-{a.arm}**, ID `{experiment}`. Dry-run passed; launch pending/being recorded below. Remote raw `{artifact}`.
- Immutable image `{evidence['image']}`, binary `{evidence['engine_sha256']}`, source `{evidence['source']}`.
- Runner snapshot `{evidence['runner']}` (SHA `{evidence['runner_sha256']}`), timeout 3600s internal / 3700s outer; logs `{a.preparation}/{experiment}.log`.
- Next read-only check: inspect raw `progress.json`, P520 runner PID/start ticks, GPU/containers and this launch log. Do not relaunch on SSH disconnection.
- Preparation `{a.preparation}`; original 15 assets verified; frozen C2 calibration matched; DFlash2 stock pack pinned, spec6/conf {evidence['draft_conf']:g}. Independent GPU/CPU mapping/context/KV unchanged.
- Initial serving empty. Cleanup stops only run-labelled container IDs, preserves all containers/images/evidence. Historical serving stays stopped; no power/clock/host/port/tunnel changes.
- User amendment: observed SM clocks up to {contract['shared']['sm_clock_ceiling_mhz']} MHz are accepted for this campaign; hardware settings are not changed. The original U1 startup-only clock-gate failure is closed, zero scored batches.
- Commit/push not requested. Prior stage history and references are immutable.

---

'''
    state.write_text(current + text)
    launch = '''from pathlib import Path
import json,os,subprocess as s,sys
p=Path(sys.argv[1]);eid=sys.argv[2];cmd=json.loads(sys.argv[3]);log=(p/(eid+'.log')).open('x')
q=s.Popen(['timeout','--signal=TERM','--kill-after=60s','3700s',*cmd],stdin=s.DEVNULL,stdout=log,stderr=s.STDOUT,start_new_session=True,cwd=p)
r={'pid':q.pid,'pid_start_ticks':Path('/proc/'+str(q.pid)+'/stat').read_text().split()[21],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'command':cmd,'timeout_s':3700,'id':eid}
(p/(eid+'-launch.json')).write_text(json.dumps(r,indent=2)+'\\n');print(json.dumps(r))
'''
    launched = json.loads(remote(launch, a.preparation, experiment, json.dumps(command)))
    local = root / 'results/stage9-launches'
    local.mkdir(exist_ok=True)
    (local / (experiment + '.json')).write_text(json.dumps(dict(launched, artifact=artifact, preparation=a.preparation, arm=a.arm), indent=2) + '\n')
    state.write_text(state.read_text().replace('launch pending/being recorded below', f"running under outer PID {launched['pid']}, start ticks {launched['pid_start_ticks']}, boot {launched['boot_id']}"))
    print(json.dumps(dict(launched, artifact=artifact), indent=2))


if __name__ == '__main__':
    main()
