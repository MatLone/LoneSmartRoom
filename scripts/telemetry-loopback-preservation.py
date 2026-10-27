"""Read-only before/after evidence for the explicitly authorized development run."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from diagnostics.windows_readers import WindowsReaders, STATE

OUT=ROOT/'.cache/telemetry-loopback-authorized-2026-10-27'
INSTALL=(Path.home() / 'AppData/Local/Programs/Lone Smart Room')
PROFILE=(Path.home() / 'AppData/Roaming/Lone Smart Room')
BACKUP=(Path.home() / 'Documents/Lone Smart Room Backups/Windows-before-dev7-20261026T152048Z')

def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def tree(root):
    return {p.relative_to(root).as_posix():sha(p) for d,dirs,files in os.walk(root,followlinks=False) for p in (Path(d)/n for n in files)}

def main():
    if sys.argv[1:] not in (['--before'],['--after']):raise ValueError('fixed_stage_required')
    stage=sys.argv[1][2:];OUT.mkdir(exist_ok=True)
    prior=json.loads((ROOT/'.cache/telemetry-homologation-preparation-2026-10-27/operational-before-private.json').read_text())
    r=WindowsReaders()
    try:
        r.begin(time.monotonic()+20);c=r.census(deadline=time.monotonic()+15);db=r.database()
        status=r.status(deadline=time.monotonic()+3) if c['agent_verified'] else {'ok':False}
    finally:r.close()
    protected={name:sha(STATE/name) for name in prior['protected_file_hashes']}
    installed=tree(INSTALL);profile=tree(PROFILE)
    manifest=json.loads((BACKUP/'manifest.json').read_text(encoding='utf-8-sig'))
    backup_ok=all(sha(BACKUP/f['destinationRelative'])==f['sha256'] for f in manifest['files'])
    old_install=json.loads((ROOT/'.cache/validation/windows-homologation-dev7-2026-10-27/installation-before-private.json').read_text())
    assert all(installed.get(k)==v for k,v in old_install.items()),'installed_source_changed'
    assert set(installed)-set(old_install)=={'debug.log'},'unexpected_installation_file'
    assert installed['debug.log']=='3c07a1353428a6ee9239f0e7b0576d95a84dca4dd40d07281499ba062dd73c9c','debug_log_changed'
    assert c['agent_verified'] and c['agent_identity_digest']==prior['census']['agent_identity_digest'],'agent_changed'
    assert db['integrity_ok'] and db['grants']==0 and db['identity_sha256']==prior['database']['identity_sha256'],'database_changed'
    assert db['permissions_sha256']==prior['database']['permissions_sha256'] and protected==prior['protected_file_hashes'],'permissions_or_files_changed'
    assert status['ok'] and status['tls']=='TLSv1.3' and status['pin_verified'] and status['hostname_verified'],'https_failed'
    assert c['monitoring_count']==0 and backup_ok,'monitoring_or_backup_gate'
    stable=dict(agent_identity=c['agent_identity_digest'],protected=protected,database_identity=db['identity_sha256'],permissions=db['permissions_sha256'],installation=installed,profile=profile,run_hash=c['startup']['run_sha256'])
    baseline=OUT/'preservation-before-private.json'
    if stage=='before':
        with baseline.open('x',encoding='utf-8') as f:json.dump(stable,f)
    else:assert stable==json.loads(baseline.read_text()),'preservation_difference'
    report=dict(ok=True,stage=stage,observed_at=datetime.now(timezone.utc).isoformat(),agent_processes=c['agent_processes'],listeners=c['listeners'],status=status,
        zero_grants=True,database_integrity=True,same_agent_identity=True,protected_files_unchanged=True,installation_files=len(installed),original_installed_files_unchanged=len(old_install),
        debug_log_preserved=True,profile_files=len(profile),backup_files_verified=len(manifest['files']),backup_integrity=True,monitoring_processes=c['monitoring_count'],
        installation_profile_run_unchanged=stage=='after')
    (OUT/('preservation-'+stage+'.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':main()
