"""Explicit, bounded, one-shot development session. Never used by installed Electron.

Measures only the session's known process tree; never controls an existing process.
No sensor API in this observer, no socket/IPC server, no automatic repetition/kill.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import statistics
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from monitoring.winpipe import WindowsPipeApi, ticks
from ctypes import wintypes as w
import ctypes as ct


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--real-once',action='store_true');args=parser.parse_args()
    folder=ROOT/'.cache/validation/monitoring-electron-2026-10-25';folder.mkdir(parents=True,exist_ok=True)
    mode='physical' if args.real_once else 'simulated';out=folder/mode;out.mkdir(exist_ok=True)
    if args.real_once:
        approval=json.loads((folder/'physical-gate.json').read_text())
        assert approval.get('ok') is True and approval.get('agentIdentityVerified') is True
        for name,digest in approval['source_hashes'].items():
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,'Gate source changed'
        assert json.loads((folder/'simulated/electron-result.json').read_text())['ok']
    api=WindowsPipeApi();session=secrets.token_hex(16)
    allowed_images={os.path.normcase(os.path.realpath(ROOT/'apps/windows-ui/node_modules/electron/dist/electron.exe')),
                    os.path.normcase(os.path.realpath(sys.executable))}
    if args.real_once:
        with (folder/'physical-attempt.json').open('x',encoding='utf-8') as f:
            json.dump({'utc':datetime.now(timezone.utc).isoformat(),'runId':session,'maximumSeconds':90},f)
    environment=dict(os.environ);environment.pop('ELECTRON_RUN_AS_NODE',None)
    environment['NODE_OPTIONS']='--require="'+(ROOT/'tests/electron-monitoring-bootstrap.cjs').as_posix()+'"'
    environment['LONE_MONITORING_RUN_ID']=session
    executable=ROOT/'apps/windows-ui/node_modules/electron/dist/electron.exe'
    command=[str(executable),'apps/windows-ui','--lone-development-review','--lone-monitoring-development','--force-device-scale-factor=1']
    if not args.real_once:command.append('--lone-monitoring-simulated')
    started=time.monotonic();started_at=datetime.now(timezone.utc);handles={};identities={};cpu_final={};samples=[];previous={}
    for name in ('stdout.log','stderr.log','electron-result.json','resource-report.json'):
        existing=out/name
        if existing.exists():existing.rename(out/(name+'.previous-'+started_at.strftime('%H%M%S%f')))
    with (out/'stdout.log').open('wb') as stdout,(out/'stderr.log').open('wb') as stderr:
        proc=subprocess.Popen(command,cwd=ROOT,env=environment,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,
                              shell=False,creationflags=0x08000000)
        try:
            while time.monotonic()-started<89:
                metadata=out/'runtime-pids.json'
                try:
                    runtime=json.loads(metadata.read_text())
                    if runtime['mainPid']==proc.pid:
                        for pid in runtime['pids']:
                            if pid not in handles:
                                try:
                                    handle=api.hold_process(pid);identity=api.identity(handle)
                                    if identity['sid']!=api.own['sid'] or identity['session']!=api.own['session'] or identity['elevated']:
                                        api.close(handle);raise PermissionError('Unexpected session process')
                                    if identity['image'] not in allowed_images or identity['created']/10_000_000-11644473600 < started_at.timestamp()-0.5:
                                        api.close(handle);raise PermissionError('Unexpected session image')
                                    handles[pid]=handle;identities[pid]=identity
                                except OSError:pass  # a transient Electron utility process may already have exited.
                except (OSError,ValueError,KeyError):pass
                current={};resident=0;commit=0;interval_cpu=0;now=time.monotonic()
                for pid,handle in handles.items():
                    creation,exit_at,kernel,user=(w.FILETIME() for _ in range(4))
                    if api.k.GetProcessTimes(handle,ct.byref(creation),ct.byref(exit_at),ct.byref(kernel),ct.byref(user)):
                        cpu=(ticks(kernel)+ticks(user))/10_000_000;cpu_final[pid]=cpu
                        if pid in previous:interval_cpu+=max(0,cpu-previous[pid])
                        current[pid]=cpu
                    if api.alive(handle):
                        memory=api.resources(handle);resident+=memory['working_set_bytes'];commit+=memory['private_commit_bytes']
                elapsed=now-started
                samples.append({'elapsed_seconds':elapsed,'process_count':sum(api.alive(h) for h in handles.values()),
                    'working_set_sum_bytes':resident,'private_commit_sum_bytes':commit,
                    'interval_cpu_seconds':interval_cpu,'cpu_total_percent':interval_cpu/(now-last_time)/os.cpu_count()*100 if previous else None})
                previous=current;last_time=now
                if proc.poll() is not None and all(not api.alive(h) for h in handles.values()):break
                time.sleep(1)
            elapsed=time.monotonic()-started
            residual=[pid for pid,h in handles.items() if api.alive(h)]
            result_path=out/'electron-result.json'
            result=json.loads(result_path.read_text()) if result_path.exists() else {'ok':False,'error':'missing_result'}
            complete=proc.poll() is not None and not residual and bool(result.get('ok')) and result.get('runId')==session
            data={'ok':complete,'real_sensors':args.real_once,'session_id':session,'started_at':started_at.isoformat(),
                'elapsed_seconds':elapsed,'electron_exit_code':proc.poll(),'residual_pids':residual,'processes_seen':len(handles),
                'logical_processors':os.cpu_count(),'cpu_seconds_sum':sum(cpu_final.values()),
                'average_cpu_total_percent':sum(cpu_final.values())/elapsed/os.cpu_count()*100,
                'memory_method':'sum_working_sets_may_double_count_shared_pages','samples':samples,
                'cpu_method':'GetProcessTimes kernel+user of observed session processes since creation, divided by wall time and logical CPUs',
                'new_network_listener':False,'process_control_used':False,'forced_shutdown':False,'repeated_real_session':False}
            (out/'resource-report.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
            print(json.dumps({k:v for k,v in data.items() if k!='samples'}))
            return 0 if complete and elapsed<90 else 1
        finally:
            for handle in handles.values():api.close(handle)
            # No terminate/kill/retry, including failure or deadline: report failure and leave authorization decision to user.


if __name__=='__main__':raise SystemExit(main())
