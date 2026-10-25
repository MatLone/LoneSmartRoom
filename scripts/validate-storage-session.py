"""One additional storage validation, explicit authorization and exclusive new ledger.

Only instrumentation changes: uses unmodified Electron main, bridge, collector and
providers. No real operations on import. No agent control, termination, retry or load.
"""
import argparse
import ctypes as ct
from ctypes import wintypes as w
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def summary(rows,final_cpu,duration,cores):
    if duration<=0 or cores<=0:raise ValueError('Invalid measurement denominator')
    result={}
    for group in ('collector','ipc','electron','total'):
        readings=[r['groups'][group] for r in rows if r['complete']]
        values=[x['working_set_bytes'] for x in readings]
        result[group]={'cpu_seconds':sum(v['cpu_seconds'] for v in final_cpu.values() if group=='total' or v['group']==group),
          'resident_samples':len(values),'working_set_bytes':{'min':min(values),'mean':sum(values)/len(values),'max':max(values)} if values else None}
        result[group]['average_cpu_total_percent']=result[group]['cpu_seconds']/duration/cores*100
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--authorized-storage-session',action='store_true',required=True);args=parser.parse_args()
    out=ROOT/'.cache/validation/monitoring-storage-2026-10-25'
    gate=json.loads((out/'preflight.json').read_text());assert gate['ok'] and gate['zeroGrants']
    for name,digest in gate['source_hashes'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,'Validated source changed'
    from monitoring.winpipe import WindowsPipeApi,ticks
    api=WindowsPipeApi();session=secrets.token_hex(16);started_at=datetime.now(timezone.utc)
    with (out/'physical-attempt.json').open('x',encoding='utf-8') as f:json.dump({'runId':session,'utc':started_at.isoformat(),'maximumSeconds':90},f)
    env=dict(os.environ);env.pop('ELECTRON_RUN_AS_NODE',None)
    env['NODE_OPTIONS']='--require="'+(ROOT/'tests/electron-storage-bootstrap.cjs').as_posix()+'"';env['LONE_MONITORING_RUN_ID']=session
    electron=ROOT/'apps/windows-ui/node_modules/electron/dist/electron.exe'
    allowed={os.path.normcase(os.path.realpath(electron)),os.path.normcase(os.path.realpath(sys.executable))}
    handles={};roles={};cpu_final={};rows=[];last_cpu={};last_at=None;started=time.monotonic()
    with (out/'stdout.log').open('xb') as stdout,(out/'stderr.log').open('xb') as stderr:
        proc=subprocess.Popen([str(electron),'apps/windows-ui','--lone-development-review','--lone-monitoring-development','--force-device-scale-factor=1'],
          cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,shell=False,creationflags=0x08000000)
        try:
            while time.monotonic()-started<89:
                try:runtime=json.loads((out/'runtime-pids.json').read_text())
                except (OSError,ValueError):runtime={}
                if runtime.get('mainPid')==proc.pid:
                    for group,pids in runtime['groups'].items():
                        for pid in pids:
                            if pid in handles:
                                if roles[pid]!=group:raise ValueError('Process role changed')
                                continue
                            try:
                                handle=api.hold_process(pid)
                                identity=api.identity(handle)
                                if identity['sid']!=api.own['sid'] or identity['session']!=api.own['session'] or identity['elevated'] or identity['image'] not in allowed or identity['created']/1e7-11644473600<started_at.timestamp()-0.5:
                                    api.close(handle);raise PermissionError('Unexpected session process')
                                handles[pid]=handle;roles[pid]=group
                            except PermissionError:raise
                            except OSError:pass  # exited transient utility; never substitute another process.
                now=time.monotonic();groups={k:{'processes':0,'working_set_bytes':0,'private_commit_bytes':0,'interval_cpu_seconds':0} for k in ('collector','ipc','electron')}
                for pid,handle in handles.items():
                    role=roles[pid];creation,exit_at,kernel,user=(w.FILETIME() for _ in range(4))
                    if api.k.GetProcessTimes(handle,ct.byref(creation),ct.byref(exit_at),ct.byref(kernel),ct.byref(user)):
                        cpu=(ticks(kernel)+ticks(user))/1e7;cpu_final[pid]={'group':role,'cpu_seconds':cpu}
                        if pid in last_cpu:groups[role]['interval_cpu_seconds']+=max(0,cpu-last_cpu[pid])
                        last_cpu[pid]=cpu
                    if api.alive(handle):
                        usage=api.resources(handle);groups[role]['processes']+=1
                        groups[role]['working_set_bytes']+=usage['working_set_bytes'];groups[role]['private_commit_bytes']+=usage['private_commit_bytes']
                groups['total']={k:sum(g[k] for g in groups.values()) for k in next(iter(groups.values()))}
                for group,g in groups.items():g['cpu_total_percent']=g['interval_cpu_seconds']/(now-last_at)/os.cpu_count()*100 if last_at is not None else None
                rows.append({'elapsed_seconds':now-started,'complete':all(groups[k]['processes']>0 for k in ('collector','ipc','electron')),'groups':groups});last_at=now
                if proc.poll() is not None and all(not api.alive(h) for h in handles.values()):break
                time.sleep(1)
            elapsed=time.monotonic()-started;residual=[pid for pid,h in handles.items() if api.alive(h)]
            try:ui=json.loads((out/'electron-result.json').read_text())
            except (OSError,ValueError):ui={'ok':False}
            report={'ok':proc.poll()==0 and not residual and ui.get('ok') is True and ui.get('runId')==session and elapsed<=90,
              'runId':session,'started_at':started_at.isoformat(),'elapsed_seconds':elapsed,'logical_processors':os.cpu_count(),
              'exit_code':proc.poll(),'residual_pids':residual,'pids_by_component':{g:[pid for pid,role in roles.items() if role==g] for g in ('collector','ipc','electron')},
              'components':summary(rows,cpu_final,elapsed,os.cpu_count()),'samples':rows,
              'method':'GetProcessTimes cumulative kernel+user since creation / session wall time / logical CPUs * 100; working sets summed, shared pages may repeat',
              'observer_excluded':True,'processes_forced':False,'real_session_repeated':False}
            (out/'resources.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
            print(json.dumps({k:v for k,v in report.items() if k!='samples'}));return 0 if report['ok'] else 1
        finally:
            for handle in handles.values():api.close(handle)
            # No terminate/kill/retry, including failure or timeout.


if __name__=='__main__':raise SystemExit(main())
