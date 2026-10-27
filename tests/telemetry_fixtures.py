"""Explicitly simulated collector/cache fixtures; not PC measurements."""
from datetime import datetime, timezone
from monitoring.cache import MetricCache
from monitoring.contracts import Sample, Observation, DataKind
from telemetry.contract import SPECS


def snapshot(now, mono=100., sequence_samples=True):
    values = {'percent': 0.025, 'celsius': 43., 'bytes': 1024**3, 'bytes_per_second': 0.,
              'rpm': 0, 'megahertz': 500, 'watts': 12., 'megabytes': 100}
    cache = MetricCache(SPECS.values())
    samples = []
    for key, spec in SPECS.items():
        value = values[spec.unit.value]
        if key in ('ram.total', 'storage.c.total', 'storage.d.total'): value = 2 * 1024**3
        if key.endswith('vram_total_mb'): value = 12288
        interval = 60 if spec.cadence.value == 'capacity' else 2 if key.startswith('gpu.') else 1
        samples.append(Sample(Observation(key, value), 'fixture.adlx' if key.startswith('gpu.') else 'fixture.metrics',
            DataKind.SIMULATED, datetime.fromtimestamp(now, timezone.utc), mono, interval))
    cache.publish(samples)
    return cache.snapshot(mono, datetime.fromtimestamp(now, timezone.utc))
