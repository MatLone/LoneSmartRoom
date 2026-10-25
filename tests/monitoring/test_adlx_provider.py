"""ADLX fixtures only; no native SDK or driver. These values are NOT PC measurements."""
from dataclasses import replace
import json
from threading import Event
import unittest

from monitoring.adlx_provider import (AdlxProvider,Capability,CHANNELS,Device,DeviceLost,Frame,GPU_SPECS,Reading,basic_v1_projection)
from monitoring.collector import Collector,ReadContext
from monitoring.contracts import Availability as A,ContractError,DataKind,Observation,Sample,Unit
from monitoring.catalog import DEFAULT_METRICS
from monitoring.windows_basic import basic_catalog
from monitoring_fakes import FakeClock,FakeProvider,by_id


class FakeAdlx:
    data_kind=DataKind.SIMULATED
    def __init__(self,clock):
        self.clock=clock;self.calls=[];self.failure=None;self.open_failure=None;self.close_failure=None;self.frame_hook=lambda x:x
        self.gpus=(Device('intel.0','Intel UHD Graphics 730',0x8086,False),Device('amd.7','AMD Radeon RX 6750 XT',0x1002,True))
        self.caps={'gpu.adlx.'+c.key:Capability(True,True) for c in CHANNELS if c.support}
        self.values={'utilization':25.0,'temperature':40.0,'hotspot_temperature':50.0,'vram_used_mb':2048,
                     'core_clock':500,'power':20.0,'fan_rpm':0}
        self.capacity=Reading(A.AVAILABLE,12288)
    def open(self):
        self.calls.append('open')
        if self.open_failure:raise self.open_failure
    def devices(self):self.calls.append('devices');return self.gpus
    def capabilities(self,key):self.calls.append('capabilities');return self.caps
    def total_vram(self,key):self.calls.append('total_vram');return self.capacity
    def latest(self,key):
        self.calls.append('latest')
        if self.failure:raise self.failure
        return self.frame_hook(Frame(key,int(self.clock.now*1000),.05,{'gpu.adlx.'+k:Reading(A.AVAILABLE,v) for k,v in self.values.items()}))
    def close(self):
        self.calls.append('close')
        if self.close_failure:raise self.close_failure
    def set_clock(self,*_):raise AssertionError('Tuning is forbidden')


class AdlxTests(unittest.TestCase):
    def setUp(self):
        self.clock=FakeClock();self.api=FakeAdlx(self.clock);self.provider=AdlxProvider(self.api,'amd.7');self.stop=Event()
    def context(self):return ReadContext(self.clock.utcnow(),self.clock.now,self.clock.now+.25,self.stop)
    def read(self,ids=None):return {x.metric_id:x for x in self.provider.read(ids or self.provider.metric_ids,self.context())}
    def test_constructor_and_import_do_not_initialize_native_or_collect(self):
        self.assertEqual(self.api.calls,[]);self.provider.close();self.provider.close();self.assertEqual(self.api.calls,[])
    def test_no_dll_path_or_untyped_adapter_is_accepted(self):
        for adapter in ('amdadlx64.dll',None,object()):
            with self.assertRaises(ContractError):AdlxProvider(adapter,'amd.7')
    def test_capability_discovery_before_read_and_explicit_amd_selection(self):
        values=self.read();self.assertEqual(self.api.calls,['open','devices','capabilities','total_vram','latest'])
        self.assertEqual(len(values),8);self.assertEqual(values['gpu.adlx.fan_rpm'].value,0)
    def test_provenance_units_and_cache_schema_are_explicit(self):
        c=Collector(GPU_SPECS,[self.provider],clock=self.clock);c.step();s=c.snapshot()
        self.assertEqual(s['schema_version'],1);self.assertTrue(s['contains_simulated'])
        self.assertTrue(all(x['source']=='fixture.adlx' and x['collected_at'] and x['valid'] for x in s['metrics']))
        m=by_id(s);self.assertEqual(m['gpu.adlx.core_clock']['unit'],'megahertz');self.assertEqual(m['gpu.adlx.power']['unit'],'watts')
        self.assertEqual(m['gpu.adlx.vram_used_mb']['unit'],'megabytes');self.assertEqual(m['gpu.adlx.vram_used_mb']['value'],2048)
        self.assertTrue(c.stop().clean)
    def test_not_supported_never_read_as_zero_and_independent_capacity(self):
        self.api.caps={k:Capability(True,False) for k in self.api.caps};values=self.read()
        self.assertNotIn('latest',self.api.calls)
        for k,v in values.items():
            if k!='gpu.adlx.vram_total_mb':self.assertEqual((v.value,v.state),(None,A.UNSUPPORTED))
    def test_failed_or_missing_capability_query_is_unavailable(self):
        self.api.caps['gpu.adlx.power']=Capability(False,True);del self.api.caps['gpu.adlx.temperature']
        v=self.read();self.assertEqual(v['gpu.adlx.power'].state,A.UNAVAILABLE);self.assertIsNone(v['gpu.adlx.temperature'].value)
    def test_zero_is_real_only_on_supported_success_including_fan_stop(self):
        self.api.values={k:0 for k in self.api.values};v=self.read()
        self.assertTrue(all(x.value==0 and x.state==A.AVAILABLE for k,x in v.items() if k!='gpu.adlx.vram_total_mb'))
    def test_invalid_numeric_reading_does_not_poison_other_metrics(self):
        for bad in [None,True,'2',float('nan'),float('inf'),-1,101]:
            with self.subTest(bad=type(bad).__name__):
                self.clock.advance(1);self.api.values['utilization']=bad;v=self.read()
                self.assertEqual((v['gpu.adlx.utilization'].value,v['gpu.adlx.utilization'].state),(None,A.ERROR))
                self.assertEqual(v['gpu.adlx.temperature'].value,40)
    def test_integer_native_units_and_power_bounds(self):
        for key,value in [('core_clock',1.5),('fan_rpm',1.5),('vram_used_mb',1.5),('power',5001)]:
            self.clock.advance(1);self.api.values[key]=value;v=self.read();self.assertEqual(v['gpu.adlx.'+key].state,A.ERROR)
    def test_vram_used_cannot_exceed_total_or_be_silently_clamped(self):
        self.api.values['vram_used_mb']=20000;v=self.read();self.assertEqual(v['gpu.adlx.vram_used_mb'].state,A.ERROR)
        self.assertEqual(v['gpu.adlx.vram_total_mb'].value,12288)
    def test_total_vram_failure_is_not_hardcoded_twelve_gib(self):
        self.api.capacity=Reading(A.UNAVAILABLE,None);v=self.read();self.assertIsNone(v['gpu.adlx.vram_total_mb'].value)
        self.assertEqual(v['gpu.adlx.vram_used_mb'].value,2048)
    def test_zero_total_vram_and_removed_device_do_not_look_valid(self):
        self.api.capacity=Reading(A.AVAILABLE,0);self.assertEqual(self.read()['gpu.adlx.vram_total_mb'].state,A.ERROR)
        self.clock.advance(1);self.api.failure=DeviceLost();self.assertTrue(all(x.value is None for x in self.read().values()))
        self.clock.advance(1);self.read();self.assertEqual(self.api.calls.count('open'),1);self.assertEqual(self.api.calls.count('close'),1)
    def test_repeated_regressed_or_aged_sdk_frames_do_not_become_fresh_valid_values(self):
        self.read();self.clock.advance(1);self.api.frame_hook=lambda f:replace(f,sdk_timestamp_ms=0)
        v=self.read();self.assertEqual(v['gpu.adlx.utilization'].state,A.UNAVAILABLE)
        for change in [dict(age_seconds=10),dict(age_seconds=-1),dict(sdk_timestamp_ms=-1),dict(device_key='intel.0'),dict(age_seconds=float('nan'))]:
            self.clock.advance(1);self.api.frame_hook=lambda f,change=change:replace(f,**change)
            self.assertEqual(self.read()['gpu.adlx.utilization'].state,A.ERROR)
    def test_polling_gate_and_capacity_cached_not_queried_per_channel(self):
        self.read();self.clock.advance(.5);v=self.read();self.assertEqual(v['gpu.adlx.utilization'].state,A.UNAVAILABLE)
        self.clock.advance(.5);self.read();self.assertEqual(self.api.calls.count('latest'),2);self.assertEqual(self.api.calls.count('total_vram'),1)
    def test_temporary_read_error_and_recovery_with_new_sample(self):
        self.api.failure=RuntimeError('do not log private adapter payload');self.assertEqual(self.read()['gpu.adlx.power'].state,A.ERROR)
        self.clock.advance(1);self.api.failure=None;self.assertEqual(self.read()['gpu.adlx.power'].state,A.AVAILABLE)
        self.assertNotIn('private',json.dumps(self.provider.diagnostics()))
    def test_open_failure_cleanup_no_automatic_reinitialize_loop(self):
        self.api.open_failure=RuntimeError('private');self.assertEqual(self.read()['gpu.adlx.utilization'].state,A.ERROR)
        self.clock.advance(1);self.read();self.provider.close();self.assertEqual(self.api.calls,['open','close'])
    def test_permission_denied_is_distinct(self):
        self.api.open_failure=PermissionError('private');self.assertEqual(self.read()['gpu.adlx.power'].state,A.PERMISSION_DENIED)
    def test_bad_or_ambiguous_devices_fail_closed(self):
        for devices in [(self.api.gpus[0],),(self.api.gpus[1],self.api.gpus[1]),(Device('amd.7','Other Radeon',0x1002,True),)]:
            api=FakeAdlx(self.clock);api.gpus=devices;p=AdlxProvider(api,'amd.7')
            self.assertTrue(all(x.value is None for x in p.read(p.metric_ids,self.context())));self.assertNotIn('latest',api.calls)
    def test_unknown_channels_and_forged_readings_rejected(self):
        with self.assertRaises(ContractError):self.provider.read(('SetGPUClock',),self.context())
        self.api.frame_hook=lambda f:replace(f,readings={'execute.cmd':Reading(A.AVAILABLE,1)})
        self.assertEqual(self.read()['gpu.adlx.utilization'].state,A.ERROR)
    def test_close_and_cancellation_are_idempotent(self):
        self.stop.set();self.read();self.assertEqual(self.api.calls,[])
        self.stop.clear();self.read();self.provider.close();self.provider.close();self.assertEqual(self.api.calls.count('close'),1)
        self.assertTrue(all(x.value is None for x in self.read().values()))
    def test_cache_stale_keeps_timestamp_and_limits_history(self):
        c=Collector(GPU_SPECS,[self.provider],clock=self.clock,history_limit=2);c.step();stamp=by_id(c.snapshot())['gpu.adlx.utilization']['collected_at']
        self.clock.advance(3);v=by_id(c.snapshot())['gpu.adlx.utilization'];self.assertTrue(v['stale']);self.assertIsNone(v['value']);self.assertEqual(v['collected_at'],stamp)
        for _ in range(8):self.clock.advance(1);c.step()
        self.assertLessEqual(c.cache.sample_count,len(GPU_SPECS)*2);c.stop()
    def test_active_and_inactive_cadences_reuse_collector(self):
        c=Collector(GPU_SPECS,[self.provider],clock=self.clock);c.step();self.clock.advance(1);c.step()
        self.assertEqual(self.api.calls.count('latest'),2);c.set_active(False);self.clock.advance(1);c.step()
        self.assertEqual(self.api.calls.count('latest'),2);self.clock.advance(4);c.step();self.assertEqual(self.api.calls.count('latest'),3);c.stop()
    def test_thermal_cadence_does_not_renew_timestamp_every_fast_read(self):
        c=Collector(GPU_SPECS,[self.provider],clock=self.clock);c.step();stamp=by_id(c.snapshot())['gpu.adlx.temperature']['collected_at']
        self.clock.advance(1);c.step();self.assertEqual(by_id(c.snapshot())['gpu.adlx.temperature']['collected_at'],stamp)
        self.clock.advance(1);c.step();self.assertNotEqual(by_id(c.snapshot())['gpu.adlx.temperature']['collected_at'],stamp);c.stop()
    def test_deadline_overrun_is_not_accepted_as_valid(self):
        def late(frame):self.clock.advance(1);return frame
        self.api.frame_hook=late;c=Collector(GPU_SPECS,[self.provider],clock=self.clock);c.step()
        self.assertTrue(all(not m['valid'] and m['value'] is None for m in c.snapshot()['metrics']))
        self.assertTrue(any(e['code']=='read_deadline_exceeded' for e in c.diagnostics()));c.stop()
    def test_failed_release_is_reported_once_without_automatic_retry(self):
        c=Collector(GPU_SPECS,[self.provider],clock=self.clock);c.step();self.api.close_failure=RuntimeError('private')
        stopped=c.stop();self.assertTrue(stopped.stopped);self.assertFalse(stopped.clean)
        self.assertEqual(self.api.calls.count('close'),1);self.assertNotIn('private',json.dumps(c.diagnostics()))
    def test_legacy_v1_catalog_and_projection_do_not_advertise_gpu_units(self):
        self.assertEqual(len(DEFAULT_METRICS),22);self.assertEqual(len(basic_catalog(('C:\\','D:\\'))),21)
        c=Collector(basic_catalog(('C:\\','D:\\'))+GPU_SPECS,[self.provider],clock=self.clock);c.step()
        snapshot=c.snapshot();projected=basic_v1_projection(snapshot)
        self.assertEqual(len(projected['metrics']),21);self.assertFalse(projected['contains_simulated'])
        self.assertTrue(all(x['unit'] not in ('watts','megahertz','megabytes') for x in projected['metrics']));c.stop()
    def test_basic_projection_preserves_existing_wire_fields_and_values(self):
        specs=basic_catalog(('C:\\','D:\\'))
        base=Collector(specs,[FakeProvider(specs)],clock=self.clock);base.step()
        extended=Collector(specs+GPU_SPECS,[FakeProvider(specs),self.provider],clock=self.clock);extended.step()
        old=base.snapshot();projected=basic_v1_projection(extended.snapshot())
        # A shared cache's monotonic sequence also counts GPU publications, as designed.
        self.assertGreaterEqual(projected['sequence'],old['sequence'])
        old.pop('sequence');projected.pop('sequence');self.assertEqual(old,projected);base.stop();extended.stop()
    def test_additive_unit_validation_does_not_change_legacy_semantics(self):
        for unit,bad in [(Unit.WATTS,-1),(Unit.WATTS,5001),(Unit.MEGAHERTZ,100001),(Unit.MEGABYTES,1.2)]:
            with self.assertRaises(ContractError):replace(GPU_SPECS[0],unit=unit).validate_value(bad)


if __name__=='__main__':unittest.main()
