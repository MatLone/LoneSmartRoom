"""Simulated session clock and backend. Never starts the physical-session script."""
from pathlib import Path
from unittest.mock import Mock
import unittest

from monitoring.basic_session import resource_sample, run_session, stats
from monitoring.contracts import ContractError
from monitoring.windows_basic import DiskCounter, VolumeSpace
from monitoring_fakes import FakeClock


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.clock, self.api = FakeClock(), Mock()
        self.api.logical_processors.return_value = 12
        self.api.cpu_times.side_effect = lambda: (int(self.clock.now * 25), int(self.clock.now * 80), int(self.clock.now * 20))
        self.api.memory.return_value = (16 * 1024**3, 6 * 1024**3)
        self.api.volume_space.return_value = VolumeSpace(1000, 700, 600, 250)
        self.api.disk_counters.side_effect = lambda: {key: DiskCounter(int(self.clock.now * 100), int(self.clock.now * 100), value)
            for key, value in [('storage.c.read_rate', 1024), ('storage.c.write_rate', 2048), ('storage.c.activity', 10)]}
        self.api.own_resources.side_effect = lambda: {'cpu_seconds': self.clock.now * 0.001,
                                                    'working_set_bytes': 24 * 1024**2, 'private_commit_bytes': 12 * 1024**2}

    def test_session_cadences_summaries_and_clean_exit(self):
        result = run_session(self.api, ('C:\\',), self.clock, self.clock.advance, duration=65)
        self.assertEqual(result['reason'], 'duration_complete')
        self.assertTrue(result['stop']['clean'])
        self.assertFalse(result['monitoring_threads_remaining'])
        self.assertEqual(len(result['rows']), 65)
        self.assertEqual(result['metrics']['cpu.utilization']['states']['warming_up'], 1)
        self.assertEqual(result['metrics']['cpu.utilization']['values']['count'], 64)
        self.assertEqual(result['metrics']['storage.c.total']['values']['count'], 2)
        self.assertEqual(result['metrics']['storage.c.total']['interval_seconds']['mean'], 60)
        self.assertEqual(result['metrics']['storage.c.read_rate']['interval_seconds']['mean'], 1)
        self.assertLessEqual(result['final_cache_samples'], result['max_cache_samples'])
        self.api.close_disk_query.assert_called_once()

    def test_resource_cpu_normalized_by_all_logical_processors(self):
        previous = {'cpu_seconds': 1}
        values = resource_sample({'cpu_seconds': 1.12, 'working_set_bytes': 100,
                                  'private_commit_bytes': 200}, previous, 1, 12)
        self.assertAlmostEqual(values['cpu_percent_total_normalized'], 1)
        self.assertIsNone(resource_sample({'cpu_seconds': 1, 'working_set_bytes': 1,
                                          'private_commit_bytes': 2}, None, 0, 12)['cpu_percent_total_normalized'])

    def test_resource_reset_or_invalid_values_not_fake_percent(self):
        self.assertIsNone(resource_sample({'cpu_seconds': 1, 'working_set_bytes': 1, 'private_commit_bytes': 2},
                                          {'cpu_seconds': 2}, 1, 12)['cpu_percent_total_normalized'])
        for value in (True, -1, float('nan')):
            with self.assertRaises(ContractError):
                resource_sample({'cpu_seconds': value, 'working_set_bytes': 1, 'private_commit_bytes': 2}, None, 0, 12)

    def test_basic_error_stops_once_no_second_attempt(self):
        self.api.memory.side_effect = OSError('PRIVATE')
        result = run_session(self.api, ('C:\\',), self.clock, self.clock.advance, duration=10)
        self.assertEqual(result['reason'], 'basic_read_failed')
        self.assertEqual(len(result['rows']), 1)
        self.assertNotIn('PRIVATE', str(result))
        self.assertTrue(result['stop']['clean'])

    def test_missing_disk_counters_does_not_block_cpu_ram(self):
        self.api.disk_counters.return_value = {}
        self.api.disk_counters.side_effect = None
        result = run_session(self.api, ('C:\\',), self.clock, self.clock.advance, duration=3)
        self.assertEqual(result['reason'], 'duration_complete')
        self.assertEqual(result['metrics']['storage.c.activity']['values']['count'], 0)
        self.assertGreater(result['metrics']['cpu.utilization']['values']['count'], 0)

    def test_duration_bound_rejects_long_sessions(self):
        for duration in (0, -1, 90, True, float('inf')):
            with self.assertRaises(ContractError):
                run_session(self.api, (), self.clock, self.clock.advance, duration=duration)
        self.api.cpu_times.assert_not_called()

    def test_session_without_volumes_collects_only_cpu_ram(self):
        result = run_session(self.api, (), self.clock, self.clock.advance, duration=2)
        self.assertEqual(result['metric_slots'], 5)
        self.api.disk_counters.assert_not_called()
        self.api.volume_space.assert_not_called()

    def test_statistics_do_not_invent_values_when_absent(self):
        self.assertEqual(stats([]), {'count': 0, 'min': None, 'mean': None, 'max': None})
        self.assertEqual(stats([0, 10, 20]), {'count': 3, 'min': 0, 'mean': 10, 'max': 20})

    def test_physical_runner_guard_and_marker_precede_native_construction(self):
        path = Path(__file__).resolve().parents[2] / 'scripts/monitoring-basic-session.py'
        text = path.read_text(encoding='utf-8')
        self.assertLess(text.index("'--authorized-single-session'"), text.index('WindowsReadApi()'))
        self.assertLess(text.index(".open('x'"), text.index('WindowsReadApi()'))
        self.assertIn("proof.get('source_hashes') != source_hashes(ROOT)", text)
