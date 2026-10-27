"""Explicit bounded mock evidence sources; never a live reader implementation."""
from collections import deque
from datetime import timedelta
from itertools import islice
import json

from .contracts import Component as C,DiagnosticError
from .evidence_contract import AdapterKind as A,EvidenceFrame,SECURITY_CHECKS
from .evidence_cache import EvidenceHub
from .scenarios import NOW,status_payload,monitoring_payload,startup_payload


class MockEvidenceSource:
    def __init__(self,kind,frames=()):
        if type(kind) is not A:raise DiagnosticError('invalid_mock_source')
        frames=tuple(islice(frames,65))
        if len(frames)>64:raise DiagnosticError('mock_source_limit')
        self.kind=kind;self._frames=deque(frames)

    def read(self):
        if not self._frames:return None
        value=self._frames.popleft()
        if isinstance(value,Exception):raise value
        if value is not None and (type(value) is not EvidenceFrame or value.adapter!=self.kind):raise DiagnosticError('invalid_mock_frame')
        return value


def drain(source,hub,*,now,monotonic,mode='active'):
    if type(source) is not MockEvidenceSource:raise DiagnosticError('mock_source_required')
    try:value=source.read()
    except Exception:
        hub.provider_failed(source.kind,now=now,monotonic=monotonic,mode=mode)
        return {'accepted':False,'code':'provider_failed'}
    if value is None:return {'accepted':False,'code':'no_new_evidence'}
    return hub.submit(value,now=now,monotonic=monotonic,mode=mode)


def frame(kind,payload,*,sequence=1,seconds=0):
    return EvidenceFrame(kind,sequence,NOW+timedelta(seconds=seconds),100+seconds,
        json.dumps(payload,allow_nan=False,separators=(',',':')).encode())


def agent_payload(*,seconds=0):
    return dict(schema_version=1,processes=dict(
        supervisor=dict(pid=101,created_at=(NOW-timedelta(seconds=20)).isoformat(),verdict='verified'),
        worker=dict(pid=102,created_at=(NOW-timedelta(seconds=19)).isoformat(),verdict='verified'),
        lineage='verified',same_account=True,same_session=True,non_elevated=True),
        listener=dict(present=True,owner_pid=102,port=8776,network_authorized=True),
        status=status_payload()|{'checked_at':(NOW+timedelta(seconds=seconds)).isoformat()})


def pipe_payload(*,generation=1,connected=True):
    return dict(schema_version=1,generation=generation,connected=connected,local=True,sid_verified=True,
        session_verified=True,server_identity_verified=True,acl_verified=True,contract_version=1,
        result='ok' if connected else 'disconnected')


def monitor_payload(*,seconds=1,generation=1,age=0,mode='active',state='available'):
    now=NOW+timedelta(seconds=seconds)
    values=[monitoring_payload(c,now=now,age=age,mode=mode,state=state)['snapshot']['metrics'] for c in (C.CPU,C.GPU,C.RAM)]
    return dict(schema_version=1,generation=generation,application_open=True,collector_running=True,mode=mode,
        snapshot=dict(schema_version=1,sequence=1,generated_at=now.isoformat(),contains_simulated=True,metrics=sum(values,[])),
        bridge=dict(schema_version=1,running=True,library_verified=True,last_frame='valid',ingress_age_seconds=.25,sample_age_seconds=age),
        resume_pending=False)


def security_payload(*,seconds=0):
    return dict(schema_version=1,checks=[dict(id=k,authorized=True,result='verified',
        checked_at=(NOW+timedelta(seconds=seconds)).isoformat()) for k in SECURITY_CHECKS])


def seed():
    hub=EvidenceHub()
    for kind,payload in ((A.AGENT,agent_payload()),(A.IPC,pipe_payload()),(A.STARTUP,startup_payload()),(A.SECURITY,security_payload())):
        hub.submit(frame(kind,payload),now=NOW,monotonic=100)
    hub.submit(frame(A.MONITORING,monitor_payload(),seconds=1),now=NOW+timedelta(seconds=1),monotonic=101)
    return hub


def reports():
    """Frozen end-to-end test reports, not operational UI data or measurements."""
    result={}
    names=('online','offline','auth-failure','listener-mismatch','inactive','unsupported','stale','recovery','permanent-failure','reconnecting','reconnected','provider-error','startup-inconclusive','security-failure')
    for name in names:
        hub=seed();now=NOW+timedelta(seconds=2)
        if name in ('offline','auth-failure','listener-mismatch','permanent-failure','recovery'):
            p=agent_payload(seconds=2)
            if name=='offline':
                p['listener'].update(present=False,owner_pid=None)
                p['status'].update(result='connection_refused',http_status=None,tls_verified=None,hostname_verified=None,pin_verified=None,hmac_request_used=None)
            elif name=='listener-mismatch':p['listener']['owner_pid']=999
            else:p['status']['http_status']=401
            hub.submit(frame(A.AGENT,p,sequence=2,seconds=2),now=now,monotonic=102)
            if name=='recovery':
                now=NOW+timedelta(seconds=3)
                hub.submit(frame(A.AGENT,agent_payload(seconds=3),sequence=3,seconds=3),now=now,monotonic=103)
        if name=='inactive':
            p=monitor_payload(seconds=2);p.update(application_open=False,collector_running=False,snapshot=None)
            p['bridge'].update(running=False,last_frame='unavailable',ingress_age_seconds=None,sample_age_seconds=None)
            hub.submit(frame(A.MONITORING,p,sequence=2,seconds=2),now=now,monotonic=102)
            hub.submit(frame(A.IPC,pipe_payload(connected=False),sequence=2,seconds=2),now=now,monotonic=102)
        if name=='unsupported':
            p=monitor_payload(seconds=2,state='unsupported')
            p['bridge'].update(last_frame='unavailable',ingress_age_seconds=None,sample_age_seconds=None)
            hub.submit(frame(A.MONITORING,p,sequence=2,seconds=2),now=now,monotonic=102)
        if name=='stale':now=NOW+timedelta(seconds=5)
        if name in ('reconnecting','reconnected'):
            hub.submit(frame(A.IPC,pipe_payload(connected=False),sequence=2,seconds=2),now=now,monotonic=102)
            now=NOW+timedelta(seconds=3)
            hub.submit(frame(A.IPC,pipe_payload(generation=2),sequence=3,seconds=3),now=now,monotonic=103)
            if name=='reconnected':
                now=NOW+timedelta(seconds=4)
                hub.submit(frame(A.MONITORING,monitor_payload(seconds=4,generation=2),sequence=2,seconds=4),now=now,monotonic=104)
        if name=='provider-error':hub.provider_failed(A.MONITORING,now=now,monotonic=102)
        if name=='security-failure':
            p=security_payload(seconds=2);p['checks'][2]['result']='failed'
            hub.submit(frame(A.SECURITY,p,sequence=2,seconds=2),now=now,monotonic=102)
        tick=100+(now-NOW).total_seconds()
        result[name]={'report':hub.snapshot(now=now,monotonic=tick),'audit':hub.audit(now=now,monotonic=tick)}
        hub.close()
    return result
