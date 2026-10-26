"""Explicit mock receipts for review/tests. None of these are local PC measurements."""
from datetime import datetime, timedelta, timezone
import json

from .contracts import Component as C
from .evidence import ReceiptFrame, FixtureReader
from .adapters import ReceiptProvider
from .metric_evidence import GROUPS, SPECS
from .engine import DiagnosticEngine

NOW=datetime(2026,10,26,12,tzinfo=timezone.utc)


def receipt(payload, *, now=NOW, monotonic=100):
    return ReceiptFrame(now,monotonic,json.dumps(payload,allow_nan=False).encode('utf-8'))


def status_payload(**changes):
    return dict(schema_version=1,result='response',method='GET',endpoint='/v2/status',http_status=200,
                tls_verified=True,hostname_verified=True,pin_verified=True,hmac_request_used=True)|changes


def monitoring_payload(component, *, age=0, mode='active', state='available', interval=None, now=NOW):
    values={'cpu.utilization':0,'ram.total':16*1024**3,'ram.used':8*1024**3,'ram.available':8*1024**3,'ram.utilization':50,
            'gpu.adlx.utilization':0,'gpu.adlx.temperature':45,'gpu.adlx.hotspot_temperature':55,
            'gpu.adlx.vram_used_mb':512,'gpu.adlx.vram_total_mb':12288,'gpu.adlx.core_clock':500,
            'gpu.adlx.power':15,'gpu.adlx.fan_rpm':0}
    metrics=[]
    for key in GROUPS[component]:
        spec=SPECS[key];gpu=component==C.GPU;static=key.endswith('total_mb')
        cadence=60 if static else 10 if gpu and mode=='inactive' else 2 if gpu else interval or (5 if mode=='inactive' else 1)
        metric=dict(id=key,unit=spec.unit.value,source='fixture.adlx' if gpu else 'fixture.metrics',data_kind='simulated',
                    state=state,value=values[key] if state=='available' else None,valid=state=='available',stale=state=='stale',
                    collected_at=(now-timedelta(seconds=age)).isoformat(),age_seconds=age,interval_seconds=cadence)
        if gpu and not static and state=='available':
            metric.update(ingress_age_seconds=.25,information_age_seconds=age+.25)
        metrics.append(metric)
    return dict(schema_version=1,running=True,mode=mode,snapshot=dict(schema_version=1,sequence=1,
                generated_at=now.isoformat(),contains_simulated=True,metrics=metrics))


def startup_payload():
    return dict(schema_version=1,configured=True,target_verified=True,login_at=(NOW-timedelta(seconds=30)).isoformat(),
                same_session_verified=True,lineage_verified=True,dispatch_proven=None,
                events=[dict(utc=(NOW-timedelta(seconds=20)).isoformat(),pid=101,event='attempt',phase='supervisor'),
                        dict(utc=(NOW-timedelta(seconds=10)).isoformat(),pid=102,event='bootstrap_ready',phase='worker')])


def mixed_review():
    inputs={C.HTTPS:status_payload(),
            C.LISTENER:dict(schema_version=1,port=8776,present=True,image_verified=True,creation_verified=True,parent_verified=True),
            C.IPC:dict(schema_version=1,connected=False,local=True,sid_verified=True,session_verified=True,server_identity_verified=True,contract_version=1,result='disconnected'),
            C.CPU:monitoring_payload(C.CPU,age=4),C.GPU:monitoring_payload(C.GPU,state='unsupported'),
            C.RAM:monitoring_payload(C.RAM,state='error'),
            C.ADLX:dict(schema_version=1,running=True,library_verified=True,last_frame='invalid_frame',ingress_age_seconds=None,sample_age_seconds=None),
            C.STARTUP:startup_payload()}
    engine=DiagnosticEngine([ReceiptProvider(c,FixtureReader([receipt(data)])) for c,data in inputs.items()])
    return engine.collect(NOW,100)
