"""Read-only hashes of explicitly scoped application/profile/backup paths and DB integrity.

Does not decrypt credentials, inspect document contents, restore or change ACLs.
Private inventories stay in ignored cache; public report contains only counts/booleans.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.cache/validation/monitoring-electron-2026-10-25'


def tree(root):
    if not root.is_dir():raise ValueError('Expected preserved directory missing')
    records={}
    for directory,dirs,files in os.walk(root,followlinks=False):
        for name in dirs+files:
            p=Path(directory)/name
            if p.is_symlink() or getattr(p.stat(),'st_file_attributes',0)&0x400:
                raise ValueError('Unexpected preserved reparse point')
        for name in files:
            p=Path(directory)/name
            with p.open('rb') as stream:records[p.relative_to(root).as_posix()]=hashlib.file_digest(stream,'sha256').hexdigest()
    return records


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=('before','after'),required=True);args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    home=Path.home();backups=home/'Documents/Lone Smart Room Backups'
    locations={'installed_electron':home/'AppData/Local/Programs/Lone Smart Room',
               'production_profile':home/'AppData/Roaming/Lone Smart Room',
               'backup_dev3':backups/'Windows-before-dev3-20261024T145523Z',
               'backup_dev4':backups/'Windows-before-dev4-20261024T174801Z'}
    trees={key:tree(value) for key,value in locations.items()}
    database=ROOT/'.runtime/secure-agent/devices.db'
    protected=json.loads((ROOT/'.cache/validation/agent-startup-diagnosis-2026-10-24/protected-before-private.json').read_text())
    authorized={ROOT/'apps/windows-ui'/name for name in ('desktop-main.cjs','desktop-policy.cjs','index.html','package.json','preload.cjs')}
    for path in authorized:
        baseline=subprocess.check_output([str(ROOT/'.tools/git/cmd/git.exe'),'-c','safe.directory='+str(ROOT),
            'show','8b5ef78:'+path.relative_to(ROOT).as_posix()])
        candidates=(baseline,baseline.replace(b'\n',b'\r\n'))  # Git normalized text vs original Windows checkout.
        assert protected[str(path)] in {hashlib.sha256(b).hexdigest() for b in candidates},'Reviewed checkpoint/source mismatch'
    changed=sum(not Path(p).is_file() or hashlib.sha256(Path(p).read_bytes()).hexdigest()!=expected
                for p,expected in protected.items() if Path(p)!=database and Path(p) not in authorized)
    assert changed==0,'Protected operational files changed'
    with sqlite3.connect(database.as_uri()+'?mode=ro',uri=True,timeout=0.5) as db:
        assert db.execute('PRAGMA quick_check').fetchall()==[('ok',)]
        grants=db.execute('SELECT COUNT(*) FROM app_permissions').fetchone()[0]
        pending=db.execute("SELECT COUNT(*) FROM app_commands WHERE state IN ('accepted','dispatching')").fetchone()[0]
        digest=lambda rows:hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()
        logical={'devices':digest(db.execute('SELECT id,label,hex(secret),revoked FROM devices ORDER BY id').fetchall()),
                 'permissions':digest(db.execute('SELECT * FROM app_permissions ORDER BY 1,2').fetchall()),
                 'schema':digest(db.execute("SELECT type,name,sql FROM sqlite_master WHERE type IN ('table','index') ORDER BY type,name").fetchall())}
    assert grants==pending==0
    reference=json.loads((ROOT/'.cache/validation/agent-recovery-2026-10-25/database-logical-before.json').read_text())
    assert logical==reference
    trees['authorized_development_sources']={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in authorized}
    if args.stage=='before':
        (OUT/'preserved-trees-private.json').write_text(json.dumps(trees),encoding='utf-8')
    else:
        assert trees==json.loads((OUT/'preserved-trees-private.json').read_text()),'Installed/profile/backup tree changed'
    report={'ok':True,'utc':datetime.now(timezone.utc).isoformat(),'stage':args.stage,
            'file_counts':{key:len(value) for key,value in trees.items()},'databaseQuickCheckOk':True,
            'zeroGrants':True,'zeroPendingCommands':True,'logicalIdentitiesSecretsPermissionsSchemaPreserved':True,
            'protectedOperationalFiles':len(protected)-1-len(authorized),'protectedDifferences':0,
            'authorizedDevelopmentSourceChanges':len(authorized),
            'profileInstallationBackupsUnchanged':True if args.stage=='after' else None,'credentialsDecrypted':False}
    (OUT/('preservation-'+args.stage+'.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':main()
