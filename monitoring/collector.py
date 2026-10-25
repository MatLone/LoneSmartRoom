"""Injected providers only. No real sensors, native libraries, files or network I/O.

Providers must honor cancellation/deadlines. Python cannot safely preempt an arbitrary
blocking provider: stop reports timeout without killing any process or thread.
"""
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import islice
from threading import Event, Lock, RLock, Thread, current_thread
import time
from typing import Protocol

from .cache import MetricCache
from .contracts import (Availability as A, ContractError, DataKind,
                        Observation, Sample, finite, identifier, monotonic_time, utc)


class Clock:
    def monotonic(self):
        return time.monotonic()

    def utcnow(self):
        return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class Schedule:
    fast: float = 1
    thermal: float = 2
    capacity: float = 60
    inactive_fast: float = 5
    inactive_thermal: float = 10
    inactive_capacity: float = 60
    read_budget: float = 0.25

    def __post_init__(self):
        for name in ('fast', 'thermal', 'capacity', 'inactive_fast',
                     'inactive_thermal', 'inactive_capacity'):
            if not 0.1 <= finite(getattr(self, name)) <= 3600:
                raise ContractError('invalid_interval')
        if any(getattr(self, 'inactive_' + name) < getattr(self, name)
               for name in ('fast', 'thermal', 'capacity')):
            raise ContractError('inactive_cannot_be_faster')
        if not 0 < finite(self.read_budget) <= 5:
            raise ContractError('invalid_read_budget')

    def interval(self, cadence, active):
        return getattr(self, ('' if active else 'inactive_') + cadence.value)


@dataclass(frozen=True, slots=True)
class ReadContext:
    collected_at: datetime
    started_monotonic: float
    deadline_monotonic: float
    stop_requested: Event


class Provider(Protocol):
    source: str
    data_kind: DataKind
    metric_ids: tuple[str, ...]

    def read(self, metric_ids: tuple[str, ...], context: ReadContext): ...
    def close(self): ...


@dataclass(frozen=True, slots=True)
class StopResult:
    stopped: bool
    clean: bool
    timed_out: bool


class Collector:
    def __init__(self, specs, providers=(), *, schedule=None, clock=None,
                 history_limit=120, stale_factor=3):
        self.cache = MetricCache(specs, history_limit, stale_factor)
        self.schedule = schedule or Schedule()
        if type(self.schedule) is not Schedule:
            raise ContractError('invalid_schedule')
        self.clock = clock or Clock()
        self._providers = tuple(providers)
        if len(self._providers) > len(self.cache.specs):
            raise ContractError('too_many_providers')
        self._bindings = []
        assigned, sources = set(), set()
        for provider in self._providers:
            source = identifier(provider.source)
            ids = tuple(provider.metric_ids)
            if (source in sources or not ids or len(set(ids)) != len(ids)
                    or not set(ids) <= self.cache.specs.keys() or assigned.intersection(ids)
                    or provider.data_kind not in (DataKind.SIMULATED, DataKind.REAL)
                    or not isinstance(provider.data_kind, DataKind)
                    or not callable(provider.read) or not callable(provider.close)):
                raise ContractError('invalid_provider_binding')
            assigned.update(ids)
            sources.add(source)
            self._bindings.append((provider, source, provider.data_kind, ids))
        self._last_attempt = {key: None for key in assigned}
        self._active = True
        self._stop = Event()
        self._wake = Event()
        self._step_lock = Lock()
        self._state_lock = RLock()
        self._state = 'created'
        self._thread = None
        self._close_clean = True
        self._diagnostics = deque(maxlen=64)
        self._last_tick = None
        self.cache.publish(tuple(Sample(Observation(key, None, A.WARMING_UP), source,
                                        DataKind.NOT_COLLECTED, None, None,
                                        self.schedule.interval(self.cache.specs[key].cadence, True))
                                 for _provider, source, _kind, ids in self._bindings for key in ids))

    @property
    def state(self):
        with self._state_lock:
            return self._state

    def _event(self, code, source='collector'):
        # Only fixed codes and previously validated provider IDs, never exceptions.
        with self._state_lock:
            self._diagnostics.append({'code': code, 'source': source})

    def diagnostics(self):
        with self._state_lock:
            return tuple(dict(value) for value in self._diagnostics)

    def set_active(self, active):
        if type(active) is not bool:
            raise ContractError('boolean_required')
        with self._state_lock:
            self._active = active
        self._wake.set()

    def request_stop(self):
        self._stop.set()
        self._wake.set()
        with self._state_lock:
            if self._state != 'stopped':
                self._state = 'stopping'

    def step(self):
        """One due pass, also usable with an injected clock and no background thread."""
        if not self._step_lock.acquire(blocking=False):
            raise RuntimeError('collection_already_running')
        try:
            with self._state_lock:
                if self._stop.is_set() or self._state in ('stopping', 'stopped'):
                    return False
                self._state = 'running'
            now = monotonic_time(self.clock.monotonic())
            if self._last_tick is not None and now < self._last_tick:
                raise ContractError('clock_moved_backwards')
            self._last_tick = now
            for provider, source, data_kind, ids in self._bindings:
                if self._stop.is_set():
                    break
                now = monotonic_time(self.clock.monotonic())
                with self._state_lock:
                    active = self._active
                intervals = {key: self.schedule.interval(self.cache.specs[key].cadence, active) for key in ids}
                due = tuple(key for key in ids if self._last_attempt[key] is None
                            or now - self._last_attempt[key] >= intervals[key])
                if not due:
                    continue
                stamp = utc(self.clock.utcnow())
                context = ReadContext(stamp, now, now + self.schedule.read_budget, self._stop)
                for key in due:
                    self._last_attempt[key] = now
                try:
                    # Bound even a buggy generator; native calls must still cooperate.
                    batch = tuple(islice(iter(provider.read(due, context)), len(due) + 1))
                    if (len(batch) != len(due) or any(type(x) is not Observation for x in batch)
                            or {x.metric_id for x in batch} != set(due)):
                        raise ContractError('invalid_provider_batch')
                    for observation in batch:
                        observation.validate(self.cache.specs[observation.metric_id])
                    ended = monotonic_time(self.clock.monotonic())
                    if ended < now:
                        raise ContractError('clock_moved_backwards')
                    if ended > context.deadline_monotonic:
                        self._event('read_deadline_exceeded', source)
                        batch = tuple(Observation(key, None, A.ERROR) for key in due)
                except PermissionError:
                    batch = tuple(Observation(key, None, A.PERMISSION_DENIED) for key in due)
                    self._event('read_permission_denied', source)
                except Exception:
                    batch = tuple(Observation(key, None, A.ERROR) for key in due)
                    self._event('read_failed', source)
                self.cache.publish(tuple(Sample(x, source, data_kind, stamp, now,
                                                intervals[x.metric_id]) for x in batch))
            return True
        finally:
            self._step_lock.release()

    def snapshot(self):
        return self.cache.snapshot(self.clock.monotonic(), self.clock.utcnow())

    def _finish(self):
        # Caller owns step lock. close is called at most once, never during read.
        with self._state_lock:
            if self._state == 'stopped':
                return
        for provider, source, _kind, _ids in self._bindings:
            try:
                provider.close()
            except Exception:
                self._close_clean = False
                self._event('provider_close_failed', source)
        with self._state_lock:
            self._state = 'stopped'
        self._event('collector_stopped')

    def _run(self):
        try:
            while not self._stop.is_set():
                self._wake.clear()
                self.step()
                if self._stop.is_set():
                    break
                with self._state_lock:
                    active = self._active
                now = self.clock.monotonic()
                remaining = [self.schedule.interval(self.cache.specs[key].cadence, active) - (now - last)
                             for key, last in self._last_attempt.items() if last is not None]
                self._wake.wait(max(0.01, min([1.0] + remaining)))
        except Exception:
            self._event('collector_failed')
            self._close_clean = False
            self.request_stop()
        finally:
            with self._step_lock:
                self._finish()

    def start(self):
        with self._state_lock:
            if self._state != 'created' or self._stop.is_set():
                raise RuntimeError('collector_already_started_or_stopped')
            self._state = 'running'
            self._thread = Thread(target=self._run, name='LoneMonitoring', daemon=True)
            self._thread.start()

    def stop(self, timeout=1):
        if not 0 <= finite(timeout) <= 30:
            raise ContractError('invalid_stop_timeout')
        started = time.monotonic()
        self.request_stop()
        with self._state_lock:
            if self._thread is None and self._state != 'stopped':
                # Keep the deadline meaningful even if a close callback blocks.
                self._thread = Thread(target=self._close_manual, name='LoneMonitoringClose', daemon=True)
                self._thread.start()
            thread = self._thread
        if thread is current_thread():
            return StopResult(False, False, False)
        if thread is not None:
            thread.join(timeout)
        stopped = self.state == 'stopped' and (thread is None or not thread.is_alive())
        if not stopped:
            self._event('stop_timeout')
        return StopResult(stopped, stopped and self._close_clean, not stopped
                          and time.monotonic() - started >= timeout)

    def _close_manual(self):
        with self._step_lock:
            self._finish()
