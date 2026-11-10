"""CPU-only regression checks for the new runner's preservation boundaries."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('stage9', ROOT / 'scripts/115-stage9-c2.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.base = dict(args=['--max-context', '131072', '--kv', 'int8', '--kv-resident', '32768',
                               '--pack', '/iq3xxs/pack/iq3_xxs-native',
                               '--spec', '4', '--spec-min-p', '0.5', '--prefill', 'auto',
                               '--expert-cache', 'auto', '--mtp', '/shared-mtp/rt', '--mmap-experts'],
                         gpu=0, gpus_asked=True)

    def test_frozen_inputs_remain_unchanged_for_all_arms(self):
        original = json.dumps(self.base, sort_keys=True)
        for arm in runner.SOURCES:
            cfg, expected = runner.config_for(self.base, arm, 0.7, 'qwen3.8-flash-next-iq3_xxs')
            self.assertEqual(json.dumps(self.base, sort_keys=True), original)
            self.assertIn('--mmap-experts', cfg['args'])
            self.assertEqual(expected['--kv-resident'], '32768')
        self.base['args'][1] = '65536'
        with self.assertRaises(AssertionError):
            runner.config_for(self.base, 'U1', None, 'test')

    def test_dflash_rejects_mtp_fallback_or_wrong_pack(self):
        good = ['--draft', 'dflash2', '--draft-fallback', 'none', '--draft-model',
                '/stage9-data/dflash2/' + runner.PACK_NAME, '--spec', '6', '--draft-conf', '0.7',
                '--mtp-draft-vocab', '/shared-mtp/rt/draft_vocab.bin']
        runner.validate_drafter(good, 'D1', 0.7)
        for bad in (good + ['--mtp', '/shared-mtp/rt'],
                    [x if x != 'none' else 'mtp' for x in good],
                    [x if x != '/stage9-data/dflash2/' + runner.PACK_NAME else '/wrong.pack' for x in good]):
            with self.assertRaises(AssertionError):
                runner.validate_drafter(bad, 'D1', 0.7)

    def test_foreign_container_cannot_be_stopped(self):
        with patch.object(runner, 'run', return_value=json.dumps([{'Config': {'Labels': {'lab.stage9.run': 'another-id'}}}])) as call:
            with self.assertRaises(AssertionError):
                runner.stop_owned('foreign', 'our-id')
            self.assertEqual(call.call_count, 1)
        with patch.object(runner, 'run', side_effect=[json.dumps([{'Config': {'Labels': {'lab.stage9.run': 'our-id'}}}]), 'owned']) as call:
            runner.stop_owned('owned', 'our-id')
            self.assertEqual(call.call_args.args[:2], ('docker', 'stop'))

    def test_latest_clock_receipt_overrides_earlier_boot_entry(self):
        lines = []
        for limit in (1110, 1245):
            for bus in ('00000000:65:00.0', '00000000:B3:00.0'):
                lines.append(f'GPU clocks set to "(gpuClkMin 135, gpuClkMax {limit})" for GPU {bus}')
        runner.verify_latest_clock_receipt('\n'.join(lines), 1245)
        with self.assertRaises(AssertionError):
            runner.verify_latest_clock_receipt('\n'.join(lines), 1110)

    def test_sampler_preserves_complete_records_on_sigterm(self):
        with tempfile.TemporaryFile(mode='w+') as log:
            child = subprocess.Popen([sys.executable, str(ROOT / 'scripts/115-stage9-c2.py'), '--sample-host'], stdout=log)
            try:
                time.sleep(1.2)
                child.terminate()
                child.wait(timeout=5)
                log.seek(0)
                rows = [json.loads(line) for line in log]
                self.assertTrue(rows)
                self.assertIn('MemAvailable', rows[0]['memory'])
                self.assertIn('cpu', rows[0]['cpu_ticks'])
            finally:
                if child.poll() is None:
                    child.kill()
                    child.wait()

    def test_report_excludes_post_response_prefill_from_request_io(self):
        spec = importlib.util.spec_from_file_location('stage9_report', ROOT / 'scripts/117-stage9-report.py')
        report = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(report)
        with tempfile.TemporaryDirectory() as temp:
            raw = Path(temp) / 'test-id'
            logs = raw / 'batch-1/logs'
            logs.mkdir(parents=True)
            (logs / 'agent-a.log').write_text(
                'strata serve: prompt 126967 tokens = 0 reused + 126967 read in 100000 ms (1269.7 tok/s), 1500 generated in 50000 ms (30.0 tok/s)\n'
                'strata serve: file tier I/O this request: the OS read 100.0 MB from storage\n'
                'strata serve: KV streaming: 98.0% of 100 block reads hit VRAM\n'
                'strata serve: prompt 128000 tokens = 126000 reused + 2000 read in 1000 ms (2000 tok/s), 0 generated in 0 ms (0.0 tok/s)\n'
                'strata serve: file tier I/O this request: the OS read 5.0 MB from storage\n'
                'strata serve: KV streaming: 97.0% of 200 block reads hit VRAM\n')
            result = report.phase_receipt(raw, {'id': 'test-id-batch-1', 'scored': True, 'verdict': 'PASS'})
            self.assertEqual(result['request_physical_read_mb']['a'], 100.0)
            self.assertEqual(result['kv_vram_hit_pct']['a'], 98.0)
            self.assertEqual(result['post_response_idle_prefill']['a'][0]['physical_read_mb'], 5.0)


if __name__ == '__main__':
    unittest.main()
