"""Future opt-in launcher: start/stop only. Not installed into Run or activated.

Imports and command parsing never run an agent. The active legacy launcher cannot
receive these new local events and is NOT upgraded by adding these source files.
"""
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agent_launcher import Layout, clean_environment, environment_valid, legacy_present
from launcher_win32 import Windows, BusyError, checked_path
from lifecycle_logs import LifecycleLog, error_code
from local_shutdown import LocalEvents, identity


def supervise(layout, log, windows, popen=None):
    popen = subprocess.Popen if popen is None else popen
    log.emit('attempt', phase='supervisor')
    layout.validate()
    entry = checked_path(layout.root/'agent/windows/graceful_launcher.py')
    if not entry.is_file() or not environment_valid(layout, windows):
        log.emit('environment_invalid', phase='environment')
        return 11
    try:
        child = popen([str(layout.python),'-I','-B',str(entry),'_worker'],
            executable=str(layout.python), cwd=str(layout.root), shell=False, close_fds=True,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            env=clean_environment(), creationflags=subprocess.CREATE_NO_WINDOW)
    except OSError as error:
        log.emit('spawn_failed', phase='supervisor', code=error_code(error))
        return 12
    log.emit('child_created', phase='supervisor')
    result = child.wait()
    log.emit('child_exit', phase='supervisor', code=result)
    return result


def run_agent(layout, channel, log):
    # Only a future explicitly launched worker reaches operational configuration.
    from secure_store import DPAPI
    from secure_protocol import Store, validate_lan
    from secure_tls import server_context
    from secure_startup import private_profile
    from secure_apps import AppRegistry, launch_allowed
    from graceful_runtime import serve
    state = layout.root/'.runtime/secure-agent'
    protector = DPAPI()
    config = json.loads(protector.open((state/'config.dpapi').read_bytes()))
    validate_lan(config['host'], config['network'])
    store = Store(state/'devices.db', protector)
    return serve(config, store, channel, log,
        private_guard=lambda:private_profile(config['host']),
        context_factory=lambda:server_context(state, protector),
        registry_factory=AppRegistry, executor=launch_allowed)


def worker(layout, log, windows, events, *, runner=run_agent, guard=legacy_present):
    channel = None
    try:
        layout.validate()
        if not environment_valid(layout, windows):
            log.emit('environment_invalid', phase='environment')
            return 11
        with windows.mutex(layout.mutex_name(windows.sid)):
            if guard():
                log.emit('legacy_present', phase='guard')
                return 13
            channel = events.create(identity(layout.root, windows.sid))
            log.emit('bootstrap_ready', phase='worker')
            result = runner(layout, channel, log)
        # Ack only after runtime cleanup returned AND the instance lease released.
        log.emit('mutex_released', phase='worker')
        if result in (0, None):
            channel.complete()
            return 0
        return result
    except BusyError:
        log.emit('duplicate', phase='worker')
        return 18
    except BaseException as error:
        log.emit('agent_failed', phase='worker', code=error_code(error))
        return 17
    finally:
        if channel is not None:
            channel.close()


def request_stop(layout, log, windows, events, timeout=30):
    if windows.elevated:
        return 11
    result = events.request(identity(layout.root, windows.sid), timeout)
    log.emit({'completed':'stop_completed','timed_out':'stop_timed_out',
              'not_running':'stop_not_running'}[result], phase='supervisor')
    return {'completed':0,'timed_out':24,'not_running':25}[result]


def main(arguments=None):
    arguments = sys.argv[1:] if arguments is None else arguments
    if arguments not in (['start'], ['stop'], ['_worker']):
        return 20
    try:
        windows = Windows()
        if windows.elevated:return 11
        layout = Layout(Path(__file__).resolve().parents[2])
        name = identity(layout.root, windows.sid)
        log = LifecycleLog(layout.root/'.runtime/agent-lifecycle-logs', windows, name)
        events = LocalEvents(windows)
        if arguments == ['start']:return supervise(layout, log, windows)
        if arguments == ['stop']:return request_stop(layout, log, windows, events)
        return worker(layout, log, windows, events)
    except BaseException:
        return 21  # No raw error message or unprotected fallback log.


if __name__ == '__main__':
    raise SystemExit(main())
