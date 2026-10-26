"""Diagnostic fixtures only. Denies network, native DLLs, process launch and Registry."""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]


def deny(event,args):
    if event.startswith(('socket.','winreg.')) or event in (
        'subprocess.Popen','os.system','os.startfile','os.startfile/2',
        'ctypes.dlopen','ctypes.call_function','os.exec','os.posix_spawn'):
        raise RuntimeError('External operations forbidden in diagnostic fixtures')


def main():
    sys.addaudithook(deny)
    suite=unittest.defaultTestLoader.loadTestsFromName('test_diagnostics')
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'ok':result.wasSuccessful() and not result.skipped,'tests':result.testsRun,
            'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
            'onlySimulatedProviders':True,'realProbes':False,'repairsImplemented':False,
            'externalOperationsDenied':True,'productionIntegration':False}
    out=ROOT/'.cache/validation/diagnostics-foundation-2026-10-26';out.mkdir(parents=True,exist_ok=True)
    (out/'tests-summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report));return 0 if report['ok'] else 1


if __name__=='__main__':raise SystemExit(main())
