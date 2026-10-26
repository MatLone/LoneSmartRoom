"""Mock-only Python regression gate for diagnostic center fixtures and contracts."""
import ctypes,ssl
import hashlib,json
from pathlib import Path
import sys,unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]


def deny(event,args):
    if event.startswith(('socket.','winreg.')) or event in ('subprocess.Popen','os.system','os.startfile','os.startfile/2','ctypes.dlopen','ctypes.call_function','os.exec','os.posix_spawn'):
        raise RuntimeError('External operations forbidden in diagnostic UI mocks')


if __name__=='__main__':
    sys.addaudithook(deny)
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in (
        'test_diagnostics','test_diagnostic_adapters','test_diagnostic_readers','test_diagnostic_ui_fixtures'))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    files=sorted((ROOT/'diagnostics').glob('*.py'))+[ROOT/'scripts/prepare-diagnostic-fixtures.py',Path(__file__).resolve()]+[
        ROOT/'tests'/n for n in ('test_diagnostics.py','test_diagnostic_adapters.py','test_diagnostic_readers.py','test_diagnostic_ui_fixtures.py')]
    report={'ok':result.wasSuccessful() and not result.skipped,'tests':result.testsRun,
        'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
        'operationalReaders':False,'externalOperationsDenied':True,
        'sourceHashes':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    out=ROOT/'.cache/validation/diagnostic-center-2026-10-26';out.mkdir(parents=True,exist_ok=True)
    (out/'python-tests.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='sourceHashes'}));raise SystemExit(0 if report['ok'] else 1)
