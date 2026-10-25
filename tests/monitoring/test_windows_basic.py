"""Basic provider algorithms against synthetic inputs; never constructs WindowsReadApi."""
from threading import Event
from unittest.mock import Mock
import unittest

from monitoring.collector import Collector, ReadContext
from monitoring.contracts import Availability as A, ContractError
from monitoring.windows_basic import (CpuProvider, DiskCounter, DiskIoProvider, MemoryProvider,
                                      VolumeProvider, VolumeSpace, basic_catalog, volume_root)
from monitoring_fakes import FakeClock, by_id


class BasicTests(unittest.TestCase):
    def setUp(self):
        self.api = Mock()
        self.clock = FakeClock()
        self.context = ReadContext(self.clock.utcnow(), 0, 1, Event())

    def read(self, provider):
        return {x.metric_id: x for x in provider.read(provider.metric_ids, self.context)}

    def test_catalog_contains_only_authorized_metric_types(self):
        specs = basic_catalog(('C:\\', 'D:\\'))
        self.assertEqual(len(specs), 21)
        self.assertFalse(any(any(x in s.metric_id for x in ('gpu', 'fan', 'temperature', 'vram')) for s in specs))
        self.assertEqual(len(basic_catalog(())), 5)

    def test_only_fixed_letter_roots_accepted_and_catalog_bounded(self):
        for root in ('C:', 'c:\\', 'C:\\private', '\\\\server\\share\\', 'steam://open/main', '../file', 'C:\\x\x00'):
            with self.assertRaises(ContractError):
                volume_root(root)
        for roots in (('C:\\', 'C:\\'), tuple(chr(65 + n) + ':\\' for n in range(8))):
            with self.assertRaises(ContractError):
                basic_catalog(roots)

    def test_cpu_first_sample_warming_not_zero(self):
        self.api.cpu_times.return_value = (100, 200, 100)
        value = self.read(CpuProvider(self.api))['cpu.utilization']
        self.assertEqual(value.state, A.WARMING_UP)
        self.assertIsNone(value.value)

    def test_cpu_correct_delta_kernel_already_contains_idle(self):
        self.api.cpu_times.side_effect = [(100, 200, 100), (140, 260, 140)]
        provider = CpuProvider(self.api)
        self.read(provider)
        self.assertEqual(self.read(provider)['cpu.utilization'].value, 60)

    def test_cpu_real_zero_utilization_is_valid(self):
        self.api.cpu_times.side_effect = [(10, 20, 10), (20, 30, 10)]
        provider = CpuProvider(self.api)
        self.read(provider)
        result = self.read(provider)['cpu.utilization']
        self.assertEqual((result.state, result.value), (A.AVAILABLE, 0))

    def test_cpu_zero_delta_or_counter_reset_reprime(self):
        self.api.cpu_times.side_effect = [(10, 20, 10), (10, 20, 10), (1, 2, 1), (3, 7, 6)]
        provider = CpuProvider(self.api)
        for _ in range(3):
            self.assertEqual(self.read(provider)['cpu.utilization'].state, A.WARMING_UP)
        self.assertEqual(self.read(provider)['cpu.utilization'].value, 80)

    def test_cpu_failed_read_discards_old_baseline(self):
        self.api.cpu_times.side_effect = [(1, 2, 1), OSError('secret'), (2, 3, 2)]
        provider = CpuProvider(self.api)
        self.read(provider)
        with self.assertRaises(OSError):
            self.read(provider)
        self.assertEqual(self.read(provider)['cpu.utilization'].state, A.WARMING_UP)

    def test_cpu_invalid_counters_and_idle_delta(self):
        for invalid in ((-1, 1, 1), (True, 2, 2), (1.5, 3, 3), (1, 2), (1, 2, 2**64)):
            self.api.cpu_times.return_value = invalid
            with self.assertRaises(ContractError):
                self.read(CpuProvider(self.api))
        self.api.cpu_times.side_effect = [(1, 2, 1), (100, 3, 2)]
        provider = CpuProvider(self.api)
        self.read(provider)
        self.assertEqual(self.read(provider)['cpu.utilization'].state, A.ERROR)

    def test_memory_bytes_percent_and_single_coherent_read(self):
        self.api.memory.return_value = (16 * 1024**3, 6 * 1024**3)
        values = self.read(MemoryProvider(self.api))
        self.assertEqual(values['ram.used'].value, 10 * 1024**3)
        self.assertEqual(values['ram.utilization'].value, 62.5)
        self.assertEqual(values['ram.used'].value + values['ram.available'].value, values['ram.total'].value)
        self.api.memory.assert_called_once_with()

    def test_invalid_memory_not_clamped_or_zeroed(self):
        for pair in ((0, 0), (100, 101), (-1, 0), (True, 0)):
            self.api.memory.return_value = pair
            with self.assertRaises(ContractError):
                self.read(MemoryProvider(self.api))

    def test_volume_physical_occupation_independent_from_caller_quota(self):
        self.api.volume_space.return_value = VolumeSpace(1000, 700, 100, 200)
        values = self.read(VolumeProvider(self.api, 'C:\\'))
        self.assertEqual(values['storage.c.occupation'].value, 20)
        self.assertEqual(values['storage.c.available'].value, 100)
        self.assertEqual(values['storage.c.free'].value, 700)
        # Reserved/pool space and quota are NOT silently counted as occupied bytes.
        self.assertEqual(values['storage.c.used'].value, 200)

    def test_volume_unavailable_api_reports_unsupported(self):
        self.api.volume_space.side_effect = NotImplementedError()
        self.assertTrue(all(x.state == A.UNSUPPORTED and x.value is None
                            for x in self.read(VolumeProvider(self.api, 'C:\\')).values()))

    def test_volume_invalid_geometry_rejected(self):
        for space in (VolumeSpace(0, 0, 0, 0), VolumeSpace(100, 101, 0, 0),
                      VolumeSpace(100, 0, -1, 0), VolumeSpace(100, 0, 0, 1.5)):
            with self.assertRaises(ContractError):
                space.validate()

    def disk_provider(self):
        return DiskIoProvider(self.api, ('C:\\',))

    def counters(self, first=100, second=100, read=2048, write=4096, activity=7):
        return {key: DiskCounter(first, second, value) for key, value in
                zip(('storage.c.read_rate', 'storage.c.write_rate', 'storage.c.activity'), (read, write, activity))}

    def test_io_first_sample_warming_then_rates_remain_bytes_per_second(self):
        self.api.disk_counters.side_effect = [self.counters(), self.counters(200, 200)]
        provider = self.disk_provider()
        self.assertTrue(all(x.state == A.WARMING_UP for x in self.read(provider).values()))
        values = self.read(provider)
        self.assertEqual(values['storage.c.read_rate'].value, 2048)
        self.assertEqual(values['storage.c.write_rate'].value, 4096)
        self.assertEqual(values['storage.c.activity'].value, 7)

    def test_io_missing_counter_does_not_become_zero(self):
        self.api.disk_counters.return_value = {}
        self.assertTrue(all(x.state == A.UNAVAILABLE and x.value is None for x in self.read(self.disk_provider()).values()))

    def test_io_counter_reset_and_invalid_time_reprime(self):
        self.api.disk_counters.side_effect = [self.counters(), self.counters(1, 101), self.counters(5, 101), self.counters(10, 200)]
        provider = self.disk_provider()
        for _ in range(3):
            self.assertTrue(all(x.state == A.WARMING_UP for x in self.read(provider).values()))
        self.assertTrue(all(x.state == A.AVAILABLE for x in self.read(provider).values()))

    def test_io_failure_then_recovery_requires_new_pair(self):
        self.api.disk_counters.side_effect = [self.counters(), OSError(), self.counters(200, 200), self.counters(300, 300)]
        provider = self.disk_provider()
        self.read(provider)
        with self.assertRaises(OSError):
            self.read(provider)
        self.assertTrue(all(x.state == A.WARMING_UP for x in self.read(provider).values()))
        self.assertTrue(all(x.state == A.AVAILABLE for x in self.read(provider).values()))

    def test_io_invalid_rates_and_activity_not_substituted_or_clamped(self):
        for read, activity in ((float('nan'), 101), (-1, -1), (float('inf'), float('inf')), (None, None)):
            self.api.disk_counters.side_effect = [self.counters(), self.counters(200, 200, read=read, activity=activity)]
            provider = self.disk_provider()
            self.read(provider)
            values = self.read(provider)
            self.assertEqual(values['storage.c.read_rate'].state, A.UNAVAILABLE)
            self.assertEqual(values['storage.c.activity'].state, A.UNAVAILABLE)
            self.assertEqual(values['storage.c.write_rate'].value, 4096)

    def test_io_corrupt_raw_counter_rejected(self):
        self.api.disk_counters.return_value = {'storage.c.read_rate': DiskCounter(-1, 100, 20)}
        self.assertEqual(self.read(self.disk_provider())['storage.c.read_rate'].state, A.UNAVAILABLE)

    def test_provider_cache_cadence_recovery_and_staleness(self):
        self.api.memory.side_effect = [(100, 25), OSError('PRIVATE'), (100, 50)]
        collector = Collector(basic_catalog(())[1:], [MemoryProvider(self.api)], clock=self.clock)
        self.addCleanup(collector.stop)
        collector.step()
        self.assertEqual(by_id(collector.snapshot())['ram.used']['value'], 75)
        self.clock.advance(1)
        collector.step()
        self.assertIsNone(by_id(collector.snapshot())['ram.used']['value'])
        self.clock.advance(1)
        collector.step()
        self.assertEqual(by_id(collector.snapshot())['ram.used']['value'], 50)
        self.clock.advance(3)
        view = by_id(collector.snapshot())['ram.used']
        self.assertEqual(view['state'], 'stale')
        self.assertIsNone(view['value'])

    def test_io_close_only_releases_query(self):
        self.disk_provider().close()
        self.api.close_disk_query.assert_called_once_with()
