"""Windows monitoring substitute regressions with external operations denied."""
import ctypes, json, sys, unittest, time, subprocess, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tests'),str(ROOT/'tests/monitoring')]
def deny(event,args):
    if event=='subprocess.Popen':
        exe=str(ROOT/'.cache/adlx-build/bridge-mock.exe')
        cases='normal unsupported cap_error read_fail load_fail init_fail invalid stale warming slow close_fail unverified --self-test'.split()
        commands={subprocess.list2cmdline([exe,case]) for case in cases}|{subprocess.list2cmdline([exe,case,'--diagnostics']) for case in cases if case!='--self-test'}
        receipt=json.loads((ROOT/'.cache/adlx-build/bridge-mock-build.json').read_text())
        if args[0] not in (None,exe) or args[1] not in commands or not receipt['mock'] or hashlib.sha256(Path(exe).read_bytes()).hexdigest()!=receipt['exeSha256']:
            raise RuntimeError('Only the verified compiled fixture may run')
        return
    if event.startswith(('socket.','winreg.')) or event in ('os.system','os.startfile','os.startfile/2','ctypes.dlopen','ctypes.call_function','os.posix_spawn','os.exec'):
        raise RuntimeError('Operational access denied in isolated regression suite')
sys.addaudithook(deny)
start=time.perf_counter();cpu=time.process_time()
suite=unittest.defaultTestLoader.discover(str(ROOT/'tests/monitoring'),pattern='test_*.py')
result=unittest.TextTestRunner(verbosity=1).run(suite)
from test_adlx_bridge import PROCESSES
residual=[p.pid for p in PROCESSES if p.poll() is None]
report={'ok':result.wasSuccessful() and not result.skipped and not residual,'native_mock_processes':len(PROCESSES),'residual_mock_processes':residual,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'wall_seconds':time.perf_counter()-start,'process_cpu_seconds':time.process_time()-cpu,'hardware_sessions':0,'native_calls':False}
out=ROOT/'.cache/validation/windows-dev8/regressions';out.mkdir(parents=True,exist_ok=True);(out/'python-tests.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report));raise SystemExit(0 if report['ok'] else 1)
