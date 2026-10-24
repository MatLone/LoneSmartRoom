"""Test-only mutex holder, NEVER imports/runs the operational agent or sockets."""
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'agent/windows'))
from launcher_win32 import BusyError, Windows

if __name__ == '__main__':
    # A production mutex cannot be used by this helper.
    name = sys.argv[1]
    if not name.startswith('Global\\LoneSmartRoom.LauncherTests.'):
        raise SystemExit(90)
    windows = Windows()
    try:
        with windows.mutex(name):
            print('held', flush=True)
            if sys.stdin.readline().strip() == 'crash':
                os._exit(7)  # Only this disposable substitute exits abnormally.
    except BusyError:
        print('busy', flush=True)
        raise SystemExit(18)
