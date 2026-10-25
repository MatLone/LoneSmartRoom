"""Basic read-only providers; native API is injected and never constructed here."""
from dataclasses import dataclass
import math
import re

from .contracts import (Availability as A, Cadence as C, ContractError, DataKind,
                        MetricSpec as M, Observation as O, Unit as U)


def volume_root(root):
    if not isinstance(root, str) or not re.fullmatch(r'[A-Z]:\\', root):
        raise ContractError('fixed_volume_root_required')
    return root


def basic_catalog(volumes):
    roots = tuple(volume_root(v) for v in volumes)
    if len(set(roots)) != len(roots) or len(roots) > 7:
        raise ContractError('volume_catalog_limit')
    specs = [M('cpu.utilization', 'cpu', 'CPU · tempo ocupado total', U.PERCENT, C.FAST),
             M('ram.total', 'ram', 'RAM · total físico utilizável', U.BYTES, C.FAST),
             M('ram.used', 'ram', 'RAM · utilizada', U.BYTES, C.FAST),
             M('ram.available', 'ram', 'RAM · disponível', U.BYTES, C.FAST),
             M('ram.utilization', 'ram', 'RAM · utilização', U.PERCENT, C.FAST)]
    for root in roots:
        prefix = 'storage.' + root[0].lower()
        for suffix, label, unit, cadence in (
                ('total', 'capacidade física', U.BYTES, C.CAPACITY),
                ('free', 'livre físico', U.BYTES, C.CAPACITY),
                ('available', 'disponível à conta', U.BYTES, C.CAPACITY),
                ('used', 'alocação utilizada', U.BYTES, C.CAPACITY),
                ('occupation', 'ocupação do volume', U.PERCENT, C.CAPACITY),
                ('read_rate', 'leitura', U.BYTES_PER_SECOND, C.FAST),
                ('write_rate', 'gravação', U.BYTES_PER_SECOND, C.FAST),
                ('activity', 'tempo ativo do volume · PDH', U.PERCENT, C.FAST)):
            specs.append(M(prefix + '.' + suffix, prefix, root[:2] + ' · ' + label, unit, cadence))
    return tuple(specs)


def integers(values):
    if any(type(v) is not int or not 0 <= v <= 2**64 - 1 for v in values):
        raise ContractError('invalid_native_counters')


class CpuProvider:
    source = 'win32.systemtimes'
    data_kind = DataKind.REAL
    metric_ids = ('cpu.utilization',)

    def __init__(self, api):
        self.api, self.previous = api, None

    def read(self, ids, context):
        try:
            values = tuple(self.api.cpu_times())
            if len(values) != 3:
                raise ContractError('invalid_cpu_counters')
            integers(values)
        except Exception:
            self.previous = None
            raise
        previous, self.previous = self.previous, values
        if previous is None or any(a < b for a, b in zip(values, previous)):
            return [O(ids[0], None, A.WARMING_UP)]
        idle, kernel, user = (a - b for a, b in zip(values, previous))
        total = kernel + user  # GetSystemTimes kernel includes idle.
        if total == 0:
            return [O(ids[0], None, A.WARMING_UP)]
        if idle > total:
            return [O(ids[0], None, A.ERROR)]
        return [O(ids[0], (total - idle) * 100 / total)]

    def close(self):
        self.previous = None


class MemoryProvider:
    source = 'win32.memory'
    data_kind = DataKind.REAL
    metric_ids = ('ram.total', 'ram.used', 'ram.available', 'ram.utilization')

    def __init__(self, api):
        self.api = api

    def read(self, ids, context):
        total, available = self.api.memory()
        integers((total, available))
        if total == 0 or available > total:
            raise ContractError('invalid_memory_counters')
        used = total - available
        values = dict(zip(self.metric_ids, (total, used, available, 100 * used / total)))
        return [O(key, values[key]) for key in ids]

    def close(self):
        pass


@dataclass(frozen=True)
class VolumeSpace:
    total: int
    free: int
    available: int
    used: int

    def validate(self):
        integers((self.total, self.free, self.available, self.used))
        if not 0 < self.total <= 2**63 - 1 or max(self.free, self.available, self.used) > self.total:
            raise ContractError('invalid_volume_space')


class VolumeProvider:
    data_kind = DataKind.REAL

    def __init__(self, api, root):
        self.api, self.root = api, volume_root(root)
        prefix = 'storage.' + root[0].lower()
        self.source = 'win32.volume.' + root[0].lower()
        self.metric_ids = tuple(prefix + '.' + s for s in ('total', 'free', 'available', 'used', 'occupation'))

    def read(self, ids, context):
        try:
            space = self.api.volume_space(self.root)
            space.validate()
            values = dict(zip(self.metric_ids, (space.total, space.free, space.available,
                                               space.used, 100 * space.used / space.total)))
            return [O(key, values[key]) for key in ids]
        except NotImplementedError:
            return [O(key, None, A.UNSUPPORTED) for key in ids]

    def close(self):
        pass


@dataclass(frozen=True)
class DiskCounter:
    first: int
    second: int
    value: float | None
    status: A = A.AVAILABLE


class DiskIoProvider:
    source = 'win32.pdh.logicaldisk'
    data_kind = DataKind.REAL

    def __init__(self, api, volumes):
        self.api = api
        self.metric_ids = tuple('storage.' + volume_root(root)[0].lower() + '.' + suffix
                                for root in volumes for suffix in ('read_rate', 'write_rate', 'activity'))
        self.previous = {}

    def read(self, ids, context):
        try:
            counters = self.api.disk_counters()
        except Exception:
            self.previous.clear()
            raise
        result = []
        for key in ids:
            raw = counters.get(key)
            if raw is None or raw.status != A.AVAILABLE:
                self.previous.pop(key, None)
                result.append(O(key, None, raw.status if raw else A.UNAVAILABLE))
                continue
            if (type(raw.first) is not int or type(raw.second) is not int
                    or raw.first < 0 or raw.second < 0):
                self.previous.pop(key, None)
                result.append(O(key, None, A.UNAVAILABLE))
                continue
            previous = self.previous.get(key)
            self.previous[key] = raw
            if (previous is None or raw.first < previous.first or raw.second <= previous.second):
                result.append(O(key, None, A.WARMING_UP))
                continue
            value = raw.value
            if (type(value) not in (int, float) or not math.isfinite(value) or value < 0
                    or (key.endswith('.activity') and value > 100)):
                result.append(O(key, None, A.UNAVAILABLE))
                continue
            result.append(O(key, value))
        return result

    def close(self):
        self.api.close_disk_query()
        self.previous.clear()
