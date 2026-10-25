"""Read-only IPC boundary, NOT a native transport or a proof of Windows ACLs.

Nothing binds a socket/pipe. A future trusted Windows adapter must authenticate the
peer from its OS token and enforce the documented pipe DACL BEFORE calling handle.
PeerEvidence is internal transport input, never a field accepted from JSON.
"""
from dataclasses import dataclass
import json
import re
from threading import Lock

from .contracts import ContractError, SCHEMA_VERSION, monotonic_time

MAX_REQUEST_BYTES = 256
MAX_RESPONSE_BYTES = 128 * 1024


@dataclass(frozen=True, slots=True)
class PeerEvidence:
    user_sid: str
    session_id: int
    authenticated: bool
    remote: bool


@dataclass(frozen=True, slots=True)
class LocalAccessPolicy:
    user_sid: str
    session_id: int

    def __post_init__(self):
        if (not isinstance(self.user_sid, str) or len(self.user_sid) > 184
                or not re.fullmatch(r'S-1-(?:[0-9]+-)+[0-9]+', self.user_sid)
                or type(self.session_id) is not int or not 0 <= self.session_id <= 2**32 - 1):
            raise ContractError('invalid_local_identity')

    def allows(self, peer):
        return (type(peer) is PeerEvidence and peer.authenticated is True and peer.remote is False
                and peer.user_sid == self.user_sid and type(peer.session_id) is int
                and peer.session_id == self.session_id)


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError('duplicate_json_key')
        result[key] = value
    return result


def _reject_constant(_value):
    raise ContractError('invalid_json_constant')


def encode(value):
    return json.dumps(value, ensure_ascii=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def error(code):
    return encode({'ok': False, 'error': code})


class LocalReadService:
    """Logical admission tests are not a substitute for future native ACL tests.

    Global token bucket bounds read work without an unbounded per-peer dictionary.
    No history, subscription, execution, lifecycle or configuration operations.
    """
    def __init__(self, collector, policy):
        if type(policy) is not LocalAccessPolicy:
            raise ContractError('local_policy_required')
        self._collector = collector
        self._policy = policy
        self._lock = Lock()
        self._tokens = 4.0
        self._last = None

    def _admit(self):
        now = monotonic_time(self._collector.clock.monotonic())
        with self._lock:
            if self._last is not None:
                if now < self._last:
                    return False
                self._tokens = min(4.0, self._tokens + (now - self._last) * 2)
            self._last = now
            if self._tokens < 1:
                return False
            self._tokens -= 1
            return True

    def handle(self, frame, peer):
        if not self._policy.allows(peer):
            return error('access_denied')
        try:
            if not self._admit():
                return error('rate_limited')
            if type(frame) is not bytes or not 1 <= len(frame) <= MAX_REQUEST_BYTES:
                return error('invalid_request')
            try:
                request = json.loads(frame.decode('utf-8'), object_pairs_hook=_object,
                                     parse_constant=_reject_constant)
            except (UnicodeDecodeError, ValueError, RecursionError):
                return error('invalid_request')
            if (type(request) is not dict or set(request) != {'v', 'op'}
                    or type(request['v']) is not int or request['v'] != SCHEMA_VERSION
                    or type(request['op']) is not str
                    or request['op'] not in ('snapshot', 'capabilities')):
                return error('invalid_request')
            if self._collector.state in ('stopping', 'stopped'):
                return error('collector_stopped')
            if request['op'] == 'snapshot':
                body = {'ok': True, 'snapshot': self._collector.snapshot()}
            else:
                body = {'ok': True, 'schema_version': SCHEMA_VERSION,
                        'transport': 'not_implemented',
                        'hardware_inventory': 'declared_slots_not_detected',
                        'real_providers_included': False,
                        'metrics': [spec.as_dict() for spec in self._collector.cache.specs.values()]}
            response = encode(body)
            return response if len(response) <= MAX_RESPONSE_BYTES else error('response_too_large')
        except Exception:
            # Do not echo inputs, SID, paths, provider data or exception messages.
            return error('service_unavailable')
