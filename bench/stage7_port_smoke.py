#!/usr/bin/env python3
"""Non-scored, fresh dual-agent 128K compatibility/dispatch check on P520."""
import argparse
import concurrent.futures
import fcntl
import json
import pathlib
import signal
import socket
import subprocess
import time
import urllib.request


def command(*args):
    return subprocess.check_output(args, text=True).strip()


def get(url):
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.load(response)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('arm', choices=['14', '15', '16'])
    ap.add_argument('image_id')
    ap.add_argument('diagnostic_id')
    ap.add_argument('--trace-library', type=pathlib.Path)
    args = ap.parse_args()
    assert len(args.image_id) == 71 and args.image_id.startswith('sha256:')
    assert args.diagnostic_id.startswith(f'smoke{args.arm}-') and args.diagnostic_id.replace('-', '').isalnum()
    root = pathlib.Path.home() / 'v100-x2-strata-qwen3.8-flash-next'
    lock = (root / 'results/.stage7-experiment.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert not command('docker', 'ps', '-q'), 'running container'
    assert not command('nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'), 'GPU workload'
    for port in (18084, 18085):
        with socket.socket() as check:
            check.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            check.bind(('127.0.0.1', port))
    assert command('docker', 'image', 'inspect', args.image_id, '--format', '{{.Id}}') == args.image_id
    directory = root / 'results/stage7-iq3xxs-v100-port' / args.diagnostic_id
    directory.mkdir(exist_ok=False)
    (directory / 'logs').mkdir()
    (directory / 'receipt.json').write_text(json.dumps(vars(args), default=str, indent=2))
    containers = []
    flags = ['STRATA_SELECT_SIMT=1', 'STRATA_SM70_TABLE=1', 'STRATA_PF_WMMA=1']
    if args.arm in ('15', '16'):
        flags.append('STRATA_PF_WMMA2=1')
    if args.arm == '16':
        flags.append('STRATA_PF_WMMA_LEAN=1')
    try:
        for suffix, gpu, cpus, port in [('a', 0, '0-2,6-8', 18084), ('b', 1, '3-5,9-11', 18085)]:
            config = json.loads((root / f'results/stage5-iq3xxs/agent-{suffix}.json').read_text())
            config['model_name'] = f'qwen3.8-flash-next-iq3_xxs-{args.diagnostic_id}-{suffix}'
            (directory / f'agent-{suffix}.json').write_text(json.dumps(config, indent=2))
            run = ['docker', 'run', '-d', '--name', f'strata-s7-port-{args.diagnostic_id}-{suffix}',
                   '--cpuset-cpus', cpus, '--gpus', f'"device={gpu}"', '--restart', 'no',
                   '-p', f'127.0.0.1:{port}:8080',
                   '-v', '/srv/models/strata-iq3xxs:/iq3xxs:ro',
                   '-v', '/srv/models/strata-data/mtp:/shared-mtp:ro',
                   '-v', f'{directory}/logs:/trial-logs',
                   '-v', f'{directory}/agent-{suffix}.json:/opt/strata/config.json:ro']
            for flag in flags:
                run.extend(['-e', flag])
            if args.trace_library:
                run.extend(['-v', f'{args.trace_library}:/s7-trace.so:ro', '-e', 'LD_PRELOAD=/s7-trace.so'])
            run.extend(['--entrypoint', '/opt/strata/.venv/bin/python', args.image_id,
                        '/opt/strata/serve/server.py', '--engine', 'strata', '--config', '/opt/strata/config.json',
                        '--host', '0.0.0.0', '--port', '8080'])
            containers.append(command(*run))
            (directory / f'container-{suffix}.id').write_text(containers[-1] + '\n')
            for attempt in range(600):
                try:
                    health = get(f'http://127.0.0.1:{port}/health')
                    if health.get('loaded') and health.get('status') == 'ok':
                        assert health['max_context'] == 131072 and health['model'] == config['model_name']
                        break
                except (OSError, ValueError):
                    pass
                assert command('docker', 'inspect', containers[-1], '--format', '{{.State.Running}}') == 'true'
                time.sleep(1)
            else:
                raise RuntimeError('health timeout')
            assert get(f'http://127.0.0.1:{port}/metrics')['requests_kept'] == 0

        def request(suffix, port, expected):
            payload = json.loads((root / f'results/stage7-iq3xxs-v100-port/xxs-14-1/c2/payload-{suffix}.json').read_text())
            # Original 128K prompt; reduced output explicitly makes this non-scored.
            payload.update(model=f'qwen3.8-flash-next-iq3_xxs-{args.diagnostic_id}-{suffix}', max_tokens=32, stream=False)
            payload.pop('stream_options', None)
            req = urllib.request.Request(f'http://127.0.0.1:{port}/v1/chat/completions',
                                         json.dumps(payload).encode(), {'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=900) as response:
                data = json.load(response)
            (directory / f'response-{suffix}.json').write_text(json.dumps(data, indent=2))
            assert data['usage']['prompt_tokens'] == expected
            assert data['usage'].get('prompt_tokens_details', {}).get('cached_tokens', 0) == 0
            assert data['choices'][0]['message']['content']
            health = get(f'http://127.0.0.1:{port}/health')
            assert health['loaded'] and health['status'] == 'ok'
            return data['usage']

        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            futures = [pool.submit(request, 'a', 18084, 126967), pool.submit(request, 'b', 18085, 126968)]
            usages = [future.result() for future in futures]
        for suffix in 'ab':
            text = (directory / f'logs/agent-{suffix}.log').read_text()
            if args.arm in ('15', '16'):
                assert 'S7_WMMA2 launched ty=18 ' in text, 'IQ3_XXS WMMA2 dispatch missing'
            if args.arm == '16':
                assert 'S7_WMMA_LEAN eligible:' in text and 'ids=1 tile=128x64' in text
            if args.trace_library:
                assert 'S7_CUPTI kernel=' in text and 'result=0' in text, 'CUDA launch trace missing'
        (directory / 'summary.json').write_text(json.dumps({'scored': False, 'compatibility_128k': True, 'usage': usages}, indent=2))
        (directory / 'verdict').write_text('SMOKE_PASS_NOT_SCORED\n')
    finally:
        for cid in containers:
            subprocess.run(['docker', 'stop', '-t', '20', cid], check=False, stdout=subprocess.DEVNULL)
        (directory / 'finished').write_text(time.strftime('%Y-%m-%dT%H:%M:%S%z') + '\n')


if __name__ == '__main__':
    def terminate(signum, frame):
        raise SystemExit(124)
    signal.signal(signal.SIGTERM, terminate)
    main()
