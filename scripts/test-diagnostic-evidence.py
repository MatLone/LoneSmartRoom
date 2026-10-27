"""Adapter and preserved Python regressions, denied external operations."""
import ctypes,ssl
import hashlib,json,sys,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT,ROOT/'tests',ROOT/'tests/monitoring'):sys.path.insert(0,str(p))


def deny(event,args):
    if event.startswith(('socket.','winreg.')) or event in ('subprocess.Popen','os.system','os.startfile','os.startfile/2','ctypes.dlopen','ctypes.call_function','os.exec','os.posix_spawn'):
        raise RuntimeError('External operations forbidden in adapter mocks')


if __name__=='__main__':
    sys.addaudithook(deny)
    names=('test_diagnostics','test_diagnostic_adapters','test_diagnostic_readers','test_diagnostic_ui_fixtures','test_evidence_adapters',
           'test_contracts','test_collector','test_ipc','test_windows_basic','test_windows_native','test_basic_session','test_baseline',
           'test_wol_backup','test_steam_launcher','test_cs2_launcher','test_pipe_transport','test_application_lifetime','test_adlx_instrumented_session')
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in names)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    files=set((ROOT/'diagnostics').glob('*.py'))|set((ROOT/'monitoring').glob('*.py'))|{Path(__file__).resolve(),ROOT/'scripts/prepare-diagnostic-adapter-fixtures.py',ROOT/'scripts/preservation_rules.py'}
    for name in names:
        direct=ROOT/'tests'/(name+'.py')
        files.add(direct if direct.is_file() else ROOT/'tests/monitoring'/(name+'.py'))
    files=sorted(files)
    report={'ok':result.wasSuccessful() and not result.skipped,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
        'externalOperationsDenied':True,'realReadersActivated':False,'physicalSessions':0,'modules':list(names),
        'sourceHashes':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    out=ROOT/'.cache/validation/diagnostic-evidence-adapters-2026-10-26';out.mkdir(parents=True,exist_ok=True)
    (out/'python-tests.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='sourceHashes'}));raise SystemExit(0 if report['ok'] else 1)
