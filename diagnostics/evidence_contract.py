"""Adapter receipt v1, separate from diagnostic report/telemetry v1.

Only explicit simulated evidence is accepted in this preparation stage. This
module does not load Windows APIs, open files or instantiate operational readers.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .contracts import DiagnosticError,tick,utc
from .evidence import MAX_INPUT_BYTES


class AdapterKind(StrEnum):
    AGENT='agent'
    MONITORING='monitoring'
    IPC='ipc'
    STARTUP='startup'
    SECURITY='security'


VERDICTS=('verified','mismatch','unknown')
SECURITY_CHECKS=('process_identity','tls_identity','hmac','antireplay','device_permissions','pipe_acl','local_only')
KNOWN_ISSUES=('tls_10054','startup_unresolved','graceful_shutdown_unvalidated','crashpad_0xe9','dev7_partial')


def integer(value,*,minimum=1,maximum=2**31-1):
    if type(value) is not int or not minimum<=value<=maximum:
        raise DiagnosticError('invalid_evidence_integer')
    return value


@dataclass(frozen=True,slots=True)
class EvidenceFrame:
    adapter: AdapterKind
    sequence: int
    observed_at: datetime
    observed_monotonic: float
    payload: bytes
    schema_version: int=1
    evidence_kind: str='simulated'

    def __post_init__(self):
        if type(self.adapter) is not AdapterKind:raise DiagnosticError('invalid_adapter_kind')
        integer(self.sequence);utc(self.observed_at);tick(self.observed_monotonic)
        if type(self.schema_version) is not int or self.schema_version!=1:raise DiagnosticError('incompatible_adapter_contract')
        if self.evidence_kind!='simulated':raise DiagnosticError('operational_evidence_not_authorized')
        if type(self.payload) is not bytes or not 1<=len(self.payload)<=MAX_INPUT_BYTES:raise DiagnosticError('adapter_size_limit')


@dataclass(frozen=True,slots=True)
class AdapterProjection:
    probes: tuple
    generation: int|None=None
    application_open: bool|None=None
    connected: bool|None=None
    peer_verified: bool|None=None
    security: object=None
