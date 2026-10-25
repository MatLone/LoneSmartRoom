"""Lifecycle tests with fake executors/stores; TCP fixtures use loopback port 0 only."""
from contextlib import contextmanager
import json
from pathlib import Path
import socket
import sqlite3
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'agent/windows'))
import graceful_launcher as launcher
from graceful_runtime import DrainingServer, DrainingDispatcher, Shutdown, serve
from lifecycle_logs import LifecycleLog
from local_shutdown import LocalEvents, identity
from secure_apps import AppError, AppRegistry
from test_agent_launcher import FakeWindows


class Store:
    def __init__(self,path):
        self.path=path; self.clock=time.time
        with self.connect() as db:
            db.execute('CREATE TABLE devices(id TEXT PRIMARY KEY,revoked INTEGER)')
            db.execute('INSERT INTO devices VALUES (?,0)',('a'*32,))

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=3)
        try:
            with db:yield db
        finally:db.close()


class Log:
    def __init__(self):self.events=[]
    def emit(self,event,**kwargs):self.events.append(event)


class ShutdownTests(unittest.TestCase):
    def setUp(self):
        self.log=Log(); self.release=threading.Event(); self.entered=threading.Event()
        self.server=Mock(); self.apps=Mock(); self.serving=Mock()
        self.server.wait_drained.side_effect=lambda:self.release.wait(3)
        self.server.stop_admission.side_effect=self.entered.set
        self.release.set()
        self.addCleanup(self.release.set)

    def plan(self,grace=1):return Shutdown(self.server,self.apps,self.serving,self.log,grace)

    def test_normal_order_closes_listener_before_waiting_for_handlers(self):
        order=[]
        for label,obj,name in [('gate',self.server,'stop_admission'),('apps',self.apps,'quiesce'),
                ('shutdown',self.server,'shutdown'),('join',self.serving,'join'),
                ('close',self.server,'server_close'),('requests',self.server,'wait_drained'),
                ('executor',self.apps,'wait_drained')]:
            getattr(obj,name).side_effect=lambda *args,label=label:order.append(label)
        self.assertTrue(self.plan().stop())
        self.assertEqual(order,['gate','apps','shutdown','join','close','requests','executor'])
        self.assertEqual(self.log.events,['shutdown_requested','listener_closed','shutdown_complete'])

    def test_inflight_request_finishes_before_completion(self):
        self.release.clear(); plan=self.plan()
        thread=threading.Thread(target=plan.stop);thread.start()
        self.assertTrue(self.entered.wait(1));self.assertFalse(plan.done.wait(.03))
        self.server.server_close.assert_called_once()
        self.release.set();thread.join(2)
        self.assertFalse(thread.is_alive());self.assertTrue(plan.done.is_set())

    def test_concurrent_shutdown_has_one_cleanup_owner(self):
        self.release.clear();plan=self.plan()
        threads=[threading.Thread(target=plan.stop) for _ in range(4)]
        for thread in threads:thread.start()
        self.assertTrue(self.entered.wait(1));self.release.set()
        for thread in threads:thread.join(2);self.assertFalse(thread.is_alive())
        self.server.shutdown.assert_called_once();self.server.server_close.assert_called_once()
        self.assertEqual(self.log.events.count('shutdown_complete'),1)

    def test_deadline_does_not_abort_inflight_or_claim_completion(self):
        self.release.clear();plan=self.plan(.03)
        thread=threading.Thread(target=plan.stop);thread.start()
        until=time.monotonic()+1
        while not plan.expired and time.monotonic()<until:time.sleep(.005)
        self.assertTrue(plan.expired);self.assertFalse(plan.done.is_set());self.assertTrue(thread.is_alive())
        self.assertNotIn('shutdown_complete',self.log.events)
        self.release.set();thread.join(2);self.assertFalse(thread.is_alive())
        self.assertEqual(self.log.events.count('shutdown_deadline_exceeded'),1)

    def test_unexpected_server_thread_exit_skips_shutdown_deadlock(self):
        self.serving.is_alive.return_value=False
        self.assertTrue(self.plan().stop())
        self.server.shutdown.assert_not_called();self.server.server_close.assert_called_once()

    def test_log_failure_does_not_skip_cleanup_or_report_healthy_logs(self):
        self.log.emit=Mock(side_effect=OSError('SYNTHETIC_SECRET'))
        plan=self.plan();self.assertFalse(plan.stop())
        self.server.server_close.assert_called_once();self.apps.wait_drained.assert_called_once()
        self.assertTrue(plan.done.is_set())


class DispatcherTests(unittest.TestCase):
    def setUp(self):
        (ROOT/'.cache/tests').mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'.cache/tests');self.addCleanup(self.temp.cleanup)
        self.registry=AppRegistry(Store(Path(self.temp.name)/'synthetic.db'))
        self.registry.set_permission('a'*32,['steam','cs2'],True)
        self.started,self.release=threading.Event(),threading.Event();self.calls=[]
        def executor(app):self.calls.append(app);self.started.set();self.release.wait(3)
        self.dispatcher=DrainingDispatcher(self.registry,executor,lambda:True)
        self.addCleanup(self.finish)

    def finish(self):self.release.set();self.dispatcher.close()
    def submit(self,identifier,app='steam'):
        return self.dispatcher.submit('a'*32,{'request_id':identifier*32,'app':app,'confirmed':True})

    def test_claimed_execution_finishes_but_queued_work_is_cancelled(self):
        self.submit('1');self.assertTrue(self.started.wait(1));self.submit('2','cs2')
        self.dispatcher.quiesce()
        with self.assertRaises(AppError) as error:self.submit('3')
        self.assertEqual((error.exception.status,error.exception.code),(503,'agent_stopping'))
        queued=self.registry.result('a'*32,'2'*32)
        self.assertEqual((queued['state'],queued['error']),('failed','agent_stopping'))
        self.assertTrue(self.dispatcher.worker.is_alive())
        self.release.set();self.dispatcher.wait_drained()
        self.assertEqual(self.calls,['steam'])
        self.assertEqual(self.registry.result('a'*32,'1'*32)['state'],'executed')
        self.assertFalse(self.dispatcher.worker.is_alive())

    def test_permissions_and_command_validation_are_still_enforced(self):
        self.registry.set_permission('a'*32,['steam','cs2'],False)
        with self.assertRaises(AppError) as error:self.submit('4')
        self.assertEqual(error.exception.status,403)
        for payload in ({'app':'cmd.exe'},{'request_id':'5'*32,'app':'steam','confirmed':True,'args':['bad']}):
            with self.assertRaises(AppError):self.dispatcher.submit('a'*32,payload)
        self.assertEqual(self.calls,[])

    def test_idle_and_repeated_close_leave_no_dispatcher_thread(self):
        self.dispatcher.close();self.dispatcher.close()
        self.assertFalse(self.dispatcher.worker.is_alive())


class TcpFixtureTests(unittest.TestCase):
    def setUp(self):
        self.release=threading.Event();self.entered=threading.Event()
        class Context:
            def wrap_socket(_,request,server_side):return request  # Toy TLS substitute only.
        self.server=DrainingServer(('127.0.0.1',0),Context(),None,'127.0.0.0/8',private_guard=lambda:True)
        self.assertNotEqual(self.server.server_port,8776)
        def handler(request,address):
            self.entered.set();self.release.wait(3)
        self.server.finish_request=handler
        self.serving=threading.Thread(target=self.server.serve_forever,kwargs={'poll_interval':.01})
        self.serving.start()
        self.addCleanup(self.cleanup)

    def cleanup(self):
        self.release.set()
        if self.serving.is_alive():self.server.shutdown()
        self.serving.join(2);self.server.server_close();self.server.wait_drained()

    def test_listener_port_can_be_rebound_after_clean_shutdown(self):
        port=self.server.server_port
        self.assertTrue(Shutdown(self.server,Mock(),self.serving,Log()).stop())
        with socket.socket() as probe:probe.bind(('127.0.0.1',port))

    def test_accepted_fake_handler_drains_after_listener_closes(self):
        client=socket.create_connection(self.server.server_address,timeout=2)
        self.addCleanup(client.close);self.assertTrue(self.entered.wait(1))
        plan=Shutdown(self.server,Mock(),self.serving,Log(),grace=.05)
        stopper=threading.Thread(target=plan.stop);stopper.start()
        until=time.monotonic()+1
        while self.server.socket.fileno()!=-1 and time.monotonic()<until:time.sleep(.005)
        self.assertEqual(self.server.socket.fileno(),-1)
        self.assertFalse(plan.done.is_set());self.assertTrue(stopper.is_alive())
        self.release.set();stopper.join(2);self.assertFalse(stopper.is_alive())
        self.assertEqual(self.server.active_requests,0)

    def test_new_admission_is_rejected_without_creating_handler(self):
        self.server.stop_admission();request=Mock()
        self.server.process_request(request,('127.0.0.1',12345))
        request.close.assert_called_once();self.assertEqual(self.server.active_requests,0)


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.win=FakeWindows();self.layout=launcher.Layout(ROOT)
        self.log=Log();self.channel=Mock();self.events=Mock()
        self.events.create.return_value=self.channel
        self.enterContext(patch.object(launcher.Layout,'validate'))
        self.enterContext(patch.object(launcher,'environment_valid',return_value=True))
        self.enterContext(patch('socket.socket',side_effect=AssertionError('launcher unit socket forbidden')))
        self.enterContext(patch('subprocess.Popen',side_effect=AssertionError('real launcher forbidden')))

    def test_mutex_released_before_completion_ack_and_channel_closed(self):
        self.channel.complete.side_effect=lambda:self.assertFalse(self.win.active)
        runner=Mock(side_effect=lambda *_:self.assertTrue(self.win.active))
        self.assertEqual(launcher.worker(self.layout,self.log,self.win,self.events,runner=runner,guard=lambda:False),0)
        self.channel.complete.assert_called_once();self.channel.close.assert_called_once()
        self.assertIn('mutex_released',self.log.events)

    def test_worker_exception_cleans_channel_and_never_acknowledges_success(self):
        runner=Mock(side_effect=RuntimeError('SYNTHETIC_SECRET'))
        self.assertEqual(launcher.worker(self.layout,self.log,self.win,self.events,runner=runner,guard=lambda:False),17)
        self.assertFalse(self.win.active);self.channel.close.assert_called_once();self.channel.complete.assert_not_called()
        self.assertNotIn('SYNTHETIC_SECRET',str(self.log.events))

    def test_busy_or_legacy_worker_never_creates_stop_channel(self):
        self.win.busy=True
        self.assertEqual(launcher.worker(self.layout,self.log,self.win,self.events,runner=Mock(),guard=lambda:False),18)
        self.win.busy=False
        self.assertEqual(launcher.worker(self.layout,self.log,self.win,self.events,runner=Mock(),guard=lambda:True),13)
        self.events.create.assert_not_called()

    def test_supervisor_spawn_failure_without_worker_returns_and_creates_no_channel(self):
        popen=Mock(side_effect=OSError(5,'SYNTHETIC_SECRET'))
        self.assertEqual(launcher.supervise(self.layout,self.log,self.win,popen),12)
        popen.assert_called_once();self.events.create.assert_not_called()

    def test_supervisor_waits_once_and_propagates_unexpected_child_exit(self):
        popen=Mock(return_value=SimpleNamespace(wait=Mock(return_value=7)))
        self.assertEqual(launcher.supervise(self.layout,self.log,self.win,popen),7)
        popen.return_value.wait.assert_called_once();popen.assert_called_once()
        args,kwargs=popen.call_args
        self.assertEqual(args[0][-1],'_worker');self.assertIs(kwargs['shell'],False)
        self.assertEqual(kwargs['cwd'],str(ROOT))

    def test_local_stop_completed_timeout_and_absence_are_distinct(self):
        for result,code in (('completed',0),('timed_out',24),('not_running',25)):
            self.events.request.return_value=result
            self.assertEqual(launcher.request_stop(self.layout,self.log,self.win,self.events),code)
        self.events.create.assert_not_called()

    def test_wrong_arguments_and_elevation_cannot_start_or_stop(self):
        for args in ([],['start','bad'],['stop','bad'],['shell'],['_worker','path']):
            self.assertEqual(launcher.main(args),20)
        self.win.elevated=True
        self.assertEqual(launcher.request_stop(self.layout,self.log,self.win,self.events),11)
        self.events.request.assert_not_called()


class LogAndChannelTests(unittest.TestCase):
    def test_schema_and_rotation_preserve_sanitization(self):
        (ROOT/'.cache/tests').mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'.cache/tests') as tmp:
            folder=Path(tmp)/'logs';log=LifecycleLog(folder,FakeWindows(),'test')
            log.MAX_BYTES=512
            for _ in range(30):log.emit('shutdown_requested',phase='worker')
            with self.assertRaises(ValueError):log.emit('SYNTHETIC_SECRET')
            with self.assertRaises(TypeError):log.emit('shutdown_requested',message='SYNTHETIC_SECRET')
            for path in folder.iterdir():
                self.assertLessEqual(path.stat().st_size,512)
                self.assertNotIn('SYNTHETIC_SECRET',path.read_text())
                for line in path.read_text().splitlines():
                    self.assertLessEqual(set(json.loads(line)),{'utc','pid','event','phase','code','dependency'})
            self.assertEqual(len(list(folder.iterdir())),4)

    def test_channel_name_is_fixed_scope_and_rejects_arbitrary_commands(self):
        name=identity(ROOT,'S-1-5-21-test')
        LocalEvents.validate(name)
        for bad in ('steam','cmd.exe',name+' --bad','Global\\Other.name',name+'.stop'):
            with self.assertRaises(OSError):LocalEvents.validate(bad)


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.stop=threading.Event();self.serving_done=threading.Event();self.created=threading.Event()
        self.channel=SimpleNamespace(wait_stop=self.stop.wait)
        self.log=Log();self.apps=Mock();self.server=Mock();self.count=0
        self.server.serve_forever.side_effect=lambda **kw:self.serving_done.wait(3)
        self.server.shutdown.side_effect=self.serving_done.set
        self.config={'host':'127.0.0.1','port':0,'network':'127.0.0.0/8'}
        self.context=Mock(return_value=object())
        self.addCleanup(self.stop.set);self.addCleanup(self.serving_done.set)

    def runtime(self,**kw):
        def factory(*args,**kwargs):self.created.set();return self.server
        return serve(self.config,object(),self.channel,self.log,
            private_guard=kw.get('guard',lambda:True),context_factory=self.context,
            registry_factory=Mock(),executor=Mock(),
            server_factory=kw.get('factory',factory),dispatcher_factory=kw.get('dispatcher',Mock(return_value=self.apps)))

    def test_stop_before_bind_opens_no_listener(self):
        self.stop.set();factory=Mock()
        self.assertEqual(self.runtime(factory=factory),0);factory.assert_not_called();self.context.assert_not_called()

    def test_waiting_for_private_network_can_be_stopped(self):
        factory=Mock();thread=threading.Thread(target=lambda:self.runtime(guard=lambda:False,factory=factory))
        thread.start();self.stop.set();thread.join(2)
        self.assertFalse(thread.is_alive());factory.assert_not_called()

    def test_local_stop_closes_server_dispatcher_and_serve_thread(self):
        result=[];thread=threading.Thread(target=lambda:result.append(self.runtime()))
        thread.start();self.assertTrue(self.created.wait(1));self.stop.set();thread.join(2)
        self.assertFalse(thread.is_alive());self.assertEqual(result,[0])
        self.server.server_close.assert_called_once();self.apps.wait_drained.assert_called_once()
        self.assertFalse(any(t.name=='lsr-https' for t in threading.enumerate()))

    def test_dispatcher_creation_failure_closes_bound_listener(self):
        with self.assertRaises(OSError):self.runtime(dispatcher=Mock(side_effect=OSError('SYNTHETIC_SECRET')))
        self.server.server_close.assert_called_once();self.server.serve_forever.assert_not_called()

    def test_unexpected_serve_exit_is_not_restarted(self):
        self.server.serve_forever.side_effect=None
        with self.assertRaisesRegex(RuntimeError,'serve_loop_exited'):self.runtime()
        self.server.serve_forever.assert_called_once();self.server.server_close.assert_called_once()

    def test_network_change_rebinds_even_if_network_recovers_during_cleanup(self):
        count=[0]
        def factory(*args,**kwargs):
            count[0]+=1
            if count[0]==2:self.stop.set()
            self.serving_done.clear()
            return self.server
        guard_calls=[0]
        def guard():
            guard_calls[0]+=1
            return guard_calls[0]!=2
        self.assertEqual(self.runtime(guard=guard,factory=factory),0)
        self.assertEqual(count[0],2)

    def test_stop_during_tls_context_creation_does_not_bind(self):
        self.context.side_effect=lambda:self.stop.set()
        factory=Mock();self.assertEqual(self.runtime(factory=factory),0);factory.assert_not_called()


if __name__=='__main__':unittest.main()
