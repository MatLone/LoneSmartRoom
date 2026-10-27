"""Windows process/ACL/pipe integration with EXPLICITLY SIMULATED metrics only.

No operational agent, collector, GPU DLL, credentials or port 8776 is accessed.
The child is a cache publisher; parent owns HTTPS. Stdin EOF is the only stop.
"""
import hashlib
import hmac
import http.client
import json
import os
from pathlib import Path
import queue
import secrets
import ssl
import subprocess
import sys
import tempfile
import threading
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'agent/windows'),str(ROOT/'tests')]
from monitoring.winpipe import WindowsPipeApi
from telemetry.broker import SnapshotBroker
from telemetry.relay import RelayServer,RelayReader
from telemetry_fixtures import snapshot


def publisher(session):
    api=WindowsPipeApi();handle=api.hold_process(os.getppid());identity=api.identity(handle)
    if identity['image']!=api.own['image']:raise PermissionError('unexpected_bootstrap')
    stop=threading.Event();broker=SnapshotBroker(simulation=True)
    raw=snapshot(time.time());broker.publish(raw)
    server=RelayServer(api,broker,session,handle,identity,stop)
    def lifetime():
        sys.stdin.buffer.read(1);stop.set()
    def publish():
        sequence=raw['sequence']
        while not stop.wait(.6):
            sequence+=1;value=snapshot(time.time());value['sequence']=sequence;broker.publish(value)
    threading.Thread(target=lifetime,daemon=True).start()
    feed=threading.Thread(target=publish,daemon=True);feed.start()
    timer=threading.Timer(12,stop.set);timer.start()
    try:
        server.open();print(json.dumps(dict(ready=True,pid=os.getpid(),simulated=True)),flush=True)
        server.serve()
    finally:
        stop.set();timer.cancel();feed.join(timeout=1);server.close();api.close(handle)
    print(json.dumps(dict(stopped=True,counts=server.counts)),flush=True)


def main():
    if sys.argv[1:2]==['--publisher'] and len(sys.argv)==3:
        from telemetry.relay import pipe_name
        pipe_name(sys.argv[2]);publisher(sys.argv[2]);return
    if sys.argv[1:]:raise ValueError('fixed_test_only')
    from telemetry_runtime import TelemetryStatusServer
    from secure_protocol import Store,canonical
    from secure_tls import create_identity,server_context
    from secure_apps import AppRegistry
    from test_remote_telemetry import TestProtector
    api=WindowsPipeApi();session=secrets.token_hex(16);start=time.monotonic();handle=None;reader=None;server=None
    child=subprocess.Popen([sys._base_executable,'-I','-S','-B',str(Path(__file__).resolve()),'--publisher',session],
        cwd=ROOT,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=0x08000000)
    lines=queue.Queue(maxsize=4)
    def read_output():
        for line in iter(child.stdout.readline,b''):
            if len(line)>4096:break
            lines.put_nowait(json.loads(line))
    thread=threading.Thread(target=read_output,daemon=True);thread.start();checks=0
    try:
        ready=lines.get(timeout=4);assert ready==dict(ready=True,pid=child.pid,simulated=True);checks+=1
        handle=api.hold_process(child.pid);identity=api.identity(handle)
        assert identity['image']==api.own['image'] and not identity['elevated'];checks+=1
        reader=RelayReader(api,session,handle,identity,simulation=True)
        with tempfile.TemporaryDirectory(prefix='lsr-native-relay-') as folder:
            state=Path(folder);protector=TestProtector();create_identity(state,'127.0.0.1',protector)
            store=Store(state/'devices.db',protector);token,_=store.begin_pairing();device=store.pair(token,'simulated native relay only')
            server=TelemetryStatusServer(('127.0.0.1',0),server_context(state,protector),store,'127.0.0.0/8',relay=reader,enabled=True,read_devices=[device['device_id']])
            serving=threading.Thread(target=server.serve_forever,daemon=True);serving.start()
            context=ssl.create_default_context(cafile=str(state/'server.crt'))
            def read(auth):
                conn=http.client.HTTPSConnection('127.0.0.1',server.server_port,context=context,timeout=2)
                try:
                    headers={}
                    if auth:
                        stamp=str(int(time.time()));nonce=secrets.token_hex(16)
                        signature=hmac.new(bytes.fromhex(device['secret']),canonical(stamp,nonce,device['device_id'],'GET','/v2/telemetry',b''),hashlib.sha256).hexdigest()
                        headers=dict(zip(('X-Lone-Device','X-Lone-Timestamp','X-Lone-Nonce','X-Lone-Signature'),(device['device_id'],stamp,nonce,signature)))
                    conn.request('GET','/v2/telemetry',headers=headers);response=conn.getresponse();return response.status,json.loads(response.read(32769))
                finally:conn.close()
            assert read(False)[0]==401;checks+=1
            status,body=read(True);assert status==200 and body['snapshot'] is not None;checks+=1
            assert body['snapshot']['contains_simulated'] is True and len(body['snapshot']['metrics'])==29;checks+=1
            assert next(m for m in body['snapshot']['metrics'] if m['id']=='gpu.adlx.fan_rpm')['value']==0;checks+=1
            assert AppRegistry(store).permissions(device['device_id'])==[];checks+=1
            server.shutdown();server.server_close();serving.join(timeout=2);server=None
    finally:
        if server is not None:server.shutdown();server.server_close()
        if reader is not None:reader.close()
        child.stdin.close()
        try:child.wait(timeout=5)
        except subprocess.TimeoutExpired:raise RuntimeError('owned_test_child_shutdown_pending_no_force') from None
        if handle is not None:api.close(handle)
    thread.join(timeout=1);stopped=lines.get(timeout=1)
    assert child.returncode==0 and stopped['stopped'] is True;checks+=1
    assert stopped['counts']['responses']==1 and stopped['counts']['rejected']==0;checks+=1
    # No second producer or credential material in this sanitized receipt.
    result=dict(ok=True,checks=checks,simulated=True,physical_hardware=False,elapsed_seconds=time.monotonic()-start,
        publisher_pid=child.pid,publisher_exited=True,zero_command_grants=True,separate_https_and_publisher_processes=True,native_acl_and_identity_validated=True)
    out=ROOT/'.cache/telemetry-final-integration-2026-10-27';out.mkdir(exist_ok=True)
    (out/'native-relay-test.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()
