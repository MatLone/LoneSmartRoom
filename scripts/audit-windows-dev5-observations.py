"""Offline reanalysis of committed dev.5 telemetry, UI markers and sanitized logs.

No live process, driver, sensor, IPC, network or Electron operation.
Mode windows are estimates from observations, NOT independent visibility traces.
"""
from datetime import datetime,timedelta,timezone
import json
from pathlib import Path
import re
import statistics

ROOT=Path(__file__).resolve().parents[1]


def analyze(resources,events,logs):
    start=datetime.fromisoformat(resources['startedUtc']);duration=resources['elapsedSeconds']
    markers={e['name']:(datetime.fromisoformat(e['utc'].replace('Z','+00:00'))-start).total_seconds() for e in events}
    dashboard=markers['02-dashboard-controles'];widget=markers['08-widget-monitoramento'];hidden=markers['explicit-hide-to-tray-clicked']
    phases={}
    for label,low,high in [('startup_and_initial_widget',0,dashboard),('observed_dashboard',dashboard,widget),
            ('observed_widget',widget,hidden),('after_hide_including_manual_restore_and_exit',hidden,duration)]:
        samples=[s for s in resources['samples'] if s['interval_seconds'] and low<=s['elapsed_seconds']-s['interval_seconds'] and s['elapsed_seconds']<=high and s['alive_pids']]
        seconds=sum(s['interval_seconds'] for s in samples)
        groups={}
        for group in ('collector','ipc','electron'):
            groups[group]={'cpuPercentOfMachine':sum(s['groups'][group]['cpu_delta_seconds'] for s in samples)/seconds/resources['logicalProcessors']*100 if seconds else None,
                'rssMeanMiB':statistics.mean(s['groups'][group]['working_set_bytes']/1024**2 for s in samples) if samples else None}
        phases[label]={'boundsSeconds':[low,high],'sampledSeconds':seconds,'samples':len(samples),'groups':groups}
    crashes=[]
    for line in logs['lines']:
        m=re.match(r'\[(\d{2})(\d{2})/(\d{2})(\d{2})(\d{2})\.(\d{3}):',line)
        if not m:continue
        month,day,hour,minute,second,ms=map(int,m.groups())
        stamp=datetime(start.year,month,day,hour,minute,second,ms*1000,tzinfo=timezone(timedelta(hours=-3)))
        delta=(stamp-start).total_seconds();crashes.append({'utc':stamp.astimezone(timezone.utc).isoformat(),
            'afterStartSeconds':delta,'beforeEndSeconds':duration-delta,'originCrashpad':'registration_protocol_win.cc' in line,'code':'0xE9' if '(0xE9)' in line else None})
    total=resources['stats']['total']['cpuMeanPercentOfMachine'];electron=resources['stats']['electron']['cpuMeanPercentOfMachine']
    return {'electronShareOfComponentCpuPercent':100*electron/total,'modeWindowsEstimatedNotVisibilityTrace':True,
        'phases':phases,'crashpadMessages':crashes,'messageGapSeconds':crashes[1]['afterStartSeconds']-crashes[0]['afterStartSeconds'] if len(crashes)==2 else None,
        'equivalentIdleComparisonAvailable':False,'liveSessionRun':False}


def main():
    folder=ROOT/'docs/windows-first-run-dev5-2026-10-25/evidence'
    resources=json.loads((folder/'resources.json').read_text());events=[json.loads(line) for line in (folder/'ui-observations.jsonl').read_text().splitlines()]
    logs=json.loads((folder/'electron-log-sanitized.json').read_text())
    result=analyze(resources,events,logs)
    out=ROOT/'.cache/validation/adlx-preparation-2026-10-25';out.mkdir(parents=True,exist_ok=True)
    (out/'dev5-observations-analysis.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))


if __name__=='__main__':main()
