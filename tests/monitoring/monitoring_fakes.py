"""Synthetic fixtures only. These numbers are NOT measurements of the user's PC."""
from collections import deque
from datetime import datetime, timedelta, timezone

from monitoring.contracts import Availability, DataKind, Observation, Unit


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.wall_offset = 0

    def monotonic(self):
        return self.now

    def utcnow(self):
        return datetime(2026, 10, 24, tzinfo=timezone.utc) + timedelta(seconds=self.now + self.wall_offset)

    def advance(self, seconds):
        self.now += seconds


class FakeProvider:
    source = 'fixture.metrics'
    data_kind = DataKind.SIMULATED

    def __init__(self, specs):
        self.specs = {s.metric_id: s for s in specs}
        self.metric_ids = tuple(self.specs)
        self.calls = deque(maxlen=128)
        self.call_count = 0
        self.closed = 0
        self.failure = None
        self.state = Availability.AVAILABLE
        self.read_hook = None
        self.close_hook = None

    def read(self, ids, context):
        self.calls.append((ids, context.started_monotonic))
        self.call_count += 1
        if self.read_hook:
            return self.read_hook(ids, context)
        if self.failure:
            raise self.failure
        values = {Unit.PERCENT: 25.0, Unit.CELSIUS: 40.0, Unit.BYTES: 16 * 1024**3,
                  Unit.BYTES_PER_SECOND: 1024.0, Unit.RPM: 0}
        return [Observation(key, values[self.specs[key].unit]
                            if self.state == Availability.AVAILABLE else None, self.state) for key in ids]

    def close(self):
        self.closed += 1
        if self.close_hook:
            self.close_hook()


def by_id(snapshot):
    return {value['id']: value for value in snapshot['metrics']}
