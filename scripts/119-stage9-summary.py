#!/usr/bin/env python3
"""Consolidate completed Stage 9 receipts with frozen historical references."""
import argparse
import csv
import json
from pathlib import Path
import re
import statistics as st


def distribution(row, key, values):
    values = [v for v in values if isinstance(v, (int, float))]
    if values:
        row[key] = st.median(values)
        row[key + '_min'], row[key + '_max'] = min(values), max(values)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    rows, batches = [], []
    for path in sorted(a.output.glob('*/receipts.json')):
        data = json.loads(path.read_text())
        progress = data['progress']
        phases = [r for r in data['phases'] if r['phase']['scored'] and r['phase'].get('verdict') == 'PASS' and 'summary' in r]
        row = dict(arm=progress['arm'], id=progress['id'], status=data['status'], valid_batches=len(phases),
                   source=progress['source_sha'], image=progress['image_id'], engine_sha256=progress['engine_sha256'],
                   draft_conf=progress.get('draft_conf'), report=str(path.parent.relative_to(a.output) / 'report.md'))
        for i, side in enumerate('ab'):
            for metric in ('prefill_tok_s', 'decode_tok_s', 'ttft_s', 'output_tokens', 'wall_s', 'expert_hit_rate', 'file_mb'):
                distribution(row, metric + '_' + side, [r['summary']['requests'][i].get(metric) for r in phases])
            distribution(row, 'draft_acceptance_pct_' + side, [100 * r['request_metrics'][side]['drafts_accepted'] / r['request_metrics'][side]['drafts_offered']
                for r in phases if r['request_metrics'].get(side, {}).get('drafts_offered')])
            distribution(row, 'kv_vram_hit_pct_' + side, [r.get('kv_vram_hit_pct', {}).get(side) for r in phases])
            active = [r.get('dflash2_activity', {}).get(side) for r in phases]
            active = [v for v in active if v and v['dflash2_offered']]
            distribution(row, 'dflash2_only_acceptance_pct_' + side,
                         [100 * v['dflash2_accepted'] / v['dflash2_offered'] for v in active])
            distribution(row, 'dflash2_only_offered_' + side, [v['dflash2_offered'] for v in active])
            physical = [r.get('request_physical_read_mb', {}).get(side) for r in phases]
            distribution(row, 'engine_physical_read_mb_' + side, physical)
            distribution(row, 'post_response_idle_prefill_count_' + side,
                         [len(r.get('post_response_idle_prefill', {}).get(side, [])) for r in phases])
            for metric in ('temperature_c', 'power_w', 'vram_mib', 'sm_mhz', 'util_pct'):
                gpu = [r['gpu_full_lifetime'][side][metric] for r in phases if side in r['gpu_full_lifetime']]
                if gpu:
                    row[metric + '_mean_' + side] = st.mean(v['mean'] for v in gpu)
                    row[metric + '_peak_' + side] = max(v['peak'] for v in gpu)
        for key in ('pgmajfault', 'pswpin', 'pswpout', 'pgpgin', 'pgpgout'):
            distribution(row, key, [r.get('host_vmstat_delta', {}).get(key) for r in phases])
        host = [r['host_full_lifetime'] for r in phases if r.get('host_full_lifetime')]
        if host:
            row['host_cpu_busy_mean_pct'] = st.mean(h['cpu']['busy_pct'] for h in host if h['cpu'])
            row['host_cpu_user_mean_pct'] = st.mean(h['cpu']['user_pct'] for h in host if h['cpu'])
            row['ram_unavailable_peak_gib'] = max(h['ram_unavailable_gib']['peak'] for h in host)
            row['ram_available_min_gib'] = min(h['ram_available_gib']['min'] for h in host)
            row['swap_used_peak_gib'] = max(h['swap_used_gib']['peak'] for h in host)
        row['decode_30_each_batch_both_agents'] = data['decode_30_each_batch_both_agents']
        if phases:
            row['slower_agent_decode_median'] = min(row.get('decode_tok_s_a', 0), row.get('decode_tok_s_b', 0))
        for r in phases:
            batch = dict(arm=row['arm'], id=r['phase']['id'], overlap_s=r['summary']['decode_overlap_s'])
            for i, side in enumerate('ab'):
                for key in ('prefill_tok_s', 'decode_tok_s', 'ttft_s', 'output_tokens'):
                    batch[key + '_' + side] = r['summary']['requests'][i][key]
            batches.append(batch)
        rows.append(row)
    for skip in sorted(a.output.glob('*-skipped.json')):
        rows.append(json.loads(skip.read_text()))
    order = {'S9-U1': 0, 'S9-D1': 1, 'S9-F1': 2}
    rows.sort(key=lambda r: order.get(r['arm'], 9))
    for name, data in (('summary', rows), ('batches', batches)):
        (a.output / (name + '.json')).write_text(json.dumps(data, indent=2) + '\n')
        fields = list(dict.fromkeys(k for row in data for k in row))
        with (a.output / (name + '.csv')).open('w') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(data)
    def pair(row, metric, digits=1):
        return ' / '.join(f'{row[metric + "_" + s]:.{digits}f}' if metric + '_' + s in row else '—' for s in 'ab')
    lines = ['# Stage 9 results — 2026-11-10', '',
             '| Arm | Valid C2 | Prefill A/B tok/s | Decode A/B tok/s | TTFT A/B s |',
             '|---|---:|---:|---:|---:|',
             '| S7-XXS-14 (archived) | 3/3 historical | 997.6 / 1006.6 | 26.4 / 26.2 | 127.53 / 126.48 |',
             '| S8-C1 (archived) | 3/3 historical | 998.1 / 1007.2 | 26.2 / 28.3 | 127.45 / 126.32 |',
             '| S8-C0 (archived) | 3/3 historical | 997.2 / 1006.3 | 25.6 / 27.9 | 127.57 / 126.42 |']
    for r in rows:
        label = f"[{r['arm']}]({r['report']})" if r.get('report') else r['arm']
        lines.append(f"| {label} | {r.get('valid_batches', 0)}/3 ({r.get('status', 'SKIPPED')}) | {pair(r, 'prefill_tok_s')} | {pair(r, 'decode_tok_s')} | {pair(r, 'ttft_s', 2)} |")
    lines += ['', '| Arm | GPU mean/peak temp °C A/B | GPU mean/peak W A/B | Host CPU user % | RAM unavailable peak GiB |', '|---|---:|---:|---:|---:|']
    for r in rows:
        temp = pair(r, 'temperature_c_mean') + ' / peak ' + pair(r, 'temperature_c_peak')
        power = pair(r, 'power_w_mean', 2) + ' / peak ' + pair(r, 'power_w_peak', 2)
        cpu = f"{r['host_cpu_user_mean_pct']:.1f}" if 'host_cpu_user_mean_pct' in r else '—'
        ram = f"{r['ram_unavailable_peak_gib']:.2f}" if 'ram_unavailable_peak_gib' in r else '—'
        lines.append(f"| {r['arm']} | {temp} | {power} | {cpu} | {ram} |")
    lines += ['', 'GPU means cover each full process lifetime including loading, built-in post-response idle-prefill and shutdown; reported means average the three batch means. The sole generated request supplies physical I/O and KV figures; decode-free GEN 0 events are recorded separately. Scored HTTP requests have no prefix reuse and the next batch starts new processes. RAM unavailable = MemTotal − MemAvailable, sampled each second. Full per-batch data, ranges, draft acceptance, Expert/KV cache, page faults, swap and I/O are in summary.json and linked receipts.', '',
              'Original IQ3_XXS, independent GPU/CPU mapping, 131072 context, INT8 KV and 150 W configured cap remain fixed. User explicitly approved proceeding at 1245 MHz. The host service journal shows a separate clock-policy change after initial inspection, settling at 135–1245 MHz at 17:15:59 before all scored runs; this agent issued no clock/power command. Historical 1110 MHz runs therefore have a different clock envelope. D1 uses stock DFlash2 selector-Q4 with source-derived spec6/conf0.7; U1/F1 use MTP4/min-p0.5. D1 and U1 share the exact same engine image. Fork defaults are part of that fork candidate, with WMMA2 explicitly disabled.', '',
              'Historical S7/S8 references were not rerun. Cross-date cache/swap/output/clock/thermal differences prevent causal version-speedup claims. Decode gains alone do not establish a balanced Prefill/TTFT/power/temperature upgrade. Missing profiling-only draft/verify times are marked, never invented. Mechanical PASS is not semantic-quality validation; no production promotion.', '']
    (a.output / 'summary.md').write_text('\n'.join(lines))
    print(json.dumps([{'arm': r['arm'], 'valid_batches': r.get('valid_batches', 0), 'status': r.get('status')} for r in rows]))


if __name__ == '__main__':
    main()
