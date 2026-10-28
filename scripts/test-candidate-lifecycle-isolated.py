"""Real redirected pythonw with MOCK events; no real agent or port 8776."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
import uuid
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests')]
import test_reliable_bootstrap as tests
m=tests.m

def main():
    original=subprocess.Popen
    results=[]
    for recovery in (False,True):
        clock=tests.Clock()
        # Real processes; mock OS inventory/events so NO production names touched.
        stop=threading.Event()
        class Control:
            def create(self,name):return self
            def wait_stop(self,n):return stop.wait(min(n,.01) if n>1 else n)
            def complete(self):self.completed=True
            def close(self):pass
            completed=False
        control=Control();owned=[]
        def launch(args,**kw):
            expected=[str(m.Layout(ROOT).python),'-I','-B',str(ROOT/'agent/development/reliable_bootstrap.py'),'_worker']
            assert args==expected and kw['shell'] is False
            mode='clean-exit' if recovery and not owned else 'cooperate'
            child=original([args[0],'-I','-B',str(ROOT/'tests/candidate_lifecycle_substitute.py'),mode],**kw)
            owned.append(child);return child
        timer=threading.Timer(.8,stop.set);timer.start();start=time.monotonic()
        try:
            with patch.object(m.Layout,'validate'),patch.object(m,'environment_valid',return_value=True),patch('socket.socket',side_effect=AssertionError('no network')):
                code=m.supervise(m.Layout(ROOT),tests.FakeWindows(),Mock(),popen=launch,guard=lambda _:False,
                    events=control,attempts=2 if recovery else 1)
            assert code==0 and control.completed
            assert len(owned)==(2 if recovery else 1) and all(c.poll() is not None for c in owned)
            results.append(dict(recovery=recovery,children=len(owned),normal_exit=True,duration_seconds=round(time.monotonic()-start,3)))
        finally:
            timer.cancel()
            for child in owned:
                if not child.stdin.closed:child.stdin.close()
                child.wait(timeout=6)
    child=original([str(m.Layout(ROOT).python),'-I','-B',str(ROOT/'tests/candidate_lifecycle_substitute.py'),'local-stop'],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=ROOT,shell=False,creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        code=child.wait(timeout=6)
        assert code==0 and child.stdout.read(129)==b'{"v":1,"event":"listener_bound"}\n'
        assert child.stderr.read(1024)==b''
        results.append(dict(local_stop_with_stdin_open=True,normal_exit=True,buffered_stdin_shutdown_error=False))
    finally:
        child.stdin.close();child.stdout.close();child.stderr.close()
    output=ROOT/'.cache/validation/agent-consolidation';output.mkdir(parents=True,exist_ok=True)
    receipt=dict(ok=True,tests=3,actual_redirected_pythonw=True,production_agent_allowed=False,hardware_collection=False,os_events_mocked=True,results=results)
    (output/'subprocess-tests.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))
if __name__=='__main__':main()
