"""C1 regressions with operational I/O denied, independent of the C0 cache."""
import ctypes
import ssl
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests'), str(ROOT / 'tests/monitoring')]


def deny(event, _args):
    if event.startswith(('socket.', 'winreg.')) or event in (
        'subprocess.Popen', 'os.system', 'os.startfile', 'os.startfile/2',
        'ctypes.dlopen', 'ctypes.call_function', 'os.exec', 'os.posix_spawn',
    ):
        raise RuntimeError('Operational I/O forbidden in C1 offline tests')


if __name__ == '__main__':
    sys.addaudithook(deny)
    modules = (
        'test_preload_review', 'test_baseline', 'test_wol_backup', 'test_steam_launcher', 'test_cs2_launcher',
        'test_contracts', 'test_collector', 'test_ipc', 'test_windows_basic', 'test_windows_native',
        'test_basic_session', 'test_pipe_transport', 'test_application_lifetime', 'test_adlx_provider',
        'test_gpu_development', 'test_diagnostics', 'test_diagnostic_adapters', 'test_diagnostic_readers',
        'test_diagnostic_ui_fixtures',
    )
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in modules)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = dict(ok=result.wasSuccessful() and not result.skipped, tests=result.testsRun,
                  failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped),
                  modules=modules, externalOperationsDenied=True, realSensors=False,
                  productionAgentAccess=False)
    out = ROOT / '.cache/hardware-readonly-c1'
    out.mkdir(exist_ok=True, parents=True)
    (out / 'python-tests.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))
    raise SystemExit(0 if report['ok'] else 1)
