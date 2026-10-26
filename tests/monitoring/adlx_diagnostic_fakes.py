"""Synthetic frames/resources only. No native construction, UI, files or sensors."""
from collections import deque
from copy import deepcopy
import time
from monitoring.adlx_bridge import DYNAMIC,NativeAdapter
from monitoring.adlx_diagnostics import PROFILE,CLOCKS
from monitoring.contracts import DataKind


def frame(*,clock='unix_ms',stamp=1790000000000,age=.1,diagnostics=True):
    readings={
        'gpu.adlx.utilization':{'state':'available','value':12.5},
        'gpu.adlx.temperature':{'state':'available','value':42},
        'gpu.adlx.hotspot_temperature':{'state':'available','value':52},
        'gpu.adlx.vram_used_mb':{'state':'available','value':1024},
        'gpu.adlx.core_clock':{'state':'available','value':500},
        'gpu.adlx.power':{'state':'available','value':18},
        'gpu.adlx.fan_rpm':{'state':'available','value':0}}
    value={'v':1,'event':'frame','timestamp_ms':stamp,'age_seconds':age,'clock_source':clock,'readings':readings}
    if diagnostics:
        deltas={name:(int(age*1000) if name==clock and age is not None else 1000000000000) for name in CLOCKS}
        value['diagnostic']={'profile':PROFILE,'rule':'clock_matched','timestamp_unit':'milliseconds','age_unit':'seconds',
            'deltas_ms':deltas,'match_count':1,'converted_age_seconds':age,'selected_clock':clock}
    return value


def unmatched(*,stamp=0,delta=-1):
    value=frame(stamp=stamp,age=None)
    value['clock_source']='unverified';d=value['diagnostic']
    d.update(rule='clock_unmatched',deltas_ms={'uptime_ms':delta,'unix_ms':1000000000000,'windows_ms':12000000000000},
        match_count=0,converted_age_seconds=None,selected_clock='unverified')
    return value


class Process:
    pid=12345;returncode=None


class MemoryTransport:
    def __init__(self,frames,diagnostics=True):
        self.process=Process();self.frames=deque(deepcopy(frames));self.queue=deque();self.sent=[];self.starts=0;self.closed=False;self.received_at=None
        self.ready={'v':1,'event':'ready','simulated':True,'pid':12345,
            'device':{'key':'amd-rx6750xt','name':'AMD Radeon RX 6750 XT','vendor_id':4098,'discrete':True},
            'sdk_version':'fixture','sdk_interval_ms':1000,'total_vram_mb':{'state':'available','value':12288},
            'capabilities':{name:{'ok':True,'supported':True} for name in DYNAMIC}}
        if diagnostics:self.ready['diagnostic_profile']=PROFILE
    def start(self):self.starts+=1;self.queue.append(self.ready)
    def receive(self,timeout):return self.queue.popleft(),self.received_at if self.received_at is not None else time.monotonic()
    def send(self,command):
        self.sent.append(command)
        if command=='latest':self.queue.append(self.frames.popleft())
    def close(self):self.closed=True;self.process.returncode=0;return True


def adapter(frames,*,diagnostics=True):
    transport=MemoryTransport(frames,diagnostics)
    a=NativeAdapter(transport,data_kind=DataKind.SIMULATED,diagnostics=diagnostics);a.open();return a
