"""Simulated diagnostic session only: hardware/process/network access forbidden."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'tests/monitoring')]


def deny(event, args):
    if event.startswith(('socket.', 'winreg.')) or event in ('ctypes.dlopen', 'ctypes.call_function', 'subprocess.Popen', 'os.system', 'os.startfile', 'os.startfile/2'):
        raise RuntimeError('External operations forbidden in diagnostic mocks')


if __name__ == '__main__':
    sys.addaudithook(deny)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('test_adlx_instrumented_session'))
    files = ['scripts/adlx-instrumented-session.py', 'scripts/test-adlx-instrumented-isolated.py', 'tests/monitoring/test_adlx_instrumented_session.py']
    report = {'ok': result.wasSuccessful() and not result.skipped, 'tests':result.testsRun,
              'failures':len(result.failures), 'errors':len(result.errors), 'skipped':len(result.skipped),
              'realADLXLoaded':False, 'sourceHashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}}
    out = ROOT/'.cache/validation/recovery-adlx-instrumented-2026-10-25'
    out.mkdir(exist_ok=True, parents=True)
    (out/'instrumented-tests.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))
    raise SystemExit(0 if report['ok'] else 1)
