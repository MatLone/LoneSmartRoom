"""No hardware, sockets, Registry, process creation or DLL loading in this suite."""
import ctypes
import hashlib
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tests/monitoring')]

def deny(event,args):
    if event.startswith(('socket.','winreg.')) or event in ('ctypes.dlopen','ctypes.call_function','subprocess.Popen','os.system','os.startfile','os.startfile/2','os.exec','os.posix_spawn'):
        raise RuntimeError('External operations forbidden in GPU integration mocks')

if __name__=='__main__':
    sys.addaudithook(deny)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('test_gpu_development'))
    files=['monitoring/gpu_development.py','monitoring/development_collector.py','monitoring/pipe_server.py',
           'monitoring/adlx_bridge.py','monitoring/adlx_provider.py','monitoring/contracts.py','native/adlx/bridge.cpp',
           'scripts/monitoring-pipe-server.py','scripts/monitoring-pipe-client.py','tests/monitoring/test_gpu_development.py',
           'scripts/test-gpu-development-isolated.py']
    report={'ok':r.wasSuccessful() and not r.skipped,'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),
            'skipped':len(r.skipped),'realSensors':False,'nativeProcesses':False,
            'sourceHashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}}
    out=ROOT/'.cache/validation/gpu-dashboard-integration-2026-10-26';out.mkdir(exist_ok=True,parents=True)
    (out/'gpu-python-tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='sourceHashes'}))
    raise SystemExit(0 if report['ok'] else 1)
