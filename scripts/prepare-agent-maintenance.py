"""Prepare protected recovery material; never writes Run or starts the agent."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
import winreg
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'agent/windows'),str(ROOT/'agent/development')]
from launcher_win32 import Windows,checked_path
from agent_launcher import Layout
from reliable_bootstrap import startup_command,validate_candidate
from diagnostics.windows_readers import WindowsReaders

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    if sys.argv[1:]:raise ValueError('prepare_only_no_arguments')
    windows=Windows()
    if windows.elevated:raise PermissionError('normal_user_required')
    layout=Layout(ROOT);validate_candidate(layout)
    readers=WindowsReaders(candidate=True);deadline=time.monotonic()+15
    try:
        readers.begin(deadline);census=readers.census(deadline=deadline)
        if census['agent_processes'] or census['listeners']:raise ValueError('agent_must_be_offline')
        database=readers.database()
        if not database['integrity_ok'] or database['grants']!=0:raise ValueError('database_gate')
    finally:readers.close()
    keyname=r'Software\Microsoft\Windows\CurrentVersion\Run'
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,keyname,0,winreg.KEY_READ) as key:
        matches=[winreg.EnumValue(key,i) for i in range(winreg.QueryInfoKey(key)[1])]
    matches=[r for r in matches if isinstance(r[1],str) and 'secure_agent.py' in r[1]]
    if len(matches)!=1 or matches[0][2]!=winreg.REG_SZ:raise ValueError('run_gate')
    value_name,old_value,kind=matches[0]
    base=checked_path(Path.home()/'Documents/Lone Smart Room Backups')
    destination=base/('Agent-before-reliable-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    if destination.exists():raise FileExistsError('preserve_prior_backup')
    files=[]
    state=checked_path(ROOT/'.runtime/secure-agent')
    for source in state.rglob('*'):
        checked_path(source)
        if source.is_file():files.append((source,'state/'+source.relative_to(state).as_posix()))
    for folder in ('agent/windows','agent/development'):
        files.extend((p,'source/'+p.relative_to(ROOT).as_posix()) for p in (ROOT/folder).glob('*.py'))
    if len(files)>128 or sum(p.stat().st_size for p,_ in files)>64*1024*1024:raise ValueError('backup_budget')
    inventory={name:dict(sha256=sha(p),bytes=p.stat().st_size) for p,name in files}
    windows.private_directory(destination)
    for source,name in files:
        output=destination/name;parents=[];cursor=output.parent
        while not cursor.exists():parents.append(cursor);cursor=cursor.parent
        for folder in reversed(parents):windows.private_directory(folder)
        windows.private_file(output)
        with source.open('rb') as r,output.open('wb') as w:shutil.copyfileobj(r,w,1024*1024)
        windows.verify_private(output)
        if sha(output)!=inventory[name]['sha256'] or sha(source)!=inventory[name]['sha256']:raise ValueError('unstable_backup')
    private=destination/'run-recovery.json';windows.private_file(private)
    private.write_text(json.dumps(dict(v=1,key=keyname,name=value_name,kind=kind,previous=old_value,proposed=startup_command(layout)),indent=2),encoding='utf-8');windows.verify_private(private)
    manifest=destination/'manifest.json';windows.private_file(manifest)
    manifest.write_text(json.dumps(dict(v=1,complete=True,files=inventory,run_recovery_sha256=sha(private)),indent=2),encoding='utf-8');windows.verify_private(manifest);windows.verify_private(destination)
    report=dict(v=1,ok=True,backup=str(destination),files=len(files)+2,manifest_sha256=sha(manifest),owner_only_acl_verified=True,registry_written=False,agent_started=False,credentials_decrypted=False,grants=0,previous_run_sha256=hashlib.sha256(old_value.encode()).hexdigest(),proposed_run_sha256=hashlib.sha256(startup_command(layout).encode()).hexdigest(),dispatch_after_login_proven=False)
    out=ROOT/'.cache/validation/agent-maintenance';out.mkdir(parents=True,exist_ok=True)
    with (out/'preparation.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
    print(json.dumps(report))
if __name__=='__main__':main()
