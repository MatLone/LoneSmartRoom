"""Disposable event/lease supervisor+worker. No operational configuration or agent."""
from pathlib import Path
import os
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'agent/windows'))
from launcher_win32 import Windows
from local_shutdown import LocalEvents

def main():
    mode,name=sys.argv[1:]
    if not name.startswith('Global\\LoneSmartRoom.GracefulTests.'):
        return 90
    LocalEvents.validate(name)
    if mode in ('supervisor','supervisor-crash'):
        childmode='worker' if mode=='supervisor' else 'crash'
        child=subprocess.Popen([sys.executable,'-I','-B',str(Path(__file__).resolve()),childmode,name],
            shell=False,close_fds=True,stdin=subprocess.DEVNULL,stdout=sys.stdout,stderr=sys.stderr)
        code=child.wait()
        print('supervisor_exited',flush=True)
        return code
    win=Windows();events=LocalEvents(win);channel=None
    try:
        with win.mutex(name+'.lease'):
            channel=events.create(name)
            print('ready:'+str(os.getpid()),flush=True)
            if not channel.wait_stop(5):return 28  # Bounded toy lifetime, never force kill.
            if mode=='crash':os._exit(7)  # This disposable test process only.
            if mode=='slow':time.sleep(.25)
        channel.complete()  # Lease release precedes acknowledgement.
        print('worker_exited',flush=True)
        return 0
    finally:
        if channel is not None:channel.close()

if __name__=='__main__':raise SystemExit(main())
