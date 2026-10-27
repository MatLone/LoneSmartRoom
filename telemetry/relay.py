"""Cache-only Windows pipe between a publisher and one registered HTTPS worker.

Retained peer handles MUST originate in a trusted local bootstrap after its image
and command policy checks. There is no renderer/network registration API; peer
identities are internal inputs, never fields accepted from a pipe read request.
This protects account/session/instance identity, not malicious same-account code.
No collection, native loading or process startup occurs on import.
"""
import json
import re
import secrets
import threading
import time

from monitoring.pipe_protocol import request as monitoring_request
from monitoring.ipc import LocalAccessPolicy
from .contract import MAX_BYTES, project

PREFIX = r'\\.\pipe\LoneSmartRoom.Telemetry.ReadOnly.v1.'
REQUEST = b'{"v":1,"op":"snapshot"}'
MAX_REQUEST = 128


def pipe_name(session):
    if type(session) is not str or not re.fullmatch('[a-f0-9]{32}',session):
        raise ValueError('invalid_relay_session')
    return PREFIX+session


def registered_peer(api, handle, expected):
    actual=api.identity(handle)
    if (not api.alive(handle) or actual!=expected or actual['elevated']
            or any(actual[k]!=api.own[k] for k in ('sid','session'))):
        raise PermissionError('relay_peer_identity')
    return actual


def encode(value):
    data=json.dumps(value,allow_nan=False,separators=(',',':')).encode('utf-8')
    if len(data)>MAX_BYTES:raise ValueError('relay_response_limit')
    return data


class RelayServer:
    """One first-instance handle, one exact reader, no sensor read on requests."""
    def __init__(self,api,broker,session,reader_handle,reader_identity,stop,*,clock=time.monotonic):
        registered_peer(api,reader_handle,reader_identity)
        self.api,self.broker,self.stop=api,broker,stop
        self.reader_handle,self.reader_identity=reader_handle,reader_identity
        self.name=pipe_name(session);self.handle=None;self.clock=clock;self.last=None
        self.counts=dict(responses=0,rejected=0,rate_limited=0)

    def open(self):
        if self.handle is not None:raise ValueError('relay_already_open')
        self.handle=self.api.create_server(self.name)
        try:self.api.inspect_dacl(self.handle)
        except BaseException:self.close();raise

    def serve(self):
        if self.handle is None:raise ValueError('relay_not_open')
        try:
            while not self.stop.is_set() and self.api.alive(self.reader_handle):
                connected=False
                try:
                    self.api.accept(self.handle,self.clock()+.25,self.stop);connected=True
                    self.api.peer(self.handle,self.reader_handle,self.reader_identity,server_side=True)
                    token=self.api.client_token(self.handle)
                    if not LocalAccessPolicy(self.api.own['sid'],self.api.own['session']).allows(token):
                        raise PermissionError('relay_client_token')
                    deadline=self.clock()+1.5
                    payload=self.api.read_frame(self.handle,MAX_REQUEST,deadline,self.stop)
                    if monitoring_request(payload)['op']!='snapshot':raise ValueError('relay_operation')
                    now=self.clock()
                    if self.last is not None and now-self.last<.5:
                        self.counts['rate_limited']+=1
                        raise ValueError('relay_read_rate')
                    self.last=now
                    self.api.write_frame(self.handle,encode(self.broker.read()),MAX_BYTES,deadline,self.stop)
                    if self.api.read_exact(self.handle,1,deadline,self.stop)!=b'\x06':raise ValueError('relay_ack')
                    self.counts['responses']+=1
                except TimeoutError:
                    if connected:self.counts['rejected']+=1
                except (OSError,ValueError):
                    self.counts['rejected']+=1;self.stop.wait(.02)
                finally:
                    if connected:self.api.k.DisconnectNamedPipe(self.handle)
        finally:self.close()

    def close(self):
        if self.handle is not None:
            handle,self.handle=self.handle,None;self.api.close(handle)


class RelayReader:
    """HTTPS-worker source; new connection per read, bounded and fail closed.

    The exact publisher handle is registered by local bootstrap, not the Android.
    No stale fallback on disconnect. Caller retains ownership of that handle.
    """
    def __init__(self,api,session,publisher_handle,publisher_identity,*,simulation=False,clock=time.monotonic):
        registered_peer(api,publisher_handle,publisher_identity)
        self.api,self.handle,self.expected=api,publisher_handle,publisher_identity
        self.name=pipe_name(session);self.simulation=simulation;self.clock=clock
        self.stop=threading.Event();self.lock=threading.Lock();self.generation=secrets.token_hex(16)

    def unavailable(self):
        return dict(ok=True,telemetry_version=1,generation=self.generation,state='unavailable',snapshot=None)

    def read(self):
        with self.lock:
            connection=None
            if self.stop.is_set():return self.unavailable()
            started=self.clock()
            try:
                registered_peer(self.api,self.handle,self.expected)
                deadline=self.clock()+1.5
                connection=self.api.connect(self.name,self.handle,self.expected,deadline,self.stop)
                # Account-only ACL is verified at both ends before transferring data.
                self.api.inspect_dacl(connection)
                self.api.write_frame(connection,REQUEST,MAX_REQUEST,deadline,self.stop)
                payload=self.api.read_frame(connection,MAX_BYTES,deadline,self.stop)
                if type(payload) is not bytes or not 1<=len(payload)<=MAX_BYTES:raise ValueError('relay_response_limit')
                def pairs(items):
                    value={}
                    for k,v in items:
                        if k in value:raise ValueError('relay_duplicate_key')
                        value[k]=v
                    return value
                body=json.loads(payload,object_pairs_hook=pairs,
                    parse_constant=lambda _ : (_ for _ in ()).throw(ValueError('relay_nonfinite')))
                if (type(body) is not dict or set(body)!={'ok','telemetry_version','generation','state','snapshot'}
                        or body['ok'] is not True or type(body['telemetry_version']) is not int or body['telemetry_version']!=1
                        or type(body['generation']) is not str or not re.fullmatch('[a-f0-9]{32}',body['generation'])):
                    raise ValueError('relay_envelope')
                if body['snapshot'] is None:
                    if body['state']!='unavailable':raise ValueError('relay_null_state')
                else:
                    if body['state']!='available':raise ValueError('relay_state')
                    body['snapshot']=project(body['snapshot'],simulation=self.simulation)
                    # project also checks UTC lag. Carry all transport time into ages.
                    from .contract import stamp
                    from datetime import datetime,timezone
                    now=datetime.now(timezone.utc).timestamp()
                    lag=max(0,now-stamp(body['snapshot']['generated_at']))
                    transit=max(0,self.clock()-started)
                    for m in body['snapshot']['metrics']:
                        if m['age_seconds'] is not None:
                            m['age_seconds']=max(m['age_seconds']+transit,now-stamp(m['collected_at'])) if m['collected_at'] else m['age_seconds']+lag+transit
                            if m['age_seconds']>=m['expires_after_seconds']:
                                m.update(value=None,valid=False,stale=True)
                                if m['state']=='available':m['state']='stale'
                # Acknowledge only a validated response; no data reaches the renderer here.
                import ctypes as ct
                self.api._io(connection,'write',ct.create_string_buffer(b'\x06'),1,deadline,self.stop)
                self.generation=body['generation']
                return body
            except (OSError,ValueError,TypeError,KeyError,TimeoutError):
                return self.unavailable()
            finally:
                if connection is not None:self.api.close(connection)

    def close(self):self.stop.set()
