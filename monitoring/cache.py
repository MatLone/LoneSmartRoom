"""Bounded in-memory cache; snapshots never renew a sample's collection time."""
from collections import deque
from threading import RLock
from types import MappingProxyType

from .contracts import (Availability, ContractError, DataKind, SCHEMA_VERSION,
                        Sample, catalog, finite, monotonic_time, utc_text)


class MetricCache:
    def __init__(self, specs, history_limit=120, stale_factor=3):
        self.specs = MappingProxyType(catalog(specs))
        if type(history_limit) is not int or not 1 <= history_limit <= 120:
            raise ContractError('invalid_history_limit')
        if not 1 <= finite(stale_factor) <= 10:
            raise ContractError('invalid_stale_factor')
        self.history_limit = history_limit
        self.stale_factor = stale_factor
        self._history = {key: deque(maxlen=history_limit) for key in self.specs}
        self._lock = RLock()
        self._sequence = 0
        self._last_clock = None

    def publish(self, samples):
        batch = tuple(samples)
        if len(batch) > len(self.specs):
            raise ContractError('batch_too_large')
        seen = set()
        for sample in batch:
            if type(sample) is not Sample:
                raise ContractError('invalid_sample')
            key = sample.observation.metric_id
            if key not in self.specs or key in seen:
                raise ContractError('unknown_or_duplicate_metric')
            seen.add(key)
            sample.validate(self.specs[key])
        with self._lock:
            for sample in batch:
                history = self._history[sample.observation.metric_id]
                if (history and history[-1].collected_monotonic is not None
                        and (sample.collected_monotonic is None
                             or sample.collected_monotonic < history[-1].collected_monotonic)):
                    raise ContractError('sample_time_regression')
            for sample in batch:
                self._history[sample.observation.metric_id].append(sample)
            if batch:
                self._sequence += 1

    def snapshot(self, now, generated_at):
        monotonic_time(now)
        stamp = utc_text(generated_at)
        with self._lock:
            if self._last_clock is not None and now < self._last_clock:
                raise ContractError('clock_moved_backwards')
            self._last_clock = now
            values = []
            for key, spec in self.specs.items():
                history = self._history[key]
                if history:
                    values.append(history[-1].view(spec, now, self.stale_factor))
                else:
                    values.append({**spec.as_dict(), 'source': 'unconfigured',
                                   'data_kind': DataKind.NOT_COLLECTED.value,
                                   'value': None, 'state': Availability.UNSUPPORTED.value,
                                   'valid': False, 'stale': False, 'collected_at': None,
                                   'age_seconds': None, 'interval_seconds': None})
            return {'schema_version': SCHEMA_VERSION, 'sequence': self._sequence,
                    'generated_at': stamp, 'contains_simulated': any(
                        v['data_kind'] == DataKind.SIMULATED for v in values), 'metrics': values}

    def history(self, metric_id):
        with self._lock:
            if metric_id not in self._history:
                raise ContractError('unknown_metric')
            return tuple(self._history[metric_id])

    @property
    def sample_count(self):
        with self._lock:
            return sum(len(values) for values in self._history.values())
