"""Coherent synthetic metrics, NEVER labeled as real measurements."""
from monitoring.contracts import DataKind, Observation


class FixtureProvider:
    source = 'fixture.metrics'
    data_kind = DataKind.SIMULATED

    def __init__(self, specs): self.metric_ids = tuple(s.metric_id for s in specs)

    def read(self, ids, context):
        result = []
        for key in ids:
            if key == 'cpu.utilization': value = 25.0
            elif key.startswith('ram.'):
                value = {'total': 16*1024**3, 'used': 8*1024**3,
                         'available': 8*1024**3, 'utilization': 50.0}[key.split('.')[-1]]
            else:
                value = {'total': 256*1024**3, 'free': 192*1024**3, 'available': 192*1024**3,
                         'used': 64*1024**3, 'occupation': 25.0, 'read_rate': 1024.0,
                         'write_rate': 2048.0, 'activity': 1.0}[key.split('.')[-1]]
            result.append(Observation(key, value))
        return result

    def close(self): pass
