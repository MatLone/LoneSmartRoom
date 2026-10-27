"""Specific pure evidence projections; no reader activation or generic commands.

Verdicts are assertions supplied by trusted *mock* sources, not independent OS
or cryptographic checks. Future real sources require a separately reviewed path.
"""
from dataclasses import replace
import json

from .contracts import Component as C,DetailCode as D,DiagnosticError,Outcome as O,Probe,stamp
from .evidence import ReceiptFrame,FixtureReader,boolean,decode,exact,utc_string
from .evidence_contract import AdapterKind as A,AdapterProjection,EvidenceFrame,KNOWN_ISSUES,SECURITY_CHECKS,VERDICTS,integer
from .adapters import ReceiptProvider


GROUPS={A.AGENT:(C.HTTPS,C.LISTENER),A.MONITORING:(C.CPU,C.GPU,C.RAM,C.ADLX),
        A.IPC:(C.IPC,),A.STARTUP:(C.STARTUP,),A.SECURITY:()}


def observation(frame,component,facts,detail=D.PASSIVE_UNVERIFIED,outcome=O.UNKNOWN):
    return Probe(component,frame.observed_at,frame.observed_monotonic,facts,outcome,detail_code=detail)


def legacy(frame,component,payload,*,checked_at=None):
    when=frame.observed_at if checked_at is None else utc_string(checked_at)
    age=(frame.observed_at-when).total_seconds()
    if age<0 or age>frame.observed_monotonic:raise DiagnosticError('invalid_adapter_clock_domain')
    try:raw=json.dumps(payload,allow_nan=False,separators=(',',':')).encode()
    except (ValueError,TypeError,OverflowError):raise DiagnosticError('invalid_adapter_value') from None
    receipt=ReceiptFrame(when,frame.observed_monotonic-age,raw)
    return ReceiptProvider(component,FixtureReader([receipt])).read()


def body(frame,kind):
    if type(frame) is not EvidenceFrame:raise DiagnosticError('adapter_frame_required')
    if frame.adapter!=kind:raise DiagnosticError('adapter_kind_mismatch')
    data=decode(frame.payload)
    if type(data.get('schema_version')) is not int or data['schema_version']!=1:raise DiagnosticError('incompatible_adapter_payload')
    return data


def process(value,frame):
    if value is None:return None
    exact(value,('pid','created_at','verdict'))
    integer(value['pid'],maximum=2**32-1)
    if value['verdict'] not in VERDICTS:raise DiagnosticError('invalid_process_verdict')
    if utc_string(value['created_at'])>frame.observed_at:raise DiagnosticError('future_process_creation')
    return value


class AgentEvidenceAdapter:
    kind=A.AGENT

    def project(self,frame):
        p=body(frame,self.kind);exact(p,('schema_version','processes','listener','status'))
        processes=p['processes'];exact(processes,('supervisor','worker','lineage','same_account','same_session','non_elevated'))
        supervisor=process(processes['supervisor'],frame);worker=process(processes['worker'],frame)
        if processes['lineage'] not in VERDICTS:raise DiagnosticError('invalid_lineage_verdict')
        for key in ('same_account','same_session','non_elevated'):boolean(processes[key],True)
        if supervisor and worker and (supervisor['pid']==worker['pid'] or utc_string(worker['created_at'])<utc_string(supervisor['created_at'])):
            raise DiagnosticError('invalid_process_relationship')
        identity=bool(supervisor and worker and supervisor['verdict']==worker['verdict']==processes['lineage']=='verified'
            and all(processes[k] is True for k in ('same_account','same_session','non_elevated')))
        l=p['listener'];exact(l,('present','owner_pid','port','network_authorized'))
        boolean(l['present'],True);boolean(l['network_authorized'],True)
        if type(l['port']) is not int or l['port']!=8776:raise DiagnosticError('unexpected_listener_port')
        if l['owner_pid'] is not None:integer(l['owner_pid'],maximum=2**32-1)
        if l['present'] is False and l['owner_pid'] is not None:raise DiagnosticError('contradictory_listener')
        matched=identity and l['present'] is True and l['network_authorized'] is True and l['owner_pid']==worker['pid']
        mismatch=l['present'] is True and (l['network_authorized'] is False or processes['lineage']=='mismatch'
            or any(x and x['verdict']=='mismatch' for x in (supervisor,worker))
            or identity and l['owner_pid'] is not None and l['owner_pid']!=worker['pid'])
        lp=observation(frame,C.LISTENER,dict(present=l['present'],identity_matches=True if matched else False if mismatch else None,port=8776),
            D.LISTENER_OK if matched else D.LISTENER_MISMATCH,O.OK if matched or mismatch or l['present'] is False else O.UNKNOWN)
        status=p['status']
        if status is None:
            hp=observation(frame,C.HTTPS,dict(responded=None,authenticated=None,tls_verified=None))
        else:
            exact(status,('schema_version','result','method','endpoint','http_status','tls_verified','hostname_verified','pin_verified','hmac_request_used','checked_at'))
            if status['checked_at'] is None:raise DiagnosticError('status_check_time_required')
            payload={k:v for k,v in status.items() if k!='checked_at'}
            hp=legacy(frame,C.HTTPS,payload,checked_at=status['checked_at'])
            if (status['result']=='response' and any(status[k] is None for k in ('tls_verified','hostname_verified','pin_verified','hmac_request_used'))):
                hp=replace(hp,outcome=O.UNKNOWN,detail_code=D.PASSIVE_UNVERIFIED)
            if hp.outcome==O.OK and hp.facts.get('authenticated') is True and not matched:
                hp=replace(hp,outcome=O.UNKNOWN,detail_code=D.PASSIVE_UNVERIFIED)
        return AdapterProjection((hp,lp))


class PipeEvidenceAdapter:
    kind=A.IPC

    def project(self,frame):
        p=body(frame,self.kind);exact(p,('schema_version','generation','connected','local','sid_verified','session_verified','server_identity_verified','acl_verified','contract_version','result'))
        generation=integer(p['generation']);boolean(p['acl_verified'],True)
        payload={k:v for k,v in p.items() if k not in ('generation','acl_verified')}
        probe=legacy(frame,C.IPC,payload)
        keys=('local','sid_verified','session_verified','server_identity_verified','acl_verified')
        peer=p['connected'] is True and all(p[k] is True for k in keys) and p['contract_version']==1 and p['result']=='ok'
        if p['connected'] is True and p['result']=='ok':
            if any(p[k] is False for k in keys):probe=replace(probe,facts=dict(probe.facts)|{'peer_validated':False},outcome=O.ERROR,detail_code=D.PIPE_IDENTITY_FAILED)
            elif any(p[k] is None for k in keys):probe=replace(probe,facts=dict(probe.facts)|{'peer_validated':None},outcome=O.UNKNOWN,detail_code=D.PASSIVE_UNVERIFIED)
        return AdapterProjection((probe,),generation=generation,connected=p['connected'],peer_verified=peer)


class MonitoringEvidenceAdapter:
    kind=A.MONITORING

    def project(self,frame):
        p=body(frame,self.kind);exact(p,('schema_version','generation','application_open','collector_running','mode','snapshot','bridge','resume_pending'))
        generation=integer(p['generation'])
        for key in ('application_open','collector_running'):boolean(p[key],True)
        boolean(p['resume_pending'])
        if p['mode'] not in ('active','inactive'):raise DiagnosticError('invalid_monitoring_mode')
        if p['application_open'] is False and p['collector_running'] is True:raise DiagnosticError('contradictory_collector_lifecycle')
        probes=[]
        for component in (C.CPU,C.GPU,C.RAM):
            if p['snapshot'] is not None:
                probe=legacy(frame,component,dict(schema_version=1,running=p['collector_running'],mode=p['mode'],snapshot=p['snapshot'],resume_pending=p['resume_pending']))
            else:
                probe=observation(frame,component,dict(collector_running=p['collector_running'],sample_valid=None,sample_stale=None),D.METRICS_MISSING,
                    O.UNAVAILABLE if p['collector_running'] is not None else O.UNKNOWN)
            if p['application_open'] is False and p['collector_running'] is False:
                probe=replace(probe,outcome=O.UNAVAILABLE,detail_code=D.NORMAL_INACTIVE,
                    sample_interval_seconds=(5 if p['mode']=='inactive' else 1) if component in (C.CPU,C.RAM) else None)
            probes.append(probe)
        if p['bridge'] is None:
            bridge=observation(frame,C.ADLX,dict(running=None,dll_verified=None,sample_valid=None,sample_stale=None),D.ADLX_NOT_RUNNING)
        else:
            bridge=legacy(frame,C.ADLX,p['bridge'])
            if p['bridge']['library_verified'] is None and p['bridge']['running'] is True:
                bridge=replace(bridge,outcome=O.UNKNOWN,detail_code=D.ADLX_UNVERIFIED)
            if p['application_open'] is False and p['bridge']['running'] is False:
                bridge=replace(bridge,outcome=O.UNAVAILABLE,detail_code=D.NORMAL_INACTIVE)
        probes.append(bridge)
        return AdapterProjection(tuple(probes),generation=generation,application_open=p['application_open'])


class StartupEvidenceAdapter:
    kind=A.STARTUP

    def project(self,frame):
        p=body(frame,self.kind)
        return AdapterProjection((legacy(frame,C.STARTUP,p),))


class SecurityEvidenceAdapter:
    kind=A.SECURITY

    def project(self,frame):
        p=body(frame,self.kind);exact(p,('schema_version','checks'))
        if type(p['checks']) is not list or len(p['checks'])>len(SECURITY_CHECKS):raise DiagnosticError('security_check_limit')
        checks=[];seen=set()
        for row in p['checks']:
            exact(row,('id','authorized','result','checked_at'))
            if row['id'] not in SECURITY_CHECKS or row['id'] in seen:raise DiagnosticError('unknown_security_check')
            seen.add(row['id']);boolean(row['authorized'])
            if row['result'] not in ('verified','failed','unknown','not_checked'):raise DiagnosticError('invalid_security_result')
            if not row['authorized'] and row['result'] not in ('unknown','not_checked'):raise DiagnosticError('unauthorized_security_claim')
            when=utc_string(row['checked_at']) if row['checked_at'] is not None else None
            if when is not None and when>frame.observed_at:raise DiagnosticError('future_security_check')
            if row['result'] in ('verified','failed') and when is None:raise DiagnosticError('missing_security_check_time')
            checks.append(dict(row)|{'checked_at':stamp(when) if when is not None else None})
        # Separate versioned sidecar: never adds a ninth component to report v1.
        return AdapterProjection((),security={'schema_version':1,'simulation':True,'state':'error' if any(r['result']=='failed' for r in checks) else 'unknown',
            'observed_at':stamp(frame.observed_at),'checks':checks,'known_issues':list(KNOWN_ISSUES),'repair_capability':False})


ADAPTERS={a.kind:a for a in (AgentEvidenceAdapter(),MonitoringEvidenceAdapter(),PipeEvidenceAdapter(),StartupEvidenceAdapter(),SecurityEvidenceAdapter())}
