"""Toy child only: no imports from agent, network, credentials or hardware."""
import sys
import threading
import time
from pathlib import Path
if sys.argv[1:] not in (['cooperate'], ['clean-exit'], ['local-stop']): raise SystemExit(20)
# pythonw redirected handles must be valid just as in the future candidate.
if sys.stdin is None or sys.stdout is None: raise SystemExit(73)
sys.stdout.buffer.write(b'{"v":1,"event":"listener_bound"}\n');sys.stdout.buffer.flush()
if sys.argv[1:] == ['clean-exit']: raise SystemExit(71)
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'agent/development'))
from reliable_bootstrap import ParentEvents
started=time.monotonic()
class Local:
    def create(self,name):return self
    def wait_stop(self,n):return sys.argv[1:]==['local-stop'] and time.monotonic()-started>=.2
    def close(self):pass
    def complete(self):pass
channel=ParentEvents(Local(),sys.stdin.buffer).create('mock-only')
# Independent toy lifetime; never leaves a blocked fixture indefinitely.
raise SystemExit(0 if channel.wait_stop(5) else 72)
