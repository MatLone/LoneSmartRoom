"""Limited simulated receipts. No native, network, file, log or credential reader."""
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from itertools import islice
import json

from .contracts import DiagnosticError, tick, utc

MAX_INPUT_BYTES = 32768


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise DiagnosticError('duplicate_evidence_key')
        result[key] = value
    return result


def reject_constant(_value):
    raise DiagnosticError('nonfinite_evidence')


def decode(raw):
    if type(raw) is not bytes or not 1 <= len(raw) <= MAX_INPUT_BYTES:
        raise DiagnosticError('evidence_size_limit')
    try:
        result = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=reject_constant)
    except (ValueError, UnicodeError, RecursionError, OverflowError):
        raise DiagnosticError('invalid_evidence_json') from None
    if type(result) is not dict:
        raise DiagnosticError('evidence_object_required')
    return result


def exact(value, required, optional=()):
    if type(value) is not dict or set(value)-set(required)-set(optional) or set(required)-set(value):
        raise DiagnosticError('invalid_evidence_fields')


def boolean(value, nullable=False):
    if type(value) is not bool and not (nullable and value is None):
        raise DiagnosticError('invalid_evidence_boolean')
    return value


def utc_string(value):
    if type(value) is not str or len(value)>40:
        raise DiagnosticError('invalid_evidence_time')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return utc(result)
    except ValueError:
        raise DiagnosticError('invalid_evidence_time') from None


@dataclass(frozen=True, slots=True)
class ReceiptFrame:
    observed_at: datetime
    observed_monotonic: float
    payload: bytes
    evidence_kind: str = 'simulated'

    def __post_init__(self):
        utc(self.observed_at);tick(self.observed_monotonic)
        if self.evidence_kind != 'simulated':
            raise DiagnosticError('operational_readers_not_authorized')
        if type(self.payload) is not bytes or not 1<=len(self.payload)<=MAX_INPUT_BYTES:
            raise DiagnosticError('evidence_size_limit')


class FixtureReader:
    """A finite queue, not a connection factory. No URL, pipe name or file argument."""
    def __init__(self, frames=()):
        frames=tuple(islice(frames,65))
        if len(frames)>64:
            raise DiagnosticError('fixture_queue_limit')
        self._frames=deque(frames)
        self.reads=0

    def read(self):
        self.reads+=1
        if not self._frames:
            return None
        result=self._frames.popleft()
        if result is None:
            return None
        if isinstance(result,Exception):
            raise result
        if type(result) is not ReceiptFrame:
            raise DiagnosticError('invalid_receipt_frame')
        return result
