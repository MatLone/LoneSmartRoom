"""Explicit once-only development transport session. No production startup/repair.

Owns one temporary loopback HTTPS identity, one existing pipe intermediary and
one collector/ADLX bridge. Requests normal EOF shutdown only. No Electron launch.
"""
from datetime import datetime, timezone
import hashlib
import hmac
import http.client
import json
import os
from pathlib import Path
import queue
import secrets
import ssl
import statistics
import subprocess
import sys
import threading
import time

ROOT=Path(__file__).resolve().parents[1]
PHASE=ROOT/'.cache/telemetry-homologation-preparation-2026-10-27'
sys.path[:0]=[str(ROOT),str(ROOT/'agent/windows')]


class OwnedTransport:
    physical=True
    def __init__(self, state, device, api):
        self.state,self.device,self.api=state,device,api
        self.messages=queue.Queue(maxsize=16);self.events=[];self.resources=[];self.handles={}
        self.ready=None;self.port=None;self.process=None;self.stop_record=None;self.invalid_lines=False
        self.pin=None;self.context=None;self.stdin_closed=False
        self.last_resources=0
        self.thread=None
        self.snapshot_pending=False
        self.telemetry_diagnostics=None

    def start(self, session):
        from secure_tls import fingerprint
        self.pin=fingerprint(self.state)
        self.context=ssl.create_default_context(cafile=str(self.state/'server.crt'))
        self.context.minimum_version=ssl.TLSVersion.TLSv1_3
        home=next(line.split('=',1)[1].strip() for line in (ROOT/'.venv/pyvenv.cfg').read_text().splitlines() if line.startswith('home'))
        python=Path(home)/'python.exe'
        self.python_image=os.path.normcase(os.path.realpath(python));self.started_at=time.time()
        env={k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','TEMP','TMP','PATH')}
        self.error_file=(self.state/'transport-stderr.log').open('xb')
        self.process=subprocess.Popen([str(python),'-I','-S','-B',str(ROOT/'scripts/monitoring-telemetry-client.py'),
            '--session',session,'--duration','50','--gpu-development'],cwd=ROOT,shell=False,env=env,
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.error_file,creationflags=0x08000000,bufsize=0)
        self.hold(self.process.pid,'intermediary')
        def output():
            while True:
                line=self.process.stdout.readline(132098)
                if not line:break
                if len(line)>132097 or not line.endswith(b'\n'):self.invalid_lines=True;break
                try:self.messages.put_nowait(json.loads(line))
                except (ValueError,queue.Full):self.invalid_lines=True;break
        self.thread=threading.Thread(target=output,daemon=True);self.thread.start()
        deadline=time.monotonic()+10
        while time.monotonic()<deadline and self.alive() and (self.port is None or self.ready is None):
            self.drain();time.sleep(.05)
        if self.port is None or self.ready is None:raise ValueError('bootstrap_failed')

    def hold(self,pid,kind):
        if pid in self.handles:return
        handle=self.api.hold_process(pid);identity=self.api.identity(handle)
        if (identity['sid']!=self.api.own['sid'] or identity['session']!=self.api.own['session'] or identity['elevated']
                or identity['image']!=self.python_image or identity['created']/10000000-11644473600<self.started_at-.1):
            self.api.close(handle);raise ValueError('unexpected_owned_identity')
        self.handles[pid]=(handle,kind)

    def drain(self):
        while True:
            try:value=self.messages.get_nowait()
            except queue.Empty:break
            event=value.get('event')
            if event=='telemetry_ready':
                if self.port is not None or value.get('host')!='127.0.0.1' or type(value.get('port')) is not int or not 1024<=value['port']<=65535:
                    raise ValueError('invalid_discovery')
                self.port=value['port']
            elif event=='ready':
                if self.ready is not None or value.get('simulated') is not False or value.get('transport')!='windows_named_pipe_v1':raise ValueError('unexpected_pipe_ready')
                self.ready=value;self.hold(value['collector_pid'],'collector')
            elif event=='stopped':self.stop_record=value
            elif event in ('error','shutdown_pending','disconnected'):
                self.events.append(event);self.snapshot_pending=False
            elif event=='response':
                self.snapshot_pending=False
                if value.get('body',{}).get('ok') is not True:self.events.append('snapshot_error')
            elif event=='telemetry_diagnostics':
                rules={None,'inconsistent_capacity','inconsistent_occupation','inconsistent_vram','invalid_provenance',
                    'invalid_timestamp','expired_snapshot','invalid_interval','unexpected_source','invalid_adlx_ingress',
                    'future_sample','missing_sample','null_required','unexpected_metric','unexpected_unit','invalid_state','invalid_snapshot'}
                if (set(value)!={'v','event','accepted','rejected','last_rule'} or value['v']!=1
                        or any(type(value[k]) is not int or not 0<=value[k]<=1000 for k in ('accepted','rejected'))
                        or value['last_rule'] not in rules):raise ValueError('invalid_diagnostic_record')
                self.telemetry_diagnostics={k:value[k] for k in ('accepted','rejected','last_rule')}
        if self.invalid_lines:raise ValueError('invalid_transport_output')
        if time.monotonic()-self.last_resources>=1:
            self.last_resources=time.monotonic()
            for pid,(handle,kind) in self.handles.items():
                if self.api.alive(handle):
                    r=self.api.resources(handle)
                    self.resources.append(dict(pid=pid,component=kind,monotonic=time.monotonic(),**r))

    def alive(self):return self.process is not None and self.process.poll() is None
    def request_snapshot(self):
        if not self.ready:raise ValueError('collector_not_ready')
        if self.snapshot_pending:return
        self.snapshot_pending=True
        self.process.stdin.write(b'{"v":1,"op":"snapshot"}\n');self.process.stdin.flush()

    def read_telemetry(self):
        from secure_protocol import canonical
        path='/v2/telemetry';stamp=str(int(time.time()));nonce=secrets.token_hex(16)
        signature=hmac.new(bytes.fromhex(self.device['secret']),canonical(stamp,nonce,self.device['device_id'],'GET',path,b''),hashlib.sha256).hexdigest()
        headers=dict(zip(('X-Lone-Device','X-Lone-Timestamp','X-Lone-Nonce','X-Lone-Signature'),(self.device['device_id'],stamp,nonce,signature)))
        connection=http.client.HTTPSConnection('127.0.0.1',self.port,context=self.context,timeout=2)
        started=time.monotonic()
        try:
            connection.connect()
            if hashlib.sha256(connection.sock.getpeercert(binary_form=True)).hexdigest()!=self.pin:raise ValueError('pin_mismatch')
            tls=connection.sock.version();connection.request('GET',path,headers=headers);r=connection.getresponse();raw=r.read(32769)
            if r.status!=200 or len(raw)>32768:raise ValueError('bounded_https_read_failed')
            body=json.loads(raw)
            if body.get('ok') is not True or body.get('telemetry_version')!=1:raise ValueError('invalid_envelope')
            if body.get('snapshot') is not None:
                from telemetry.contract import project
                project(body['snapshot'],simulation=False)
            return dict(ok=True,received_at=datetime.now(timezone.utc).isoformat(),tls=tls,pin_verified=True,
                hostname_verified=True,transport_seconds=time.monotonic()-started,body=body)
        finally:connection.close()

    def close(self):
        if self.process is None:
            if hasattr(self,'error_file'):self.error_file.close()
            return True
        if not self.stdin_closed:
            self.process.stdin.close();self.stdin_closed=True
        deadline=time.monotonic()+10
        while self.process.poll() is None and time.monotonic()<deadline:
            try:self.drain()
            except (ValueError,OSError):self.invalid_lines=True
            time.sleep(.05)
        try:self.drain()
        except (ValueError,OSError):self.invalid_lines=True
        if self.process.poll() is not None:
            if self.thread is not None:self.thread.join(timeout=1)
            self.process.stdout.close()
        self.error_file.close()
        return not self.invalid_lines and self.process.poll()==0 and bool(self.stop_record and self.stop_record.get('clean'))

    def finish(self):
        residual=[pid for pid,(h,_) in self.handles.items() if self.api.alive(h)]
        for handle,_ in self.handles.values():self.api.close(handle)
        return dict(residual_pids=residual,events=self.events,stop=self.stop_record,resources=self.resources,
            telemetry_diagnostics=self.telemetry_diagnostics,loopback_port=self.port,intermediary_pid=self.process.pid if self.process else None)


def main():
    if sys.argv[1:]!=['--real-once']:raise ValueError('explicit_once_required')
    if (PHASE/'REAL-SESSION-CONSUMED.json').exists():raise ValueError('physical_session_already_consumed')
    gate=json.loads((PHASE/'real-session-gate.json').read_text())
    if gate.get('ok') is not True:raise ValueError('gates_required')
    for name,digest in gate['source_hashes'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise ValueError('tested_source_changed')
    from monitoring.winpipe import WindowsPipeApi
    from launcher_win32 import Windows
    from secure_store import DPAPI
    from secure_protocol import Store
    from secure_tls import create_identity
    from telemetry.validation import run_observation
    api=WindowsPipeApi();security=Windows();session=secrets.token_hex(16)
    parent=ROOT/'.cache/telemetry-development';parent.mkdir(exist_ok=True)
    state=parent/session;security.private_directory(state)
    protector=DPAPI();scratch=state/'generated-identity';security.private_directory(scratch)
    create_identity(scratch,'127.0.0.1',protector)
    for name in ('server.crt','server.key','tls.dpapi'):
        security.private_file(state/name);(state/name).write_bytes((scratch/name).read_bytes())
    for name in ('DEVELOPMENT-TELEMETRY','devices.db','telemetry-readers.json') :security.private_file(state/name)
    (state/'DEVELOPMENT-TELEMETRY').write_bytes(b'LSR-TELEMETRY-DEV-LOOPBACK-v1\n')
    store=Store(state/'devices.db',protector);token,_=store.begin_pairing();device=store.pair(token,'Loopback telemetry validation')
    (state/'telemetry-readers.json').write_text(json.dumps([device['device_id']]),encoding='ascii')
    marker=PHASE/'REAL-SESSION-CONSUMED.json'
    with marker.open('x',encoding='utf-8') as f:json.dump({'started_at':datetime.now(timezone.utc).isoformat(),'observation_seconds':30,'run_id':session},f)
    transport=OwnedTransport(state,device,api);started=time.monotonic();result={}
    try:
        transport.start(session)
        result=run_observation(transport,now=time.monotonic,wait=time.sleep,duration=30)
    except Exception:
        result=dict(v=1,reason='bootstrap_failed',clean_stop=transport.close(),records=[],forced_shutdown=False,repeated=False,physical=True)
    finally:
        result.update(transport.finish());result['total_elapsed_seconds']=time.monotonic()-started
        # Revoke only the temporary DEV read identity, never production state/grants.
        store.revoke(device['device_id']);(state/'telemetry-readers.json').write_text('[]',encoding='ascii')
        result['temporary_read_identity_revoked']=True;result['production_agent_modified']=False
        (PHASE/'real-transport-result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    summary={k:v for k,v in result.items() if k not in ('records','resources','stop')}
    summary['https_reads']=len(result['records']);print(json.dumps(summary))
    return 0 if result.get('clean_stop') and not result['residual_pids'] and result.get('transport_validated') is True else 1

if __name__=='__main__':raise SystemExit(main())
