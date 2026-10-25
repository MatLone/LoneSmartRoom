"""Owned basic provider composition. Injected API only; import never starts sensors."""
from .collector import Collector
from .windows_basic import CpuProvider, MemoryProvider, VolumeProvider, DiskIoProvider, basic_catalog


def create_basic_collector(sensors):
    volumes=tuple(v for v in sensors.fixed_volumes() if v in ('C:\\','D:\\'))
    providers=[CpuProvider(sensors),MemoryProvider(sensors)]+[VolumeProvider(sensors,v) for v in volumes]
    opened=False
    try:
        if volumes:
            opened=True
            sensors.open_disk_query(volumes)  # Required native setup, before the collector thread's first read.
            providers.append(DiskIoProvider(sensors,volumes))
        return Collector(basic_catalog(volumes),providers)
    except Exception:
        if opened:sensors.close_disk_query()
        raise
