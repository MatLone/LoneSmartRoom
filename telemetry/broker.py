"""One latest snapshot; no collection, polling, worker creation or persistent secrets."""
from copy import deepcopy
from datetime import datetime, timezone
import secrets
from threading import RLock
import time

from .contract import project, stamp


class SnapshotBroker:
    def __init__(self, *, simulation=False, monotonic=time.monotonic, utc=time.time):
        self.simulation, self.monotonic, self.utc = simulation, monotonic, utc
        self.generation = secrets.token_hex(16)
        self.lock = RLock()
        self.last = None
        self.at = None
        self.accepted = 0
        self.rejected = 0
        self.last_rejection = None

    def publish(self, snapshot):
        received = self.monotonic()
        try:
            value = project(snapshot, simulation=self.simulation, now=self.utc())
        except (ValueError,TypeError) as error:
            # Fixed internal rule only: never raw exception text/payloads/paths.
            allowed = {'inconsistent_capacity','inconsistent_occupation','inconsistent_vram','invalid_provenance',
                'invalid_timestamp','expired_snapshot','invalid_interval','unexpected_source','invalid_adlx_ingress',
                'future_sample','missing_sample','null_required','unexpected_metric','unexpected_unit','invalid_state'}
            code = error.args[0] if len(error.args)==1 and type(error.args[0]) is str else None
            with self.lock:
                self.rejected += 1
                self.last_rejection = code if code in allowed else 'invalid_snapshot'
            raise
        with self.lock:
            if self.last and value['sequence'] <= self.last['sequence']:
                return False  # Re-reading a cache must not renew its residence time.
            lag = max(0, self.utc() - stamp(value['generated_at']))
            for m in value['metrics']:
                if m['age_seconds'] is not None: m['age_seconds'] += lag
            self.last, self.at = value, received
            self.accepted += 1
        return True

    def diagnostics(self):
        with self.lock:
            return dict(v=1,accepted=self.accepted,rejected=self.rejected,last_rule=self.last_rejection)

    def clear(self):
        with self.lock:
            self.last = None; self.at = None
            self.generation = secrets.token_hex(16)

    def read(self):
        with self.lock:
            now = self.monotonic()
            if self.last is None or now < self.at:
                return dict(ok=True, telemetry_version=1, generation=self.generation, state='unavailable', snapshot=None)
            result = deepcopy(self.last)
            for m in result['metrics']:
                age = m['age_seconds']
                if age is not None:
                    m['age_seconds'] = round(age + now - self.at, 6)
                    expired = m['age_seconds'] >= m['expires_after_seconds']
                    if expired:
                        m.update(value=None, valid=False, stale=True)
                        if m['state'] == 'available': m['state'] = 'stale'
            return dict(ok=True, telemetry_version=1, generation=self.generation, state='available', snapshot=result)
