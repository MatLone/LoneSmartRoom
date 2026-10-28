"""Explicit Electron-only upgrade backup; no agent state/credentials are copied."""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'agent/windows'))
from launcher_win32 import Windows,checked_path

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def inventory(root):
    result={}
    for folder,dirs,files in os.walk(root,followlinks=False):
        for name in dirs+files:checked_path(Path(folder)/name)
        for name in files:
            path=Path(folder)/name
            result[path.relative_to(root).as_posix()]=dict(bytes=path.stat().st_size,sha256=sha(path))
    return result

def main():
    if sys.argv[1:]:raise ValueError('fixed_scope_only')
    home=Path.home();win=Windows()
    if win.elevated:raise PermissionError('normal_user_required')
    base=checked_path(home/'Documents/Lone Smart Room Backups')
    if not base.is_dir():raise FileNotFoundError('backup_parent_required')
    destination=base/('Windows-before-dev9-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    if destination.exists():raise FileExistsError('preserve_previous_backup')
    sources={'installation':home/'AppData/Local/Programs/Lone Smart Room',
             'production-profile':home/'AppData/Roaming/Lone Smart Room'}
    inventories={label:inventory(checked_path(source)) for label,source in sources.items()}
    if not all(inventories.values()):raise ValueError('missing_production_data')
    win.private_directory(destination)
    records=[]
    for label,source in sources.items():
        target=destination/label;win.private_directory(target)
        for relative,item in inventories[label].items():
            output=target/relative
            chain=[];cursor=output.parent
            while not cursor.exists():chain.append(cursor);cursor=cursor.parent
            for folder in reversed(chain):win.private_directory(folder)
            win.private_file(output)
            # No replacement of originals; destination is new and owner-only.
            with (source/relative).open('rb') as reader,output.open('wb') as writer:shutil.copyfileobj(reader,writer,1024*1024)
            win.verify_private(output)
            if sha(output)!=item['sha256'] or sha(source/relative)!=item['sha256']:raise ValueError('unstable_source_or_copy')
            records.append(dict(source=label,relative=relative,destinationRelative=label+'/'+relative,**item))
    if {label:inventory(source) for label,source in sources.items()}!=inventories:raise ValueError('source_changed_during_backup')
    manifest=destination/'manifest.json';win.private_file(manifest)
    manifest.write_text(json.dumps(dict(v=1,complete=True,installed_version='2.0.0-dev.8',target_version='2.0.0-dev.9',files=records),indent=2)+'\n',encoding='utf-8')
    assert all(sha(destination/r['destinationRelative'])==r['sha256'] for r in records)
    win.verify_private(manifest);win.verify_private(destination)
    report=dict(ok=True,backup=str(destination),files=len(records),bytes=sum(r['bytes'] for r in records),manifest_sha256=sha(manifest),owner_only_acl_verified=True,originals_modified=False,agent_database_copied=False,credentials_decrypted=False,counts={k:len(v) for k,v in inventories.items()})
    out=ROOT/'.cache/validation/windows-dev9-installation';out.mkdir(parents=True,exist_ok=True)
    with (out/'backup-receipt.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
    print(json.dumps(report))
if __name__=='__main__':main()
