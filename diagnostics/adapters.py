"""Read-only projections from explicit fixture receipts into the existing reducer.

These are NOT HTTP/pipe/native clients. Real readers need separate approval and
trust-boundary validation before supplying comparable evidence.
"""
from datetime import timedelta

from .contracts import Component as C, DetailCode as D, DiagnosticError, Outcome as O, Probe, tick
from .evidence import FixtureReader, boolean, decode, exact


def probe(component, frame, facts, detail, outcome=O.OK, age=0, interval=None):
    tick(age)
    if age>frame.observed_monotonic:
        raise DiagnosticError('metric_clock_domain_invalid')
    return Probe(component,frame.observed_at-timedelta(seconds=age),frame.observed_monotonic-age,
                 facts,outcome,detail_code=detail,sample_interval_seconds=interval)


def https(frame,p):
    exact(p,('schema_version','result','method','endpoint','http_status','tls_verified','hostname_verified','pin_verified','hmac_request_used'))
    if p['method']!='GET' or p['endpoint']!='/v2/status':
        raise DiagnosticError('status_only_request_required')
    for k in ('tls_verified','hostname_verified','pin_verified','hmac_request_used'):boolean(p[k],True)
    if p['http_status'] is not None and (type(p['http_status']) is not int or not 100<=p['http_status']<=599):
        raise DiagnosticError('invalid_http_status')
    if p['result'] in ('timeout','connection_refused','network_unavailable'):
        if p['http_status'] is not None:raise DiagnosticError('contradictory_status_receipt')
        return probe(C.HTTPS,frame,dict(responded=False,authenticated=None,tls_verified=None),D.CONNECTION_FAILED)
    if p['result'] not in ('response','tls_rejected'):raise DiagnosticError('invalid_status_result')
    verified=all(p[k] is True for k in ('tls_verified','hostname_verified','pin_verified'))
    facts=dict(responded=True,authenticated=verified and p['hmac_request_used'] is True and p['http_status']==200,tls_verified=verified)
    if not verified or p['result']=='tls_rejected':
        facts['tls_verified']=False;facts['authenticated']=False
        return probe(C.HTTPS,frame,facts,D.TLS_FAILED)
    if p['http_status'] in (401,403) or p['hmac_request_used'] is not True:
        return probe(C.HTTPS,frame,facts,D.AUTH_FAILED)
    if p['http_status']!=200:
        return probe(C.HTTPS,frame,facts,D.HTTP_FAILED,O.ERROR)
    return probe(C.HTTPS,frame,facts,D.HTTPS_OK)


def listener(frame,p):
    exact(p,('schema_version','port','present','image_verified','creation_verified','parent_verified'))
    if type(p['port']) is not int or p['port']!=8776:raise DiagnosticError('fixed_listener_required')
    for k in ('present','image_verified','creation_verified','parent_verified'):boolean(p[k],True)
    identity=all(p[k] is True for k in ('image_verified','creation_verified','parent_verified'))
    detail=(D.LISTENER_OK if identity else D.LISTENER_MISMATCH) if p['present'] is True else None
    return probe(C.LISTENER,frame,dict(present=p['present'],identity_matches=identity if p['present'] is True else None,port=8776),detail)


def pipe(frame,p):
    exact(p,('schema_version','connected','local','sid_verified','session_verified','server_identity_verified','contract_version','result'))
    for k in ('connected','local','sid_verified','session_verified','server_identity_verified'):boolean(p[k],True)
    if type(p['contract_version']) is not int or p['contract_version'] not in (1,2):raise DiagnosticError('invalid_pipe_contract')
    if p['result'] not in ('ok','timeout','disconnected','size_limit','rate_limit','invalid_frame'):raise DiagnosticError('invalid_pipe_result')
    peer=all(p[k] is True for k in ('local','sid_verified','session_verified','server_identity_verified'))
    facts=dict(connected=p['connected'],peer_validated=peer,contract_version=p['contract_version'])
    if p['connected'] is False or p['result'] in ('timeout','disconnected'):
        facts['connected']=False;return probe(C.IPC,frame,facts,D.PIPE_DISCONNECTED)
    if p['result'] in ('size_limit','rate_limit','invalid_frame'):
        return probe(C.IPC,frame,facts,D.PIPE_LIMIT,O.ERROR)
    detail=D.PIPE_IDENTITY_FAILED if not peer else D.PIPE_CONTRACT_FAILED if p['contract_version']!=1 else None
    return probe(C.IPC,frame,facts,detail)


def adlx(frame,p):
    exact(p,('schema_version','running','library_verified','last_frame','ingress_age_seconds','sample_age_seconds'))
    boolean(p['running'],True);boolean(p['library_verified'],True)
    if p['last_frame'] not in ('valid','invalid_frame','warming_up','unavailable','error'):raise DiagnosticError('invalid_adlx_receipt')
    facts=dict(running=p['running'],dll_verified=p['library_verified'],sample_valid=False,sample_stale=False)
    if p['running'] is False:return probe(C.ADLX,frame,facts,D.ADLX_NOT_RUNNING)
    if p['running'] is None:return probe(C.ADLX,frame,facts,D.ADLX_NOT_RUNNING,O.UNKNOWN)
    if p['library_verified'] is not True:return probe(C.ADLX,frame,facts,D.ADLX_UNVERIFIED,O.ERROR)
    if p['last_frame']=='valid':
        tick(p['ingress_age_seconds']);tick(p['sample_age_seconds'])
        if p['ingress_age_seconds']>1.5:raise DiagnosticError('adlx_ingress_rejected')
        facts['sample_valid']=True
        return probe(C.ADLX,frame,facts,D.ADLX_OK,age=p['sample_age_seconds'])
    if p['ingress_age_seconds'] is not None or p['sample_age_seconds'] is not None:
        raise DiagnosticError('invalid_frame_cannot_claim_age')
    return probe(C.ADLX,frame,facts,D.ADLX_REJECTED,O.ERROR if p['last_frame']=='error' else O.UNAVAILABLE)


class ReceiptProvider:
    evidence_kind='simulated'

    def __init__(self,component,reader):
        if type(component) is not C or type(reader) is not FixtureReader:
            raise DiagnosticError('fixture_reader_required')
        self.component,self.reader=component,reader

    def read(self):
        frame=self.reader.read()
        if frame is None:return None
        payload=decode(frame.payload)
        if type(payload.get('schema_version')) is not int or payload['schema_version']!=1:
            raise DiagnosticError('incompatible_evidence_contract')
        if self.component in (C.CPU,C.GPU,C.RAM):
            from .metric_evidence import metrics
            return metrics(self.component,frame,payload)
        if self.component==C.STARTUP:
            from .startup_evidence import startup
            return startup(frame,payload)
        return {C.HTTPS:https,C.LISTENER:listener,C.IPC:pipe,C.ADLX:adlx}[self.component](frame,payload)
