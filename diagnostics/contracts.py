"""Bounded diagnostic v1; deliberately separate from telemetry contract v1."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from types import MappingProxyType
import math

SCHEMA_VERSION = 1
MAX_REPORT_BYTES = 16 * 1024


class DiagnosticError(ValueError):
    """Only fixed codes may cross the diagnostic boundary, never input values."""


class Component(StrEnum):
    HTTPS = 'agent_https'
    LISTENER = 'listener_8776'
    IPC = 'monitoring_ipc'
    CPU = 'cpu_collector'
    GPU = 'gpu_collector'
    RAM = 'ram_collector'
    ADLX = 'adlx_bridge'
    STARTUP = 'agent_startup'


class Outcome(StrEnum):
    OK = 'ok'
    UNKNOWN = 'unknown'
    UNAVAILABLE = 'unavailable'
    ERROR = 'error'
    UNSUPPORTED = 'unsupported'


class DetailCode(StrEnum):
    HTTPS_OK = 'https_status_verified'
    CONNECTION_FAILED = 'connection_failed'
    TLS_FAILED = 'tls_identity_failed'
    AUTH_FAILED = 'authentication_failed'
    HTTP_FAILED = 'status_response_failed'
    LISTENER_MISMATCH = 'listener_owner_unverified'
    LISTENER_OK = 'listener_identity_verified'
    PIPE_DISCONNECTED = 'pipe_disconnected'
    PIPE_IDENTITY_FAILED = 'pipe_identity_failed'
    PIPE_CONTRACT_FAILED = 'pipe_contract_failed'
    PIPE_LIMIT = 'pipe_limit_rejected'
    METRICS_OK = 'metrics_valid'
    METRICS_PARTIAL = 'metrics_partial_support'
    METRICS_MISSING = 'metrics_missing'
    METRICS_READ_ERROR = 'metrics_read_error'
    METRICS_WARMING = 'metrics_warming_up'
    METRICS_UNSUPPORTED = 'metrics_unsupported'
    METRICS_STALE = 'metrics_stale'
    AWAITING_FRESH = 'awaiting_new_sample'
    ADLX_NOT_RUNNING = 'adlx_not_running'
    ADLX_UNVERIFIED = 'adlx_library_unverified'
    ADLX_REJECTED = 'adlx_frame_rejected'
    ADLX_OK = 'adlx_frame_valid'
    STARTUP_NOT_CONFIGURED = 'startup_entry_absent'
    STARTUP_TARGET_INVALID = 'startup_target_unverified'
    STARTUP_NOT_VERIFIED = 'startup_context_unverified'
    STARTUP_DISPATCH_UNCONFIRMED = 'startup_dispatch_unconfirmed'
    STARTUP_BOOTSTRAP_FAILED = 'startup_bootstrap_failed'
    STARTUP_BOOTSTRAP_SEEN = 'startup_bootstrap_seen'
    STARTUP_EXITED = 'startup_agent_returned'
    STARTUP_EXISTING_INSTANCE = 'startup_existing_instance'


FACTS = {
    Component.HTTPS: ('responded', 'authenticated', 'tls_verified'),
    Component.LISTENER: ('present', 'identity_matches', 'port'),
    Component.IPC: ('connected', 'peer_validated', 'contract_version'),
    Component.CPU: ('collector_running', 'sample_valid', 'sample_stale'),
    Component.GPU: ('collector_running', 'sample_valid', 'sample_stale'),
    Component.RAM: ('collector_running', 'sample_valid', 'sample_stale'),
    Component.ADLX: ('running', 'dll_verified', 'sample_valid', 'sample_stale'),
    Component.STARTUP: ('configured', 'login_observed', 'dispatch_observed', 'bootstrap_succeeded'),
}


def utc(value):
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise DiagnosticError('utc_required')
    return value


def stamp(value):
    return utc(value).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def tick(value):
    if type(value) not in (int, float):
        raise DiagnosticError('invalid_monotonic_time')
    try:
        valid = math.isfinite(value) and value >= 0
    except OverflowError:
        valid = False
    if not valid:
        raise DiagnosticError('invalid_monotonic_time')
    return value


@dataclass(frozen=True, slots=True)
class Probe:
    component: Component
    observed_at: datetime
    observed_monotonic: float
    facts: object
    outcome: Outcome = Outcome.OK
    schema_version: int = SCHEMA_VERSION
    evidence_kind: str = 'simulated'
    detail_code: DetailCode | None = None
    sample_interval_seconds: float | None = None

    def __post_init__(self):
        if type(self.component) is not Component or type(self.outcome) is not Outcome:
            raise DiagnosticError('invalid_component_or_outcome')
        if type(self.schema_version) is not int or self.schema_version != SCHEMA_VERSION:
            raise DiagnosticError('incompatible_contract')
        if self.evidence_kind != 'simulated':
            raise DiagnosticError('operational_providers_not_authorized')
        if self.detail_code is not None and type(self.detail_code) is not DetailCode:
            raise DiagnosticError('invalid_detail_code')
        if self.sample_interval_seconds is not None and (
                self.component not in (Component.CPU, Component.RAM)
                or tick(self.sample_interval_seconds) not in (1,5)):
            raise DiagnosticError('invalid_diagnostic_sample_interval')
        utc(self.observed_at)
        tick(self.observed_monotonic)
        if (type(self.facts) not in (dict, MappingProxyType)
                or len(self.facts) > len(FACTS[self.component])
                or set(self.facts) - set(FACTS[self.component])):
            raise DiagnosticError('invalid_facts')
        copied = dict(self.facts)
        for name, value in copied.items():
            if name == 'port':
                if type(value) is not int or value != 8776:
                    raise DiagnosticError('unexpected_port')
            elif name == 'contract_version':
                if type(value) is not int or value not in (1, 2):
                    raise DiagnosticError('invalid_contract_version')
            elif value is not None and type(value) is not bool:
                raise DiagnosticError('invalid_fact_type')
        object.__setattr__(self, 'facts', MappingProxyType(copied))
