"""Reproducible OFFLINE suite: deny all bind/connect; only disposable toy children.

No operational agent import/launch; no HTTPS fixture or production credentials.
Requires Windows user context for native ACL tests. Writes sanitized results only.
"""
import json
from pathlib import Path
import socket
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tests'))
MODULES = ('test_agent_launcher', 'test_launcher_win32', 'test_baseline',
           'test_wol_backup', 'test_steam_launcher', 'test_cs2_launcher')


def main():
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in MODULES)
    from launcher_win32 import Windows
    test_context_elevated = Windows().elevated
    original = subprocess.Popen
    helper = str(ROOT/'tests/launcher_substitute.py')

    def toy_only(args, *positional, **kwargs):
        if not (isinstance(args, list) and len(args) == 5
                and Path(args[0]).resolve() == Path(sys.executable).resolve()
                and args[1:4] == ['-I', '-B', helper]
                and args[4].startswith('Global\\LoneSmartRoom.LauncherTests.')):
            raise AssertionError('Non-substitute process denied by isolated runner')
        return original(args, *positional, **kwargs)

    denied = AssertionError('All network bind/connect denied by isolated runner')
    with patch('subprocess.Popen', side_effect=toy_only), \
            patch.object(socket.socket, 'bind', side_effect=denied), \
            patch.object(socket.socket, 'connect', side_effect=denied), \
            patch.object(socket.socket, 'connect_ex', side_effect=denied):
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    receipt = {'modules': list(MODULES), 'tests': result.testsRun,
               'failures': len(result.failures), 'errors': len(result.errors),
               'skipped': len(result.skipped), 'ok': result.wasSuccessful(),
               'testContextElevated': test_context_elevated,
               'networkOperationsAllowed': False, 'operationalAgentAllowed': False,
               'realApplicationLaunchAllowed': False}
    directory = ROOT/'.cache/validation/agent-launcher-preparation-2026-10-24'
    directory.mkdir(parents=True, exist_ok=True)
    (directory/'tests-summary.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(receipt))
    return 0 if result.wasSuccessful() and not result.skipped else 1


if __name__ == '__main__':
    raise SystemExit(main())
