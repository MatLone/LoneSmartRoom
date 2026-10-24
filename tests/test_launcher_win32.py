"""Native Windows ACL/mutex tests, using disposable files and toy processes only.

No agent imports, runtime credentials, production mutex, network or port opening.
"""
from concurrent.futures import ThreadPoolExecutor
import ctypes as c
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import queue
import threading
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'agent/windows'))
from launcher_logs import StartupLog
from launcher_win32 import BusyError, SecurityError, Windows, checked_path


@unittest.skipUnless(os.name == 'nt', 'Windows ACL and named mutex required')
class NativeLauncherTests(unittest.TestCase):
    def setUp(self):
        cache = ROOT / '.cache/tests'; cache.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='launcher native ', dir=cache)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.win = Windows()
        self.name = 'Global\\LoneSmartRoom.LauncherTests.' + uuid.uuid4().hex
        self.children = []
        self.addCleanup(self.close_children)

    def close_children(self):
        # Only test substitutes created by THIS test; never terminate production.
        for child in self.children:
            child.communicate(input='release\n', timeout=10)

    def child(self):
        child = subprocess.Popen([sys.executable, '-I', '-B', str(ROOT/'tests/launcher_substitute.py'), self.name],
            cwd=str(self.root), shell=False, close_fds=True,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.children.append(child)
        return child

    def read_status(self, child):
        result = queue.Queue()
        threading.Thread(target=lambda: result.put(child.stdout.readline()), daemon=True).start()
        status = result.get(timeout=10).strip()
        self.assertIn(status, ('held', 'busy'))
        return status

    def test_private_directory_and_files_have_only_current_account_acl(self):
        folder = self.root/'private logs'
        self.win.private_directory(folder)
        self.win.verify_private(folder)
        path = folder/'startup.log'
        self.win.private_file(path)
        self.win.verify_private(path)
        path.write_text('synthetic receipt', encoding='ascii')
        self.assertEqual(path.read_text(), 'synthetic receipt')
        self.win.private_directory(folder)  # Existing exact ACL is accepted unchanged.

    def test_existing_broad_directory_is_rejected_not_repaired(self):
        folder = self.root/'broad'; folder.mkdir()
        before = folder.stat().st_ctime_ns
        with self.assertRaises(SecurityError): self.win.private_directory(folder)
        self.assertEqual(folder.stat().st_ctime_ns, before)
        self.assertEqual(list(folder.iterdir()), [])

    def test_existing_broad_file_is_rejected_not_repaired(self):
        folder = self.root/'private'; self.win.private_directory(folder)
        broad = self.root/'broad.log'; broad.write_text('preserve')
        # Rename retains this file's inherited broad DACL.
        target = folder/'startup.log'; broad.rename(target)
        with self.assertRaises(SecurityError): self.win.private_file(target)
        self.assertEqual(target.read_text(), 'preserve')

    def test_hard_link_cannot_redirect_logs(self):
        folder = self.root/'private'; self.win.private_directory(folder)
        original = folder/'original'; self.win.private_file(original)
        alias = folder/'startup.log'; os.link(original, alias)
        with self.assertRaises(SecurityError): self.win.private_file(alias)

    def test_unsafe_local_paths_are_rejected(self):
        for path in ('relative', r'C:relative', r'\\server\share\file', r'C:\bad\..\file',
                     r'C:\bad\file:stream', 'C:\\bad\nfile', r'%LOCALAPPDATA%\file'):
            with self.subTest(path=path), self.assertRaises(SecurityError): checked_path(path)

    def test_reparse_component_is_rejected_without_creating_a_link(self):
        info = SimpleNamespace(st_mode=0o040700, st_file_attributes=0x400)
        with patch.object(Path, 'lstat', return_value=info), self.assertRaises(SecurityError):
            checked_path(self.root/'logs')

    def test_actual_cross_process_mutex_excludes_second_substitute(self):
        first = self.child(); self.assertEqual(self.read_status(first), 'held')
        second = self.child(); self.assertEqual(self.read_status(second), 'busy')
        second.wait(timeout=10); self.assertEqual(second.returncode, 18)
        with self.assertRaises(BusyError):
            with self.win.mutex(self.name): self.fail('second owner')
        first.stdin.write('release\n'); first.stdin.flush(); first.wait(timeout=10)
        with self.win.mutex(self.name) as recovered:
            self.assertFalse(recovered)

    def test_preexisting_unprotected_mutex_is_rejected_without_repair(self):
        handle = self.win.k.CreateMutexW(None, False, self.name)
        self.assertTrue(handle)
        try:
            with self.assertRaises(SecurityError):
                with self.win.mutex(self.name): self.fail('unsafe mutex accepted')
        finally:
            self.win.k.CloseHandle(handle)

    def test_two_simultaneous_substitutes_have_only_one_owner(self):
        first, second = self.child(), self.child()
        states = [self.read_status(first), self.read_status(second)]
        self.assertCountEqual(states, ['held', 'busy'])

    def test_abandoned_mutex_recovers_after_substitute_crash(self):
        child = self.child(); self.assertEqual(self.read_status(child), 'held')
        # Keep a reference so WAIT_ABANDONED is observable after the owner exits.
        with self.win.attributes(kernel=True) as attributes:
            keeper = self.win.k.CreateMutexW(c.byref(attributes), False, self.name)
        self.assertTrue(keeper)
        try:
            child.stdin.write('crash\n'); child.stdin.flush(); child.wait(timeout=10)
            self.assertEqual(child.returncode, 7)
            with self.win.mutex(self.name) as recovered:
                self.assertTrue(recovered)
            with self.win.mutex(self.name) as recovered:
                self.assertFalse(recovered)
        finally:
            self.win.k.CloseHandle(keeper)

    def test_native_logs_are_private_rotated_and_valid_jsonl(self):
        folder = self.root/'logs'; log = StartupLog(folder, self.win, self.name)
        log.MAX_BYTES = 512
        for _ in range(60): log.emit('attempt', phase='supervisor')
        files = list(folder.iterdir()); self.assertEqual(len(files), 4)
        for path in files:
            self.win.verify_private(path)
            self.assertLessEqual(path.stat().st_size, 512)
            for line in path.read_text().splitlines():
                self.assertEqual(json.loads(line)['event'], 'attempt')

    def test_parallel_log_writers_do_not_corrupt_rotation(self):
        folder = self.root/'logs'; log = StartupLog(folder, self.win, self.name)
        log.MAX_BYTES = 1024
        def write(_):
            for _ in range(12): log.emit('attempt', phase='worker')
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(write, range(4)))
        for path in folder.iterdir():
            self.win.verify_private(path)
            self.assertLessEqual(path.stat().st_size, 1024)
            for line in path.read_text().splitlines(): json.loads(line)


if __name__ == '__main__':
    unittest.main()
