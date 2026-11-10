#!/usr/bin/env python3
"""Inside the pinned upstream image: DFlash2 preparation and offline C2 gate.

No GPU, engine start, model repack or existing-asset writes. Mount /work read-only,
/iq3xxs read-only, /shared-mtp read-only and a fresh /stage9 writable directory.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.path.insert(0, '/opt/strata')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline-only', action='store_true', help='Also usable on the MTP-only fork')
    options = parser.parse_args()
    out = Path('/stage9')
    assert not (out / 'preparation.json').exists(), 'Do not overwrite preparation receipts'
    base = json.loads(Path('/work/results/stage5-iq3xxs/agent-a.json').read_text())
    frozen = base['args']
    spec = importlib.util.spec_from_file_location('c2_frozen', '/work/bench/c2_v100_contract.py')
    c2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c2)
    cfg_path = out / 'offline-config.json'
    cfg_path.write_text(json.dumps(base, indent=2) + '\n')
    tok, template, frontend = c2.load_tokenizer_and_template(cfg_path)
    manifest = json.loads(Path('/work/bench/workloads/v100-performance-v1.json').read_text())
    calibration = []
    for task in manifest['requests']:
        row = c2.materialize_one(manifest, task, tok, template, frontend)
        calibration.append({k: row[k] for k in ('id', 'prompt_tokens', 'raw_prompt_sha256')})
    expected = json.loads(Path('/stage9/expected-calibration.json').read_text())
    assert calibration == expected, (calibration, expected)
    (out / 'offline-c2-calibration.json').write_text(json.dumps(calibration, indent=2) + '\n')
    if options.offline_only:
        print('OFFLINE_CALIBRATION_PASS_NOT_C2', flush=True)
        return
    from strata_control import drafting, drafting_fetch
    assert callable(drafting_fetch.ensure) and callable(drafting_fetch.convert_selector)
    held = drafting.slots_of(frozen, 16384)
    confidence = drafting.conf_for('cuda', held)
    assert drafting.window_for('cuda', ['sm_70'], 16384, held) == 6
    assert drafting.supported_model('qwen3.8-flash-next-iq3_xxs_s9_d1_batch_1_a')
    (out / 'confidence-policy.json').write_text(json.dumps(dict(expected_slots=held, draft_conf=confidence, spec=6), indent=2) + '\n')
    last = [None]
    def report(message, done, total):
        key = message, int(done / max(total, 1) * 10)
        if last[0] != key:
            print(message, done, total, flush=True)
            last[0] = key
    drafting_fetch.ensure(out / 'draft-data', progress=report)
    # Require the exact stock selector variant, never a tuned or legacy pack.
    drafting_fetch.convert_selector(out / 'draft-data', progress=report)
    pack = out / 'draft-data/dflash2' / drafting.CONVERTED_NAME
    assert pack.stat().st_size == 339694592
    assert sha(pack) == '4a42b98220ea7880664002c8edda1563aecbae754b762a2e2f31b2b91ee93ecd'
    assert drafting.engine_reads_selector_q4('/opt/strata/engine/strata')
    prepared = dict(source_revision='712fec6b4297c9cfd32ab43daaa2979a9aa01edf',
                    pack_name=pack.name, pack_bytes=pack.stat().st_size, pack_sha256=sha(pack),
                    weight_revision=drafting.REVISION, expected_slots=held, draft_conf=confidence,
                    spec=6, original_vocab_sha256=sha(Path('/shared-mtp/rt/draft_vocab.bin')),
                    confidence_policy='drafting.conf_for(cuda, drafting.slots_of(frozen_args,16384))',
                    offline_calibration=calibration, verdict='PREPARATION_PASS_NOT_C2')
    (out / 'preparation.json').write_text(json.dumps(prepared, indent=2) + '\n')
    print(json.dumps(prepared, indent=2), flush=True)


if __name__ == '__main__':
    main()
