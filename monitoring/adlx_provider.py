"""Opt-in ADLX provider core with an injected, narrow READ-ONLY adapter.

No DLL loader, SDK, ctypes, file, network, process or tuning API is imported here.
The native adapter is a separately reviewed dependency, not implemented/installed
by this mock-only phase. This provider is NOT wired into installed/source workers.
"""
from dataclasses import dataclass
import math
import re
from threading import RLock
from typing import Protocol

from .contracts import Availability as A, Cadence as C, ContractError, DataKind, MetricSpec as M, Observation as O, Unit as U


@dataclass(frozen=True)
class Channel:
    key: str
    getter: str
    support: str | None
    unit: U
    cadence: C


CHANNELS=(
    Channel('utilization','GPUUsage','IsSupportedGPUUsage',U.PERCENT,C.FAST),
    Channel('temperature','GPUTemperature','IsSupportedGPUTemperature',U.CELSIUS,C.THERMAL),
    Channel('hotspot_temperature','GPUHotspotTemperature','IsSupportedGPUHotspotTemperature',U.CELSIUS,C.THERMAL),
    Channel('vram_used_mb','GPUVRAM','IsSupportedGPUVRAM',U.MEGABYTES,C.FAST),
    Channel('vram_total_mb','TotalVRAM',None,U.MEGABYTES,C.CAPACITY),
    Channel('core_clock','GPUClockSpeed','IsSupportedGPUClockSpeed',U.MEGAHERTZ,C.FAST),
    Channel('power','GPUPower','IsSupportedGPUPower',U.WATTS,C.THERMAL),
    Channel('fan_rpm','GPUFanSpeed','IsSupportedGPUFanSpeed',U.RPM,C.THERMAL),
)
GPU_SPECS=tuple(M('gpu.adlx.'+c.key,'gpu.amd','ADLX · '+c.key,c.unit,c.cadence) for c in CHANNELS)
BY_ID={s.metric_id:c for s,c in zip(GPU_SPECS,CHANNELS)}
SPECS={s.metric_id:s for s in GPU_SPECS}


@dataclass(frozen=True)
class Device:
    key: str
    name: str
    vendor_id: int
    discrete: bool


@dataclass(frozen=True)
class Capability:
    # ok+supported are distinct: an unsuccessful capability query is NOT unsupported.
    ok: bool
    supported: bool


@dataclass(frozen=True)
class Reading:
    state: A
    value: int | float | None


@dataclass(frozen=True)
class Frame:
    device_key: str
    sdk_timestamp_ms: int
    age_seconds: float
    readings: dict[str, Reading]


class ReadOnlyAdapter(Protocol):
    data_kind: DataKind
    def open(self): ...
    def devices(self) -> tuple[Device,...]: ...
    def capabilities(self, device_key: str) -> dict[str,Capability]: ...
    def total_vram(self, device_key: str) -> Reading: ...
    def latest(self, device_key: str) -> Frame: ...
    def close(self): ...


class DeviceLost(RuntimeError):
    """Fixed adapter indication of an invalid/removed GPU, not a transient read failure."""


class WarmingUp(RuntimeError):
    """The SDK history buffer has not produced its first sample yet."""


class AdlxProvider:
    metric_ids=tuple(BY_ID)

    def __init__(self,adapter:ReadOnlyAdapter,device_key:str,*,minimum_interval=1.0,maximum_sample_age=1.5):
        if (not isinstance(device_key,str) or not re.fullmatch(r'[a-z0-9_.-]{1,64}',device_key)
                or type(minimum_interval) not in (int,float) or not math.isfinite(minimum_interval) or not 1<=minimum_interval<=60
                or type(maximum_sample_age) not in (int,float) or not math.isfinite(maximum_sample_age) or not 0<maximum_sample_age<=5):
            raise ContractError('invalid_adlx_configuration')
        if (getattr(adapter,'data_kind',None) not in (DataKind.SIMULATED,DataKind.REAL)
                or not isinstance(adapter.data_kind,DataKind)
                or any(not callable(getattr(adapter,name,None)) for name in ('open','devices','capabilities','total_vram','latest','close'))):
            raise ContractError('invalid_adlx_provenance')
        self.data_kind=adapter.data_kind;self.source='fixture.adlx' if self.data_kind==DataKind.SIMULATED else 'amd.adlx'
        self._adapter=adapter;self._key=device_key;self._minimum=minimum_interval;self._max_age=maximum_sample_age
        self._lock=RLock();self._opened=False;self._attempted=False;self._closed=False;self._caps={}
        self._last_attempt=None;self._last_stamp=None;self._capacity=Reading(A.UNAVAILABLE,None);self._events=[];self._released=False

    def _event(self,code):
        self._events.append(code);self._events=self._events[-16:]

    def _note(self,rule,metric=None):
        # Optional local diagnostics; cannot alter success/failure of a metric read.
        callback=getattr(self._adapter,'note_provider',None)
        if callable(callback):
            try:callback(rule,metric=metric)
            except Exception:pass

    def diagnostics(self):
        return {'opened':self._opened,'closed':self._closed,'sdk_timestamp_ms':self._last_stamp,'events':tuple(self._events)}

    def _prepare(self):
        self._attempted=True
        self._adapter.open()
        devices=self._adapter.devices()
        if type(devices) not in (tuple,list) or not 1<=len(devices)<=16 or any(type(d) is not Device for d in devices) or len({d.key for d in devices})!=len(devices):
            raise ContractError('invalid_adlx_devices')
        selected=[d for d in devices if d.key==self._key]
        if len(selected)!=1:raise ContractError('adlx_device_not_found')
        d=selected[0]
        if (d.vendor_id!=0x1002 or d.discrete is not True or not isinstance(d.name,str)
                or len(d.name)>128 or re.sub('[^A-Z0-9]','',d.name.upper()) not in ('AMDRADEONRX6750XT','RADEONRX6750XT')):
            raise ContractError('unexpected_adlx_device')
        caps=self._adapter.capabilities(self._key)
        if not isinstance(caps,dict) or not set(caps)<=set(BY_ID):raise ContractError('invalid_adlx_capabilities')
        for cap in caps.values():
            if type(cap) is not Capability or type(cap.ok) is not bool or type(cap.supported) is not bool:
                raise ContractError('invalid_adlx_capability')
        self._caps=dict(caps)
        # TotalVRAM has no IsSupported* method: its return status is the capability evidence.
        try:
            self._capacity=self._validate('gpu.adlx.vram_total_mb',self._adapter.total_vram(self._key))
            if self._capacity.state==A.AVAILABLE and self._capacity.value==0:self._capacity=Reading(A.ERROR,None)
        except Exception:self._capacity=Reading(A.ERROR,None)
        self._opened=True

    @staticmethod
    def _validate(key,value):
        if type(value) is not Reading or value.state==A.STALE:raise ContractError('invalid_adlx_reading')
        O(key,value.value,value.state).validate(SPECS[key])
        # Native getters for these quantities return adlx_int/adlx_uint.
        if value.state==A.AVAILABLE and BY_ID[key].unit in (U.MEGABYTES,U.MEGAHERTZ,U.RPM) and type(value.value) is not int:
            raise ContractError('invalid_adlx_integer')
        return value

    def read(self,ids,context):
        with self._lock:
            if not ids or len(ids)!=len(set(ids)) or not set(ids)<=set(BY_ID):raise ContractError('invalid_adlx_request')
            empty=lambda state:[O(key,None,state) for key in ids]
            if self._closed or context.stop_requested.is_set():return empty(A.UNAVAILABLE)
            if not self._opened:
                if self._attempted:return empty(A.UNAVAILABLE)  # no repeated bootstrap/loading loop
                try:self._prepare()
                except PermissionError:self._event('permission_denied');self._release(True);return empty(A.PERMISSION_DENIED)
                except Exception:self._event('initialization_failed');self._release(True);return empty(A.ERROR)
            results={};dynamic=[]
            for key in ids:
                if key=='gpu.adlx.vram_total_mb':
                    value=self._capacity;results[key]=O(key,value.value,value.state);continue
                cap=self._caps.get(key)
                if cap is None or not cap.ok:results[key]=O(key,None,A.UNAVAILABLE)
                elif not cap.supported:results[key]=O(key,None,A.UNSUPPORTED)
                else:dynamic.append(key)
            if dynamic:
                if self._last_attempt is not None and context.started_monotonic-self._last_attempt<self._minimum:
                    results.update((key,O(key,None,A.UNAVAILABLE)) for key in dynamic)
                else:
                    self._last_attempt=context.started_monotonic
                    try:
                        frame=self._adapter.latest(self._key)
                        if (type(frame) is not Frame or frame.device_key!=self._key or type(frame.sdk_timestamp_ms) is not int
                                or not 0<=frame.sdk_timestamp_ms<=2**63-1 or type(frame.age_seconds) not in (int,float)
                                or not math.isfinite(frame.age_seconds) or not 0<=frame.age_seconds<=self._max_age
                                or not isinstance(frame.readings,dict) or not set(frame.readings)<=set(BY_ID)):
                            stale=(type(frame) is Frame and type(frame.age_seconds) in (int,float)
                                   and frame.age_seconds>self._max_age)
                            self._note('provider_sample_age_limit' if stale else 'provider_frame_shape')
                            raise ContractError('invalid_adlx_frame')
                        if self._last_stamp is not None and frame.sdk_timestamp_ms<=self._last_stamp:
                            self._note('provider_timestamp_not_advanced')
                            self._event('sample_not_advanced');results.update((k,O(k,None,A.UNAVAILABLE)) for k in dynamic)
                        else:
                            self._last_stamp=frame.sdk_timestamp_ms
                            for key in dynamic:
                                try:
                                    value=self._validate(key,frame.readings.get(key,Reading(A.UNAVAILABLE,None)))
                                    results[key]=O(key,value.value,value.state,
                                                   frame.age_seconds if value.state==A.AVAILABLE else None)
                                except Exception:
                                    results[key]=O(key,None,A.ERROR);self._event('invalid_reading');self._note('provider_reading_invalid',key)
                            used=frame.readings.get('gpu.adlx.vram_used_mb')
                            if (used and used.state==A.AVAILABLE and self._capacity.state==A.AVAILABLE
                                    and type(used.value) is int and used.value>self._capacity.value):
                                if 'gpu.adlx.vram_used_mb' in results:results['gpu.adlx.vram_used_mb']=O('gpu.adlx.vram_used_mb',None,A.ERROR)
                                self._event('inconsistent_vram')
                                self._note('provider_vram_inconsistent','gpu.adlx.vram_used_mb')
                    except WarmingUp:
                        results.update((k,O(k,None,A.WARMING_UP)) for k in dynamic)
                    except DeviceLost:
                        self._opened=False;self._event('device_lost');self._release(True);return empty(A.UNAVAILABLE)
                    except PermissionError:results.update((k,O(k,None,A.PERMISSION_DENIED)) for k in dynamic);self._event('permission_denied')
                    except Exception:results.update((k,O(k,None,A.ERROR)) for k in dynamic);self._event('read_failed')
            if context.stop_requested.is_set():return empty(A.UNAVAILABLE)
            return [results[k] for k in ids]

    def _release(self,suppress=False):
        if self._attempted and not self._released:
            self._released=True
            try:self._adapter.close()
            except Exception:
                self._event('close_failed')
                if not suppress:raise

    def close(self):
        with self._lock:
            if self._closed:return
            self._closed=True;self._opened=False
            self._release()


def basic_v1_projection(snapshot):
    """Future explicit boundary only; not wired to live IPC. GPU fields never leak to legacy UI."""
    from .windows_basic import basic_catalog
    allowed={s.metric_id for s in basic_catalog(('C:\\','D:\\'))}
    metrics=[m for m in snapshot['metrics'] if m['id'] in allowed]
    return {**snapshot,'metrics':metrics,'contains_simulated':any(m['data_kind']=='simulated' for m in metrics)}
