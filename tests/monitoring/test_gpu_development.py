"""GPU + basic + cache/IPC integration with synthetic providers and process handles."""
from dataclasses import replace
import json
import hashlib
from tempfile import TemporaryDirectory
from pathlib import Path
from subprocess import TimeoutExpired
from unittest.mock import Mock,patch
import unittest
from threading import Event

from monitoring.adlx_bridge import BridgeError,launch_native
from monitoring.adlx_provider import Capability,Reading,basic_v1_projection
from monitoring.contracts import Availability as A
from monitoring.development_collector import create_basic_collector
from monitoring.gpu_development import validate_gpu_mode,validate_gpu_bundle,claim_gpu_owner,finish_gpu,ReadActivity
from monitoring.ipc import LocalReadService,LocalAccessPolicy,PeerEvidence,MAX_RESPONSE_BYTES
from monitoring.windows_basic import VolumeSpace,DiskCounter
from monitoring.pipe_server import PipeServer
from monitoring_fakes import FakeClock,by_id
from test_adlx_provider import FakeAdlx

SID='S-1-5-21-100000000-200000000-300000000-1001'


class GpuIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.clock=FakeClock();self.api=Mock()
        self.api.fixed_volumes.return_value=('C:\\','D:\\','E:\\')
        self.api.cpu_times.side_effect=lambda:(int(self.clock.now*100),int(self.clock.now*200),int(self.clock.now*100))
        self.api.memory.return_value=(16*1024**3,8*1024**3)
        self.api.volume_space.return_value=VolumeSpace(1000,600,600,400)
        self.api.disk_counters.side_effect=lambda:{'storage.'+v+'.'+s:DiskCounter(int(self.clock.now*10),int(self.clock.now*100),0.) for v in ('c','d') for s in ('read_rate','write_rate','activity')}
        self.gpu=FakeAdlx(self.clock);self.gpu.gpus=(replace(self.gpu.gpus[1],key='amd-rx6750xt'),)
        self.collector=create_basic_collector(self.api,gpu_adapter=self.gpu,clock=self.clock)
        self.addCleanup(lambda:self.collector.stop(2))

    def sample(self,advance=0):
        self.clock.advance(advance);self.collector.step();return by_id(self.collector.snapshot())

    def test_construction_does_not_open_gpu_or_sample(self):
        self.assertFalse(self.gpu.calls);self.api.cpu_times.assert_not_called()
        self.assertEqual(len(self.collector.cache.specs),29)
        self.assertTrue(all(m['value'] is None for m in self.collector.snapshot()['metrics']))

    def test_cpu_one_second_gpu_two_seconds_capacity_sixty(self):
        self.sample();self.sample(1);self.assertEqual(self.gpu.calls.count('latest'),1)
        s=self.sample(1);self.assertEqual(self.gpu.calls.count('latest'),2)
        self.assertEqual(s['gpu.adlx.temperature']['interval_seconds'],2)
        self.assertEqual(s['cpu.utilization']['interval_seconds'],1)
        self.assertEqual(s['gpu.adlx.vram_total_mb']['interval_seconds'],60)
        self.assertEqual(s['storage.c.total']['interval_seconds'],60)
        self.assertEqual(self.gpu.calls.count('open'),1)

    def test_first_age_null_rejected_then_recovers_without_restart(self):
        self.gpu.failure=BridgeError('invalid_frame',rule='age_null',stage='time')
        first=self.sample();self.assertIsNone(first['gpu.adlx.utilization']['value'])
        self.assertEqual(first['gpu.adlx.utilization']['state'],'error')
        self.assertTrue(first['ram.used']['valid'])
        self.gpu.failure=None;second=self.sample(2)
        self.assertTrue(second['gpu.adlx.utilization']['valid']);self.assertTrue(second['cpu.utilization']['valid'])
        self.assertEqual(self.gpu.calls.count('open'),1)

    def test_partial_support_and_zero_preserved(self):
        self.gpu.caps['gpu.adlx.power']=Capability(True,False)
        self.gpu.values['fan_rpm']=0
        s=self.sample();self.assertEqual(s['gpu.adlx.fan_rpm']['value'],0)
        self.assertTrue(s['gpu.adlx.fan_rpm']['valid'])
        self.assertEqual((s['gpu.adlx.power']['value'],s['gpu.adlx.power']['state']),(None,'unsupported'))

    def test_loss_of_bridge_does_not_poison_basic_or_restart(self):
        self.sample();self.gpu.failure=BridgeError('worker_eof');s=self.sample(2)
        self.assertIsNone(s['gpu.adlx.temperature']['value']);self.assertTrue(s['cpu.utilization']['valid'])
        self.assertTrue(s['storage.d.read_rate']['valid']);self.assertEqual(self.gpu.calls.count('open'),1)
        self.assertTrue(self.collector.stop(2).clean)
        self.assertEqual(self.gpu.calls.count('close'),1)

    def test_temporal_and_nonfinite_values_remain_rejected(self):
        for age in (-.002,1.500001,float('nan'),float('inf')):
            self.gpu.frame_hook=lambda f,age=age:replace(f,age_seconds=age)
            s=self.sample(2);self.assertIsNone(s['gpu.adlx.utilization']['value'])
        self.gpu.frame_hook=lambda f:f;self.gpu.values['temperature']=float('nan')
        s=self.sample(2);self.assertIsNone(s['gpu.adlx.temperature']['value'])
        self.assertTrue(s['gpu.adlx.utilization']['valid'])

    def test_stale_cache_never_renews_collection_time(self):
        self.sample();before=by_id(self.collector.snapshot())['gpu.adlx.utilization']
        self.clock.advance(6);after=by_id(self.collector.snapshot())['gpu.adlx.utilization']
        self.assertEqual(after['collected_at'],before['collected_at'])
        self.assertEqual((after['value'],after['state'],after['valid']),(None,'stale',False))

    def test_additive_ingress_and_information_age_not_cache_age(self):
        self.gpu.frame_hook=lambda f:replace(f,age_seconds=.5)
        first=self.sample()['gpu.adlx.utilization']
        self.assertEqual(first['ingress_age_seconds'],.5)
        self.assertEqual(first['information_age_seconds'],first['age_seconds']+.5)
        self.clock.advance(2.69)
        cached=by_id(self.collector.snapshot())['gpu.adlx.utilization']
        self.assertEqual(cached['age_seconds'],2.69)
        self.assertEqual(cached['information_age_seconds'],3.19)
        self.assertEqual(cached['collected_at'],first['collected_at'])

    def test_long_owned_session_no_duplicate_provider_and_clean_stop(self):
        for n in range(500):self.sample(2)
        self.assertEqual(self.gpu.calls.count('open'),1)
        self.assertEqual(self.gpu.calls.count('latest'),500)
        self.assertLessEqual(self.collector.cache.sample_count,29*120)
        self.assertTrue(self.collector.stop(2).clean)
        self.assertEqual(self.gpu.calls.count('close'),1)

    def test_inactive_cadences_no_new_gpu_process(self):
        self.sample();self.collector.set_active(False);s=self.sample(5)
        self.assertEqual(self.gpu.calls.count('latest'),1)
        self.assertEqual(s['cpu.utilization']['interval_seconds'],5)
        s=self.sample(5);self.assertEqual(self.gpu.calls.count('latest'),2)
        self.assertEqual(s['gpu.adlx.utilization']['interval_seconds'],10)
        self.collector.set_active(True);self.sample(2)
        self.assertEqual(self.gpu.calls.count('open'),1)

    def test_v1_pipe_cache_read_and_access_controls_unchanged(self):
        self.sample();service=LocalReadService(self.collector,LocalAccessPolicy(SID,1))
        peer=PeerEvidence(SID,1,True,False);calls=len(self.gpu.calls)
        raw=service.handle(b'{"v":1,"op":"snapshot"}',peer);result=json.loads(raw)
        self.assertTrue(result['ok']);self.assertEqual(result['snapshot']['schema_version'],1)
        self.assertEqual(len(result['snapshot']['metrics']),29);self.assertLess(len(raw),MAX_RESPONSE_BYTES)
        self.assertEqual(len(self.gpu.calls),calls)
        self.assertEqual(json.loads(service.handle(b'{"v":1,"op":"snapshot"}',PeerEvidence(SID,2,True,False)))['error'],'access_denied')
        for bad in (b'{"v":1,"op":"set_clock"}',b'{"v":1,"op":"snapshot","active":true}'):
            self.assertEqual(json.loads(service.handle(bad,peer))['error'],'invalid_request')

    def test_cache_limit_and_old_v1_projection(self):
        for _ in range(260):self.sample(1)
        self.assertLessEqual(self.collector.cache.sample_count,29*120)
        basic=basic_v1_projection(self.collector.snapshot())
        self.assertEqual(len(basic['metrics']),21)
        self.assertFalse(any(m['id'].startswith('gpu.') for m in basic['metrics']))
        self.assertTrue(all(by_id(basic)[id]['valid'] for id in ('cpu.utilization','ram.used','storage.c.total','storage.d.total')))

    def test_only_authorized_snapshot_changes_internal_demand(self):
        self.sample()
        for authorized in (False,True):
            with self.subTest(authorized=authorized):
                stop=Event();api=Mock();api.own={'sid':SID,'session':1};api.alive.return_value=True
                api.accept.side_effect=lambda *args:stop.set()
                api.read_frame.return_value=b'{"v":1,"op":"snapshot"}'
                api.read_exact.return_value=b'\x06'
                api.client_token.return_value=PeerEvidence(SID,1,authorized,False)
                activity=Mock()
                server=PipeServer(api,self.collector,'a'*32,12,{},stop,activity=activity)
                server.handle=99;server.serve()
                self.assertEqual(activity.read.call_count,int(authorized))
                api.close.assert_called_once_with(99)


class OwnershipTests(unittest.TestCase):
    def test_packaged_gpu_requires_integrity_and_real_owned_context(self):
        test_root=Path(__file__).resolve().parents[2]/'.cache/tests';test_root.mkdir(exist_ok=True,parents=True)
        with TemporaryDirectory(dir=test_root) as directory:
            root=Path(directory);build=root/'native/adlx';build.mkdir(parents=True)
            exe=build/'bridge.exe';exe.write_bytes(b'not executable - test substitute')
            digest=hashlib.sha256(exe.read_bytes()).hexdigest()
            receipt={'mock':False,'verifyOnly':False,'sdkCommit':'66557d410ce4c463f5f7106597d94f53dd84bc82','exeSha256':digest}
            (build/'bridge-build.json').write_text(json.dumps(receipt))
            policy={'schema':1,'version':'2.0.0-dev.6','realOnly':True,'gpuReadOnly':True,'nativeSha256':digest}
            (root/'BUNDLED-MONITORING.json').write_text(json.dumps(policy))
            validate_gpu_mode(root,True,True,False,None)
            self.assertEqual(validate_gpu_bundle(root),build)
            for args in ((True,False,False,70),(True,True,True,None),(True,True,False,70)):
                with self.assertRaises(PermissionError):validate_gpu_mode(root,*args)
            exe.write_bytes(b'tampered')
            with self.assertRaises(PermissionError):validate_gpu_bundle(root)
            with patch('monitoring.adlx_bridge.subprocess.Popen') as spawn:
                with self.assertRaises(BridgeError):launch_native(application=True)
                with self.assertRaises(BridgeError):launch_native(application=True,owner_handle=123,diagnostics=True)
                spawn.assert_not_called()

    def test_bundle_native_spawn_fixed_application_flag_inherited_lease_only(self):
        from monitoring.adlx_bridge import ROOT
        with patch('monitoring.gpu_development.validate_gpu_bundle',return_value=ROOT/'.cache/adlx-build'),\
             patch('monitoring.adlx_bridge.os.get_handle_inheritable',return_value=False),\
             patch('monitoring.adlx_bridge.os.set_handle_inheritable') as inherit,\
             patch('monitoring.adlx_bridge.subprocess.Popen') as spawn:
            launch_native(application=True,owner_handle=123)
            command,=spawn.call_args.args
            self.assertEqual(command,[str(ROOT/'.cache/adlx-build/bridge.exe'),'--application'])
            self.assertEqual(spawn.call_args.kwargs['startupinfo'].lpAttributeList,{'handle_list':[123]})
            self.assertFalse(spawn.call_args.kwargs['shell'])
            self.assertEqual(inherit.call_args_list[-1].args,(123,False))

    def test_bounded_development_only_not_packaged_or_simulated(self):
        root=Path(__file__).resolve().parents[2]
        validate_gpu_mode(root,True,False,False,70)
        for application,simulated,duration in ((True,False,None),(False,True,70),(False,False,75),(False,False,True)):
            with self.assertRaises(PermissionError):validate_gpu_mode(root,True,application,simulated,duration)

    def test_owner_uses_fixed_account_name_and_verified_dacl(self):
        api=Mock();api.own={'sid':SID,'elevated':False};api.create_server.return_value=12
        self.assertEqual(claim_gpu_owner(api),12)
        name=api.create_server.call_args.args[0]
        self.assertTrue(name.startswith(r'\\.\pipe\LoneSmartRoom.Monitoring.Gpu.Dev.Owner.'))
        api.inspect_dacl.assert_called_once_with(12)
        api.create_server.side_effect=OSError('occupied')
        with self.assertRaises(OSError):claim_gpu_owner(api)
        api.close.assert_not_called()

    def test_owner_bad_acl_closes_handle_and_elevation_refused(self):
        api=Mock();api.own={'sid':SID,'elevated':False};api.create_server.return_value=12;api.inspect_dacl.side_effect=PermissionError()
        with self.assertRaises(PermissionError):claim_gpu_owner(api)
        api.close.assert_called_once_with(12);api.own['elevated']=True
        with self.assertRaises(PermissionError):claim_gpu_owner(api)
        self.assertEqual(api.create_server.call_count,1)

    def test_shutdown_waits_for_actual_exit_after_timeout_without_kill(self):
        adapter=Mock();adapter.clean=True;process=adapter.transport.process
        adapter.close.side_effect=[BridgeError('shutdown_timeout'),None]
        process.poll.side_effect=[None,0];process.wait.side_effect=TimeoutExpired('fixture',.25)
        pending=Mock();self.assertTrue(finish_gpu(adapter,pending))
        pending.assert_called_once();process.kill.assert_not_called();process.terminate.assert_not_called()
        self.assertEqual(adapter.close.call_count,2)

    def test_nonzero_exit_never_reports_clean(self):
        adapter=Mock();adapter.clean=False;adapter.transport.process.poll.return_value=2
        self.assertFalse(finish_gpu(adapter))

    def test_process_query_error_retains_owner_until_exit_confirmed(self):
        adapter=Mock();adapter.clean=True;adapter.transport.process.poll.side_effect=[OSError('private'),0]
        pending=Mock();self.assertTrue(finish_gpu(adapter,pending));pending.assert_called_once()
        adapter.transport.process.kill.assert_not_called()

    def test_internal_demand_no_extra_wire_command(self):
        clock=FakeClock();collector=Mock();activity=ReadActivity(collector,clock.monotonic)
        clock.advance(4);activity.tick();collector.set_active.assert_called_once_with(False)
        clock.advance(6);activity.read();self.assertFalse(activity.active)
        clock.advance(1);activity.read();self.assertTrue(activity.active)
        collector.set_active.assert_called_with(True)

    def test_only_gpu_owner_handle_inherited_and_parent_restored(self):
        with patch('monitoring.adlx_bridge.os.get_handle_inheritable',return_value=False),patch('monitoring.adlx_bridge.os.set_handle_inheritable') as inherit,patch('monitoring.adlx_bridge.subprocess.Popen') as spawn:
            process=launch_native(owner_handle=123)
            self.assertIs(process,spawn.return_value)
            args,options=spawn.call_args
            self.assertEqual(len(args[0]),1);self.assertFalse(options['shell']);self.assertTrue(options['close_fds'])
            self.assertEqual(options['startupinfo'].lpAttributeList,{'handle_list':[123]})
            self.assertEqual([c.args for c in inherit.call_args_list],[(123,True),(123,False)])

    def test_owner_inheritance_reset_even_if_creation_fails(self):
        with patch('monitoring.adlx_bridge.os.get_handle_inheritable',return_value=False),patch('monitoring.adlx_bridge.os.set_handle_inheritable') as inherit,patch('monitoring.adlx_bridge.subprocess.Popen',side_effect=OSError('private')):
            with self.assertRaises(OSError):launch_native(owner_handle=123)
            self.assertEqual(inherit.call_args_list[-1].args,(123,False))

    def test_created_process_is_not_lost_if_handle_reset_fails(self):
        with patch('monitoring.adlx_bridge.os.get_handle_inheritable',return_value=False),patch('monitoring.adlx_bridge.os.set_handle_inheritable',side_effect=[None,OSError('private')]),patch('monitoring.adlx_bridge.subprocess.Popen') as spawn:
            process=launch_native(owner_handle=123)
            self.assertIs(process,spawn.return_value)
            self.assertTrue(process._lone_owner_reset_failed)

    def test_owner_handle_invalid_or_preinheritable_refuses_spawn(self):
        with patch('monitoring.adlx_bridge.subprocess.Popen') as spawn:
            for value in (True,0,-1,'123',2**63):
                with self.assertRaises(ValueError):launch_native(owner_handle=value)
            with patch('monitoring.adlx_bridge.os.get_handle_inheritable',return_value=True):
                with self.assertRaises(BridgeError):launch_native(owner_handle=123)
            spawn.assert_not_called()


if __name__=='__main__':unittest.main()
