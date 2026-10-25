"""Explicit one-attempt GPU session. No GUI, network, registry, controls or restart."""
import argparse
import ctypes as ct
from ctypes import wintypes as w
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import threading
import sqlite3

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from monitoring.adlx_bridge import real_adapter
from monitoring.adlx_session import run_session
from monitoring.collector import Clock
from monitoring.windows_native import WindowsReadApi,ProcessMemory,ticks,check

OUT=ROOT/'.cache/validation/adlx-native-2026-10-25'


class Resources:
    def __init__(self,api,adapter):self.api=api;self.adapter=adapter
    def logical_processors(self):return self.api.logical_processors()
    def collector(self):return self.api.own_resources()
    def bridge_cpu(self):
        handle=w.HANDLE(int(self.adapter.transport.process._handle))
        creation,exit_time,kernel,user=(w.FILETIME() for _ in range(4))
        check(self.api.kernel.GetProcessTimes(handle,ct.byref(creation),ct.byref(exit_time),ct.byref(kernel),ct.byref(user)))
        return (ticks(kernel)+ticks(user))/10_000_000
    def bridge(self):
        handle=w.HANDLE(int(self.adapter.transport.process._handle));memory=ProcessMemory();memory.cb=ct.sizeof(memory)
        check(self.api.kernel.K32GetProcessMemoryInfo(handle,ct.byref(memory),ct.sizeof(memory)))
        return {'cpu_seconds':self.bridge_cpu(),'working_set_bytes':memory.working_set,'private_commit_bytes':memory.private_commit}


def gate():
    for name in ('bridge-tests.json',):
        receipt=json.loads((OUT/name).read_text());assert receipt['ok'] and not receipt['realADLXLoaded']
        for rel,digest in receipt['sourceHashes'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==digest,'Tests no longer match sources'
    source=ROOT/'monitoring/adlx_session.py';tests=json.loads((OUT/'session-tests.json').read_text());assert tests['ok']
    assert tests['sourceSha256']==hashlib.sha256(source.read_bytes()).hexdigest()
    before=json.loads((OUT/'physical-agent-before.json').read_text(encoding='utf-8-sig'))
    assert before['identityGatePassed'] and before['listenerPid']==8680 and before['listenerCount']==1 and before['collectorProcesses']==0
    now=datetime.now(timezone.utc)
    assert 0<=(now-datetime.fromisoformat(before['checkedUtc'].replace('Z','+00:00'))).total_seconds()<60,'Agent preflight is stale'
    auth=json.loads((OUT/'authenticated-initial.json').read_text());assert all(r['httpStatus']==200 for r in auth['results'])
    assert auth['results'][1]['allowedApps']==[]
    verified=json.loads((OUT/'runtime-verification.json').read_text());assert verified['ok']
    assert verified['sourceSha256']==hashlib.sha256((ROOT/'native/adlx/bridge.cpp').read_bytes()).hexdigest()
    with sqlite3.connect((ROOT/'.runtime/secure-agent/devices.db').as_uri()+'?mode=ro',uri=True,timeout=.5) as db:
        assert db.execute('PRAGMA quick_check').fetchall()==[('ok',)]
        assert db.execute('SELECT COUNT(*) FROM app_permissions').fetchone()[0]==0
        assert db.execute("SELECT COUNT(*) FROM app_commands WHERE state IN ('accepted','dispatching')").fetchone()[0]==0


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--execute-once',action='store_true');args=parser.parse_args()
    if not args.execute_once:raise SystemExit('Explicit authorized one-session flag required')
    gate();api=WindowsReadApi();api.require_non_elevated()
    adapter=real_adapter();resources=Resources(api,adapter)
    with (OUT/'session-attempt.json').open('x',encoding='utf-8') as stream:
        json.dump({'startedUtc':datetime.now(timezone.utc).isoformat(),'maximumSeconds':90,'plannedCollectionSeconds':70,'retryAllowed':False},stream)
    print('Starting the single authorized GPU session; no GUI or other sensors.',flush=True)
    with (OUT/'session-live.jsonl').open('x',encoding='utf-8') as evidence:
        def save_row(row):
            evidence.write(json.dumps(row,ensure_ascii=False)+'\n');evidence.flush()
        result=run_session(adapter,resources,Clock(),threading.Event().wait,duration=70,on_row=save_row)
    process=adapter.transport.process
    result.update({'bridgePid':process.pid if process else None,'bridgeReturnCode':process.poll() if process else None,
        'bridgeResidual':bool(process and process.poll() is None),'ready':adapter.ready,
        'collectorPid':__import__('os').getpid(),'ipc':'private_inherited_stdio','realGpuSession':True,
        'profileUsed':False,'networkInterfaceCreated':False,'driverOrConfigurationChanged':False})
    (OUT/'session-result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','metrics','resourceSummary','ready')},ensure_ascii=False),flush=True)
    return 0 if result['shutdownClean'] and not result['bridgeResidual'] and result['reason']=='duration_complete' and result['validDynamicMetrics'] else 1


if __name__=='__main__':raise SystemExit(main())
