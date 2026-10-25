"""Native pipe tests only. No real sensor module is constructed or called."""
import ctypes as ct
import json
import os
from pathlib import Path
import queue
import secrets
import subprocess
import sys
import threading
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from monitoring.winpipe import WindowsPipeApi
from monitoring.pipe_protocol import pipe_name
from monitoring.ipc import MAX_REQUEST_BYTES, MAX_RESPONSE_BYTES
from monitoring.development_gate import source_hashes


def main():
    api=WindowsPipeApi();stop=threading.Event();checks=[]
    def check(value,label):
        if not value:raise AssertionError(label)
        checks.append(label)
    name=pipe_name(secrets.token_hex(16));handle=api.create_server(name)
    try:
        security=api.inspect_dacl(handle);check(security['account_only'] and security['protected'],'Native DACL inspected: protected account-only ACE')
        try:duplicate=api.create_server(name)
        except OSError:check(True,'FIRST_PIPE_INSTANCE rejects occupied endpoint')
        else:api.close(duplicate);raise AssertionError('Duplicate endpoint created')
    finally:api.close(handle)
    again=api.create_server(name);api.close(again);check(True,'Endpoint reusable only after owner closes handle')
    session=secrets.token_hex(16)
    proc=subprocess.Popen([sys.executable,'-I','-B',str(ROOT/'scripts/monitoring-pipe-client.py'),
                           '--session',session,'--duration','15','--simulated'],cwd=ROOT,
                          stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          creationflags=0x08000000,bufsize=0)
    lines=queue.Queue()
    def read():
        for line in iter(proc.stdout.readline,b''):lines.put(json.loads(line))
    threading.Thread(target=read,daemon=True).start()
    try:
        ready=lines.get(timeout=8);check(ready.get('event')=='ready' and ready['simulated'],'Fixed bridge and collector ready with simulated provider')
        worker=api.hold_process(ready['collector_pid']);identity=api.identity(worker)
        bridge=api.hold_process(ready['bridge_pid'])
        try:
            # Connect as an unexpected PID under the same account: server must reject before serving data.
            unauthorized=api.connect(pipe_name(session),worker,identity,time.monotonic()+2,stop)
            try:
                try:
                    api.write_frame(unauthorized,b'{"v":1,"op":"snapshot"}',MAX_REQUEST_BYTES,time.monotonic()+1,stop)
                    api.read_frame(unauthorized,MAX_RESPONSE_BYTES,time.monotonic()+1,stop)
                except OSError:check(True,'Unexpected same-account process receives no cache data')
                else:raise AssertionError('Unexpected PID authorized')
            finally:api.close(unauthorized)
            # A request via the spawned, attested bridge must succeed after that rejection.
            for index in range(3):
                proc.stdin.write(b'{"v":1,"op":"snapshot"}\n');proc.stdin.flush()
                message=lines.get(timeout=4)
                check(message.get('event')=='response' and message['body']['ok'],'Read/reconnect '+str(index+1))
                check(message['body']['snapshot']['contains_simulated'] is True,'Native wire cannot present fixture as real '+str(index+1))
                time.sleep(0.55)
            # Wrong server attestation fails even if the actual server has the same account.
            wrong={**identity,'created':identity['created']+1}
            try:bad=api.connect(pipe_name(session),worker,wrong,time.monotonic()+1,stop)
            except PermissionError:check(True,'Wrong server creation identity rejected')
            else:api.close(bad);raise AssertionError('Server identity bypass')
        finally:api.close(worker);api.close(bridge)
    finally:
        proc.stdin.close()
        code=proc.wait(timeout=8)
    final=lines.get(timeout=2)
    check(final['event']=='stopped' and final['clean'] and code==0,'Lifetime EOF stops bridge and collector normally')
    check(final['worker']['stop']=={'clean':True,'stopped':True,'timed_out':False},'Collector cooperative stop confirmed')
    # Both endpoint handles and workers have been released, without process termination APIs.
    end=api.create_server(pipe_name(session));api.close(end);check(True,'Endpoint released after normal shutdown')
    report={'ok':True,'checks':len(checks),'cases':checks,'simulated':True,'real_sensors':False,
            'native_pipe_exercised':True,'other_account_runtime_tested':False,'acl':security,
            'bridge_exit_code':code,'worker_result':final['worker']}
    report['source_hashes']=source_hashes(ROOT)
    out=ROOT/'.cache/validation/monitoring-electron-2026-10-25';out.mkdir(parents=True,exist_ok=True)
    (out/'native-pipe-tests.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='source_hashes'}))


if __name__=='__main__':main()
