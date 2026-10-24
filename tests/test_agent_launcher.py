"""Mock-only launcher orchestration. Never calls real agent, Popen or network."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'agent/windows'))
import agent_launcher as launcher
from launcher_logs import StartupLog, error_code
from launcher_win32 import BusyError, SecurityError
ENVIRONMENT_VALID = launcher.environment_valid


class FakeWindows:
    sid = 'S-1-5-21-100000000-200000000-300000000-1001'
    elevated = False
    busy = False
    abandoned = False
    active = False

    @contextmanager
    def mutex(self, name, timeout=0):
        if self.busy:
            raise BusyError('do not log private exception contents')
        self.active = True
        try:
            yield self.abandoned
        finally:
            self.active = False

    def private_directory(self, path):
        path.mkdir(exist_ok=True)

    def private_file(self, path):
        path.touch(exist_ok=True)

    def verify_private(self, path):
        pass


class LauncherTests(unittest.TestCase):
    def setUp(self):
        cache = ROOT / '.cache/tests'; cache.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='launcher mock ', dir=cache)
        self.addCleanup(self.temp.cleanup)
        self.layout = launcher.Layout(Path(self.temp.name))
        for path in (self.layout.python, self.layout.launcher, self.layout.agent,
            self.layout.root / '.venv/pyvenv.cfg',
            self.layout.root / 'agent/windows/launcher_logs.py',
            self.layout.root / 'agent/windows/launcher_win32.py'):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'MZfake; never execute')
        (self.layout.root / '.runtime').mkdir()
        self.win = FakeWindows()
        self.log = Mock()
        self.popen = Mock(return_value=SimpleNamespace(wait=Mock(return_value=0)))
        self.runner, self.guard, self.importer = Mock(), Mock(return_value=False), Mock()
        self.enterContext(patch.object(launcher, 'environment_valid', return_value=True))
        self.chdir = self.enterContext(patch.object(launcher.os, 'chdir'))
        # Global safety nets: no accidental real process/runpy/server invocation.
        self.real_popen = self.enterContext(patch('subprocess.Popen', side_effect=AssertionError('real Popen forbidden')))
        self.enterContext(patch('runpy.run_path', side_effect=AssertionError('real agent forbidden')))
        self.enterContext(patch('socket.socket', side_effect=AssertionError('sockets forbidden')))

    def supervise(self):
        return launcher.supervise(self.layout, self.log, self.win, self.popen)

    def worker(self):
        return launcher.worker(self.layout, self.log, self.win,
            runner=self.runner, guard=self.guard, importer=self.importer)

    def events(self):
        return [call.args[0] for call in self.log.emit.call_args_list]

    def test_success_fixed_absolute_interpreter_argv_cwd_and_no_shell(self):
        self.assertEqual(self.supervise(), 0)
        args, kwargs = self.popen.call_args
        self.assertEqual(args[0], [str(self.layout.python), '-I', '-B', str(self.layout.launcher), '--worker'])
        self.assertEqual(kwargs['executable'], str(self.layout.python))
        self.assertEqual(kwargs['cwd'], str(self.layout.root))
        self.assertIs(kwargs['shell'], False)
        self.assertIs(kwargs['close_fds'], True)
        for name in ('stdin', 'stdout', 'stderr'):
            self.assertEqual(kwargs[name], launcher.subprocess.DEVNULL)
        self.assertEqual(kwargs['creationflags'], launcher.subprocess.CREATE_NO_WINDOW)
        self.assertEqual(self.events(), ['attempt', 'paths_ok', 'child_created', 'child_exit'])

    def test_missing_required_paths_never_spawn(self):
        for path in (self.layout.python, self.layout.agent, self.layout.launcher,
                     self.layout.root / '.venv/pyvenv.cfg'):
            with self.subTest(path=path.name):
                data = path.read_bytes(); path.unlink()
                self.assertEqual(self.supervise(), 10)
                path.write_bytes(data)
        self.popen.assert_not_called()

    def test_bad_working_directory_never_spawns(self):
        with patch.object(launcher.Layout, 'validate', side_effect=SecurityError('bad cwd')):
            self.assertEqual(self.supervise(), 10)
        self.popen.assert_not_called()

    def test_missing_runtime_parent_rejected_without_creating_operational_state(self):
        (self.layout.root/'.runtime').rmdir()
        self.assertEqual(self.supervise(), 10)
        self.assertFalse((self.layout.root/'.runtime').exists())
        self.popen.assert_not_called()

    def test_non_pe_interpreter_rejected(self):
        self.layout.python.write_bytes(b'not executable')
        self.assertEqual(self.supervise(), 10)
        self.popen.assert_not_called()

    def test_wrong_venv_or_elevated_environment_is_rejected(self):
        with patch.object(launcher, 'environment_valid', return_value=False):
            self.assertEqual(self.supervise(), 11)
            self.assertEqual(self.worker(), 11)
        self.popen.assert_not_called(); self.runner.assert_not_called()

    def test_creation_failure_and_exception_contents_are_not_logged(self):
        self.popen.side_effect = OSError(5, 'SYNTHETIC_SECRET_MUST_NOT_LEAK')
        self.assertEqual(self.supervise(), 12)
        self.assertNotIn('SYNTHETIC_SECRET', str(self.log.emit.call_args_list))
        self.assertIn('spawn_failed', self.events())

    def test_child_exit_logged_once_without_retry(self):
        self.popen.return_value.wait.return_value = 0xc0000005
        self.assertEqual(self.supervise(), 0xc0000005)
        self.popen.assert_called_once()
        self.log.emit.assert_any_call('child_exit', phase='supervisor', code=0xc0000005)

    def test_worker_holds_lock_during_fixed_runner_and_sets_cwd(self):
        self.runner.side_effect = lambda layout: self.assertTrue(self.win.active)
        self.assertEqual(self.worker(), 0)
        self.runner.assert_called_once_with(self.layout)
        self.chdir.assert_called_once_with(self.layout.root)
        self.assertFalse(self.win.active)
        self.assertEqual([c.args[0] for c in self.importer.call_args_list],
                         ['cryptography', 'cffi', 'pycparser'])

    def test_duplicate_does_not_import_or_run_agent(self):
        self.win.busy = True
        self.assertEqual(self.worker(), 18)
        self.guard.assert_not_called(); self.importer.assert_not_called(); self.runner.assert_not_called()
        self.assertIn('duplicate', self.events())

    def test_recovery_after_abandoned_owner(self):
        self.win.abandoned = True
        self.assertEqual(self.worker(), 0)
        self.assertIn('lock_recovered', self.events())

    def test_missing_dependency(self):
        for dependency in ('cryptography', 'cffi', 'pycparser'):
            self.importer.side_effect = lambda name: (_ for _ in ()).throw(
                ModuleNotFoundError('private detail')) if name == dependency else None
            self.assertEqual(self.worker(), 15)
            self.log.emit.assert_any_call('dependency_missing', phase='environment', dependency=dependency)
        self.runner.assert_not_called()

    def test_broken_dependency_does_not_expose_traceback(self):
        self.importer.side_effect = ImportError('SYNTHETIC_SECRET')
        self.assertEqual(self.worker(), 16)
        self.runner.assert_not_called()
        self.assertNotIn('SYNTHETIC_SECRET', str(self.log.emit.call_args_list))

    def test_legacy_process_or_listener_prevents_start(self):
        self.guard.return_value = True
        self.assertEqual(self.worker(), 13)
        self.runner.assert_not_called(); self.importer.assert_not_called()

    def test_failed_readonly_inventory_fails_closed(self):
        self.guard.side_effect = OSError('SYNTHETIC_SECRET')
        self.assertEqual(self.worker(), 14)
        self.runner.assert_not_called()

    def test_legacy_inventory_uses_only_fixed_readonly_command_and_system_executable(self):
        self.win.system_directory = Path('C:/Windows/System32')
        with patch.object(launcher, 'checked_path'), \
                patch.object(launcher.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout='free\n')) as run:
            self.assertFalse(launcher.legacy_present(self.win))
            args, kwargs = run.call_args
            self.assertEqual(Path(args[0][0]), self.win.system_directory/'WindowsPowerShell/v1.0/powershell.exe')
            self.assertIn('Get-CimInstance Win32_Process', args[0][-1])
            self.assertIn('Get-NetTCPConnection -State Listen', args[0][-1])
            self.assertNotIn('Start-Process', args[0][-1])
            self.assertIs(kwargs['shell'], False)
            self.assertEqual(kwargs['timeout'], 20)
            run.return_value.stdout = 'occupied\n'
            self.assertTrue(launcher.legacy_present(self.win))
            for result in (SimpleNamespace(returncode=1, stdout='free'),
                           SimpleNamespace(returncode=0, stdout='unexpected')):
                run.return_value = result
                with self.assertRaises(SecurityError): launcher.legacy_present(self.win)

    def test_supervisor_wait_failure_is_not_retried(self):
        self.popen.return_value.wait.side_effect = OSError(5, 'SYNTHETIC_SECRET')
        self.assertEqual(self.supervise(), 22)
        self.popen.assert_called_once()
        self.log.emit.assert_any_call('launcher_failed', phase='supervisor', code=5)

    def test_agent_import_failure_is_a_sanitized_dependency_receipt(self):
        self.runner.side_effect = ModuleNotFoundError('SYNTHETIC_SECRET')
        self.assertEqual(self.worker(), 15)
        self.log.emit.assert_any_call('dependency_missing', phase='agent', dependency='other')
        self.assertNotIn('SYNTHETIC_SECRET', str(self.log.emit.call_args_list))

    def test_unexpected_exit_releases_lock_and_next_attempt_can_succeed(self):
        self.runner.side_effect = RuntimeError('SYNTHETIC_SECRET')
        self.assertEqual(self.worker(), 17)
        self.assertFalse(self.win.active)
        self.runner.side_effect = None
        self.assertEqual(self.worker(), 0)
        self.assertNotIn('SYNTHETIC_SECRET', str(self.log.emit.call_args_list))

    def test_system_exit_text_is_never_logged(self):
        self.runner.side_effect = SystemExit('SYNTHETIC_SECRET')
        self.assertEqual(self.worker(), 1)
        self.assertNotIn('SYNTHETIC_SECRET', str(self.log.emit.call_args_list))

    def test_log_failure_never_falls_back_to_running_agent(self):
        with patch.object(launcher, 'Windows', return_value=self.win), \
                patch.object(launcher, 'StartupLog', side_effect=PermissionError('private')):
            self.assertEqual(launcher.main([]), 21)
        self.runner.assert_not_called(); self.real_popen.assert_not_called()

    def test_extra_external_arguments_are_rejected(self):
        with patch.object(launcher, 'Windows', return_value=self.win), \
                patch.object(launcher, 'StartupLog', return_value=self.log):
            for args in (['serve'], ['--worker', 'C:/evil.exe'], ['--path', 'x'], ['--worker=1']):
                self.assertEqual(launcher.main(args), 20)
        self.real_popen.assert_not_called()

    def test_mutex_identity_is_user_scoped_and_shared_across_installation_copies(self):
        other = launcher.Layout(self.layout.root / 'copy')
        self.assertEqual(self.layout.mutex_name(self.win.sid), other.mutex_name(self.win.sid))
        self.assertNotEqual(self.layout.mutex_name(self.win.sid), other.mutex_name('S-1-5-21-1002'))
        self.assertTrue(self.layout.mutex_name(self.win.sid).startswith('Global\\'))

    def test_python_environment_is_removed_case_insensitively(self):
        with patch.dict(os.environ, {'PYTHONPATH':'bad', 'PythonHome':'bad', 'KEEP':'ok'}, clear=True):
            self.assertEqual(launcher.clean_environment(), {'KEEP':'ok'})

    def test_only_numeric_error_metadata(self):
        error = OSError(5, 'SYNTHETIC_SECRET')
        self.assertEqual(error_code(error), 5)
        self.assertEqual(error_code(Exception('SYNTHETIC_SECRET')), 1)

    def test_actual_environment_validator_checks_python_prefix_and_elevation(self):
        with patch.object(launcher.sys, 'executable', str(self.layout.python)), \
                patch.object(launcher.sys, 'prefix', str(self.layout.root/'.venv')):
            self.assertTrue(ENVIRONMENT_VALID(self.layout, self.win))
            self.win.elevated = True
            self.assertFalse(ENVIRONMENT_VALID(self.layout, self.win))


class LogTests(unittest.TestCase):
    def setUp(self):
        cache = ROOT / '.cache/tests'; cache.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=cache); self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)/'logs'
        self.win = FakeWindows()
        self.log = StartupLog(self.folder, self.win, 'test-only')

    def test_schema_has_no_raw_messages_environment_or_paths(self):
        self.log.emit('spawn_failed', phase='supervisor', code=5)
        data = json.loads((self.folder/'startup.log').read_text())
        self.assertEqual(set(data), {'utc','pid','event','phase','code'})
        self.assertTrue(data['utc'].endswith('+00:00'))
        for kwargs in ({'event':'SECRET'}, {'event':'attempt','phase':'SECRET'},
                       {'event':'attempt','code':'SECRET'}, {'event':'attempt','dependency':'SECRET'},
                       {'event':'attempt','code':True}, {'event':'attempt','code':2**40}):
            with self.assertRaises(ValueError): self.log.emit(**kwargs)
        with self.assertRaises(TypeError): self.log.emit('attempt', message='SECRET')
        self.assertNotIn('SECRET', (self.folder/'startup.log').read_text())

    def test_bounded_size_and_retention(self):
        self.log.MAX_BYTES = 512
        for _ in range(80): self.log.emit('attempt', phase='supervisor')
        files = list(self.folder.iterdir())
        self.assertEqual(len(files), 4)
        self.assertTrue(all(p.stat().st_size <= 512 for p in files))
        for path in files:
            for line in path.read_text().splitlines(): json.loads(line)

    def test_permission_failure_does_not_change_existing_acl(self):
        self.win.verify_private = Mock(side_effect=PermissionError('foreign ACL'))
        with self.assertRaises(PermissionError): self.log.emit('attempt')
        self.assertEqual(list(self.folder.iterdir()), [])

    def test_log_lock_timeout_prevents_unserialized_write(self):
        self.win.busy = True
        with self.assertRaises(BusyError): self.log.emit('attempt')
        self.assertEqual(list(self.folder.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
