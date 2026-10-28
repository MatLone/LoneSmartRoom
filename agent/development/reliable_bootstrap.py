"""Future fixed-path logon entry, opt-in only; never registers or runs on import.

Uses the existing SID mutex, protected logs and cooperative worker. Deployment
and a real logon/stop test require separate approval. No remote management API.
"""
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'windows'))
from agent_launcher import Layout, clean_environment, environment_valid, legacy_present
from launcher_win32 import Windows, BusyError
from lifecycle_logs import LifecycleLog, error_code


def startup_command(layout):
    return subprocess.list2cmdline([str(layout.python), '-I', '-B',
        str(layout.root/'agent/development/reliable_bootstrap.py')])


def supervise(layout, windows, log, *, popen=subprocess.Popen,
              guard=legacy_present, pause=time.sleep, attempts=1):
    if type(attempts) is not int or not 1 <= attempts <= 3:
        raise ValueError('bounded_attempts_required')
    log.emit('attempt', phase='supervisor')
    layout.validate()
    if not environment_valid(layout, windows):
        log.emit('environment_invalid', phase='environment')
        return 11
    entry = layout.root/'agent/windows/graceful_launcher.py'
    # Layout validates the parent; reject a replaced candidate worker file.
    from launcher_win32 import checked_path
    if not checked_path(entry).is_file(): return 10
    try:
        # Supervisor lease is separate; worker retains the existing shared agent
        # mutex for its entire lifetime, including cooperative cleanup.
        with windows.mutex(layout.mutex_name(windows.sid)+'.supervisor'):
            for index in range(attempts):
                if guard(windows):
                    log.emit('legacy_present', phase='guard')
                    return 13
                try:
                    child = popen([str(layout.python),'-I','-B',str(entry),'_worker'],
                        executable=str(layout.python),cwd=str(layout.root),shell=False,
                        close_fds=True,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,env=clean_environment(),
                        creationflags=subprocess.CREATE_NO_WINDOW)
                except OSError as error:
                    log.emit('spawn_failed',phase='supervisor',code=error_code(error))
                    return 12
                log.emit('child_created',phase='supervisor')  # NOT proof of HTTPS.
                try: result = child.wait()
                except OSError as error:
                    log.emit('launcher_failed',phase='supervisor',code=error_code(error))
                    return 22  # Unknown live child: never respawn or signal it.
                log.emit('child_exit',phase='supervisor',code=result)
                # Normal stop, invalid environment, duplicate, legacy and security
                # codes are terminal. Only an unexpected worker failure may retry,
                # opt-in, after exit was reaped and the next guard proves free.
                if result != 17 or index+1 >= attempts: return result
                pause(5*(index+1))
    except BusyError:
        log.emit('duplicate',phase='supervisor')
        return 18


def main(arguments=None):
    if (sys.argv[1:] if arguments is None else arguments): return 20
    try:
        windows=Windows()
        if windows.elevated: return 11
        layout=Layout(Path(__file__).resolve().parents[2])
        log=LifecycleLog(layout.root/'.runtime/agent-candidate-logs',windows,
            layout.mutex_name(windows.sid)+'.candidate')
        return supervise(layout,windows,log)  # One attempt; no recovery enabled.
    except BaseException: return 21  # No raw exceptions or unprotected fallback.


if __name__=='__main__': raise SystemExit(main())
