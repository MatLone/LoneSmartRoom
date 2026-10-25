"""Orchestration tests with synthetic GPU/resources/time only."""
from dataclasses import replace
import unittest
from monitoring.adlx_session import run_session
from monitoring.adlx_provider import Capability, WarmingUp
from monitoring.contracts import ContractError, Availability as A
from monitoring_fakes import FakeClock
from test_adlx_provider import FakeAdlx


class Adapter(FakeAdlx):
    def __init__(self,clock):
        super().__init__(clock);self.gpus=(self.gpus[1],);self.opened=False;self.clean=None
    def open(self):
        if self.opened:return
        super().open();self.opened=True
    def close(self):
        super().close();self.clean=True
    def diagnostics(self):return {'fixture':True,'clean':self.clean}


class Resources:
    def __init__(self,clock):self.clock=clock;self.large=False;self.fail=False
    def logical_processors(self):return 12
    def collector(self):return {'cpu_seconds':self.clock.now*.01,'working_set_bytes':16*1024**2,'private_commit_bytes':10*1024**2}
    def bridge_cpu(self):return self.clock.now*.02
    def bridge(self):
        if self.fail:raise OSError('private not logged')
        return {'cpu_seconds':self.bridge_cpu(),'working_set_bytes':(513 if self.large else 32)*1024**2,'private_commit_bytes':20*1024**2}


class SessionTests(unittest.TestCase):
    def setUp(self):self.clock=FakeClock();self.adapter=Adapter(self.clock);self.resources=Resources(self.clock)
    def run_fixture(self,duration=6):return run_session(self.adapter,self.resources,self.clock,self.clock.advance,duration=duration)
    def test_single_bootstrap_cadence_and_clean_cache(self):
        r=self.run_fixture();self.assertEqual(r['reason'],'duration_complete');self.assertTrue(r['shutdownClean'])
        self.assertEqual(self.adapter.calls.count('open'),1);self.assertEqual(self.adapter.calls.count('close'),1)
        self.assertEqual(r['metrics']['gpu.adlx.utilization']['interval_seconds']['mean'],2)
        self.assertEqual(len(r['rows']),3);self.assertLessEqual(max(x['cache_samples'] for x in r['rows']),32)
        self.assertTrue(all(x['snapshot']['contains_simulated'] for x in r['rows']))
    def test_resource_units_and_normalization(self):
        r=self.run_fixture();self.assertAlmostEqual(r['combinedCpuPercentOfMachine'],.25)
        self.assertEqual(r['combinedResidentBytes']['mean'],48*1024**2)
    def test_invalid_duration_never_opens(self):
        for duration in (0,76,float('nan'),True):
            with self.assertRaises(ContractError):self.run_fixture(duration)
        self.assertEqual(self.adapter.calls,[])
    def test_initialization_failure_no_retry_and_close(self):
        self.adapter.open_failure=RuntimeError('fixture-sensitive-marker')
        r=self.run_fixture();self.assertEqual(r['reason'],'session_failed');self.assertEqual(self.adapter.calls.count('open'),1)
        self.assertEqual(self.adapter.calls.count('close'),1);self.assertNotIn('fixture-sensitive-marker',str(r))
    def test_read_failure_stops_session_without_restart(self):
        self.adapter.failure=RuntimeError('private')
        r=self.run_fixture();self.assertEqual(r['reason'],'gpu_read_failed');self.assertTrue(r['shutdownClean'])
        self.assertEqual(self.adapter.calls.count('latest'),1);self.assertFalse(r['restarted'])
    def test_release_failure_not_success(self):
        self.adapter.close_failure=RuntimeError('private')
        r=self.run_fixture();self.assertFalse(r['shutdownClean']);self.assertFalse(r['forcedTermination'])
    def test_resource_failure_still_closes(self):
        self.resources.fail=True;r=self.run_fixture();self.assertEqual(r['reason'],'session_failed');self.assertTrue(r['shutdownClean'])
    def test_memory_budget_requests_normal_stop(self):
        self.resources.large=True;r=self.run_fixture();self.assertEqual(r['reason'],'memory_budget_exceeded');self.assertTrue(r['shutdownClean'])
    def test_unsupported_metric_never_zero(self):
        self.adapter.caps['gpu.adlx.hotspot_temperature']=Capability(True,False)
        r=self.run_fixture();m=r['metrics']['gpu.adlx.hotspot_temperature'];self.assertEqual(m['values']['count'],0)
        self.assertEqual(m['states'],{'unsupported':3})
    def test_repeated_source_timestamp_unavailable_not_fake_fresh(self):
        self.adapter.frame_hook=lambda f:replace(f,sdk_timestamp_ms=0)
        r=self.run_fixture();states=[next(m['state'] for m in x['snapshot']['metrics'] if m['id']=='gpu.adlx.utilization') for x in r['rows']]
        self.assertEqual(states,['available','unavailable','unavailable'])


if __name__=='__main__':unittest.main()
