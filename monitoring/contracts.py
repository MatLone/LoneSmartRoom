"""Versioned, bounded telemetry contract; all values are explicit about availability."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
import math
import re

SCHEMA_VERSION = 1
MAX_METRICS = 64


class ContractError(ValueError):
    """Public errors deliberately exclude the rejected input or exception text."""


class Unit(StrEnum):
    PERCENT = 'percent'
    CELSIUS = 'celsius'
    BYTES = 'bytes'
    BYTES_PER_SECOND = 'bytes_per_second'
    RPM = 'rpm'


class Cadence(StrEnum):
    FAST = 'fast'
    THERMAL = 'thermal'
    CAPACITY = 'capacity'


class Availability(StrEnum):
    AVAILABLE = 'available'
    UNSUPPORTED = 'unsupported'
    UNAVAILABLE = 'unavailable'
    PERMISSION_DENIED = 'permission_denied'
    WARMING_UP = 'warming_up'
    ERROR = 'error'
    STALE = 'stale'  # Derived by cache, never accepted from a provider.


class DataKind(StrEnum):
    NOT_COLLECTED = 'not_collected'
    SIMULATED = 'simulated'
    REAL = 'real'  # Reserved for future, separately authorized providers.


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z][a-z0-9_.-]{0,79}', value):
        raise ContractError('invalid_identifier')
    return value


def utc(value):
    if (not isinstance(value, datetime) or value.tzinfo is None
            or value.utcoffset() != timedelta(0)):
        raise ContractError('utc_timestamp_required')
    return value


def utc_text(value):
    return utc(value).astimezone(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def finite(value):
    if type(value) not in (int, float):
        raise ContractError('invalid_number')
    try:
        if not math.isfinite(value):
            raise ContractError('invalid_number')
    except OverflowError:
        raise ContractError('invalid_number') from None
    return value


def monotonic_time(value):
    if finite(value) < 0:
        raise ContractError('invalid_monotonic_time')
    return value


@dataclass(frozen=True, slots=True)
class MetricSpec:
    metric_id: str
    component_id: str
    label: str
    unit: Unit
    cadence: Cadence

    def __post_init__(self):
        identifier(self.metric_id)
        identifier(self.component_id)
        if (not isinstance(self.label, str) or not 1 <= len(self.label) <= 80
                or any(ord(c) < 32 or ord(c) == 127 for c in self.label)):
            raise ContractError('invalid_label')
        if not isinstance(self.unit, Unit) or not isinstance(self.cadence, Cadence):
            raise ContractError('invalid_metric_spec')

    def validate_value(self, value):
        finite(value)
        if self.unit in (Unit.BYTES, Unit.RPM) and type(value) is not int:
            raise ContractError('integer_required')
        limits = {Unit.PERCENT: (0, 100), Unit.CELSIUS: (-273.15, 300),
                  Unit.BYTES: (0, 2**63 - 1), Unit.RPM: (0, 1_000_000),
                  Unit.BYTES_PER_SECOND: (0, 2**63 - 1)}
        low, high = limits[self.unit]
        if not low <= value <= high:
            raise ContractError('value_out_of_range')

    def as_dict(self):
        return dict(id=self.metric_id, component=self.component_id, label=self.label,
                    unit=self.unit.value, cadence=self.cadence.value)


def catalog(specs):
    values = tuple(specs)
    if not 1 <= len(values) <= MAX_METRICS or any(type(s) is not MetricSpec for s in values):
        raise ContractError('invalid_catalog')
    if len({s.metric_id for s in values}) != len(values):
        raise ContractError('duplicate_metric')
    return {s.metric_id: s for s in values}


@dataclass(frozen=True, slots=True)
class Observation:
    metric_id: str
    value: int | float | None
    state: Availability = Availability.AVAILABLE

    def validate(self, spec):
        if self.metric_id != spec.metric_id or not isinstance(self.state, Availability):
            raise ContractError('invalid_observation')
        if self.state == Availability.STALE:
            raise ContractError('provider_cannot_set_stale')
        if self.state == Availability.AVAILABLE:
            spec.validate_value(self.value)
        elif self.value is not None:
            raise ContractError('unavailable_value_must_be_null')


@dataclass(frozen=True, slots=True)
class Sample:
    observation: Observation
    source: str
    data_kind: DataKind
    collected_at: datetime | None
    collected_monotonic: float | None
    interval_seconds: float

    def validate(self, spec):
        if type(self.observation) is not Observation:
            raise ContractError('invalid_observation')
        self.observation.validate(spec)
        identifier(self.source)
        if not isinstance(self.data_kind, DataKind) or not 0 < finite(self.interval_seconds) <= 3600:
            raise ContractError('invalid_sample')
        if self.collected_at is None or self.collected_monotonic is None:
            if (self.collected_at is not None or self.collected_monotonic is not None
                    or self.observation.state == Availability.AVAILABLE
                    or self.data_kind != DataKind.NOT_COLLECTED):
                raise ContractError('invalid_uncollected_sample')
        else:
            utc(self.collected_at)
            monotonic_time(self.collected_monotonic)
            if self.data_kind == DataKind.NOT_COLLECTED:
                raise ContractError('invalid_sample_kind')

    def view(self, spec, now, stale_factor):
        age = None if self.collected_monotonic is None else now - self.collected_monotonic
        if age is not None and age < 0:
            raise ContractError('clock_moved_backwards')
        stale = age is not None and age >= self.interval_seconds * stale_factor
        state = self.observation.state
        if stale and state == Availability.AVAILABLE:
            state = Availability.STALE
        valid = state == Availability.AVAILABLE
        return {**spec.as_dict(), 'source': self.source, 'data_kind': self.data_kind.value,
                'value': self.observation.value if valid else None, 'state': state.value,
                'valid': valid, 'stale': stale,
                'collected_at': utc_text(self.collected_at) if self.collected_at else None,
                'age_seconds': round(age, 6) if age is not None else None,
                'interval_seconds': self.interval_seconds}
