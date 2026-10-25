"""Native event tests in unique TEST namespaces. Never targets production events."""
import ctypes as c
from ctypes import wintypes as w
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import unittest
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'agent/windows'))
from launcher_win32 import Windows, BusyError, SecurityError
from local_shutdown import LocalEvents
from lifecycle_logs import LifecycleLog


@unittest.skipUnless(os.name=='nt','Windows kernel objects required')
class LocalEventTests(unittest.TestCase):
    def setUp(self):
        self.win=Windows();self.events=LocalEvents(self.win)
        self.name='Global\\LoneSmartRoom.GracefulTests.'+uuid.uuid4().hex
        self.children=[];self.addCleanup(self.finish_children)

    def finish_children(self):
        for child in self.children:
            # Helpers have a five-second natural lifetime even if an assertion
            # fails. Never terminate/kill them or touch any production process.
            child.communicate(timeout=8)

    def start(self,mode):
        child=subprocess.Popen([sys.executable,'-I','-B',str(ROOT/'tests/graceful_substitute.py'),mode,self.name],
            shell=False,close_fds=True,stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        self.children.append(child)
        ready=queue.Queue()
        threading.Thread(target=lambda:ready.put(child.stdout.readline().strip()),daemon=True).start()
        text=ready.get(timeout=3)
        self.assertTrue(text.startswith('ready:'),text)
        return child,int(text.split(':')[1])

    def test_missing_worker_does_not_create_or_signal_an_event(self):
        self.assertEqual(self.events.request(self.name,.01),'not_running')
        channel=self.events.create(self.name)
        try:self.assertFalse(channel.wait_stop(0))
        finally:channel.close()

    def test_normal_worker_stop_releases_mutex_and_all_handles(self):
        child,pid=self.start('worker')
        self.assertEqual(self.events.request(self.name,2),'completed')
        child.wait(timeout=3);self.assertEqual(child.returncode,0)
        with self.win.mutex(self.name+'.lease'):pass
        self.assertEqual(self.events.request(self.name,0),'not_running')

    def test_supervisor_and_worker_exit_without_residual_processes(self):
        child,worker_pid=self.start('supervisor')
        self.assertEqual(self.events.request(self.name,2),'completed')
        child.wait(timeout=3);self.assertEqual(child.returncode,0)
        k=self.win.k;k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
        handle=k.OpenProcess(0x100000,False,worker_pid)
        if handle:
            try:self.assertEqual(k.WaitForSingleObject(handle,0),0)
            finally:k.CloseHandle(handle)
        else:
            self.assertEqual(c.get_last_error(),87)  # PID no longer exists, not access denied.

    def test_unexpected_worker_crash_is_propagated_without_false_ack(self):
        child,_=self.start('supervisor-crash')
        self.assertEqual(self.events.request(self.name,.1),'timed_out')
        child.wait(timeout=3);self.assertEqual(child.returncode,7)
        with self.win.mutex(self.name+'.lease'):pass
        self.assertEqual(self.events.request(self.name,0),'not_running')

    def test_timeout_does_not_kill_worker_or_release_lease(self):
        child,_=self.start('slow')
        self.assertEqual(self.events.request(self.name,.01),'timed_out')
        self.assertIsNone(child.poll())
        with self.assertRaises(BusyError):
            with self.win.mutex(self.name+'.lease'):self.fail('premature release')
        child.wait(timeout=3);self.assertEqual(child.returncode,0)

    def test_simultaneous_clients_share_the_same_completion(self):
        child,_=self.start('slow')
        with ThreadPoolExecutor(max_workers=3) as pool:
            results=list(pool.map(lambda _:self.events.request(self.name,2),range(3)))
        self.assertEqual(results,['completed']*3)
        child.wait(timeout=3);self.assertEqual(child.returncode,0)

    def test_event_acl_is_exclusive_and_existing_channel_is_not_reset(self):
        channel=self.events.create(self.name)
        try:
            self.win._verify(channel.stop,kernel=True);self.win._verify(channel.done,kernel=True)
            with self.assertRaises(SecurityError):self.events.create(self.name)
            self.assertFalse(channel.wait_stop(0))
        finally:channel.close()
        replacement=self.events.create(self.name)
        try:self.assertFalse(replacement.wait_stop(0))
        finally:replacement.close()

    def test_unprotected_preexisting_events_cannot_receive_stop(self):
        handles=[self.win.k.CreateEventW(None,True,False,self.name+suffix) for suffix in ('.stop','.done')]
        self.assertTrue(all(handles))
        try:
            with self.assertRaises(SecurityError):self.events.request(self.name,.01)
            self.assertEqual(self.win.k.WaitForSingleObject(handles[0],0),0x102)
        finally:
            for handle in handles:self.win.k.CloseHandle(handle)

    def test_lifecycle_logs_are_private_bounded_and_sanitized(self):
        (ROOT/'.cache/tests').mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'.cache/tests') as tmp:
            log=LifecycleLog(Path(tmp)/'logs',self.win,self.name);log.MAX_BYTES=512
            for _ in range(30):log.emit('shutdown_complete',phase='worker')
            for path in log.directory.iterdir():
                self.win.verify_private(path);self.assertLessEqual(path.stat().st_size,512)
                for line in path.read_text().splitlines():self.assertEqual(json.loads(line)['event'],'shutdown_complete')


if __name__=='__main__':unittest.main()
