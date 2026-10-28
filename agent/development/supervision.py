"""Side-effect-free supervision policy candidate, NOT an operational launcher.

The future approved host must map START to the existing fixed-path launcher and
COOPERATIVE_STOP to its validated local channel. This module opens no handles,
starts no processes, reads no credentials and registers nothing with Windows.
Mutex ownership and worker cleanup remain the worker's responsibility.
"""
from collections import deque
from dataclasses import dataclass
from enum import Enum
import math


class Action(str, Enum):
    NONE = 'none'
    START = 'start_fixed_launcher'
    COOPERATIVE_STOP = 'request_local_stop'


@dataclass(frozen=True)
class Evidence:
    # All facts are fresh observations supplied by a trusted future host.
    preflight_verified: bool = False
    worker_alive: bool = False
    worker_exited: bool = False
    mutex_released: bool = False
    listener_absent: bool = False
    identity_verified: bool = False
    listener_verified: bool = False
    tls_verified: bool = False
    authenticated: bool = False
    duplicate: bool = False
    security_failure: bool = False
    environment_failure: bool = False
    spawn_failed: bool = False

    def __post_init__(self):
        if any(type(v) is not bool for v in vars(self).values()):
            raise ValueError('boolean_evidence_required')
        if self.worker_alive and self.worker_exited:
            raise ValueError('contradictory_worker_evidence')

    @property
    def ready(self):
        return (self.worker_alive and self.identity_verified and
                self.listener_verified and self.tls_verified and self.authenticated)

    @property
    def cleaned(self):
        return self.worker_exited and self.mutex_released and self.listener_absent


class SupervisorPolicy:
    """Bounded orchestration decisions; no implicit recovery permission.

    Timestamps are monotonic seconds. Logs are bounded fixed codes + times only.
    A bootstrap deadline requests cooperation, NEVER kills or assumes cleanup.
    An absent process/listener alone cannot demonstrate successful shutdown.
    """
    def __init__(self, *, enabled=False, attempts=1, startup_seconds=30,
                 stop_seconds=30, retry_seconds=5):
        if type(enabled) is not bool or type(attempts) is not int or not 1 <= attempts <= 3:
            raise ValueError('invalid_policy')
        for value in (startup_seconds, stop_seconds, retry_seconds):
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 < value <= 120:
                raise ValueError('invalid_deadline')
        self.enabled, self.budget = enabled, attempts
        self.startup_seconds, self.stop_seconds = startup_seconds, stop_seconds
        self.retry_seconds = retry_seconds
        self.state, self.attempts = 'idle', 0
        self.deadline, self.last_time = None, None
        self.stop_requested = False
        self.events = deque(maxlen=64)

    def _transition(self, state, code, now):
        self.state = state
        self.events.append({'at_monotonic_seconds': now, 'code': code})

    def step(self, now, facts, *, stop=False):
        if type(now) not in (int, float) or not math.isfinite(now) or now < 0:
            raise ValueError('invalid_clock')
        if self.last_time is not None and now < self.last_time:
            raise ValueError('clock_reversed')
        if type(facts) is not Evidence or type(stop) is not bool:
            raise ValueError('invalid_evidence')
        self.last_time = now
        if self.state in ('stopped', 'blocked', 'stop_timeout'):
            return Action.NONE
        if stop:
            self.stop_requested = True
        if self.state == 'idle':
            if self.stop_requested:
                self._transition('stopped', 'cancelled_before_start', now)
                return Action.NONE
            if not self.enabled:
                return Action.NONE
            if (not facts.preflight_verified or facts.worker_alive or facts.duplicate or
                    facts.security_failure or facts.environment_failure):
                self._transition('blocked', 'preflight_not_approved', now)
                return Action.NONE
            return self._start(now)
        if self.state == 'backoff':
            if self.stop_requested:
                self._transition('stopped', 'cancelled_after_cleanup', now)
            elif now >= self.deadline:
                # Fresh preflight and complete cleanup are mandatory every time.
                if facts.preflight_verified and facts.cleaned and not (
                        facts.duplicate or facts.security_failure or facts.environment_failure):
                    return self._start(now)
                self._transition('blocked', 'recovery_preflight_not_approved', now)
            return Action.NONE
        if self.state == 'draining':
            if facts.cleaned:
                self._transition('stopped', 'cooperative_cleanup_verified', now)
            elif now >= self.deadline:
                self._transition('stop_timeout', 'cleanup_deadline_exceeded_no_force', now)
            return Action.NONE
        # No recovery is attempted while a worker might still own resources.
        if facts.duplicate:
            self._transition('blocked', 'duplicate_no_process_interference', now)
            return Action.NONE
        if facts.spawn_failed and not facts.worker_alive:
            if facts.cleaned:
                self._after_exit(now, terminal=facts.security_failure or facts.environment_failure)
            else:
                self._transition('blocked', 'spawn_state_ambiguous', now)
            return Action.NONE
        if facts.worker_exited:
            if facts.cleaned:
                self._after_exit(now, terminal=self.stop_requested or facts.security_failure or facts.environment_failure)
            else:
                self._transition('blocked', 'exit_cleanup_unverified', now)
            return Action.NONE
        if self.stop_requested or facts.security_failure or facts.environment_failure:
            return self._stop(now)
        if self.state == 'starting':
            if facts.ready:
                self._transition('serving', 'https_readiness_verified', now)
            elif now >= self.deadline:
                return self._stop(now)
        elif self.state == 'serving' and not facts.ready:
            self._transition('degraded', 'readiness_lost_no_restart', now)
        elif self.state == 'degraded' and facts.ready:
            self._transition('serving', 'readiness_recovered', now)
        return Action.NONE

    def _start(self, now):
        self.attempts += 1
        self.deadline = now + self.startup_seconds
        self._transition('starting', 'fixed_launcher_start_requested', now)
        return Action.START

    def _stop(self, now):
        self.deadline = now + self.stop_seconds
        self._transition('draining', 'local_cooperative_stop_requested', now)
        return Action.COOPERATIVE_STOP

    def _after_exit(self, now, terminal):
        if terminal or self.attempts >= self.budget:
            self._transition('stopped', 'worker_exited_cleanup_verified', now)
        else:
            self.deadline = now + self.retry_seconds
            self._transition('backoff', 'bounded_recovery_wait', now)
