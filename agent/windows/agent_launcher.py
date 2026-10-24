"""Opt-in startup supervisor. Not registered or activated by installing this file.

Only the fixed internal --worker mode is accepted. No network or management API.
The worker owns the kernel mutex for the entire in-process agent lifetime.
"""
from dataclasses import dataclass
import hashlib
import importlib
import os
from pathlib import Path
import runpy
import subprocess
import sys

# -I removes the script directory as well as untrusted CWD/PYTHONPATH entries.
# Reintroduce only this fixed sibling directory, never a caller-supplied path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from launcher_logs import StartupLog, error_code
from launcher_win32 import BusyError, SecurityError, Windows, checked_path


@dataclass(frozen=True)
class Layout:
    root: Path

    @property
    def python(self):
        return self.root / '.venv/Scripts/pythonw.exe'

    @property
    def launcher(self):
        return self.root / 'agent/windows/agent_launcher.py'

    @property
    def agent(self):
        return self.root / 'agent/windows/secure_agent.py'

    @property
    def logs(self):
        return self.root / '.runtime/agent-startup-logs'

    def validate(self):
        root = checked_path(self.root)
        if not root.is_dir() or not (root / '.runtime').is_dir():
            raise SecurityError('working_directory_missing')
        for file in (self.python, self.launcher, self.agent,
                     root / '.venv/pyvenv.cfg', root / 'agent/windows/launcher_logs.py',
                     root / 'agent/windows/launcher_win32.py'):
            if not checked_path(file).is_file():
                raise SecurityError('required_file_missing')
        with self.python.open('rb') as file:
            if file.read(2) != b'MZ':
                raise SecurityError('interpreter_invalid')

    def mutex_name(self, sid):
        # One identity per user across sessions AND copies of this installation.
        digest = hashlib.sha256(sid.encode('ascii')).hexdigest()
        return 'Global\\LoneSmartRoom.SecureAgent.' + digest


def clean_environment():
    environment = dict(os.environ)
    for name in tuple(environment):
        if name.upper().startswith('PYTHON'):
            environment.pop(name)
    return environment


def environment_valid(layout, windows):
    return (not windows.elevated and Path(sys.executable).resolve() == layout.python.resolve()
            and Path(sys.prefix).resolve() == (layout.root / '.venv').resolve())


def supervise(layout, log, windows, popen=None):
    popen = subprocess.Popen if popen is None else popen
    log.emit('attempt', phase='supervisor')
    try:
        layout.validate()
    except OSError as error:
        log.emit('paths_invalid', phase='paths', code=error_code(error))
        return 10
    log.emit('paths_ok', phase='paths')
    if not environment_valid(layout, windows):
        log.emit('environment_invalid', phase='environment')
        return 11
    try:
        process = popen([str(layout.python), '-I', '-B', str(layout.launcher), '--worker'],
            executable=str(layout.python), cwd=str(layout.root), shell=False, close_fds=True,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            env=clean_environment(), creationflags=subprocess.CREATE_NO_WINDOW)
    except OSError as error:
        log.emit('spawn_failed', phase='supervisor', code=error_code(error))
        return 12
    log.emit('child_created', phase='supervisor')  # Not proof of HTTPS availability.
    try:
        result = process.wait()  # No retries; never kill a child or another process.
    except OSError as error:
        log.emit('launcher_failed', phase='supervisor', code=error_code(error))
        return 22
    log.emit('child_exit', phase='supervisor', code=result)
    return result


def legacy_present(windows=None):
    """Read-only compatibility guard for the old direct entry; no sockets opened.

    A legacy launcher bypassing our mutex can still race this snapshot. Windows'
    exclusive bind remains the final backstop; migrate only with agent stopped.
    """
    windows = Windows() if windows is None else windows
    system = windows.system_directory / 'WindowsPowerShell/v1.0/powershell.exe'
    checked_path(system)
    command = ("$ErrorActionPreference='Stop'; "
        "$p=@(Get-CimInstance Win32_Process | Where-Object { "
        "$_.Name -in @('python.exe','pythonw.exe') -and "
        "$_.CommandLine -match 'secure_agent\\.py' }); "
        "$t=@(Get-NetTCPConnection -State Listen | Where-Object LocalPort -eq 8776); "
        "if($p.Count -or $t.Count){'occupied'}else{'free'}")
    result = subprocess.run([str(system), '-NoProfile', '-NonInteractive', '-Command', command],
        cwd=str(system.parent), shell=False, close_fds=True, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=20,
        creationflags=subprocess.CREATE_NO_WINDOW, text=True)
    if result.returncode != 0 or result.stdout.strip() not in ('free', 'occupied'):
        raise SecurityError('legacy_inventory_failed')
    return result.stdout.strip() == 'occupied'


def run_agent(layout):
    # Fixed path + fixed verb. No runpy use occurs in tests; runner is substituted.
    sys.argv = [str(layout.agent), 'serve']
    # -I omits script directory: add only the validated fixed project directory.
    sys.path.insert(0, str(layout.agent.parent))
    runpy.run_path(str(layout.agent), run_name='__main__')


def worker(layout, log, windows, *, runner=run_agent, guard=legacy_present,
           importer=importlib.import_module):
    log.emit('worker_attempt', phase='worker')
    try:
        layout.validate()
        if not environment_valid(layout, windows):
            log.emit('environment_invalid', phase='environment')
            return 11
        # The same thread owns this mutex until the actual agent returns/exits.
        with windows.mutex(layout.mutex_name(windows.sid)) as recovered:
            if recovered:
                log.emit('lock_recovered', phase='worker')
            try:
                if guard():
                    log.emit('legacy_present', phase='guard')
                    return 13
            except Exception as error:
                log.emit('guard_failed', phase='guard', code=error_code(error))
                return 14
            for dependency in ('cryptography', 'cffi', 'pycparser'):
                try:
                    importer(dependency)
                except ModuleNotFoundError:
                    log.emit('dependency_missing', phase='environment', dependency=dependency)
                    return 15
                except Exception as error:
                    log.emit('dependency_failed', phase='environment', dependency=dependency,
                             code=error_code(error))
                    return 16
            os.chdir(layout.root)
            log.emit('bootstrap_ready', phase='worker')  # Still not a connected status.
            try:
                runner(layout)
            except ModuleNotFoundError:
                log.emit('dependency_missing', phase='agent', dependency='other')
                return 15
            except SystemExit as error:
                code = error.code if type(error.code) is int and -2**31 <= error.code < 2**32 else 1
                log.emit('agent_returned' if code == 0 else 'agent_failed', phase='agent', code=code)
                return code
            except BaseException as error:
                log.emit('agent_failed', phase='agent', code=error_code(error))
                return 17
            log.emit('agent_returned', phase='agent', code=0)
            return 0
    except BusyError:
        log.emit('duplicate', phase='worker')
        return 18
    except OSError as error:
        log.emit('launcher_failed', phase='worker', code=error_code(error))
        return 19


def main(arguments=None):
    arguments = sys.argv[1:] if arguments is None else arguments
    try:
        layout = Layout(Path(__file__).resolve().parents[2])
        windows = Windows()
        # Never change token privileges or request elevation.
        if windows.elevated:
            return 11
        log = StartupLog(layout.logs, windows, layout.mutex_name(windows.sid))
        if arguments not in ([], ['--worker']):
            log.emit('invalid_arguments', phase='supervisor')
            return 20
        return worker(layout, log, windows) if arguments else supervise(layout, log, windows)
    except BaseException:
        # ACL/log initialization failure: fail closed, no raw stderr/alternate log.
        return 21


if __name__ == '__main__':
    raise SystemExit(main())
