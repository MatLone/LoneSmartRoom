"""Offline reduction of previously captured receipts. Does not collect sensors."""
import csv
from datetime import datetime
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.cache/validation/windows-dev8-homologation'
OUT = ROOT / 'docs/windows-dev8-homologation'


def summary(values):
    values = list(values)
    return {'samples': len(values), 'min': min(values), 'mean': statistics.mean(values),
            'max': max(values)} if values else None


def performance(name, valid_cpu):
    rows = [json.loads(s) for s in (CACHE / name).read_text(encoding='utf-8-sig').splitlines()]
    active = [r for r in rows if r['processes']]
    result = {'active_samples': len(active), 'first_utc': active[0]['utc'],
              'last_utc': active[-1]['utc'], 'cpu_valid': valid_cpu,
              'sampling_interval_seconds': summary(b['elapsed']-a['elapsed'] for a,b in zip(rows,rows[1:])),
              'roles': {}}
    for role in ('electron', 'collector', 'ipc', 'adlx', 'total'):
        selected = [(r,[p for p in r['processes'] if role=='total' or p['role']==role]) for r in active]
        rss = [sum(p['rss_bytes'] for p in ps)/1048576 for _,ps in selected]
        weighted = []
        for i,r in enumerate(active):
            ps = selected[i][1]
            complete = ({p['role'] for p in r['processes']} == {'electron','collector','ipc','adlx'}
                        and all(p['cpu_percent_total'] is not None for p in r['processes']))
            if i and complete and ps:
                weighted.append((sum(p['cpu_percent_total'] for p in ps), r['elapsed']-active[i-1]['elapsed']))
        result['roles'][role] = {'rss_mib': summary(rss),
            'maximum_process_count': max(len(ps) for _,ps in selected),
            'cpu_percent_total': {'time_weighted_mean': sum(v*dt for v,dt in weighted)/sum(dt for _,dt in weighted),
                                  'max_sample': max(v for v,_ in weighted)} if valid_cpu and weighted else None}
    return result


def history():
    rows = list(csv.DictReader((CACHE/'real-history.csv').open(encoding='utf-8-sig', newline='')))
    metrics = {}
    for name in sorted({r['metric'] for r in rows}):
        subset = [r for r in rows if r['metric']==name]
        valid = [r for r in subset if r['value'] not in ('','null') and r['state']=='available']
        metrics[name] = {'unit': subset[0]['unit'], 'valid': len(valid), 'total': len(subset),
                         'values': summary(float(r['value']) for r in valid)}
    times = sorted({r['timestamp_utc'] for r in rows})
    intervals = [(datetime.fromisoformat(b.replace('Z','+00:00'))-datetime.fromisoformat(a.replace('Z','+00:00'))).total_seconds()
                 for a,b in zip(times,times[1:])]
    return {'rows': len(rows), 'all_simulation_false': all(r['simulation']=='false' for r in rows),
            'export_snapshot_interval_seconds': summary(intervals), 'metrics': metrics,
            'note': 'Export cadence is not a direct measurement of every underlying sensor sample.'}


if __name__ == '__main__':
    result = {'session1': performance('performance.jsonl', False),
              'session2_first_480_seconds_only': performance('performance-session2.jsonl', True),
              'history': history(),
              'limitations': ['Session 1 CPU invalid due to integer-overload rounding; not used.',
                             'RSS sum includes potentially shared pages; not private memory.',
                             'Session 2 sampling ended at 480 seconds; app remained open beyond the planned limit.']}
    (OUT/'measurements.json').write_text(json.dumps(result,indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v.get('roles',{}).get('total') for k,v in result.items() if isinstance(v,dict)}))
