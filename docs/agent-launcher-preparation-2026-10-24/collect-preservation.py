"""Read-only hash/SQLite verification; publish counts, never protected contents."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CACHE = ROOT/'.cache/validation/agent-launcher-preparation-2026-10-24'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


baseline = json.loads((ROOT/'.cache/validation/agent-startup-diagnosis-2026-10-24/protected-before-private.json').read_text())
differences = sum(not Path(name).is_file() or digest(Path(name)) != expected
                  for name, expected in baseline.items())
with sqlite3.connect((ROOT/'.runtime/secure-agent/devices.db').as_uri()+'?mode=ro&immutable=1', uri=True) as database:
    grants = database.execute('SELECT COUNT(*) FROM app_permissions').fetchone()[0]
system = json.loads((CACHE/'system-after.json').read_text(encoding='utf-8-sig'))
expected_run = '3139f837ebc03ab77c5c16bc00fcb76031fb6a50ef8ccbcd4a014d6c4b509dc5'
receipt = {'checkedUtc': datetime.now(timezone.utc).isoformat(),
    'protectedFilesVerified': len(baseline), 'differences': differences, 'grants': grants,
    'runUnchanged': system['RunSHA256'] == expected_run,
    'listener8776': system['Listener8776'], 'agentOrLauncherProcesses': system['AgentOrLauncherProcesses'],
    'productionStartupLogDirectoryCreated': (ROOT/'.runtime/agent-startup-logs').exists(),
    'credentialsDecrypted': False, 'operationalAgentExecuted': False}
receipt['ok'] = (differences == grants == receipt['listener8776'] == receipt['agentOrLauncherProcesses'] == 0
                 and receipt['runUnchanged'] and not receipt['productionStartupLogDirectoryCreated'])
HERE.joinpath('preservation.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
HERE.joinpath('tests.json').write_text((CACHE/'tests-summary.json').read_text(), encoding='utf-8')
HERE.joinpath('system.json').write_text(json.dumps(system, indent=2)+'\n', encoding='utf-8')
python = ROOT/'.venv/Scripts/pythonw.exe'
old = subprocess.list2cmdline([str(python), str(ROOT/'agent/windows/secure_agent.py'), 'serve'])
proposed = subprocess.list2cmdline([str(python), '-I', '-B', str(ROOT/'agent/windows/agent_launcher.py')])
plan = {'applied': False, 'hive': 'HKCU', 'key': r'Software\Microsoft\Windows\CurrentVersion\Run',
    'name': 'LoneSmartRoomSecureAgent', 'type': 'REG_SZ', 'current': old,
    'currentSha256': hashlib.sha256(old.encode()).hexdigest(),
    'proposed': proposed, 'proposedCharacters': len(proposed),
    'requiresSeparateApproval': True}
HERE.joinpath('run-migration-plan.json').write_text(json.dumps(plan, indent=2)+'\n', encoding='utf-8')
files = ('agent/windows/agent_launcher.py', 'agent/windows/launcher_logs.py', 'agent/windows/launcher_win32.py',
         'scripts/test-agent-launcher-isolated.py', 'tests/test_agent_launcher.py',
         'tests/test_launcher_win32.py', 'tests/launcher_substitute.py')
HERE.joinpath('implementation-sha256.json').write_text(json.dumps({name:digest(ROOT/name) for name in files}, indent=2)+'\n', encoding='utf-8')
print(json.dumps(receipt))
print(json.dumps({'proposedRunCharacters':len(proposed), 'runPlanApplied':False}))
if not receipt['ok'] or plan['currentSha256'] != expected_run or len(proposed) > 260:
    raise SystemExit(1)
