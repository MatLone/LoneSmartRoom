"""Opt-in fixed logon candidate; no Registry writes or activation on import.

Reuses worker mutex, protected events/logs and draining runtime. Stdin EOF is
cooperation, never termination. The supervisor stop channel survives backoff.
"""
from pathlib import Path
import io
import os
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT/'agent/windows'), str(Path(__file__).parent)]
from agent_launcher import Layout, clean_environment, environment_valid, legacy_present
from launcher_win32 import Windows, BusyError, checked_path
from lifecycle_logs import LifecycleLog, error_code
from local_shutdown import LocalEvents, identity

RECOVERABLE_EXIT = 71
POLL = .1
STARTUP_SECONDS = 30
STOP_SECONDS = 30


def startup_command(layout):
    return subprocess.list2cmdline([str(layout.python), '-I', '-B',
        str(layout.root/'agent/development/reliable_bootstrap.py')])


def supervisor_identity(layout, windows):
    return identity(layout.root/'agent/development/supervisor', windows.sid)


def validate_candidate(layout):
    layout.validate()
    for name in ('agent/development/reliable_bootstrap.py',
                 'agent/development/candidate_runtime.py',
                 'agent/windows/graceful_launcher.py',
                 'agent/windows/graceful_runtime.py',
                 'agent/windows/telemetry_runtime.py',
                 'agent/windows/development_telemetry_http.py',
                 'agent/windows/local_shutdown.py', 'telemetry/relay.py'):
        if not checked_path(layout.root/name).is_file():
            raise FileNotFoundError('candidate_component_missing')


class Readiness:
    """One fixed bounded receipt, never paths or free-form exceptions."""
    def __init__(self, stream):
        self.ready, self.invalid = threading.Event(), threading.Event()
        def read():
            try:
                line = stream.readline(129)
                if line != b'{"v":1,"event":"listener_bound"}\n':
                    self.invalid.set()
                else:
                    self.ready.set()
            except (OSError, ValueError, AttributeError):
                self.invalid.set()
        self.thread = threading.Thread(target=read, name='lsr-readiness', daemon=True)
        self.thread.start()
    def state(self):
        return 'invalid' if self.invalid.is_set() else 'bound' if self.ready.is_set() else 'waiting'
    def close(self): self.thread.join(timeout=1)


def supervise(layout, windows, log, *, popen=subprocess.Popen,
              guard=legacy_present, events=None, attempts=1,
              readiness=Readiness, clock=time.monotonic, pause=time.sleep):
    if type(attempts) is not int or not 1 <= attempts <= 3:
        raise ValueError('bounded_attempts_required')
    log.emit('attempt', phase='supervisor')
    try:
        validate_candidate(layout)
    except OSError as error:
        log.emit('paths_invalid',phase='paths',code=error_code(error))
        return 10
    log.emit('paths_ok',phase='paths')
    if not environment_valid(layout, windows):
        log.emit('environment_invalid', phase='environment')
        return 11
    entry = checked_path(layout.root/'agent/development/reliable_bootstrap.py')
    if not entry.is_file(): return 10
    events = LocalEvents(windows) if events is None else events
    channel, result, complete = None, 21, False
    try:
        with windows.mutex(layout.mutex_name(windows.sid)+'.supervisor'):
            channel = events.create(supervisor_identity(layout, windows))
            for index in range(attempts):
                if channel.wait_stop(0):
                    result, complete = 0, True
                    break
                if guard(windows):
                    log.emit('legacy_present', phase='guard')
                    return 13
                if channel.wait_stop(0):
                    result, complete = 0, True
                    break
                try:
                    child = popen([str(layout.python),'-I','-B',str(entry),'_worker'],
                        executable=str(layout.python),cwd=str(layout.root),shell=False,
                        close_fds=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL,env=clean_environment(),
                        creationflags=subprocess.CREATE_NO_WINDOW)
                except OSError as error:
                    log.emit('spawn_failed',phase='supervisor',code=error_code(error))
                    return 12
                log.emit('child_created',phase='supervisor')
                receipt, reaped = None, False
                started, stopping, timed_out, stop_at = clock(), False, False, None
                bound_logged = False
                startup_timeout = False
                try:
                    receipt = readiness(child.stdout)
                    while child.poll() is None:
                        now = clock()
                        state = receipt.state()
                        if state == 'bound' and not bound_logged:
                            log.emit('bootstrap_ready',phase='agent')
                            bound_logged = True
                        if stopping:
                            pause(POLL)  # Manual-reset stop stays signaled; avoid busy polling.
                            stop = True
                        else:
                            stop = channel.wait_stop(POLL)
                        if not stopping and (stop or state == 'invalid' or
                                state != 'bound' and now-started >= STARTUP_SECONDS):
                            stopping, stop_at = True, now
                            # EOF, including parent death, requests local drain.
                            child.stdin.close()
                            if not stop:
                                result = 27
                                startup_timeout = state == 'waiting'
                                log.emit('launcher_failed',phase='supervisor',code=27)
                        if stopping and not timed_out and now-stop_at >= STOP_SECONDS:
                            timed_out = True
                            log.emit('stop_timed_out',phase='supervisor')
                            # Hold the lease while child lives; never orphan,
                            # force, respawn or acknowledge incomplete cleanup.
                    code = child.wait()
                    reaped = True
                    log.emit('child_exit',phase='supervisor',code=code)
                except BaseException as error:
                    # An observation/logging failure is NOT permission to leave
                    # an owned live worker behind or attempt another launch.
                    try: child.stdin.close()
                    except OSError: pass
                    try: log.emit('launcher_failed',phase='supervisor',code=error_code(error))
                    except Exception: pass
                    while not reaped:
                        try:
                            code = child.wait()  # Cooperative EOF, no force/deadline fiction.
                            reaped = True
                        except OSError:
                            pause(1)  # Unknown child state: retain supervisor lease.
                    result, stopping = 22, True
                finally:
                    if reaped:
                        child.stdin.close()
                        if receipt is not None: receipt.close()
                        child.stdout.close()
                if guard(windows): return 13
                with windows.mutex(layout.mutex_name(windows.sid)):
                    pass  # Prove agent lease is free after reaping the child.
                if stopping:
                    result = 24 if timed_out else result if result in (22,27) else code
                    complete = result == 0
                    # Delayed private network at login: bounded fresh attempt,
                    # but only after EOF drain, observed exit, free listener and
                    # released lease. Malformed readiness/security errors never retry.
                    if not (startup_timeout and code == 0 and not timed_out and index+1 < attempts):
                        break
                else:
                    result = code
                    if code != RECOVERABLE_EXIT or index+1 >= attempts:
                        complete = code == 0
                        break
                if channel.wait_stop(5*(index+1)):
                    result, complete = 0, True
                    break
        if complete: channel.complete()  # Both leases released before ack.
        return result
    except BusyError:
        log.emit('duplicate',phase='supervisor')
        return 18
    finally:
        if channel is not None: channel.close()


class ParentEvents:
    """Existing local events plus EOF from the one owning supervisor."""
    def __init__(self, events, stream):
        self.events, self.stream = events, stream
    def create(self, name):
        local = self.events.create(name)
        stopped = threading.Event()
        def lifetime():
            try:
                try: fd = self.stream.fileno()
                except (AttributeError, io.UnsupportedOperation):
                    self.stream.read(1)  # In-memory test streams only.
                else:
                    os.read(fd,1)  # No buffered-stdin lock at interpreter shutdown.
            except OSError: pass
            finally: stopped.set()
        threading.Thread(target=lifetime, name='lsr-parent-lifetime', daemon=True).start()
        class Combined:
            def wait_stop(self, seconds=0):
                end = time.monotonic()+seconds
                while True:
                    if stopped.is_set() or local.wait_stop(0): return True
                    remaining = end-time.monotonic()
                    if remaining <= 0: return False
                    stopped.wait(min(.05,remaining))
            def complete(self): local.complete()
            def close(self): local.close()
        return Combined()


def main(arguments=None):
    arguments = sys.argv[1:] if arguments is None else arguments
    if arguments not in ([], ['stop'], ['_worker']): return 20
    try:
        windows = Windows()
        if windows.elevated: return 11
        layout = Layout(ROOT)
        log = LifecycleLog(layout.root/'.runtime/agent-candidate-logs',windows,
            layout.mutex_name(windows.sid)+'.candidate')
        events = LocalEvents(windows)
        if arguments == ['stop']:
            result = events.request(supervisor_identity(layout,windows),STOP_SECONDS)
            log.emit({'completed':'stop_completed','timed_out':'stop_timed_out',
                'not_running':'stop_not_running'}[result],phase='supervisor')
            return {'completed':0,'timed_out':24,'not_running':25}[result]
        if arguments == ['_worker']:
            validate_candidate(layout)
            from graceful_launcher import worker
            from candidate_runtime import run_candidate
            emitted = False
            def bound():
                nonlocal emitted
                if not emitted:
                    sys.stdout.buffer.write(b'{"v":1,"event":"listener_bound"}\n')
                    sys.stdout.buffer.flush()
                    emitted = True
            return worker(layout,log,windows,ParentEvents(events,sys.stdin.buffer),
                runner=lambda l,c,g:run_candidate(l,c,g,bound=bound))
        return supervise(layout,windows,log,events=events,attempts=3)
    except BaseException: return 21  # No raw error or unprotected fallback log.


if __name__ == '__main__': raise SystemExit(main())
