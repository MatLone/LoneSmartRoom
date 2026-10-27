"""Bounded adapter hub, caller-driven and mock-only. No timers, I/O or repair.

Eight existing diagnostic records plus one separate security sidecar. A verified
reconnect invalidates old healthy monitoring evidence until new-generation
samples collected after reconnection arrive. Querying never renews timestamps.
"""
from dataclasses import replace
import json
from threading import RLock

from .contracts import Component as C,DetailCode as D,DiagnosticError,Outcome as O,stamp,tick,utc
from .engine import DiagnosticEngine,classify
from .evidence_adapters import ADAPTERS,GROUPS,observation
from .evidence_contract import AdapterKind as A,EvidenceFrame


class _Inbox:
    evidence_kind='simulated'
    def __init__(self,component):self.component=component;self.pending=None
    def read(self):
        value,self.pending=self.pending,None
        if isinstance(value,Exception):raise value
        return value


class EvidenceHub:
    """Does not accept readers, connection factories, URLs or filesystem paths."""
    def __init__(self):
        self._inboxes={c:_Inbox(c) for c in C}
        self._engine=DiagnosticEngine(self._inboxes.values())
        self._water={};self._errors={};self._latest={};self._last_valid={}
        self._transport=None;self._resume_at=None;self._application_open=None;self._monitoring_generation=None
        self._security=None;self._closed=False;self._clock_tick=None;self._lock=RLock()

    def _clock(self,now,monotonic):
        utc(now);tick(monotonic)
        if self._clock_tick is not None and monotonic<self._clock_tick:raise DiagnosticError('adapter_clock_regression')
        self._clock_tick=monotonic

    def _put(self,probe):
        self._latest[probe.component]=probe;self._inboxes[probe.component].pending=probe

    def _collect(self,now,monotonic,mode):
        report=self._engine.collect(now,monotonic,mode)
        for row in report['checks']:
            if row['valid']:self._last_valid[C(row['component'])]=row['observed_at']
        return report

    def _unknown_group(self,frame,detail=D.PASSIVE_UNVERIFIED,outcome=O.UNKNOWN):
        for c in GROUPS[frame.adapter]:self._put(observation(frame,c,{},detail,outcome))

    def _invalidate_monitoring(self,frame,*,disconnected=False):
        for c in GROUPS[A.MONITORING]:
            prior=self._latest.get(c)
            if self._application_open is False and prior and prior.detail_code==D.NORMAL_INACTIVE:continue
            self._put(observation(frame,c,{},D.PIPE_DISCONNECTED if disconnected else D.AWAITING_FRESH,
                O.UNAVAILABLE if disconnected else O.UNKNOWN))

    def submit(self,frame,*,now,monotonic,mode='active'):
        with self._lock:
            if mode not in ('active','inactive'):raise DiagnosticError('invalid_activity_mode')
            self._clock(now,monotonic)
            if self._closed:return {'accepted':False,'code':'closed'}
            if type(frame) is not EvidenceFrame:raise DiagnosticError('adapter_frame_required')
            old=self._water.get(frame.adapter)
            # Invalid evidence is a verification failure, not a hardware fault.
            code=None
            if frame.observed_at>now or frame.observed_monotonic>monotonic:code='future_evidence'
            elif old and (frame.sequence<=old[0] or frame.observed_at<old[1] or frame.observed_monotonic<old[2]):code='replayed_or_out_of_order'
            elif old and monotonic-old[3]<.5:return {'accepted':False,'code':'rate_limited'}
            if code is None:
                try:
                    projection=ADAPTERS[frame.adapter].project(frame)
                    if (frame.adapter in (A.IPC,A.MONITORING) and self._transport is not None
                            and projection.generation<self._transport['generation']):
                        raise DiagnosticError('old_connection_generation')
                except Exception:code='invalid_adapter_evidence'
            if code is not None:
                self._errors[frame.adapter]=code
                event=replace(frame,observed_at=now,observed_monotonic=monotonic)
                self._unknown_group(event)
                if frame.adapter==A.IPC:
                    if self._transport:self._transport['ready']=False
                    self._invalidate_monitoring(event)
                if frame.adapter==A.SECURITY:self._security=None
                self._collect(now,monotonic,mode)
                return {'accepted':False,'code':code}
            self._water[frame.adapter]=(frame.sequence,frame.observed_at,frame.observed_monotonic,monotonic)
            self._errors.pop(frame.adapter,None)
            if frame.adapter==A.IPC:
                ready=projection.peer_verified is True
                changed=(self._transport is None or projection.generation!=self._transport['generation']
                    or not self._transport['ready'] and ready)
                self._transport={'generation':projection.generation,'connected':projection.connected,'ready':ready,
                    'observed_at':frame.observed_at,'observed_monotonic':frame.observed_monotonic}
                if changed or not ready:
                    self._resume_at=frame.observed_at
                    self._invalidate_monitoring(frame,disconnected=projection.connected is False)
            if frame.adapter==A.MONITORING:
                self._application_open=projection.application_open;self._monitoring_generation=projection.generation
                if (projection.application_open is False and self._transport and self._transport['connected'] is False
                        and self._transport['generation']==projection.generation and C.IPC in self._latest):
                    self._put(replace(self._latest[C.IPC],detail_code=D.NORMAL_INACTIVE,outcome=O.UNAVAILABLE))
            for probe in projection.probes:
                if (frame.adapter==A.IPC and projection.connected is False and self._application_open is False
                        and projection.generation==self._monitoring_generation):
                    probe=replace(probe,detail_code=D.NORMAL_INACTIVE,outcome=O.UNAVAILABLE)
                if frame.adapter==A.MONITORING and probe.detail_code!=D.NORMAL_INACTIVE:
                    trusted=(self._transport is not None and self._transport['ready']
                        and projection.generation==self._transport['generation']
                        and max((now-self._transport['observed_at']).total_seconds(),monotonic-self._transport['observed_monotonic'])<5)
                    if not trusted or classify(probe)[0]=='healthy' and (self._resume_at is None or probe.observed_at<=self._resume_at):
                        probe=observation(frame,probe.component,{},D.AWAITING_FRESH)
                self._put(probe)
            if projection.security is not None:self._security=projection.security
            self._collect(now,monotonic,mode)
            return {'accepted':True,'code':'accepted'}

    def provider_failed(self,kind,*,now,monotonic,mode='active'):
        with self._lock:
            if mode not in ('active','inactive'):raise DiagnosticError('invalid_activity_mode')
            self._clock(now,monotonic)
            if type(kind) is not A:raise DiagnosticError('invalid_adapter_kind')
            if self._closed:return
            self._errors[kind]='provider_failed'
            for c in GROUPS[kind]:
                self._inboxes[c].pending=RuntimeError('sanitized_provider_failure')
            if kind==A.SECURITY:self._security=None
            if kind==A.IPC:
                if self._transport:self._transport['ready']=False
                # No stale measurements are recertified after an IPC provider error.
                for c in GROUPS[A.MONITORING]:self._inboxes[c].pending=RuntimeError('sanitized_provider_failure')
            self._collect(now,monotonic,mode)

    def snapshot(self,*,now,monotonic,mode='active'):
        with self._lock:
            if mode not in ('active','inactive'):raise DiagnosticError('invalid_activity_mode')
            self._clock(now,monotonic)
            return self._collect(now,monotonic,mode)

    def audit(self,*,now,monotonic):
        with self._lock:
            self._clock(now,monotonic)
            security=None
            if self._security is not None:
                security=json.loads(json.dumps(self._security))
                stale=False
                from .evidence import utc_string
                for row in security['checks']:
                    age=(now-utc_string(row['checked_at'])).total_seconds() if row['checked_at'] is not None else None
                    if age is not None and age<0:raise DiagnosticError('future_cached_security_evidence')
                    row['age_seconds']=age;row['stale']=age is not None and age>=10
                    stale|=row['stale']
                security['state']='error' if any(r['authorized'] and r['result']=='failed' and not r['stale'] for r in security['checks']) else 'stale' if stale else 'unknown'
            result={'schema_version':1,'simulation':True,'operational_readers':False,'closed':self._closed,
                'last_valid':{c.value:value for c,value in self._last_valid.items()},
                'adapter_errors':{k.value:v for k,v in self._errors.items()},'security':security,
                'cache':{'diagnostic_slots':len(self._latest),'maximum_diagnostic_slots':8,'maximum_security_records':1,
                    'source_watermarks':len(self._water),'maximum_sources':5,'raw_payloads_retained':False}}
            if len(json.dumps(result).encode())>8192:raise DiagnosticError('adapter_audit_limit')
            return result

    def close(self):
        with self._lock:
            self._closed=True
            for box in self._inboxes.values():box.pending=None
            self._latest.clear();self._water.clear();self._errors.clear();self._last_valid.clear();self._security=None;self._transport=None
            self._resume_at=None;self._application_open=None;self._monitoring_generation=None
            self._engine=DiagnosticEngine(self._inboxes.values())
