"""Real ADLX executable cannot run from this mock suite; hardware loads denied."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
import subprocess
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tests/monitoring')]


def deny(event,args):
    if event.startswith(('socket.','winreg.')) or event in ('ctypes.dlopen','ctypes.call_function','os.system','os.startfile','os.startfile/2'):
        raise RuntimeError('External operation denied in mock bridge suite')
    if event=='subprocess.Popen':
        # Windows audits the final quoted command line, not the original argv list.
        executable=str(ROOT/'.cache/adlx-build/bridge-mock.exe')
        cases='normal unsupported cap_error read_fail load_fail init_fail invalid stale warming slow close_fail unverified --self-test'.split()
        commands={subprocess.list2cmdline([executable,case]) for case in cases}
        commands|={subprocess.list2cmdline([executable,case,'--diagnostics']) for case in cases if case!='--self-test'}
        if args[0] not in (None,executable) or args[1] not in commands:
            raise RuntimeError('Only the compiled fixture is allowed')


def main():
    sys.addaudithook(deny)
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in ('test_adlx_bridge','test_adlx_diagnostics'))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    from test_adlx_bridge import PROCESSES
    residual=[p.pid for p in PROCESSES if p.poll() is None]
    files=['native/adlx/bridge.cpp','monitoring/adlx_bridge.py','monitoring/adlx_provider.py','monitoring/adlx_diagnostics.py',
           'tests/monitoring/test_adlx_bridge.py','tests/monitoring/test_adlx_diagnostics.py','tests/monitoring/adlx_diagnostic_fakes.py','scripts/test-adlx-bridge-isolated.py']
    report={'ok':result.wasSuccessful() and not result.skipped and not residual,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'skipped':len(result.skipped),'nativeMockProcesses':len(PROCESSES),'residualMockProcesses':residual,'realADLXLoaded':False,
        'sourceHashes':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in files}}
    out=ROOT/'.cache/validation/adlx-frame-diagnostics-2026-10-25';out.mkdir(parents=True,exist_ok=True)
    (out/'bridge-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));return 0 if report['ok'] else 1


if __name__=='__main__':raise SystemExit(main())
