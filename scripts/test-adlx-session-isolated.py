"""No native loads, subprocesses, sockets or Registry in session fixtures."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tests/monitoring')]


def deny(event,args):
    if event.startswith(('socket.','winreg.')) or event in ('ctypes.dlopen','ctypes.call_function','subprocess.Popen','os.system','os.startfile','os.startfile/2'):
        raise RuntimeError('Real operations forbidden in session mocks')


def main():
    sys.addaudithook(deny);result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('test_adlx_session'))
    report={'ok':result.wasSuccessful() and not result.skipped,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
        'sourceSha256':hashlib.sha256((ROOT/'monitoring/adlx_session.py').read_bytes()).hexdigest(),'realADLXLoaded':False}
    out=ROOT/'.cache/validation/adlx-native-2026-10-25';out.mkdir(parents=True,exist_ok=True);(out/'session-tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report));return 0 if report['ok'] else 1


if __name__=='__main__':raise SystemExit(main())
