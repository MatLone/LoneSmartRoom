"""Owned basic provider composition. Injected API only; import never starts sensors."""
from dataclasses import replace
from .collector import Collector, Schedule
from .windows_basic import CpuProvider, MemoryProvider, VolumeProvider, DiskIoProvider, basic_catalog


def create_basic_collector(sensors, *, gpu_adapter=None, clock=None):
    volumes=tuple(v for v in sensors.fixed_volumes() if v in ('C:\\','D:\\'))
    providers=[CpuProvider(sensors),MemoryProvider(sensors)]+[VolumeProvider(sensors,v) for v in volumes]
    opened=False
    try:
        if volumes:
            opened=True
            sensors.open_disk_query(volumes)  # Required native setup, before the collector thread's first read.
            providers.append(DiskIoProvider(sensors,volumes))
        specs=basic_catalog(volumes)
        schedule=None
        if gpu_adapter is not None:
            # All dynamic GPU metrics share a 2 s cadence; CPU/RAM/I/O stay at 1 s.
            from .adlx_provider import AdlxProvider, GPU_SPECS
            from .contracts import Cadence
            specs=(*specs,*(replace(s,cadence=Cadence.THERMAL) if s.cadence!=Cadence.CAPACITY else s for s in GPU_SPECS))
            providers.append(AdlxProvider(gpu_adapter,'amd-rx6750xt',minimum_interval=2,maximum_sample_age=1.5))
            schedule=Schedule(thermal=2,inactive_thermal=10,read_budget=1)
        return Collector(specs,providers,schedule=schedule,clock=clock)
    except Exception:
        if opened:sensors.close_disk_query()
        raise
