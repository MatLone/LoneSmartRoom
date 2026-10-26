"""Explicit fixtures. No OS, HTTPS, IPC, sensor or startup probe is implemented."""
from collections import deque
from itertools import islice

from .contracts import Component, DiagnosticError, Probe


class SimulatedProvider:
    evidence_kind = 'simulated'

    def __init__(self, component, frames=()):
        if type(component) is not Component:
            raise DiagnosticError('invalid_component')
        frames = tuple(islice(frames, 65))
        if len(frames) > 64:
            raise DiagnosticError('fixture_queue_limit')
        self.component = component
        self._frames = deque(frames)
        self.reads = 0

    def read(self):
        self.reads += 1
        if not self._frames:
            return None
        frame = self._frames.popleft()
        if isinstance(frame, Exception):
            raise frame
        return frame


def healthy_fixture(component, now, monotonic):
    facts = {
        Component.HTTPS:dict(responded=True, authenticated=True, tls_verified=True),
        Component.LISTENER:dict(present=True, identity_matches=True, port=8776),
        Component.IPC:dict(connected=True, peer_validated=True, contract_version=1),
        Component.CPU:dict(collector_running=True, sample_valid=True, sample_stale=False),
        Component.GPU:dict(collector_running=True, sample_valid=True, sample_stale=False),
        Component.RAM:dict(collector_running=True, sample_valid=True, sample_stale=False),
        Component.ADLX:dict(running=True, dll_verified=True, sample_valid=True, sample_stale=False),
        Component.STARTUP:dict(configured=True, login_observed=True, dispatch_observed=True, bootstrap_succeeded=True),
    }
    return Probe(component, now, monotonic, facts[component])
