"""All monitoring tests and preserved mock-only regressions, with external I/O denied."""
import ctypes  # Standard Python bootstrap only, before denying new libraries.
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / 'tests', ROOT / 'tests/monitoring'):
    sys.path.insert(0, str(path))


def deny_external(event, _args):
    if event.startswith(('socket.', 'winreg.')) or event in (
            'subprocess.Popen', 'os.system', 'os.startfile', 'os.startfile/2',
            'ctypes.dlopen', 'ctypes.call_function', 'os.posix_spawn', 'os.exec'):
        raise RuntimeError('Native collection and external operations forbidden in simulated tests')


def main():
    sys.addaudithook(deny_external)
    modules = ('test_contracts', 'test_collector', 'test_ipc', 'test_windows_basic',
               'test_windows_native', 'test_basic_session', 'test_baseline',
               'test_wol_backup', 'test_steam_launcher', 'test_cs2_launcher')
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in modules)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    from monitoring.basic_validation import source_hashes
    receipt = {'ok': result.wasSuccessful() and not result.skipped, 'tests': result.testsRun,
               'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped),
               'real_collection': False, 'real_dlls_allowed': False, 'network_allowed': False,
               'external_processes_allowed': False, 'modules': list(modules), 'source_hashes': source_hashes(ROOT)}
    directory = ROOT / '.cache/validation/monitoring-basic-2026-10-25'
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'simulated-tests.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in receipt.items() if k != 'source_hashes'}))
    return 0 if receipt['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
