"""Read-only operational preservation checks; never initializes Store/DPAPI/IPC."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
CACHE=ROOT/'.cache/validation'
database=ROOT/'.runtime/secure-agent/devices.db'
baseline=json.loads((CACHE/'agent-startup-diagnosis-2026-10-24/protected-before-private.json').read_text())
digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
differences=sum(not Path(name).is_file() or digest(Path(name))!=expected
    for name,expected in baseline.items() if Path(name)!=database)
stable=lambda rows:hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()
with sqlite3.connect(database.as_uri()+'?mode=ro',uri=True) as db:
    grants=db.execute('SELECT COUNT(*) FROM app_permissions').fetchone()[0]
    identities=stable(db.execute('SELECT id,label,hex(secret),revoked FROM devices ORDER BY id').fetchall())
    permissions=stable(db.execute('SELECT * FROM app_permissions ORDER BY 1,2').fetchall())
    schema=stable(db.execute("SELECT type,name,sql FROM sqlite_master WHERE type IN ('table','index') ORDER BY type,name").fetchall())
    pending=db.execute("SELECT COUNT(*) FROM app_commands WHERE state IN ('accepted','dispatching')").fetchone()[0]
logical=json.loads((CACHE/'agent-launcher-manual-20261024/database-logical-before.json').read_text())
read_system=lambda stage:json.loads((CACHE/f'agent-launcher-manual-20261024/system-lifecycle-{stage}.json').read_text(encoding='utf-8-sig'))
before,after=read_system('before'),read_system('after')
report={'checkedUtc':datetime.now(timezone.utc).isoformat(),
 'protectedFilesExcludingReplayDatabase':len(baseline)-1,'protectedDifferences':differences,
 'identitiesEncryptedSecretsRevocationUnchanged':identities==logical['devices'],
 'permissionsUnchanged':permissions==logical['permissions'],'schemaUnchanged':schema==logical['schema'],
 'grants':grants,'pendingAppCommands':pending,
 'originalProcessTreeUnchanged':before['processes']==after['processes'],
 'originalListenerUnchanged':before['listeners']==after['listeners'],
 'runUnchanged':before['runSha256']==after['runSha256'],
 'firewallUnchanged':before['firewallSha256']==after['firewallSha256'],
 'newOperationalLifecycleLogDirectoryCreated':(ROOT/'.runtime/agent-lifecycle-logs').exists(),
 'operationalStopRequested':False,'operationalHttpsRequestsSent':False,
 'operationalCredentialsDecrypted':False,'activeAgentUpdated':False}
assert not differences and grants==pending==0
assert all(report[key] for key in ('identitiesEncryptedSecretsRevocationUnchanged','permissionsUnchanged',
    'schemaUnchanged','originalProcessTreeUnchanged','originalListenerUnchanged','runUnchanged','firewallUnchanged'))
assert not report['newOperationalLifecycleLogDirectoryCreated']
(HERE/'preservation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
for stage,data in (('before',before),('after',after)):
    (HERE/f'system-{stage}.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
for source,target in ((CACHE/'graceful-shutdown-2026-10-24/tests.json','tests.json'),
                      (CACHE/'agent-launcher-preparation-2026-10-24/tests-summary.json','regressions.json')):
    (HERE/target).write_text(json.dumps(json.loads(source.read_text()),indent=2)+'\n',encoding='utf-8')
files=('agent/windows/graceful_launcher.py','agent/windows/graceful_runtime.py','agent/windows/lifecycle_logs.py',
       'agent/windows/local_shutdown.py','scripts/test-graceful-shutdown-isolated.py',
       'tests/test_graceful_shutdown.py','tests/test_local_shutdown_native.py','tests/graceful_substitute.py')
(HERE/'implementation-sha256.json').write_text(json.dumps({p:digest(ROOT/p) for p in files},indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
