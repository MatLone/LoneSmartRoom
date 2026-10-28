"""Fixed candidate lifecycle under virtual time and fake processes, never OS agent."""
import importlib.util
import io
import threading
from contextlib import contextmanager
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests')]
from test_agent_launcher import FakeWindows
spec=importlib.util.spec_from_file_location('reliable_candidate',ROOT/'agent/development/reliable_bootstrap.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class Clock:
    value=0.
    def __call__(self): return self.value
    def sleep(self,n): self.value+=n

class Events:
    def __init__(self,clock,stop_at=None):
        self.clock,self.stop_at=clock,stop_at
        self.completed=self.closed=False
        self.waits=[]
    def create(self,name): self.name=name;return self
    def wait_stop(self,n):
        self.waits.append(n);self.clock.sleep(n)
        return self.stop_at is not None and self.clock()>=self.stop_at
    def complete(self):self.completed=True
    def close(self):self.closed=True

class Child:
    def __init__(self,clock,code=0,exit_at=0,eof_delay=None):
        self.clock,self.code,self.exit_at,self.eof_delay=clock,code,exit_at,eof_delay
        self.stdout=io.BytesIO(b'{"v":1,"event":"listener_bound"}\n')
        self.stdin=Mock()
        self.stdin.close.side_effect=self.eof
        self.closing=False
    def eof(self):
        if not self.closing and self.eof_delay is not None:
            self.exit_at=self.clock()+self.eof_delay
        self.closing=True
    def poll(self):return self.code if self.clock()>=self.exit_at else None
    def wait(self):
        if self.poll() is None and self.closing:
            self.clock.sleep(max(0,self.exit_at-self.clock()))
        assert self.poll() is not None
        return self.code

class BootstrapTests(unittest.TestCase):
    def run_case(self,codes=(0,),*,attempts=1,guard=None,stop_at=None,
                 exit_at=0,eof_delay=None,ready='bound',busy=False):
        clock=Clock();events=Events(clock,stop_at);log=Mock();win=FakeWindows();win.busy=busy
        children=[Child(clock,n,exit_at,eof_delay) for n in codes]
        spawn=Mock(side_effect=children)
        receipt=Mock(state=Mock(return_value=ready)) if isinstance(ready,str) else ready
        with patch.object(m.Layout,'validate'),patch.object(m,'environment_valid',return_value=True),patch('subprocess.run',side_effect=AssertionError('no real guard')):
            code=m.supervise(m.Layout(ROOT),win,log,popen=spawn,guard=guard or Mock(return_value=False),
                attempts=attempts,events=events,readiness=lambda _:receipt,clock=clock,pause=clock.sleep)
        return SimpleNamespace(code=code,spawn=spawn,clock=clock,events=events,log=log,children=children,receipt=receipt)
    def test_fixed_spawn(self):
        r=self.run_case();self.assertEqual(r.code,0)
        args=r.spawn.call_args;layout=m.Layout(ROOT)
        self.assertEqual(args.args[0],[str(layout.python),'-I','-B',str(ROOT/'agent/development/reliable_bootstrap.py'),'_worker'])
        self.assertFalse(args.kwargs['shell']);self.assertEqual(args.kwargs['cwd'],str(ROOT))
        self.assertEqual(args.kwargs['stdin'],m.subprocess.PIPE)
        self.assertEqual(args.kwargs['stderr'],m.subprocess.DEVNULL)
        self.assertTrue(r.events.completed and r.events.closed)
    def test_default_no_retry(self):
        r=self.run_case((71,));self.assertEqual(r.code,71);self.assertEqual(r.spawn.call_count,1)
    def test_missing_candidate_never_spawns(self):
        with patch.object(m,'validate_candidate',side_effect=FileNotFoundError('private path')):
            r=self.run_case();self.assertEqual(r.code,10);r.spawn.assert_not_called()
            self.assertIn('paths_invalid',[c.args[0] for c in r.log.emit.call_args_list])
    def test_simultaneous_supervisors_only_one_spawn(self):
        locks={};started=threading.Event();release=threading.Event();answers=[]
        class Windows(FakeWindows):
            @contextmanager
            def mutex(self,name,timeout=0):
                lock=locks.setdefault(name,threading.Lock())
                if not lock.acquire(False):raise m.BusyError('duplicate')
                try:yield False
                finally:lock.release()
        def launch(*a,**kw):
            started.set();self.assertTrue(release.wait(2));return Child(Clock())
        spawn=Mock(side_effect=launch)
        def run():
            answers.append(m.supervise(m.Layout(ROOT),Windows(),Mock(),popen=spawn,
                guard=lambda _:False,events=Events(Clock()),readiness=lambda _:Mock()))
        with patch.object(m.Layout,'validate'),patch.object(m,'environment_valid',return_value=True):
            thread=threading.Thread(target=run);thread.start();self.assertTrue(started.wait(2))
            run();release.set();thread.join(2)
        self.assertEqual(sorted(answers),[0,18]);self.assertEqual(spawn.call_count,1)
        self.assertFalse(any(lock.locked() for lock in locks.values()))
    def test_only_typed_clean_failure_recovers(self):
        r=self.run_case((71,71,0),attempts=3)
        self.assertEqual(r.code,0);self.assertEqual(r.spawn.call_count,3)
        self.assertEqual(r.events.waits,[0,0,5,0,0,10,0,0]);self.assertTrue(r.events.completed)
    def test_unclassified_errors_never_restart(self):
        for n in (10,11,13,17,18,21,26,-1073741819):
            r=self.run_case((n,),attempts=3)
            self.assertEqual(r.code,n);self.assertEqual(r.spawn.call_count,1);self.assertFalse(r.events.completed)
    def test_guard_before_spawn(self):
        r=self.run_case(guard=Mock(return_value=True))
        self.assertEqual(r.code,13);r.spawn.assert_not_called()
    def test_guard_after_exit_refuses_residual(self):
        r=self.run_case(guard=Mock(side_effect=[False,True]))
        self.assertEqual(r.code,13);self.assertFalse(r.events.completed)
    def test_guard_before_retry(self):
        r=self.run_case((71,),attempts=2,guard=Mock(side_effect=[False,False,True]))
        self.assertEqual(r.code,13);self.assertEqual(r.spawn.call_count,1)
    def test_stop_before_spawn(self):
        r=self.run_case(stop_at=0);self.assertEqual(r.code,0);r.spawn.assert_not_called()
    def test_stop_during_backoff(self):
        r=self.run_case((71,),attempts=3,stop_at=2)
        self.assertEqual(r.code,0);self.assertEqual(r.spawn.call_count,1)
    def test_stop_during_guard_never_creates_worker(self):
        clock=Clock();events=Events(clock)
        def guard(_):events.stop_at=0;return False
        spawn=Mock()
        with patch.object(m.Layout,'validate'),patch.object(m,'environment_valid',return_value=True):
            code=m.supervise(m.Layout(ROOT),FakeWindows(),Mock(),popen=spawn,events=events,guard=guard)
        self.assertEqual(code,0);spawn.assert_not_called();self.assertTrue(events.completed)
    def test_stop_during_worker_uses_eof(self):
        r=self.run_case(stop_at=.2,exit_at=100,eof_delay=.2)
        self.assertEqual(r.code,0);self.assertTrue(r.children[0].closing)
        self.assertTrue(r.events.completed);self.assertLess(r.clock(),1)
    def test_startup_timeout_requests_drain_no_success(self):
        r=self.run_case(ready='waiting',exit_at=200,eof_delay=.2)
        self.assertEqual(r.code,27);self.assertFalse(r.events.completed);self.assertLess(r.clock(),31)
    def test_private_network_startup_deadline_can_retry_only_after_cleanup(self):
        r=self.run_case((0,0),attempts=2,ready='waiting',exit_at=200,eof_delay=.2)
        self.assertEqual(r.code,27);self.assertEqual(r.spawn.call_count,2)
        self.assertTrue(all(c.closing for c in r.children));self.assertFalse(r.events.completed)
    def test_invalid_readiness_never_retries(self):
        r=self.run_case(attempts=3,ready='invalid',exit_at=200,eof_delay=.2)
        self.assertEqual(r.code,27);self.assertEqual(r.spawn.call_count,1)
    def test_malformed_readiness_requests_drain(self):
        r=self.run_case(ready='invalid',exit_at=200,eof_delay=.2)
        self.assertEqual(r.code,27);self.assertFalse(r.events.completed)
    def test_observer_failure_drains_owned_child_without_retry(self):
        receipt=Mock(state=Mock(side_effect=OSError('private observation error')))
        r=self.run_case(ready=receipt,exit_at=200,eof_delay=.2,attempts=3)
        self.assertEqual(r.code,22);self.assertFalse(r.events.completed)
        self.assertTrue(r.children[0].closing);self.assertEqual(r.spawn.call_count,1)
    def test_stop_timeout_is_not_success_even_if_later_cleaned(self):
        r=self.run_case(stop_at=.1,exit_at=200,eof_delay=31)
        self.assertEqual(r.code,24);self.assertFalse(r.events.completed)
        self.assertIn('stop_timed_out',[c.args[0] for c in r.log.emit.call_args_list])
        self.assertLess(r.clock(),33)
    def test_supervisor_lease_duplicate(self):
        r=self.run_case(busy=True);self.assertEqual(r.code,18);r.spawn.assert_not_called()
    def test_budget_validation(self):
        for n in (0,4,True,1.5):
            with self.assertRaises(ValueError):self.run_case(attempts=n)
    def test_readiness_fixed_bytes(self):
        for raw,expected in [(b'{"v":1,"event":"listener_bound"}\n','bound'),(b'{}\n','invalid'),(b'x'*130,'invalid'),(b'','invalid')]:
            r=m.Readiness(io.BytesIO(raw));r.close();self.assertEqual(r.state(),expected)
    def test_parent_eof_and_invalid_input_cooperate(self):
        for raw in (b'',b'arbitrary'):
            local=Mock(wait_stop=Mock(return_value=False));events=Mock(create=Mock(return_value=local))
            channel=m.ParentEvents(events,io.BytesIO(raw)).create('test')
            self.assertTrue(channel.wait_stop(.5));channel.complete();channel.close()
            local.complete.assert_called_once();local.close.assert_called_once()
    def test_startup_command_quotes(self):
        command=m.startup_command(m.Layout(ROOT));self.assertIn('"',command);self.assertIn('-I -B',command)
        self.assertNotIn('serve',command)
    def test_no_external_arguments(self):
        with patch.object(m,'Windows',side_effect=AssertionError('no native')):
            for args in (['--arbitrary'],['start'],['stop','force'],['_worker','path']):self.assertEqual(m.main(args),20)

if __name__=='__main__':unittest.main()
