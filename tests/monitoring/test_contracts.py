from datetime import datetime, timezone
import unittest

from monitoring.cache import MetricCache
from monitoring.catalog import DEFAULT_METRICS
from monitoring.contracts import (Availability as A, Cadence, ContractError, DataKind,
                                  MetricSpec, Observation, Sample, Unit, catalog)
from monitoring_fakes import FakeClock, by_id


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.spec = DEFAULT_METRICS[0]
        self.clock = FakeClock()

    def sample(self, value=25, state=A.AVAILABLE, **kwargs):
        return Sample(Observation(self.spec.metric_id, value, state), 'fixture.cpu',
                      DataKind.SIMULATED, self.clock.utcnow(), self.clock.monotonic(), 1, **kwargs)

    def test_catalog_covers_declared_hardware_and_units(self):
        specs = catalog(DEFAULT_METRICS)
        self.assertEqual(len(specs), 22)
        self.assertEqual({s.unit for s in specs.values()}, set(Unit))
        self.assertEqual({s.cadence for s in specs.values()}, set(Cadence))
        self.assertIn('cpu.package_temperature', specs)
        self.assertIn('gpu.vram_available', specs)
        self.assertIn('storage.system.activity', specs)

    def test_value_and_provenance_round_trip(self):
        cache = MetricCache([self.spec])
        cache.publish([self.sample()])
        view = by_id(cache.snapshot(0, self.clock.utcnow()))[self.spec.metric_id]
        self.assertEqual((view['value'], view['unit'], view['state']), (25, 'percent', 'available'))
        self.assertTrue(view['valid'])
        self.assertEqual(view['source'], 'fixture.cpu')
        self.assertEqual(view['data_kind'], 'simulated')
        self.assertTrue(view['collected_at'].endswith('Z'))

    def test_zero_is_valid_including_stopped_fan(self):
        for spec in DEFAULT_METRICS:
            with self.subTest(metric=spec.metric_id):
                Observation(spec.metric_id, 0).validate(spec)

    def test_unavailable_states_require_null_not_zero(self):
        for state in A:
            if state in (A.AVAILABLE, A.STALE):
                continue
            with self.subTest(state=state):
                Observation(self.spec.metric_id, None, state).validate(self.spec)
                with self.assertRaises(ContractError):
                    Observation(self.spec.metric_id, 0, state).validate(self.spec)

    def test_available_rejects_nonfinite_bool_string_and_null(self):
        for value in (None, True, False, float('nan'), float('inf'), -float('inf'), '25', 10**1000):
            with self.subTest(kind=type(value).__name__), self.assertRaises(ContractError):
                Observation(self.spec.metric_id, value).validate(self.spec)

    def test_unit_ranges_and_integer_semantics(self):
        cases = [(Unit.PERCENT, -1), (Unit.PERCENT, 101), (Unit.CELSIUS, -274),
                 (Unit.CELSIUS, 301), (Unit.BYTES, -1), (Unit.BYTES, 1.5),
                 (Unit.BYTES, 2**63), (Unit.RPM, 0.5), (Unit.RPM, 1_000_001),
                 (Unit.BYTES_PER_SECOND, -0.1)]
        for unit, value in cases:
            with self.subTest(unit=unit, value=value), self.assertRaises(ContractError):
                MetricSpec('test.value', 'test', 'Test', unit, Cadence.FAST).validate_value(value)

    def test_provider_cannot_set_stale_or_unknown_state(self):
        for state in (A.STALE, 'available', 'error'):
            with self.assertRaises(ContractError):
                Observation(self.spec.metric_id, None, state).validate(self.spec)

    def test_identifiers_labels_and_duplicate_catalog(self):
        for bad in ('../secret', 'steam://open/main', 'A', '', 'a' * 81):
            with self.assertRaises(ContractError):
                MetricSpec(bad, 'cpu', 'CPU', Unit.PERCENT, Cadence.FAST)
        for bad in ('', 'bad\nlabel', 'x' * 81):
            with self.assertRaises(ContractError):
                MetricSpec('cpu.test', 'cpu', bad, Unit.PERCENT, Cadence.FAST)
        for specs in ([], [self.spec] * 2, [None], [self.spec] * 65):
            with self.assertRaises(ContractError):
                catalog(specs)

    def test_uncollected_timestamp_rules(self):
        for kind, stamp, mono in ((DataKind.REAL, None, None),
                                  (DataKind.NOT_COLLECTED, self.clock.utcnow(), None)):
            with self.assertRaises(ContractError):
                Sample(Observation(self.spec.metric_id, None, A.UNSUPPORTED), 'unconfigured',
                       kind, stamp, mono, 1).validate(self.spec)

    def test_naive_timestamp_and_negative_monotonic_rejected(self):
        for stamp, mono in ((datetime(2026, 10, 24), 0), (self.clock.utcnow(), -1)):
            with self.assertRaises(ContractError):
                Sample(Observation(self.spec.metric_id, 1), 'fixture.cpu', DataKind.SIMULATED,
                       stamp, mono, 1).validate(self.spec)

    def test_stale_nulls_value_keeps_original_time_and_history(self):
        cache = MetricCache([self.spec])
        cache.publish([self.sample()])
        before = cache.snapshot(0, self.clock.utcnow())
        self.clock.advance(3)
        after = cache.snapshot(3, self.clock.utcnow())
        view = after['metrics'][0]
        self.assertEqual(view['state'], 'stale')
        self.assertIsNone(view['value'])
        self.assertFalse(view['valid'])
        self.assertTrue(view['stale'])
        self.assertEqual(view['collected_at'], before['metrics'][0]['collected_at'])
        self.assertEqual(before['sequence'], after['sequence'])
        self.assertEqual(cache.history(self.spec.metric_id)[0].observation.value, 25)

    def test_error_remains_error_with_stale_age(self):
        cache = MetricCache([self.spec])
        cache.publish([self.sample(None, A.ERROR)])
        view = cache.snapshot(4, self.clock.utcnow())['metrics'][0]
        self.assertEqual(view['state'], 'error')
        self.assertTrue(view['stale'])
        self.assertIsNone(view['value'])

    def test_empty_cache_is_explicitly_not_collected(self):
        view = MetricCache([self.spec]).snapshot(0, self.clock.utcnow())['metrics'][0]
        self.assertEqual((view['state'], view['data_kind']), ('unsupported', 'not_collected'))
        self.assertIsNone(view['value'])
        self.assertIsNone(view['collected_at'])

    def test_bounded_history_and_detached_snapshot(self):
        cache = MetricCache([self.spec], history_limit=3)
        for _ in range(10):
            cache.publish([self.sample()])
            self.clock.advance(1)
        self.assertEqual(cache.sample_count, 3)
        self.assertEqual(len(cache.history(self.spec.metric_id)), 3)
        snap = cache.snapshot(10, self.clock.utcnow())
        snap['metrics'][0]['value'] = 'mutated'
        self.assertNotEqual(cache.snapshot(10, self.clock.utcnow())['metrics'][0]['value'], 'mutated')
        with self.assertRaises(TypeError):
            cache.specs['new'] = self.spec

    def test_atomic_batch_rejects_unknown_duplicate_and_invalid(self):
        cache = MetricCache(DEFAULT_METRICS[:2])
        for batch in ([self.sample(), self.sample()],
                      [self.sample(), Sample(Observation('unknown', 1), 'fixture.cpu', DataKind.SIMULATED,
                                            self.clock.utcnow(), 0, 1)],
                      [self.sample(), Sample(Observation(DEFAULT_METRICS[1].metric_id, 'bad'),
                                            'fixture.cpu', DataKind.SIMULATED, self.clock.utcnow(), 0, 2)]):
            with self.assertRaises(ContractError):
                cache.publish(batch)
            self.assertEqual(cache.sample_count, 0)

    def test_cache_bounds_configuration_and_clock_regression(self):
        for kwargs in ({'history_limit': 0}, {'history_limit': 121}, {'history_limit': True},
                       {'stale_factor': 0}, {'stale_factor': float('nan')}):
            with self.assertRaises(ContractError):
                MetricCache([self.spec], **kwargs)
        cache = MetricCache([self.spec])
        self.clock.advance(1)
        cache.publish([self.sample()])
        cache.snapshot(1, self.clock.utcnow())
        with self.assertRaises(ContractError):
            cache.snapshot(0, self.clock.utcnow())
        self.clock.now = 0
        with self.assertRaises(ContractError):
            cache.publish([self.sample()])
