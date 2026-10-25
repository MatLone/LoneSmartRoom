"""Read-only preservation, distinguishing authorized repository UI changes from installed data."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import subprocess

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'.cache/validation/windows-dev5'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stage',required=True,choices=('before','after'));args=parser.parse_args()
    spec=importlib.util.spec_from_file_location('preservation',ROOT/'scripts/monitoring-development-preservation.py')
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    home=Path.home();backups=home/'Documents/Lone Smart Room Backups'
    locations={'installed':home/'AppData/Local/Programs/Lone Smart Room','profile':home/'AppData/Roaming/Lone Smart Room',
        'backup_dev3':backups/'Windows-before-dev3-20261024T145523Z','backup_dev4':backups/'Windows-before-dev4-20261024T174801Z'}
    trees={key:old.tree(value) for key,value in locations.items()}
    baseline=json.loads((ROOT/'.cache/validation/agent-startup-diagnosis-2026-10-24/protected-before-private.json').read_text())
    database=ROOT/'.runtime/secure-agent/devices.db'
    protected={raw:expected for raw,expected in baseline.items() if Path(raw)!=database and not Path(raw).is_relative_to(ROOT/'apps/windows-ui')}
    assert all(Path(raw).is_file() and hashlib.sha256(Path(raw).read_bytes()).hexdigest()==expected for raw,expected in protected.items())
    with sqlite3.connect(database.as_uri()+'?mode=ro',uri=True,timeout=0.5) as db:
        assert db.execute('PRAGMA quick_check').fetchall()==[('ok',)]
        assert db.execute('SELECT COUNT(*) FROM app_permissions').fetchone()[0]==0
        assert db.execute("SELECT COUNT(*) FROM app_commands WHERE state IN ('accepted','dispatching')").fetchone()[0]==0
        digest=lambda rows:hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()
        logical={'devices':digest(db.execute('SELECT id,label,hex(secret),revoked FROM devices ORDER BY id').fetchall()),
            'permissions':digest(db.execute('SELECT * FROM app_permissions ORDER BY 1,2').fetchall()),
            'schema':digest(db.execute("SELECT type,name,sql FROM sqlite_master WHERE type IN ('table','index') ORDER BY type,name").fetchall())}
    assert logical==json.loads((ROOT/'.cache/validation/agent-recovery-2026-10-25/database-logical-before.json').read_text())
    OUT.mkdir(parents=True,exist_ok=True);private=OUT/'preservation-private.json'
    if args.stage=='before':
        if private.exists():raise RuntimeError('Preserve prior preflight snapshot')
        private.write_text(json.dumps(trees),encoding='utf-8')
    else:assert trees==json.loads(private.read_text()),'Installed/profile/backups changed'
    git=str(ROOT/'.tools/git/cmd/git.exe')
    assert not subprocess.check_output([git,'-c','safe.directory='+str(ROOT),'diff','216dcba','--name-only','--','agent','apps/android'])
    report={'ok':True,'utc':datetime.now(timezone.utc).isoformat(),'stage':args.stage,'zeroGrants':True,'zeroPendingCommands':True,
        'databaseIntegrityAndIdentitiesPreserved':True,'protectedNonUISourceFiles':len(protected),'protectedDifferences':0,
        'fileCounts':{k:len(v) for k,v in trees.items()},'installedProfileBackupsUnchanged':args.stage=='after',
        'androidAndAgentSourcesUnchanged':True,'credentialsDecrypted':False}
    (OUT/('preservation-'+args.stage+'.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':main()
