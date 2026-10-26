"""Only the separately compiled mock executable may run in this suite."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import time
import unittest
from unittest.mock import patch

from monitoring.adlx_bridge import (BridgeError, LineTransport, NativeAdapter, decode, launch_native, MAX_LINE, ROOT)
from monitoring.adlx_provider import AdlxProvider, GPU_SPECS, WarmingUp
from monitoring.collector import Collector, Schedule
from monitoring.contracts import DataKind, Availability as A

PROCESSES=[]
BUILD=ROOT/'.cache/adlx-build'


def mock_process(scenario='normal',diagnostics=False):
    allowed={'normal','unsupported','cap_error','read_fail','load_fail','init_fail','invalid','stale','warming','slow','close_fail','unverified','--self-test'}
    assert scenario in allowed
    receipt=json.loads((BUILD/'bridge-mock-build.json').read_text());exe=BUILD/'bridge-mock.exe'
    assert receipt['mock'] is True and hashlib.sha256(exe.read_bytes()).hexdigest()==receipt['exeSha256']
    assert receipt['sourceSha256']==hashlib.sha256((ROOT/'native/adlx/bridge.cpp').read_bytes()).hexdigest()
    command=[str(exe),scenario]+(['--diagnostics'] if diagnostics else [])
    p=subprocess.Popen(command,cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
        shell=False,close_fds=True,creationflags=subprocess.CREATE_NO_WINDOW,bufsize=0)
    PROCESSES.append(p);return p


class BridgeTests(unittest.TestCase):
    def adapter(self,case='normal',**options):
        a=NativeAdapter(LineTransport(lambda:mock_process(case,options.get('diagnostics',False))),data_kind=DataKind.SIMULATED,**options)
        def close():
            try:a.close()
            except BridgeError:
                self.assertIsNotNone(a.transport.process.poll(),'Mock worker must close without force')
        self.addCleanup(close);a.open();return a

    def test_native_policy_self_tests_no_adlx_loaded(self):
        p=mock_process('--self-test');data=p.stdout.readline(MAX_LINE);p.wait(timeout=3);p.stdin.close();p.stdout.close()
        value=json.loads(data);self.assertTrue(value['ok']);self.assertEqual(value['checks'],35)

    def test_compiled_mock_contains_no_runtime_loader_or_adlx_name(self):
        data=(BUILD/'bridge-mock.exe').read_bytes().lower()
        self.assertNotIn(b'amdadlx64.dll',data);self.assertNotIn('amdadlx64.dll'.encode('utf-16le'),data)

    def test_upstream_bytes_match_manifest(self):
        root=ROOT/'third_party/adlx-v1.4';m=json.loads((root/'manifest.json').read_text())
        self.assertEqual(m['commit'],'66557d410ce4c463f5f7106597d94f53dd84bc82')
        for path,entry in m['files'].items():self.assertEqual(hashlib.sha256((root/path).read_bytes()).hexdigest(),entry['sha256'])

    def test_start_discovery_and_fixed_units(self):
        a=self.adapter();self.assertEqual(a.devices()[0].vendor_id,4098)
        self.assertTrue(all(c.supported for c in a.capabilities('amd-rx6750xt').values()))
        self.assertEqual(a.total_vram('amd-rx6750xt').value,12288)
        frame=a.latest('amd-rx6750xt');self.assertEqual(frame.readings['gpu.adlx.fan_rpm'].value,0)
        self.assertEqual(a.data_kind,DataKind.SIMULATED)

    def test_absent_sensor_is_unsupported_null(self):
        a=self.adapter('unsupported');self.assertFalse(a.capabilities('amd-rx6750xt')['gpu.adlx.hotspot_temperature'].supported)
        self.assertIsNone(a.latest('amd-rx6750xt').readings['gpu.adlx.hotspot_temperature'].value)

    def test_capability_failure_is_not_confirmed_unsupported(self):
        a=self.adapter('cap_error');cap=a.capabilities('amd-rx6750xt')['gpu.adlx.fan_rpm']
        self.assertFalse(cap.ok);self.assertFalse(cap.supported)
        self.assertEqual(a.latest('amd-rx6750xt').readings['gpu.adlx.fan_rpm'].state,A.UNAVAILABLE)

    def test_load_and_driver_initialization_failures(self):
        for scenario,code in [('load_fail','runtime_load_failed'),('init_fail','adlx_initialize_failed')]:
            a=NativeAdapter(LineTransport(lambda:mock_process(scenario)),data_kind=DataKind.SIMULATED)
            with self.assertRaises(BridgeError) as caught:a.open()
            self.assertEqual(caught.exception.code,code)
            try:a.close()
            except BridgeError:pass
            self.assertIsNotNone(a.transport.process.poll())

    def test_no_duplicate_initialization(self):
        a=self.adapter();pid=a.transport.process.pid;a.open();self.assertEqual(pid,a.transport.process.pid)
        with self.assertRaises(BridgeError):a.transport.start()

    def test_simulated_cannot_be_reported_as_real(self):
        a=NativeAdapter(LineTransport(mock_process))
        with self.assertRaises(BridgeError) as caught:a.open()
        self.assertEqual(caught.exception.code,'invalid_identity');a.close()

    def test_read_error_can_recover_with_next_requested_sample(self):
        a=self.adapter('read_fail')
        with self.assertRaises(BridgeError) as caught:a.latest('amd-rx6750xt')
        self.assertEqual(caught.exception.code,'metrics_query_failed');time.sleep(1.05)
        self.assertEqual(a.latest('amd-rx6750xt').readings['gpu.adlx.utilization'].state,A.AVAILABLE)

    def test_native_rate_limit_and_no_arbitrary_commands(self):
        a=self.adapter();a.latest('amd-rx6750xt')
        with self.assertRaises(BridgeError) as caught:a.latest('amd-rx6750xt')
        self.assertEqual(caught.exception.code,'rate_limited')
        with self.assertRaises(BridgeError):a.transport.send('powershell')

    def test_long_command_closes_owned_mock_normally(self):
        p=mock_process();ready=json.loads(p.stdout.readline(MAX_LINE));self.assertEqual(ready['event'],'ready')
        p.stdin.write(b'x'*33+b'\n');p.stdin.flush()
        events=[json.loads(line) for line in p.stdout];p.wait(timeout=3);p.stdin.close();p.stdout.close()
        self.assertEqual(events[0]['code'],'command_limit');self.assertEqual(events[-1]['event'],'stopped')

    def test_read_timeout_does_not_retry_or_kill(self):
        a=self.adapter('slow',timeout=.1)
        with self.assertRaises(BridgeError) as caught:a.latest('amd-rx6750xt')
        self.assertEqual(caught.exception.code,'read_timeout')
        with self.assertRaises(BridgeError) as caught:a.latest('amd-rx6750xt')
        self.assertEqual(caught.exception.code,'read_still_pending')
        a.close();self.assertEqual(a.transport.process.returncode,0)

    def test_collector_uses_existing_cache_and_never_presents_fixture_as_real(self):
        a=self.adapter();provider=AdlxProvider(a,'amd-rx6750xt');c=Collector(GPU_SPECS,[provider],schedule=Schedule(fast=2,thermal=2,read_budget=1))
        c.step();snapshot=c.snapshot();self.assertTrue(snapshot['contains_simulated'])
        by={m['id']:m for m in snapshot['metrics']};self.assertEqual(by['gpu.adlx.core_clock']['unit'],'megahertz')
        self.assertEqual(by['gpu.adlx.fan_rpm']['value'],0);self.assertTrue(by['gpu.adlx.fan_rpm']['valid'])
        # Cache conserves both the eight initial warming records and eight readings.
        stopped=c.stop();self.assertTrue(stopped.clean);self.assertEqual(c.cache.sample_count,16)

    def test_invalid_and_old_frames_are_not_valid(self):
        for case in ('invalid','stale'):
            a=self.adapter(case);c=Collector(GPU_SPECS,[AdlxProvider(a,'amd-rx6750xt')],schedule=Schedule(read_budget=1))
            c.step();metric=next(m for m in c.snapshot()['metrics'] if m['id']=='gpu.adlx.utilization')
            self.assertFalse(metric['valid']);self.assertIsNone(metric['value']);c.stop()

    def test_history_warmup_preserves_null(self):
        a=self.adapter('warming');c=Collector(GPU_SPECS,[AdlxProvider(a,'amd-rx6750xt')],schedule=Schedule(read_budget=1))
        c.step();m=next(m for m in c.snapshot()['metrics'] if m['id']=='gpu.adlx.utilization')
        self.assertEqual(m['state'],'warming_up');self.assertIsNone(m['value']);c.stop()

    def test_close_is_idempotent_and_reader_thread_finishes(self):
        a=self.adapter();a.close();a.close();self.assertTrue(a.clean)
        self.assertIsNotNone(a.transport.process.poll());self.assertFalse(a.transport._reader.is_alive())

    def test_failed_release_not_falsely_reported_clean(self):
        a=self.adapter('close_fail')
        with self.assertRaises(BridgeError):a.close()
        self.assertFalse(a.clean);self.assertEqual(a.transport.process.returncode,2)

    def test_close_timeout_never_forces_or_claims_success(self):
        class Transport:
            process=None
            def close(self):return False
        a=NativeAdapter(Transport())
        with self.assertRaises(BridgeError) as caught:a.close()
        self.assertEqual(caught.exception.code,'shutdown_timeout');self.assertFalse(a.clean)

    def test_protocol_invalid_duplicate_nan_oversized_and_unknown_events(self):
        for line in [b'{}\n',b'{"v":1,"v":1,"event":"ready"}\n',b'{"v":1,"event":"frame","n":NaN}\n',b'x'*(MAX_LINE+1)+b'\n',b'{"v":1,"event":"shell"}\n']:
            with self.assertRaises(BridgeError):decode(line)

    def test_queue_and_message_limits(self):
        class Output:
            def __init__(self):self.remaining=100
            def readline(self,_limit):
                self.remaining-=1;return b'{"v":1,"event":"warming_up"}\n' if self.remaining>=0 else b''
        class Child:stdout=Output()
        t=LineTransport(None);t.process=Child();t._read()
        self.assertLessEqual(t._queue.qsize(),8);self.assertEqual(t._fault,'message_queue_limit')

    def test_stale_age_and_unknown_clock_cannot_become_fresh(self):
        a=self.adapter();real=a._next
        a._next=lambda:dict(real(),age_seconds=None)
        with self.assertRaises(BridgeError) as caught:a.latest('amd-rx6750xt')
        self.assertEqual(caught.exception.code,'invalid_frame')

    def test_unknown_device_key_refused_without_request(self):
        a=self.adapter()
        with self.assertRaises(BridgeError):a.latest('arbitrary.device')

    def test_fixed_native_command_and_no_shell(self):
        with patch('monitoring.adlx_bridge.subprocess.Popen') as popen:
            launch_native();args,kwargs=popen.call_args
            self.assertEqual(args[0],[str(BUILD/'bridge.exe')]);self.assertIs(kwargs['shell'],False);self.assertIs(kwargs['close_fds'],True)

    def test_no_control_api_is_called_or_linked_helper(self):
        source=(ROOT/'native/adlx/bridge.cpp').read_text()
        for forbidden in ('->Set','->GetGPUTuning','->GetPowerTuning','ADLXInitializeWithIncompatibleDriver','adlx_load_library','std::system','ShellExecute','CreateProcess'):
            self.assertNotIn(forbidden,source)
        self.assertIn('LOAD_LIBRARY_SEARCH_SYSTEM32',source);self.assertIn('WTD_REVOKE_WHOLECHAIN',source)


if __name__=='__main__':unittest.main()
