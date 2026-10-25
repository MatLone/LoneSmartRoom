"""Offline simulated monitoring suite. No real provider, agent, IPC or network.

Audit guard forbids networking, process creation, dynamic ctypes libraries and
Registry operations. Resource benchmark measures this synthetic test workload only.
"""
import json
# Standard ctypes bootstrap resolves Python's Kernel32 error helpers on Windows.
# Existing preservation tests import its Structure types; no sensor/API query here.
import ctypes
from pathlib import Path
import sys
import time
import tracemalloc
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests/monitoring'))
sys.path.insert(0, str(ROOT / 'tests'))


def offline_guard(event, _args):
    if (event.startswith(('socket.', 'winreg.')) or event in (
            'subprocess.Popen', 'os.system', 'os.startfile', 'os.startfile/2',
            'os.posix_spawn', 'os.exec', 'ctypes.dlopen', 'ctypes.call_function')):
        raise RuntimeError('External operation forbidden by simulated monitoring runner')


def main():
    sys.addaudithook(offline_guard)
    modules = ('test_contracts', 'test_collector', 'test_ipc', 'test_baseline',
               'test_wol_backup', 'test_steam_launcher', 'test_cs2_launcher')
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in modules)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    from monitoring.catalog import DEFAULT_METRICS
    from monitoring.collector import Collector
    from monitoring_fakes import FakeClock, FakeProvider
    clock = FakeClock()
    provider = FakeProvider(DEFAULT_METRICS)
    collector = Collector(DEFAULT_METRICS, [provider], clock=clock)
    for _ in range(200):
        collector.step()
        clock.advance(60)
    tracemalloc.start()
    cpu_start, wall_start = time.process_time(), time.perf_counter()
    for _ in range(2000):
        collector.step()
        clock.advance(60)
    retained, peak = tracemalloc.get_traced_memory()
    cpu_elapsed, wall_elapsed = time.process_time() - cpu_start, time.perf_counter() - wall_start
    tracemalloc.stop()
    stopped = collector.stop()
    receipt = {'tests': result.testsRun, 'failures': len(result.failures),
               'errors': len(result.errors), 'skipped': len(result.skipped),
               'ok': result.wasSuccessful() and not result.skipped,
               'modules': list(modules), 'real_sensor_collection': False,
               'operational_agent_access': False, 'native_ipc_started': False,
               'network_or_process_launch_allowed': False,
               'native_acl_verified': False,
               'benchmark': {'kind': 'synthetic_fixture_not_pc_telemetry', 'passes': 2000,
                             'metric_slots': len(DEFAULT_METRICS), 'wall_seconds': wall_elapsed,
                             'test_process_cpu_seconds': cpu_elapsed, 'traced_retained_bytes': retained,
                             'traced_peak_bytes': peak, 'cache_samples': collector.cache.sample_count,
                             'max_cache_samples': len(DEFAULT_METRICS) * 120,
                             'stop_clean': stopped.clean}}
    directory = ROOT / '.cache/validation/monitoring-foundation'
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'tests-summary.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt))
    return 0 if receipt['ok'] and stopped.clean else 1


if __name__ == '__main__':
    raise SystemExit(main())
