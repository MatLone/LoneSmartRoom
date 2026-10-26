"""Explicit passive session orchestration. No OS access on import; no repairs.

The platform reader is injected. Existing simulated adapters remain the default.
Observed evidence never becomes simulated evidence or a live sensor reading.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import time

from .contracts import Component as C, DetailCode as D, DiagnosticError, Outcome as O, Probe
from .engine import DiagnosticEngine
from .presentation import present


@dataclass(frozen=True)
class OnceProvider:
    observation: Probe
    evidence_kind: str = 'observed'

    @property
    def component(self): return self.observation.component
    def read(self): return self.observation


def observations(census, https, now, tick):
    """Project verified platform facts only. Missing data is never success/zero."""
    def p(c, facts, detail, outcome=O.OK):
        receipt = https if c==C.HTTPS else census
        at=datetime.fromisoformat(receipt['observed_at']) if receipt.get('observed_at') else now
        at_tick=receipt.get('observed_monotonic',tick)
        return Probe(c, at, at_tick, facts, outcome, evidence_kind='observed', detail_code=detail)
    identity = census.get('agent_verified') is True
    listener = census.get('listener_count')
    result = [p(C.LISTENER, dict(present=listener > 0 if type(listener) is int else None,
        identity_matches=True if identity else None, port=8776),
        D.LISTENER_OK if identity else D.LISTENER_MISMATCH,
        O.OK if identity or listener==0 else O.UNKNOWN)]
    good = (identity and https.get('ok') is True and https.get('http_status') == 200
            and https.get('hostname_verified') is True and https.get('pin_verified') is True)
    code = D.HTTPS_OK if good else D.PASSIVE_UNVERIFIED
    outcome = O.OK if good else O.UNKNOWN
    if https.get('error') == 'tls_identity_failed': code, outcome = D.TLS_FAILED, O.ERROR
    if https.get('error') == 'authentication_failed': code, outcome = D.AUTH_FAILED, O.ERROR
    if https.get('error') == 'connection_failed': code, outcome = D.CONNECTION_FAILED, O.UNAVAILABLE
    result.append(p(C.HTTPS, dict(responded=True if good else None,
        authenticated=True if good else None, tls_verified=True if good else None), code, outcome))
    inactive = (census.get('monitoring_census_complete') is True
                and census.get('application_count') == 0 and census.get('monitoring_count') == 0)
    pipe_inactive=inactive and census.get('pipe_namespace') == {'available':True,'matching_count':0}
    detail = D.NORMAL_INACTIVE if inactive else D.PASSIVE_UNVERIFIED
    result.append(p(C.IPC,dict(connected=False if pipe_inactive else None,
        peer_validated=None,contract_version=1),D.NORMAL_INACTIVE if pipe_inactive else D.PASSIVE_UNVERIFIED,
        O.UNAVAILABLE if pipe_inactive else O.UNKNOWN))
    for component in (C.CPU,C.GPU,C.RAM):
        result.append(p(component,dict(collector_running=False if inactive else None,
            sample_valid=None,sample_stale=None), detail,O.UNAVAILABLE if inactive else O.UNKNOWN))
    result.append(p(C.ADLX,dict(running=False if inactive else None,dll_verified=None,
        sample_valid=None,sample_stale=None),detail,O.UNAVAILABLE if inactive else O.UNKNOWN))
    # Neither a Run entry nor launcher logs prove that Windows dispatched it.
    startup = census.get('startup',{})
    result.append(p(C.STARTUP,dict(configured=startup.get('configured'),login_observed=None,
        dispatch_observed=None,bootstrap_succeeded=None),D.STARTUP_DISPATCH_UNCONFIRMED,O.UNKNOWN))
    return result


def report_for(census, https, now, tick):
    engine=DiagnosticEngine([OnceProvider(x) for x in observations(census,https,now,tick)],evidence_kind='observed')
    report=engine.collect(now,tick)
    return report,present(report,allow_observed=True)


def run_session(reader, *, clock=time.monotonic, utc_now=lambda:datetime.now(timezone.utc)):
    """One explicit attempt, at most two fixed GETs, no automatic retry or sleeps.

    Reader methods have independent bounded deadlines. At 35 s no new status
    call is started; 20 s remain reserved for closing handles and final census.
    A deadline miss is reported as failure, never silently accepted as success.
    """
    start=clock(); deadline=start+60
    summary={'read_only':True,'repairs':False,'session_limit_seconds':60,
             'new_grants':False,'operational_commands':False,'completed':False}
    try:
        reader.begin(deadline)
        initial=reader.census(deadline=min(deadline-20,start+15))
        summary['initial']=initial
        if initial.get('agent_verified') is not True:
            summary['stop_code']='agent_identity_not_verified'
            return summary
        before=reader.database()
        summary['database_initial']=before
        if before.get('integrity_ok') is not True or before.get('grants') != 0:
            summary['stop_code']='database_gate_failed'
            return summary
        https=reader.status(deadline=min(deadline-20,clock()+6))
        summary['https_initial']=https
        if https.get('ok') is not True:
            summary['stop_code']='authenticated_status_not_verified'
            return summary
        summary['startup_logs']=reader.startup_logs()
        summary['report'],summary['view']=report_for(initial,https,utc_now(),clock())
        # No attachment to the monitoring pipe: its peer policy binds to the
        # Electron-owned intermediary. Presence is not an authenticated IPC test.
        summary['pipe_probe']='namespace_only_no_connection'
        summary['latest_samples']='not_accessible_via_authorized_passive_interface'
        if clock()-start>=35:
            summary['stop_code']='final_checks_budget_exhausted'
            return summary
        final=reader.census(deadline=min(deadline-8,clock()+10))
        summary['final']=final
        same=initial['agent_identity_digest']==final.get('agent_identity_digest')
        if not same or final.get('agent_verified') is not True:
            summary['stop_code']='agent_identity_changed'
            return summary
        summary['https_final']=reader.status(deadline=min(deadline-3,clock()+6))
        after=reader.database(); summary['database_final']=after
        summary['completed']=(summary['https_final'].get('ok') is True
            and before==after and after.get('grants')==0)
        if not summary['completed']:summary['stop_code']='final_gate_failed'
    except Exception:
        summary['stop_code']='passive_reader_failed'  # Never serialize exception text.
    finally:
        reader.close()
        elapsed=clock()-start
        summary['elapsed_seconds']=round(elapsed,3)
        summary['within_limit']=elapsed<=60
        if elapsed>60:summary['completed']=False;summary['stop_code']='session_deadline_exceeded'
        summary['resources']=reader.resource_summary(elapsed)
    return summary
