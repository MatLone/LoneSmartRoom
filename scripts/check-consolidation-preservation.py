"""Fixed-scope passive before/after hashes; never decrypt, launch or repair."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import winreg
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.cache/validation/windows-dev9'

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def tree(root):
    result={}
    for directory,dirs,files in os.walk(root,followlinks=False):
        for name in dirs+files:
            p=Path(directory)/name
            if p.is_symlink() or p.stat().st_file_attributes&0x400:raise ValueError('reparse_rejected')
        for name in files:
            p=Path(directory)/name;result[p.relative_to(root).as_posix()]=sha(p)
    return result

if __name__=='__main__':
    if sys.argv[1:] not in (['before'],['after']):raise ValueError('stage')
    stage=sys.argv[1];OUT.mkdir(parents=True,exist_ok=True)
    baseline=json.loads((ROOT/'.cache/telemetry-loopback-authorized-2026-10-27/preservation-before-private.json').read_text(encoding='utf-8-sig'))
    home=Path.home();installation=home/'AppData/Local/Programs/Lone Smart Room'
    backup=home/'Documents/Lone Smart Room Backups/Windows-before-dev8-20261028T035246Z'
    manifest=json.loads((backup/'manifest.json').read_text(encoding='utf-8-sig'))
    assert all(sha(backup/f['destinationRelative'])==f['sha256'] for f in manifest['files'])
    protected={name:sha(ROOT/'.runtime/secure-agent'/name) for name in baseline['protected']}
    assert protected==baseline['protected']
    with sqlite3.connect((ROOT/'.runtime/secure-agent/devices.db').as_uri()+'?mode=ro',uri=True) as db:
        assert db.execute('PRAGMA quick_check').fetchall()==[('ok',)]
        grants=db.execute('SELECT COUNT(*) FROM app_permissions').fetchone()[0]
        pending=db.execute("SELECT COUNT(*) FROM app_commands WHERE state IN ('accepted','dispatching')").fetchone()[0]
        identity=hashlib.sha256(json.dumps(db.execute('SELECT id,label,hex(secret),revoked FROM devices ORDER BY id').fetchall(),sort_keys=True,separators=(',',':')).encode()).hexdigest()
        assert identity==baseline['database_identity']
    assert grants==pending==0
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Run') as key:
        commands=[winreg.EnumValue(key,i)[1] for i in range(winreg.QueryInfoKey(key)[1])]
    agent=[s for s in commands if isinstance(s,str) and 'secure_agent.py' in s]
    assert len(agent)==1 and hashlib.sha256(agent[0].encode()).hexdigest()==baseline['run_hash']
    current={'installation':tree(installation),'profile':tree(home/'AppData/Roaming/Lone Smart Room'),'protected':protected,
             'backup_manifest':sha(backup/'manifest.json')}
    private=OUT/'preservation-baseline-private.json'
    if stage=='before':
        with private.open('x',encoding='utf-8') as f:json.dump(current,f)
    else:assert current==json.loads(private.read_text(encoding='utf-8'))
    report={'ok':True,'stage':stage,'file_counts':{k:len(v) for k,v in current.items() if isinstance(v,dict)},
        'backup_files_verified':len(manifest['files']),'database_quick_check_ok':True,'grants':grants,
        'pending_commands':pending,'protected_files_unchanged':True,'device_identities_preserved':True,'run_unchanged':True,'credentials_decrypted':False,
        'profile_installation_hashes_equal_to_before':stage=='after'}
    (OUT/('preservation-'+stage+'.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))
