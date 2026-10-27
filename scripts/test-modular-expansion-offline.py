"""Recheck existing integration contracts without operational readers or processes.

Reports go to this plan's own cache directory, preserving historical receipts.
"""
import ctypes  # Bootstrap stdlib helpers before the audit guard; no sensors.
import ssl
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests'), str(ROOT / 'tests/monitoring')]


def deny_external(event, _args):
    if event.startswith(('socket.', 'winreg.')) or event in (
        'subprocess.Popen', 'os.system', 'os.startfile', 'os.startfile/2',
        'ctypes.dlopen', 'ctypes.call_function', 'os.exec', 'os.posix_spawn',
    ):
        raise RuntimeError('Operational I/O forbidden in modular expansion offline gate')


def main():
    sys.addaudithook(deny_external)
    modules = (
        'test_baseline', 'test_wol_backup', 'test_steam_launcher', 'test_cs2_launcher',
        'test_contracts', 'test_collector', 'test_ipc', 'test_windows_basic',
        'test_windows_native', 'test_basic_session', 'test_pipe_transport',
        'test_application_lifetime', 'test_adlx_provider', 'test_gpu_development',
        'test_diagnostics', 'test_diagnostic_adapters', 'test_diagnostic_readers',
        'test_diagnostic_ui_fixtures',
    )
    suite = unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromName(name) for name in modules
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        'ok': result.wasSuccessful() and not result.skipped,
        'tests': result.testsRun, 'failures': len(result.failures),
        'errors': len(result.errors), 'skipped': len(result.skipped),
        'modules': list(modules), 'externalOperationsDenied': True,
        'operationalAgentAccess': False, 'realSensors': False,
        'productionIntegrationAdded': False,
    }
    checkpoint = json.loads((ROOT / '.cache/modular-expansion-2026-10-26/source-checkpoint.json')
                            .read_text(encoding='utf-8-sig'))
    changed = [record['path'] for record in checkpoint['files']
               if not (ROOT / record['path']).is_file()
               or hashlib.sha256((ROOT / record['path']).read_bytes()).hexdigest()
               != record['sha256']]
    # No preexisting source edits are part of this first planning checkpoint.
    report['checkpointFiles'] = len(checkpoint['files'])
    report['changedPreexistingFiles'] = changed
    report['ok'] = report['ok'] and not changed
    out = ROOT / '.cache/modular-expansion-2026-10-26'
    (out / 'python-tests.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
