import unittest
import importlib.util
from pathlib import Path
from unittest.mock import Mock,patch
from telemetry.validation import run_observation


class Fake:
    physical=False
    def __init__(self): self.time=0.;self.requests=0;self.closed=0;self.reads=0;self.fail=False;self.exit=False;self.clean=True
    def now(self): return self.time
    def wait(self,n): self.time+=n
    def alive(self): return not self.exit
    def request_snapshot(self): self.requests+=1
    def drain(self): pass
    def read_telemetry(self):
        self.reads+=1
        if self.fail: raise ValueError('sensitive text must not escape')
        return {'ok':True,'telemetry_version':1,'snapshot':None}
    def close(self): self.closed+=1;return self.clean


class ValidationTests(unittest.TestCase):
    def test_cadences_stop_once_and_no_repetition(self):
        f=Fake();r=run_observation(f,now=f.now,wait=f.wait,duration=6)
        self.assertTrue(r['clean_stop']);self.assertEqual(f.closed,1);self.assertEqual(f.reads,3)
        self.assertTrue(5<=f.requests<=6);self.assertFalse(r['physical']);self.assertFalse(r['repeated'])
    def test_read_failure_does_not_retry_or_leak(self):
        f=Fake();f.fail=True;r=run_observation(f,now=f.now,wait=f.wait,duration=6)
        self.assertEqual(f.reads,1);self.assertEqual(f.closed,1);self.assertNotIn('sensitive',str(r))
    def test_transport_exits(self):
        f=Fake();f.exit=True;r=run_observation(f,now=f.now,wait=f.wait,duration=6)
        self.assertEqual(r['reason'],'transport_exited');self.assertEqual(f.closed,1)
    def test_timeout_is_not_success_or_force(self):
        f=Fake();f.clean=False;r=run_observation(f,now=f.now,wait=f.wait,duration=2)
        self.assertFalse(r['clean_stop']);self.assertFalse(r['forced_shutdown']);self.assertEqual(f.closed,1)
    def test_limits(self):
        for n in (0,41,True,float('nan'),float('inf')):
            f=Fake()
            with self.assertRaises(ValueError):run_observation(f,now=f.now,wait=f.wait,duration=n)
    def test_http_success_without_metrics_is_not_transport_validation(self):
        f=Fake();r=run_observation(f,now=f.now,wait=f.wait,duration=2)
        self.assertTrue(r['clean_stop']);self.assertFalse(r['transport_validated']);self.assertEqual(r['snapshots_received'],0)
    def test_required_valid_metric_evidence_is_necessary(self):
        f=Fake();ids=['cpu.utilization','ram.total','ram.used','ram.available','storage.c.total','storage.d.total','gpu.adlx.utilization','gpu.adlx.temperature']
        f.read_telemetry=Mock(return_value={'ok':True,'body':{'snapshot':{'metrics':[dict(id=k,valid=True,stale=False,value=0,age_seconds=0,expires_after_seconds=3) for k in ids]}}})
        r=run_observation(f,now=f.now,wait=f.wait,duration=2);self.assertTrue(r['transport_validated']);self.assertEqual(len(r['valid_metric_ids']),8)
        f.time=0.;f.read_telemetry.return_value['transport_seconds']=3
        r=run_observation(f,now=f.now,wait=f.wait,duration=2);self.assertFalse(r['transport_validated'])


class BackendTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('isolated_transport_backend',Path(__file__).resolve().parents[1]/'scripts/validate-real-telemetry-loopback.py')
        self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
        self.backend=self.module.OwnedTransport(Path('fixture'),{},Mock())
        self.backend.hold=Mock()
    def test_discovery_is_fixed_loopback_and_single(self):
        b=self.backend;b.messages.put({'event':'telemetry_ready','host':'127.0.0.1','port':34567});b.drain();self.assertEqual(b.port,34567)
        b.messages.put({'event':'telemetry_ready','host':'0.0.0.0','port':34568})
        with self.assertRaises(ValueError):b.drain()
    def test_pipe_ready_requires_real_owned_transport(self):
        b=self.backend;b.messages.put({'event':'ready','simulated':True,'transport':'windows_named_pipe_v1','collector_pid':123})
        with self.assertRaises(ValueError):b.drain()
        b.messages.put({'event':'ready','simulated':False,'transport':'windows_named_pipe_v1','collector_pid':123});b.drain();b.hold.assert_called_once_with(123,'collector')
    def test_close_timeout_uses_eof_not_kill(self):
        b=self.backend;b.process=Mock();b.process.poll.return_value=None;b.error_file=Mock();b.drain=Mock(side_effect=ValueError('bad frame'))
        clock=[0.]
        with patch.object(self.module.time,'monotonic',side_effect=lambda:clock[0]),patch.object(self.module.time,'sleep',side_effect=lambda n:clock.__setitem__(0,clock[0]+n)):
            self.assertFalse(b.close())
        b.process.stdin.close.assert_called_once();b.process.kill.assert_not_called();b.process.terminate.assert_not_called()
    def test_sanitized_rule_is_retained_without_free_text(self):
        b=self.backend;b.messages.put(dict(v=1,event='telemetry_diagnostics',accepted=0,rejected=30,last_rule='inconsistent_capacity'));b.drain()
        self.assertEqual(b.telemetry_diagnostics['last_rule'],'inconsistent_capacity')
        b.messages.put(dict(v=1,event='telemetry_diagnostics',accepted=0,rejected=30,last_rule='secret path'))
        with self.assertRaises(ValueError):b.drain()

if __name__=='__main__':unittest.main(verbosity=2)
