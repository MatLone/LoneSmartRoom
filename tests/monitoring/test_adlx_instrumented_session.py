"""Synthetic observation policy only; no native construction or hardware access."""
import importlib.util
import json
from pathlib import Path
import unittest
from dataclasses import replace
from monitoring.adlx_bridge import BridgeError
from monitoring.contracts import ContractError
from test_adlx_session import Adapter, Resources
from monitoring_fakes import FakeClock

PATH = Path(__file__).resolve().parents[2]/'scripts/adlx-instrumented-session.py'
spec = importlib.util.spec_from_file_location('instrumented', PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class InstrumentedTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.adapter = Adapter(self.clock)
        self.resources = Resources(self.clock)

    def run_fixture(self, duration=6):
        return module.run_instrumented(self.adapter, self.resources, self.clock, self.clock.advance, duration=duration)

    def test_first_rejected_then_valid_same_bridge(self):
        original = self.adapter.latest
        calls = []
        def read(key):
            calls.append(key)
            if len(calls) == 1:
                raise BridgeError('invalid_frame', rule='age_null', stage='time')
            return original(key)
        self.adapter.latest = read
        r = self.run_fixture()
        self.assertEqual(r['frameCounts'], {'rejected':1, 'valid':2})
        self.assertEqual(r['firstFrameOutcome'], 'rejected')
        self.assertEqual(r['ruleCounts'], {'age_null':1})
        self.assertEqual(self.adapter.calls.count('open'), 1)
        self.assertEqual(self.adapter.calls.count('close'), 1)
        self.assertTrue(r['shutdownClean'])
        first = r['rows'][0]['snapshot']['metrics']
        self.assertTrue(all(m['value'] is None and not m['valid'] for m in first if m['id']!='gpu.adlx.vram_total_mb'))

    def test_all_rejected_not_reported_as_dynamic_valid(self):
        self.adapter.failure = BridgeError('invalid_frame', rule='age_null', stage='time')
        r = self.run_fixture()
        self.assertEqual(r['frameCounts'], {'rejected':3})
        self.assertEqual(r['reason'], 'duration_complete')
        self.assertEqual(r['metrics']['gpu.adlx.utilization']['values']['count'], 0)
        self.assertEqual(r['metrics']['gpu.adlx.vram_total_mb']['values']['count'], 1)

    def test_unknown_rule_stops_without_retry(self):
        self.adapter.failure = BridgeError('invalid_frame', rule='private exception marker')
        r = self.run_fixture()
        self.assertEqual(r['reason'], 'fatal_read_error')
        self.assertEqual(r['readAttempts'], 1)
        self.assertNotIn('private exception marker', str(r))

    def test_timeout_stops_and_closes(self):
        self.adapter.failure = BridgeError('read_timeout')
        r = self.run_fixture()
        self.assertEqual(r['reason'], 'fatal_read_error')
        self.assertTrue(r['shutdownClean'])
        self.assertEqual(r['readAttempts'], 1)

    def test_unexpected_error_not_silently_retried(self):
        self.adapter.failure = RuntimeError('sensitive')
        r = self.run_fixture()
        self.assertEqual(r['reason'], 'fatal_read_error')
        self.assertNotIn('sensitive', str(r))

    def test_existing_age_limit_unchanged(self):
        self.adapter.frame_hook = lambda frame: replace(frame, age_seconds=1.50001)
        r = self.run_fixture()
        self.assertEqual(r['ruleCounts'], {'provider_sample_age_limit':3})
        self.assertEqual(r['metrics']['gpu.adlx.utilization']['values']['count'], 0)

    def test_timestamp_repeat_remains_unavailable(self):
        self.adapter.frame_hook = lambda frame: replace(frame, sdk_timestamp_ms=0)
        r = self.run_fixture()
        self.assertEqual(r['frameCounts'], {'valid':1, 'rejected':2})
        self.assertEqual(r['ruleCounts'], {'provider_timestamp_not_advanced':2})

    def test_valid_cadence_and_resources(self):
        r = self.run_fixture()
        self.assertEqual(r['frameCounts'], {'valid':3})
        self.assertEqual(r['metrics']['gpu.adlx.utilization']['interval_seconds']['mean'], 2)
        self.assertAlmostEqual(sum(v['cpu_percent_total_normalized'] for v in r['resourceSummary'].values()), .25)
        self.assertEqual(r['combinedResidentBytes']['mean'], 48*1024**2)

    def test_bootstrap_failure_one_attempt_clean_release(self):
        self.adapter.open_failure = RuntimeError('private')
        r = self.run_fixture()
        self.assertEqual(r['reason'], 'session_failed')
        self.assertEqual(self.adapter.calls.count('open'), 1)
        self.assertEqual(self.adapter.calls.count('close'), 1)
        self.assertTrue(r['shutdownClean'])

    def test_shutdown_timeout_not_success(self):
        self.adapter.close_failure = RuntimeError('private')
        self.assertFalse(self.run_fixture()['shutdownClean'])

    def test_memory_limit_normal_close_no_kill(self):
        self.resources.large = True
        r = self.run_fixture()
        self.assertEqual(r['reason'], 'memory_budget_exceeded')
        self.assertFalse(r['forcedTermination'])

    def test_resource_failure_closes(self):
        self.resources.fail = True
        r = self.run_fixture()
        self.assertEqual(r['reason'], 'session_failed')
        self.assertTrue(r['shutdownClean'])

    def test_invalid_duration_cannot_open(self):
        for duration in (0,71,True,float('nan')):
            with self.assertRaises(ContractError): self.run_fixture(duration)
        self.assertFalse(self.adapter.calls)

    def test_export_byte_record_limits_first_retained(self):
        records = [{'rule':'age_null','padding':'x'*2500}]+[{'rule':'frame_structure_accepted','padding':'y'*2500} for _ in range(20)]
        encoded = module.diagnostic_bytes({'frame_diagnostics':{'records':records,'dropped':0}})
        result = json.loads(encoded)
        self.assertLessEqual(len(encoded),32768)
        self.assertLessEqual(len(result['records']),16)
        self.assertEqual(result['records'][0]['rule'],'age_null')


if __name__ == '__main__': unittest.main()
