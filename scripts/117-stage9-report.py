#!/usr/bin/env python3
"""Export sanitized Stage 9 receipts and descriptive comparisons; no promotion."""
import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import statistics as st


def load(path):
    return json.loads(path.read_text())


def stats(values):
    return {'mean': st.mean(values), 'min': min(values), 'peak': max(values)} if values else None


def cpu_usage(first, last, keys):
    a = [sum(first[k][i] for k in keys) for i in range(8)]
    b = [sum(last[k][i] for k in keys) for i in range(8)]
    delta = [y - x for x, y in zip(a, b)]
    total = sum(delta)
    return {'busy_pct': 100 * (total - delta[3] - delta[4]) / total,
            'user_pct': 100 * (delta[0] + delta[1]) / total,
            'iowait_pct': 100 * delta[4] / total} if total else None


def phase_receipt(raw, phase):
    name = phase['id'].removeprefix(raw.name + '-')
    d = raw / name
    row = {'phase': phase, 'gpu_full_lifetime': {}, 'request_metrics': {}, 'engine_notes': {}, 'processes': {}}
    if (d / 'c2/summary.json').exists():
        summary = load(d / 'c2/summary.json')
        row['summary'] = summary
        row['workload'] = load(d / 'c2/workload.json')
        row['summary_sha256'] = hashlib.sha256((d / 'c2/summary.json').read_bytes()).hexdigest()
        if phase.get('verdict') == 'PASS':
            assert summary['pass_mechanical'] and summary['active_overlap'] and summary['post_health'] and summary['warmup_count'] == 0
            assert [r['prompt_tokens'] for r in summary['requests']] == [126967, 126968]
            assert [r['raw_prompt_sha256'] for r in row['workload']['items']] == [
                '882a3617750ab8dbcb61d3e8e1d42641555a6b1450d060d7bb22a4f1161670b6',
                '5a19042f67dd7702e843595467e1d6c2b96414f565b0fbfa8036590709dba557']
            for request in summary['requests']:
                assert request['output_tokens'] >= 1024 and request['finish_reason'] == 'stop'
                assert request['cache_n'] == request['cached_tokens'] == 0
    samples = list(csv.reader((d / 'gpu-telemetry.csv').read_text().splitlines())) if (d / 'gpu-telemetry.csv').exists() else []
    for i, side in enumerate('ab'):
        selected = [r for r in samples if len(r) == 8 and r[1].strip() == str(i)]
        if selected:
            row['gpu_full_lifetime'][side] = {key: stats([float(r[ix]) for r in selected]) for key, ix in
                (('temperature_c', 2), ('power_w', 3), ('util_pct', 5), ('vram_mib', 6), ('sm_mhz', 7))}
            row['gpu_full_lifetime'][side]['sample_count'] = len(selected)
        for filename, key in ((f'engine-process-{side}.json', 'processes'), (f'metrics-after-{side}.json', 'request_metrics')):
            if (d / filename).exists():
                value = load(d / filename)
                if key == 'request_metrics':
                    value = (value.get('requests') or [{}])[0]
                row[key][side] = value
        log = d / f'logs/agent-{side}.log'
        notes = log.read_text(errors='replace').splitlines() if log.exists() else []
        records = []
        for line in notes:
            match = re.search(r'prompt (\d+) tokens = (\d+) reused \+ (\d+) read in ([\d.]+) ms.*?, (\d+) generated in ([\d.]+) ms', line)
            if match:
                values = match.groups()
                records.append(dict(prompt_tokens=int(values[0]), reused=int(values[1]), read_tokens=int(values[2]),
                                    prompt_ms=float(values[3]), generated=int(values[4]), decode_ms=float(values[5])))
            elif records:
                physical = re.search(r'file tier I/O this request: the OS read ([\d.]+) MB', line)
                kv = re.search(r'KV streaming: ([\d.]+)%', line)
                if physical:
                    records[-1]['physical_read_mb'] = float(physical[1])
                if kv:
                    records[-1]['kv_vram_hit_pct'] = float(kv[1])
        row.setdefault('engine_request_records', {})[side] = records
        generated = [v for v in records if v['generated'] > 0]
        idle = [v for v in records if v['generated'] == 0]
        row.setdefault('post_response_idle_prefill', {})[side] = idle
        if generated:
            assert len(generated) == 1, 'Unexpected additional generated engine request'
            main_request = generated[0]
            row.setdefault('request_physical_read_mb', {})[side] = main_request.get('physical_read_mb')
            row.setdefault('kv_vram_hit_pct', {})[side] = main_request.get('kv_vram_hit_pct')
            if phase['scored'] and phase.get('verdict') == 'PASS':
                assert main_request['prompt_tokens'] == (126967 if side == 'a' else 126968) and main_request['reused'] == 0
        row['engine_notes'][side] = [line for line in notes if line.startswith(('strata', 'FileExpertSource:')) and any(
            term in line.lower() for term in ('draft', 'cache', 'mmap', 'prefill', 'windows', 'worker', 'kv streaming',
                                             'vram', 'sm_70', 'wmma', 'simt', 'expert', 'timing', 'default'))]
        if row['processes'].get(side, {}).get('args', []).count('dflash2'):
            effective = row['processes'][side]['args']
            assert '--mtp' not in effective and effective[effective.index('--draft-fallback') + 1] == 'none'
            offered = row['request_metrics'].get(side, {}).get('drafts_offered')
            accepted = row['request_metrics'].get(side, {}).get('drafts_accepted')
            suffix = re.findall(r'suffix drafts: (\d+) windows, (\d+) of (\d+) drafts accepted', '\n'.join(notes))
            suffix_accepted, suffix_offered = (int(suffix[-1][1]), int(suffix[-1][2])) if suffix else (0, 0)
            assert not any('lookup chain:' in line for line in notes), 'Cannot infer separate drafter counters with a chained lookup'
            if isinstance(offered, int) and isinstance(accepted, int):
                # generate.cpp counts suffix proposals separately; without MTP/fallback
                # or lookup-chain, every remaining proposal is from DFlash2.
                activity = dict(total_offered=offered, total_accepted=accepted, suffix_offered=suffix_offered,
                                suffix_accepted=suffix_accepted, dflash2_offered=offered - suffix_offered,
                                dflash2_accepted=accepted - suffix_accepted,
                                method='Engine DONE totals minus explicitly logged suffix proposals; no MTP or lookup-chain')
                row.setdefault('dflash2_activity', {})[side] = activity
        row.setdefault('draft_verify_timing', {})[side] = {
            'lines': [line for line in notes if 'decode timing:' in line or 'window cost (' in line],
            'limitation': 'Separate draft/verify timing is emitted only with profiling enabled; scored arms retain the frozen unprofiled recipe.'}
    for when in ('before', 'after'):
        for filename, key in ((f'cache-{when}.json', f'page_cache_{when}'), (f'health-{when}-a.json', f'health_{when}_a'), (f'health-{when}-b.json', f'health_{when}_b')):
            if (d / filename).exists():
                row[key] = load(d / filename)
    if (d / 'host-telemetry.jsonl').exists():
        host = [json.loads(line) for line in (d / 'host-telemetry.jsonl').read_text().splitlines()]
        if host:
            row['host_full_lifetime'] = {
                'sample_count': len(host),
                'ram_unavailable_gib': stats([(r['memory']['MemTotal'] - r['memory']['MemAvailable']) / 2**30 for r in host]),
                'ram_available_gib': stats([r['memory']['MemAvailable'] / 2**30 for r in host]),
                'kernel_cached_gib': stats([r['memory']['Cached'] / 2**30 for r in host]),
                'swap_used_gib': stats([(r['memory']['SwapTotal'] - r['memory']['SwapFree']) / 2**30 for r in host]),
                'cpu': cpu_usage(host[0]['cpu_ticks'], host[-1]['cpu_ticks'], ['cpu']),
                'cpuset_a': cpu_usage(host[0]['cpu_ticks'], host[-1]['cpu_ticks'], ['cpu' + str(i) for i in (0, 1, 2, 6, 7, 8)]),
                'cpuset_b': cpu_usage(host[0]['cpu_ticks'], host[-1]['cpu_ticks'], ['cpu' + str(i) for i in (3, 4, 5, 9, 10, 11)]),
            }
    before, after = d / 'vmstat-before.txt', d / 'vmstat-after.txt'
    if before.exists() and after.exists():
        v0, v1 = [{k: int(v) for k, v in (line.split() for line in f.read_text().splitlines())} for f in (before, after)]
        row['host_vmstat_delta'] = {k: v1[k] - v0[k] for k in ('pgmajfault', 'pswpin', 'pswpout', 'pgpgin', 'pgpgout')}
    return row


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('raw', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    assert not a.output.exists(), 'Exports are immutable'
    progress = load(a.raw / 'progress.json')
    phases = [phase_receipt(a.raw, r) for r in progress['batches']]
    passed = [r for r in phases if r['phase']['scored'] and r['phase'].get('verdict') == 'PASS' and 'summary' in r]
    complete = len(passed) == 3 and progress['verdict'] == 'PASS' and progress.get('owned_containers_stopped')
    if progress['arm'] == 'S9-D1':
        for phase in passed:
            for side in 'ab':
                counters = phase['dflash2_activity'][side]
                assert counters['dflash2_offered'] > 0, 'No actual DFlash2 proposals'
                assert 0 <= counters['dflash2_accepted'] <= counters['dflash2_offered']
    medians = {metric: {s: st.median(r['summary']['requests'][i][metric] for r in passed) for i, s in enumerate('ab')}
               for metric in ('prefill_tok_s', 'decode_tok_s', 'ttft_s')} if complete else {}
    ranges = {metric: {s: [min(r['summary']['requests'][i][metric] for r in passed), max(r['summary']['requests'][i][metric] for r in passed)]
                       for i, s in enumerate('ab')} for metric in medians}
    result = dict(progress=progress, phases=phases, valid_batches=len(passed), medians=medians, ranges=ranges,
                  status='3/3 C2 PASS' if complete else f'INCOMPLETE {len(passed)}/3 PASS',
                  decode_30_each_batch_both_agents=bool(complete and all(q['decode_tok_s'] >= 30 for r in passed for q in r['summary']['requests'])))
    lines = [f"# {progress['arm']} — {progress['id']}", '', '**' + result['status'] + '**', '',
             f"Source `{progress['source_sha']}`; image `{progress['image_id']}`; binary `{progress['engine_sha256']}`.", '',
             '| Phase | Scored | Verdict | Prefill A/B | Decode A/B | TTFT A/B s | Output A/B | Overlap s |',
             '|---|---|---|---:|---:|---:|---:|---:|']
    for r in phases:
        ph = r['phase']
        if 'summary' in r:
            x, y = r['summary']['requests']
            pair = lambda key, fmt: f'{x[key]:{fmt}} / {y[key]:{fmt}}'
            lines.append(f"| {ph['id'].removeprefix(progress['id'] + '-')} | {ph['scored']} | {ph.get('verdict')} | {pair('prefill_tok_s', '.1f')} | {pair('decode_tok_s', '.1f')} | {pair('ttft_s', '.2f')} | {pair('output_tokens', 'd')} | {r['summary']['decode_overlap_s']:.2f} |")
        else:
            lines.append(f"| {ph['id'].removeprefix(progress['id'] + '-')} | {ph['scored']} | {ph.get('verdict')} | — | — | — | — | — |")
    if medians:
        lines += ['', '| Median | A | B |', '|---|---:|---:|']
        for key, values in medians.items():
            lines.append(f"| {key} | {values['a']:.2f} | {values['b']:.2f} |")
    lines += ['', 'All three scored batches are retained; startup is unscored. Original IQ3_XXS/native pack, independent single GPUs, CPU affinities, 131072 context and INT8 KV are preserved.', '',
              'GPU/host lifetime statistics include loading, built-in post-response idle-prefill and shutdown; they are not decode-only measurements. Decode-free GEN 0 records are separated from the sole scored generated request for physical I/O and KV reporting. They are not a second HTTP/C2 request; fresh processes prevent their prefix from being reused by the next scored batch. RAM unavailable is MemTotal minus MemAvailable. Raw GPU/host/vmstat/iostat series remain backed up. Draft/verify component timings unavailable without profiling are explicitly marked in receipts.', '',
              'Historical S7/S8 comparisons are descriptive because clock, temperature, cache, swap and output conditions vary. Mechanical C2 PASS is not semantic-quality validation or production promotion.', '']
    if progress.get('error'):
        lines += ['Recorded error: `' + progress['error'] + '`', '']
    a.output.mkdir(parents=True)
    (a.output / 'receipts.json').write_text(json.dumps(result, indent=2) + '\n')
    (a.output / 'report.md').write_text('\n'.join(lines))
    print(json.dumps({k: result[k] for k in ('status', 'valid_batches', 'medians', 'decode_30_each_batch_both_agents')}, indent=2))


if __name__ == '__main__':
    main()
