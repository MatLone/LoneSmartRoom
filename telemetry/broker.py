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

    def publish(self, snapshot):
        received = self.monotonic()
        value = project(snapshot, simulation=self.simulation, now=self.utc())
        with self.lock:
            if self.last and value['sequence'] <= self.last['sequence']:
                return False  # Re-reading a cache must not renew its residence time.
            lag = max(0, self.utc() - stamp(value['generated_at']))
            for m in value['metrics']:
                if m['age_seconds'] is not None: m['age_seconds'] += lag
            self.last, self.at = value, received
        return True

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
