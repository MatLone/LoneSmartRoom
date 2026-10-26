"""Validate simulated telemetry v1 snapshots without constructing any sensor API."""
from .contracts import Component as C, DetailCode as D, DiagnosticError, Outcome as O, tick
from .evidence import boolean, exact, utc_string
from .adapters import probe
from monitoring.contracts import Availability, ContractError
from monitoring.windows_basic import basic_catalog
from monitoring.adlx_provider import GPU_SPECS

SPECS={s.metric_id:s for s in (*basic_catalog(('C:\\','D:\\')),*GPU_SPECS)}
GROUPS={C.CPU:('cpu.utilization',),C.RAM:('ram.total','ram.used','ram.available','ram.utilization'),
        C.GPU:tuple(s.metric_id for s in GPU_SPECS)}


def normalized_snapshot(snapshot,frame,mode):
    exact(snapshot,('schema_version','sequence','generated_at','contains_simulated','metrics'))
    if (type(snapshot['schema_version']) is not int or snapshot['schema_version']!=1
            or type(snapshot['sequence']) is not int or snapshot['sequence']<0):
        raise DiagnosticError('invalid_snapshot_contract')
    boolean(snapshot['contains_simulated'])
    generated=utc_string(snapshot['generated_at'])
    if generated>frame.observed_at:raise DiagnosticError('future_snapshot')
    delivery=(frame.observed_at-generated).total_seconds()
    if type(snapshot['metrics']) is not list or len(snapshot['metrics'])>64:
        raise DiagnosticError('metric_count_limit')
    result={};simulated=False
    required=('id','unit','source','data_kind','state','value','valid','stale','collected_at','age_seconds','interval_seconds')
    optional=('label','component','cadence','ingress_age_seconds','information_age_seconds')
    for m in snapshot['metrics']:
        exact(m,required,optional)
        if type(m['id']) is not str or m['id'] not in SPECS or m['id'] in result:
            raise DiagnosticError('unknown_or_duplicate_metric')
        spec=SPECS[m['id']];gpu=m['id'].startswith('gpu.adlx.');static=gpu and m['id'].endswith('total_mb')
        if m['unit']!=spec.unit.value:raise DiagnosticError('metric_unit_mismatch')
        if m['state'] not in tuple(s.value for s in Availability):raise DiagnosticError('invalid_metric_state')
        boolean(m['valid']);boolean(m['stale'])
        if m['data_kind'] not in ('simulated','not_collected'):raise DiagnosticError('real_sensor_evidence_not_authorized')
        if m['source']!=('unconfigured' if m['data_kind']=='not_collected' else 'fixture.adlx' if gpu else 'fixture.metrics'):
            raise DiagnosticError('unexpected_metric_source')
        simulated|=m['data_kind']=='simulated'
        interval=tick(m['interval_seconds'])
        capacity=(m['id'].startswith('storage.') and not m['id'].endswith(('.read_rate','.write_rate','.activity')))
        if interval not in ((60,) if static or capacity else (2,10) if gpu else (1,5)):
            raise DiagnosticError('unexpected_metric_interval')
        available=m['state']=='available' and not m['stale']
        if m['valid']!=available:raise DiagnosticError('invalid_metric_validity')
        age=None
        if m['collected_at'] is None or m['age_seconds'] is None:
            if m['collected_at'] is not None or m['age_seconds'] is not None or available:
                raise DiagnosticError('invalid_metric_timestamp')
        else:
            collected=utc_string(m['collected_at'])
            if collected>generated:raise DiagnosticError('future_metric')
            age=max(tick(m['age_seconds'])+delivery,(frame.observed_at-collected).total_seconds())
        if m['data_kind']=='not_collected' and (age is not None or available):
            raise DiagnosticError('uncollected_sample_has_reading')
        if (m['stale'] or m['state']=='stale') and age is None:
            raise DiagnosticError('stale_sample_time_missing')
        if available:
            if m['data_kind']!='simulated':raise DiagnosticError('invalid_sample_kind')
            try:spec.validate_value(m['value'])
            except ContractError:raise DiagnosticError('invalid_metric_value') from None
        elif m['value'] is not None:raise DiagnosticError('unavailable_value_not_null')
        ingress=m.get('ingress_age_seconds')
        if ingress is not None:
            if not gpu or static or tick(ingress)>1.5:raise DiagnosticError('invalid_adlx_ingress')
        if available and gpu and not static and ingress is None:raise DiagnosticError('adlx_admission_evidence_missing')
        if 'information_age_seconds' in m:
            info=tick(m['information_age_seconds'])
            if ingress is None or m['age_seconds'] is None or abs(info-m['age_seconds']-ingress)>0.000002:
                raise DiagnosticError('invalid_information_age')
        limit=(11 if mode=='inactive' else 3) if gpu and not static else 3*interval
        result[m['id']]={**m,'effective_age':age,'expired':age is not None and age>=limit}
    if simulated!=snapshot['contains_simulated']:raise DiagnosticError('invalid_simulation_marker')
    return result


def metrics(component,frame,p):
    exact(p,('schema_version','running','mode','snapshot'),('resume_pending',))
    boolean(p['running'],True)
    if p['mode'] not in ('active','inactive'):raise DiagnosticError('invalid_metric_mode')
    if 'resume_pending' in p:boolean(p['resume_pending'])
    values=normalized_snapshot(p['snapshot'],frame,p['mode'])
    facts=dict(collector_running=p['running'],sample_valid=False,sample_stale=False)
    if p['running'] is not True:
        return probe(component,frame,facts,D.METRICS_MISSING,O.OK if p['running'] is False else O.UNKNOWN)
    selected=[values.get(k) for k in GROUPS[component]]
    if any(m is None for m in selected):return probe(component,frame,facts,D.METRICS_MISSING,O.UNAVAILABLE)
    if any(m['state'] in ('error','permission_denied') for m in selected):
        return probe(component,frame,facts,D.METRICS_READ_ERROR,O.ERROR)
    supported=[m for m in selected if m['state']!='unsupported']
    dynamic=[m for m in supported if not m['id'].endswith('total_mb')]
    if not supported or component==C.GPU and not dynamic:
        return probe(component,frame,facts,D.METRICS_UNSUPPORTED,O.UNSUPPORTED)
    if component==C.GPU and p.get('resume_pending') is True:
        return probe(component,frame,facts,D.AWAITING_FRESH,O.UNAVAILABLE)
    if any(m['stale'] or m['expired'] or m['state']=='stale' for m in supported):
        facts['sample_stale']=True
        age=max(m['effective_age'] for m in supported if m['effective_age'] is not None)
        return probe(component,frame,facts,D.METRICS_STALE,age=age)
    if any(not m['valid'] for m in supported):
        detail=D.METRICS_WARMING if any(m['state']=='warming_up' for m in supported) else D.METRICS_MISSING
        return probe(component,frame,facts,detail,O.UNAVAILABLE)
    if component==C.RAM:
        total,used,available,percent=(m['value'] for m in selected)
        if total<=0 or used+available!=total or abs(percent-used/total*100)>0.000001 or len({m['collected_at'] for m in selected})!=1:
            return probe(component,frame,facts,D.METRICS_READ_ERROR,O.ERROR)
    if component==C.GPU:
        used,total=values['gpu.adlx.vram_used_mb'],values['gpu.adlx.vram_total_mb']
        if total['valid'] and (total['value']<=0 or used['valid'] and used['value']>total['value']):
            return probe(component,frame,facts,D.METRICS_READ_ERROR,O.ERROR)
    age=max(m['effective_age'] for m in (dynamic if component==C.GPU else supported))
    facts['sample_valid']=True
    interval=min(m['interval_seconds'] for m in supported) if component in (C.CPU,C.RAM) else None
    return probe(component,frame,facts,D.METRICS_PARTIAL if len(supported)!=len(selected) else D.METRICS_OK,age=age,interval=interval)
