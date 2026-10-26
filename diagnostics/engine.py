"""Pure diagnostic reducer and bounded cache; no sockets, processes, files or timers."""
import json
from itertools import islice
from threading import RLock

from .contracts import (Component, DiagnosticError, FACTS, MAX_REPORT_BYTES,
                        Outcome, Probe, SCHEMA_VERSION, stamp, tick, utc)

# Diagnostic observation freshness, not a relaxation of native ADLX frame admission.
ACTIVE_TTL = {Component.HTTPS: 10, Component.LISTENER: 10, Component.IPC: 5,
              Component.CPU: 3, Component.GPU: 3, Component.RAM: 3,
              Component.ADLX: 3, Component.STARTUP: 300}


def classify(probe):
    f, component = probe.facts, probe.component
    if probe.outcome != Outcome.OK:
        return probe.outcome.value, 'provider_' + probe.outcome.value
    if set(FACTS[component]) - set(f):
        return 'unknown', 'insufficient_evidence'
    if component == Component.HTTPS:
        if f['responded'] is False:
            return 'offline', 'no_authenticated_response'
        if f['responded'] is True and f['authenticated'] is True and f['tls_verified'] is True:
            return 'healthy', 'authenticated_https'
        if f['responded'] is True and (f['authenticated'] is False or f['tls_verified'] is False):
            return 'error', 'unverified_identity'
        return 'unknown', 'insufficient_evidence'
    if component == Component.LISTENER:
        if f['present'] is False:
            return 'offline', 'listener_absent'
        if f['present'] is True and f['identity_matches'] is True:
            return 'healthy', 'expected_listener'
        if f['present'] is True and f['identity_matches'] is False:
            return 'error', 'listener_identity_mismatch'
    elif component == Component.IPC:
        if f['connected'] is False:
            return 'offline', 'ipc_disconnected'
        if f['connected'] is True and f['contract_version'] != 1:
            return 'error', 'ipc_contract_mismatch'
        if f['connected'] is True and f['peer_validated'] is False:
            return 'error', 'ipc_peer_unverified'
        if f['connected'] is True and f['peer_validated'] is True:
            return 'healthy', 'validated_ipc'
    elif component in (Component.CPU, Component.GPU, Component.RAM, Component.ADLX):
        running = f['running'] if component == Component.ADLX else f['collector_running']
        if running is False:
            return 'offline', 'component_not_running'
        if component == Component.ADLX and running is True and f['dll_verified'] is False:
            return 'error', 'native_library_unverified'
        if f['sample_stale'] is True:
            return 'stale', 'sample_stale'
        if running is True and f['sample_valid'] is False:
            return 'unavailable', 'sample_invalid'
        identity_ok = component != Component.ADLX or f['dll_verified'] is True
        if running is True and identity_ok and f['sample_valid'] is True and f['sample_stale'] is False:
            return 'healthy', 'valid_sample'
    elif component == Component.STARTUP:
        if f['configured'] is False:
            return 'unavailable', 'startup_not_configured'
        if f['dispatch_observed'] is False and f['bootstrap_succeeded'] is True:
            return 'unknown', 'conflicting_startup_evidence'
        if f['configured'] is True and f['dispatch_observed'] is True and f['bootstrap_succeeded'] is False:
            return 'error', 'bootstrap_failure_observed'
        if f['configured'] is True and f['dispatch_observed'] is True and f['bootstrap_succeeded'] is True:
            return 'healthy', 'bootstrap_observed'
        if f['configured'] is True and f['login_observed'] is True and f['dispatch_observed'] is False:
            return 'unknown', 'possible_dispatch_problem_unconfirmed'
    return 'unknown', 'insufficient_evidence'


class DiagnosticEngine:
    """Injected simulated providers only; collection occurs only on explicit calls.

    Provider code shares this process' authority. This class is not a sandbox for
    malicious Python providers. The test runner separately denies external I/O.
    """
    def __init__(self, providers=()):
        self.providers = tuple(islice(providers, len(Component) + 1))
        if len(self.providers) > len(Component):
            raise DiagnosticError('too_many_providers')
        self._providers = {}
        for provider in self.providers:
            if type(provider.component) is not Component or provider.component in self._providers:
                raise DiagnosticError('duplicate_or_invalid_provider')
            if provider.evidence_kind != 'simulated':
                raise DiagnosticError('operational_providers_not_authorized')
            self._providers[provider.component] = provider
        self._latest = {}
        self._high_water = {}
        self._last_good_https = None
        self._last_tick = None
        self._lock = RLock()

    def _clock(self, now, monotonic, mode):
        utc(now);tick(monotonic)
        if mode not in ('active', 'inactive'):
            raise DiagnosticError('invalid_activity_mode')
        if self._last_tick is not None and monotonic < self._last_tick:
            raise DiagnosticError('clock_regression')
        self._last_tick = monotonic

    def collect(self, now, monotonic, mode='active'):
        with self._lock:
            self._clock(now, monotonic, mode)
            for component, provider in self._providers.items():
                try:
                    probe = provider.read()
                    if probe is None:
                        continue  # No new evidence; never renew an old timestamp.
                    if type(probe) is not Probe or probe.component != component:
                        raise DiagnosticError('invalid_observation')
                    if probe.observed_monotonic > monotonic or probe.observed_at > now:
                        self._latest[component] = ('invalid_time', None)
                        continue
                    old = self._high_water.get(component)
                    if old and (probe.observed_monotonic < old[0] or probe.observed_at < old[1]):
                        self._latest[component] = ('out_of_order', None)
                        continue
                    self._high_water[component] = (probe.observed_monotonic, probe.observed_at)
                    self._latest[component] = (None, probe)
                    if component == Component.HTTPS and classify(probe)[0] == 'healthy':
                        if monotonic - probe.observed_monotonic <= ACTIVE_TTL[component] and (now-probe.observed_at).total_seconds() <= ACTIVE_TTL[component]:
                            self._last_good_https = probe.observed_at
                except TimeoutError:
                    self._latest[component] = ('provider_timeout', None)
                except Exception:
                    self._latest[component] = ('provider_failure', None)
            return self._snapshot(now, monotonic, mode)

    def snapshot(self, now, monotonic, mode='active'):
        with self._lock:
            self._clock(now, monotonic, mode)
            return self._snapshot(now, monotonic, mode)

    def _snapshot(self, now, monotonic, mode):
        records=[]
        for component in Component:
            error, probe = self._latest.get(component, ('not_observed', None))
            ttl = 11 if mode == 'inactive' and component in (Component.GPU, Component.ADLX) else ACTIVE_TTL[component]
            if probe and probe.sample_interval_seconds is not None:
                ttl = 3*probe.sample_interval_seconds
            state, code, age = 'unknown', error, None
            if probe is not None:
                monotonic_age = monotonic-probe.observed_monotonic
                utc_age = (now-probe.observed_at).total_seconds()
                age = max(monotonic_age, utc_age)
                if monotonic_age < 0 or utc_age < 0:
                    state, code = 'unknown', 'invalid_time'
                    age = None
                elif age >= ttl:
                    state, code = 'stale', 'observation_stale'
                else:
                    state, code = classify(probe)
            records.append({'component':component.value,'state':state,'code':code,
                            'detail_code':probe.detail_code.value if probe and probe.detail_code else None,
                            'evidence_kind':'simulated','observed_at':stamp(probe.observed_at) if probe else None,
                            'age_seconds':round(age, 3) if age is not None else None,
                            'valid':state == 'healthy','freshness_seconds':ttl,
                            'last_communication':stamp(self._last_good_https) if component == Component.HTTPS and self._last_good_https else None})
        report={'schema_version':SCHEMA_VERSION,'generated_at':stamp(now),'mode':mode,
                'simulation':True,'repair_capability':False,'power_state':'unknown','checks':records}
        if len(json.dumps(report,separators=(',',':')).encode('utf-8')) > MAX_REPORT_BYTES:
            raise DiagnosticError('report_too_large')
        return report
