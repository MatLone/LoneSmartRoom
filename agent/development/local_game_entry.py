"""Local Electron entry; reuse the existing allowlisted Steam/CS2 executors."""
import ctypes
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
MODULES = HERE if (HERE/'steam_launcher.py').is_file() else HERE.parent/'windows'
sys.path.insert(0, str(MODULES))

def run(app, inspect=False):
    if app not in ('steam', 'cs2'):
        raise ValueError('local_app')
    import steam_launcher as steam
    import cs2_launcher as cs2
    if os.name != 'nt' or ctypes.windll.shell32.IsUserAnAdmin():
        raise PermissionError('non_elevated_windows_required')
    session = ctypes.c_uint()
    if not ctypes.windll.kernel32.ProcessIdToSessionId(os.getpid(), ctypes.byref(session)) or session.value == 0:
        raise PermissionError('interactive_session_required')
    if inspect:
        executable = steam.validated_steam_executable()
        if app == 'cs2':
            cs2.validated_cs2_installation(executable)
        return dict(v=1, app=app, state='ready', executed=False,
                    signed_publisher_verified=True)
    (steam.launch_steam if app == 'steam' else cs2.launch_cs2)()
    return dict(v=1, app=app, state='dispatched', executed=True,
                process_running_verified=False)

def main(args):
    if len(args) not in (1,2) or args[0] not in ('steam','cs2') or len(args)==2 and args[1]!='--inspect':
        return 2
    try:
        result=run(args[0], len(args)==2)
    except Exception:
        result=dict(v=1,app=args[0],state='unavailable',executed=False,error='local_launch_validation_failed')
    print(json.dumps(result,separators=(',',':')))
    return 0 if result['state']!='unavailable' else 2
if __name__=='__main__':
    raise SystemExit(main(sys.argv[1:]))
