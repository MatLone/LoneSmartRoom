"""Diagnostic fixtures only. Denies network, native DLLs, process launch and Registry."""
import json
import hashlib
from pathlib import Path
import sys
import unittest
# Bootstrap the standard-library runtime before denying subsequent native calls.
# No reader instance, operational process, ADLX DLL or Windows query is created.
import ctypes
import ssl

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]


def deny(event,args):
    if event.startswith(('socket.','winreg.')) or event in (
        'subprocess.Popen','os.system','os.startfile','os.startfile/2',
        'ctypes.dlopen','ctypes.call_function','os.exec','os.posix_spawn'):
        raise RuntimeError('External operations forbidden in diagnostic fixtures')


def main():
    sys.addaudithook(deny)
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in ('test_diagnostics','test_diagnostic_adapters','test_diagnostic_readers'))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'ok':result.wasSuccessful() and not result.skipped,'tests':result.testsRun,
            'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
            'onlySimulatedProviders':True,'realProbes':False,'repairsImplemented':False,
            'externalOperationsDenied':True,'productionIntegration':False}
    files=sorted((ROOT/'diagnostics').glob('*.py'))+[ROOT/'diagnostics/windows-census.ps1',ROOT/'scripts/run-diagnostics-passive.py',ROOT/'tests/test_diagnostics.py',ROOT/'tests/test_diagnostic_adapters.py',ROOT/'tests/test_diagnostic_readers.py',Path(__file__).resolve()]
    report['sourceHashes']={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    out=ROOT/'.cache/validation/diagnostics-passive-2026-10-26';out.mkdir(parents=True,exist_ok=True)
    (out/'tests-summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='sourceHashes'}));return 0 if report['ok'] else 1


if __name__=='__main__':raise SystemExit(main())
