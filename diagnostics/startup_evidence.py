"""Correlate bounded existing-schema startup receipts; never opens logs/Registry."""
from .contracts import Component as C, DetailCode as D, DiagnosticError, Outcome as O
from .evidence import boolean, exact, utc_string
from .adapters import probe

EVENTS=frozenset(('attempt','paths_ok','paths_invalid','environment_invalid','spawn_failed',
    'child_created','child_exit','worker_attempt','duplicate','legacy_present','guard_failed',
    'lock_recovered','dependency_missing','dependency_failed','bootstrap_ready','agent_returned',
    'agent_failed','invalid_arguments','launcher_failed'))
FAILURES=frozenset(('paths_invalid','environment_invalid','spawn_failed','guard_failed',
    'dependency_missing','dependency_failed','agent_failed','invalid_arguments','launcher_failed'))


def startup(frame,p):
    exact(p,('schema_version','configured','target_verified','login_at','same_session_verified',
             'lineage_verified','dispatch_proven','events'))
    for k in ('configured','target_verified','same_session_verified','lineage_verified','dispatch_proven'):
        boolean(p[k],True)
    login=utc_string(p['login_at']) if p['login_at'] is not None else None
    if login is not None and login>frame.observed_at:raise DiagnosticError('future_login')
    if type(p['events']) is not list or len(p['events'])>64:raise DiagnosticError('startup_event_limit')
    events=[];previous=None
    for e in p['events']:
        exact(e,('utc','pid','event'),('phase','code','dependency'))
        when=utc_string(e['utc'])
        if when>frame.observed_at or previous is not None and when<previous:raise DiagnosticError('invalid_event_order')
        previous=when
        if type(e['event']) is not str or e['event'] not in EVENTS:raise DiagnosticError('unknown_startup_event')
        if type(e['pid']) is not int or not 0<e['pid']<=2**32-1:raise DiagnosticError('invalid_event_pid')
        if 'code' in e and (type(e['code']) is not int or not -2**31<=e['code']<2**32):raise DiagnosticError('invalid_event_code')
        if 'phase' in e and e['phase'] not in ('supervisor','worker','paths','environment','guard','agent'):raise DiagnosticError('invalid_event_phase')
        if 'dependency' in e and e['dependency'] not in ('cryptography','cffi','pycparser','other'):raise DiagnosticError('invalid_event_dependency')
        if login is not None and when>=login:events.append(e)
    facts=dict(configured=p['configured'],login_observed=login is not None,dispatch_observed=p['dispatch_proven'],bootstrap_succeeded=None)
    if p['configured'] is False:return probe(C.STARTUP,frame,facts,D.STARTUP_NOT_CONFIGURED)
    if p['target_verified'] is False:return probe(C.STARTUP,frame,facts,D.STARTUP_TARGET_INVALID,O.ERROR)
    if login is None or p['same_session_verified'] is not True or p['lineage_verified'] is not True or p['target_verified'] is not True:
        return probe(C.STARTUP,frame,facts,D.STARTUP_NOT_VERIFIED,O.UNKNOWN)
    # Only the latest correlated attempt is relevant, not an earlier successful run.
    attempts=[i for i,e in enumerate(events) if e['event']=='attempt']
    if attempts:events=events[attempts[-1]:]
    if p['dispatch_proven'] is not True:
        return probe(C.STARTUP,frame,facts,D.STARTUP_DISPATCH_UNCONFIRMED,O.UNKNOWN)
    if not attempts:return probe(C.STARTUP,frame,facts,D.STARTUP_NOT_VERIFIED,O.UNKNOWN)
    failures=[i for i,e in enumerate(events) if e['event'] in FAILURES or e['event']=='child_exit' and e.get('code',0)!=0]
    if failures:
        facts['bootstrap_succeeded']=False
        return probe(C.STARTUP,frame,facts,D.STARTUP_BOOTSTRAP_FAILED)
    if any(e['event'] in ('duplicate','legacy_present') for e in events):
        return probe(C.STARTUP,frame,facts,D.STARTUP_EXISTING_INSTANCE,O.UNKNOWN)
    if any(e['event'] in ('agent_returned','child_exit') for e in events):
        return probe(C.STARTUP,frame,facts,D.STARTUP_EXITED,O.UNAVAILABLE)
    if any(e['event']=='bootstrap_ready' for e in events):
        facts['bootstrap_succeeded']=True
        return probe(C.STARTUP,frame,facts,D.STARTUP_BOOTSTRAP_SEEN)
    return probe(C.STARTUP,frame,facts,D.STARTUP_NOT_VERIFIED,O.UNKNOWN)
