from threading import Event, Thread, enumerate as threads
import time
import tracemalloc
import unittest

from monitoring.catalog import DEFAULT_METRICS
from monitoring.collector import Clock, Collector, Schedule
from monitoring.contracts import Availability as A, ContractError, DataKind, Observation
from monitoring_fakes import FakeClock, FakeProvider, by_id


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.specs = (DEFAULT_METRICS[0], DEFAULT_METRICS[1], DEFAULT_METRICS[13])
        self.clock = FakeClock()
        self.provider = FakeProvider(self.specs)
        self.collector = Collector(self.specs, [self.provider], clock=self.clock)
        self.addCleanup(self.collector.stop)

    def advance(self, seconds):
        self.clock.advance(seconds)
        self.collector.step()

    def test_construction_does_not_read_or_start_thread(self):
        self.assertEqual(self.provider.call_count, 0)
        self.assertEqual(self.collector.state, 'created')
        self.assertEqual(self.collector.snapshot()['metrics'][0]['state'], 'warming_up')
        self.assertEqual(self.provider.call_count, 0)

    def test_defaults_one_two_and_sixty_seconds(self):
        self.collector.step()
        self.assertEqual(set(self.provider.calls[-1][0]), set(self.provider.metric_ids))
        self.advance(0.5)
        self.assertEqual(self.provider.call_count, 1)
        self.advance(0.5)
        self.assertEqual(self.provider.calls[-1][0], ('cpu.utilization',))
        self.advance(1)
        self.assertEqual(set(self.provider.calls[-1][0]), {'cpu.utilization', 'cpu.package_temperature'})
        self.advance(58)
        self.assertIn('storage.system.total', self.provider.calls[-1][0])
        self.assertEqual(self.provider.call_count, 4)  # No catch-up burst after a gap.

    def test_reduced_frequency_and_resume(self):
        self.collector.step()
        self.collector.set_active(False)
        self.advance(1)
        self.assertEqual(self.provider.call_count, 1)
        self.advance(4)
        self.assertEqual(self.provider.calls[-1][0], ('cpu.utilization',))
        self.advance(5)
        self.assertIn('cpu.package_temperature', self.provider.calls[-1][0])
        self.collector.set_active(True)
        self.advance(1)
        self.assertEqual(self.provider.calls[-1][0], ('cpu.utilization',))
        with self.assertRaises(ContractError):
            self.collector.set_active('true')

    def test_custom_intervals(self):
        collector = Collector(self.specs, [self.provider], clock=self.clock,
                              schedule=Schedule(fast=2, thermal=4, capacity=120,
                                                inactive_capacity=120))
        self.addCleanup(collector.stop)
        collector.step()
        self.clock.advance(1)
        collector.step()
        self.assertEqual(self.provider.call_count, 1)
        self.clock.advance(1)
        collector.step()
        self.assertEqual(self.provider.calls[-1][0], ('cpu.utilization',))

    def test_invalid_schedules_fail_closed(self):
        for kwargs in ({'fast': 0}, {'fast': True}, {'thermal': float('inf')},
                       {'capacity': 3601}, {'read_budget': 0}, {'inactive_fast': 0.5}):
            with self.assertRaises(ContractError):
                Schedule(**kwargs)

    def test_temporary_error_and_recovery_never_zero(self):
        self.provider.failure = RuntimeError('PRIVATE-TOKEN must not escape')
        self.collector.step()
        view = by_id(self.collector.snapshot())['cpu.utilization']
        self.assertEqual(view['state'], 'error')
        self.assertIsNone(view['value'])
        self.assertNotIn('PRIVATE-TOKEN', str(self.collector.diagnostics()))
        self.provider.failure = None
        self.advance(1)
        self.assertTrue(by_id(self.collector.snapshot())['cpu.utilization']['valid'])

    def test_permission_denied_and_unsupported(self):
        self.provider.failure = PermissionError('private/path')
        self.collector.step()
        self.assertEqual(self.collector.snapshot()['metrics'][0]['state'], 'permission_denied')
        self.provider.failure = None
        self.provider.state = A.UNSUPPORTED
        self.advance(1)
        view = self.collector.snapshot()['metrics'][0]
        self.assertEqual(view['state'], 'unsupported')
        self.assertIsNone(view['value'])

    def test_missing_provider_and_partial_hardware(self):
        collector = Collector(DEFAULT_METRICS, [self.provider], clock=self.clock)
        self.addCleanup(collector.stop)
        collector.step()
        view = by_id(collector.snapshot())['gpu.temperature']
        self.assertEqual((view['state'], view['data_kind']), ('unsupported', 'not_collected'))
        self.assertIsNone(view['value'])

    def test_invalid_batches_are_rejected_as_errors(self):
        for hook in (lambda ids, ctx: [],
                     lambda ids, ctx: [Observation('outside.allowlist', 1)] * len(ids),
                     lambda ids, ctx: [Observation(ids[0], 1)] * len(ids),
                     lambda ids, ctx: [Observation(key, float('nan')) for key in ids],
                     lambda ids, ctx: [Observation(key, 0, A.ERROR) for key in ids]):
            self.provider.read_hook = hook
            self.collector.step()
            self.assertTrue(all(v['state'] == 'error' for v in self.collector.snapshot()['metrics']))
            self.clock.advance(60)

    def test_infinite_generator_bounded_by_requested_metric_count(self):
        def bad(ids, ctx):
            while True:
                yield Observation(ids[0], 1)
        self.provider.read_hook = bad
        self.collector.step()
        self.assertEqual(self.collector.snapshot()['metrics'][0]['state'], 'error')

    def test_deadline_overrun_discards_value(self):
        def slow(ids, ctx):
            self.clock.advance(0.5)
            return [Observation(key, 1) for key in ids]
        self.provider.read_hook = slow
        self.collector.step()
        self.assertEqual(self.collector.snapshot()['metrics'][0]['state'], 'error')
        self.assertEqual(self.collector.diagnostics()[-1]['code'], 'read_deadline_exceeded')

    def test_wall_clock_change_does_not_hide_staleness(self):
        self.collector.step()
        self.clock.advance(3)
        self.clock.wall_offset = -86400
        snap = self.collector.snapshot()
        self.assertEqual(snap['metrics'][0]['state'], 'stale')
        self.assertEqual(snap['metrics'][0]['age_seconds'], 3)

    def test_duplicate_binding_unknown_id_and_unlabelled_simulation(self):
        for mutate in (lambda p: setattr(p, 'metric_ids', ('unknown',)),
                       lambda p: setattr(p, 'metric_ids', ('cpu.utilization',) * 2),
                       lambda p: setattr(p, 'data_kind', 'simulated'),
                       lambda p: setattr(p, 'source', '../private'),
                       lambda p: setattr(p, 'data_kind', DataKind.NOT_COLLECTED)):
            provider = FakeProvider(self.specs)
            mutate(provider)
            with self.assertRaises(ContractError):
                Collector(self.specs, [provider])
        with self.assertRaises(ContractError):
            Collector(self.specs, [self.provider, self.provider])

    def test_stop_is_idempotent_and_collector_does_not_restart(self):
        self.collector.step()
        for _ in range(3):
            result = self.collector.stop()
            self.assertTrue(result.stopped and result.clean)
        self.assertEqual(self.provider.closed, 1)
        self.assertFalse(self.collector.step())
        with self.assertRaises(RuntimeError):
            self.collector.start()

    def test_diagnostics_and_history_have_fixed_bounds(self):
        self.provider.failure = ValueError('private-secret')
        for _ in range(300):
            self.collector.step()
            self.clock.advance(60)
        self.assertEqual(self.collector.cache.sample_count, 3 * 120)
        self.assertEqual(len(self.collector.diagnostics()), 64)
        self.assertNotIn('private-secret', str(self.collector.diagnostics()))

    def test_memory_stabilizes_after_cache_warmup(self):
        # Allocation of this synthetic collector, not machine RAM monitoring.
        for _ in range(200):
            self.advance(60)
        tracemalloc.start()
        try:
            for _ in range(1000):
                self.advance(60)
            first = tracemalloc.get_traced_memory()[0]
            for _ in range(1000):
                self.advance(60)
            second = tracemalloc.get_traced_memory()[0]
            self.assertLess(second - first, 128 * 1024)
            self.assertEqual(self.collector.cache.sample_count, 360)
        finally:
            tracemalloc.stop()


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.specs = DEFAULT_METRICS[:1]
        self.provider = FakeProvider(self.specs)
        self.collector = Collector(self.specs, [self.provider], clock=Clock())
        self.release = Event()
        self.addCleanup(self.collector.stop)
        self.addCleanup(self.release.set)

    def test_background_run_wakes_and_stops_without_extra_read(self):
        entered = Event()
        def read(ids, ctx):
            entered.set()
            ctx.stop_requested.wait(1)
            return [Observation(ids[0], 25)]
        self.provider.read_hook = read
        self.collector.start()
        self.assertTrue(entered.wait(1))
        result = self.collector.stop(1)
        self.assertTrue(result.stopped and result.clean)
        self.assertEqual(self.provider.call_count, 1)
        self.assertEqual(self.provider.closed, 1)
        self.assertFalse(any(t.name == 'LoneMonitoring' for t in threads()))

    def test_stop_during_read_does_not_start_another_provider(self):
        other = FakeProvider(DEFAULT_METRICS[1:2])
        other.source = 'fixture.other'
        collector = Collector(DEFAULT_METRICS[:2], [self.provider, other])
        self.addCleanup(collector.stop)
        def read(ids, ctx):
            collector.request_stop()
            return [Observation(ids[0], 25)]
        self.provider.read_hook = read
        collector.step()
        self.assertTrue(collector.stop().clean)
        self.assertEqual(other.call_count, 0)
        self.assertEqual(other.closed, 1)

    def test_uncooperative_read_reports_timeout_never_forces_stop(self):
        entered = Event()
        def read(ids, ctx):
            entered.set()
            self.release.wait(2)
            return [Observation(ids[0], 25)]
        self.provider.read_hook = read
        self.collector.start()
        self.assertTrue(entered.wait(1))
        result = self.collector.stop(0.01)
        self.assertFalse(result.stopped)
        self.assertTrue(result.timed_out)
        self.assertEqual(self.provider.closed, 0)
        self.release.set()
        self.assertTrue(self.collector.stop(1).clean)

    def test_uncooperative_close_reports_timeout(self):
        entered = Event()
        def close():
            entered.set()
            self.release.wait(2)
        self.provider.close_hook = close
        result = self.collector.stop(0.01)
        self.assertTrue(entered.is_set())
        self.assertFalse(result.stopped)
        self.assertTrue(result.timed_out)
        self.release.set()
        self.assertTrue(self.collector.stop(1).clean)

    def test_simultaneous_stop_closes_exactly_once(self):
        self.collector.step()
        results = []
        workers = [Thread(target=lambda: results.append(self.collector.stop(1))) for _ in range(8)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(2)
            self.assertFalse(worker.is_alive())
        self.assertEqual(len(results), 8)
        self.assertTrue(all(r.clean for r in results))
        self.assertEqual(self.provider.closed, 1)

    def test_concurrent_step_rejected(self):
        entered = Event()
        def read(ids, ctx):
            entered.set()
            self.release.wait(2)
            return [Observation(ids[0], 25)]
        self.provider.read_hook = read
        self.collector.start()
        self.assertTrue(entered.wait(1))
        with self.assertRaises(RuntimeError):
            self.collector.step()
        self.release.set()
        self.assertTrue(self.collector.stop(1).stopped)

    def test_close_failure_sanitized_not_reported_clean(self):
        def fail():
            raise RuntimeError('PRIVATE-CREDENTIAL')
        self.provider.close_hook = fail
        result = self.collector.stop()
        self.assertTrue(result.stopped)
        self.assertFalse(result.clean)
        self.assertNotIn('PRIVATE-CREDENTIAL', str(self.collector.diagnostics()))

    def test_double_start_rejected(self):
        self.collector.start()
        with self.assertRaises(RuntimeError):
            self.collector.start()
        self.assertTrue(self.collector.stop(1).clean)

    def test_stop_racing_with_wake_clear_does_not_wait_or_read(self):
        collector = self.collector
        class StopDuringClear:
            waits = 0
            def set(self):
                pass
            def clear(self):
                collector.request_stop()  # Deterministic lost-wakeup race.
            def wait(self, timeout):
                self.waits += 1
        wake = StopDuringClear()
        collector._wake = wake
        collector.start()
        self.assertTrue(collector.stop(1).clean)
        self.assertEqual(wake.waits, 0)
        self.assertEqual(self.provider.call_count, 0)
