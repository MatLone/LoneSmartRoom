"""Static, read-only installation/backup checks. No agent launch or HTTP request."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import winreg

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'docs/windows-dev8-homologation'
INSTALL = Path.home()/'AppData/Local/Programs/Lone Smart Room'
PROFILE = Path.home()/'AppData/Roaming/Lone Smart Room'
BACKUP = Path.home()/'Documents/Lone Smart Room Backups/Windows-before-dev8-20261028T035246Z'
CANDIDATE = ROOT/'.cache/artifacts/windows/desktop-dev8-control-center-candidate'


def sha(p):
    with p.open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def tree(root):
    result = {}
    for folder, dirs, files in os.walk(root, followlinks=False):
        for name in dirs+files:
            p = Path(folder)/name
            if p.is_symlink() or p.stat().st_file_attributes & 0x400:
                raise ValueError('unexpected_reparse_point')
        for name in files:
            p = Path(folder)/name
            result[p.relative_to(root).as_posix()] = sha(p)
    return result


if __name__ == '__main__':
    before = json.loads((ROOT/'.cache/validation/windows-dev8-homologation/initial-trees-private.json').read_text(encoding='utf-8-sig'))
    baseline = json.loads((ROOT/'.cache/telemetry-loopback-authorized-2026-10-27/preservation-before-private.json').read_text(encoding='utf-8-sig'))
    manifest = json.loads((BACKUP/'manifest.json').read_text(encoding='utf-8-sig'))
    expected_manifest = '781721b0931fb49256b0db481e9e004917cea98f7fd127d0dfdf9201d31f93bd'
    assert sha(BACKUP/'manifest.json') == expected_manifest
    assert all(sha(BACKUP/f['destinationRelative']) == f['sha256'] for f in manifest['files'])
    candidate, installed, profile = tree(CANDIDATE/'win-unpacked'), tree(INSTALL), tree(PROFILE)
    assert all(installed.get(k) == v for k,v in candidate.items())
    assert all(k in installed for k in before['installation'])
    protected = {name: sha(ROOT/'.runtime/secure-agent'/name) for name in baseline['protected']}
    assert protected == baseline['protected']
    with sqlite3.connect((ROOT/'.runtime/secure-agent/devices.db').as_uri()+'?mode=ro',uri=True) as db:
        assert db.execute('PRAGMA quick_check').fetchall() == [('ok',)]
        grants = db.execute('SELECT COUNT(*) FROM app_permissions').fetchone()[0]
        pending = db.execute("SELECT COUNT(*) FROM app_commands WHERE state IN ('accepted','dispatching')").fetchone()[0]
    assert grants == pending == 0
    # Only the documented existing Run value is read. Never set/create a key.
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Run') as key:
        values = [winreg.EnumValue(key,i) for i in range(winreg.QueryInfoKey(key)[1])]
    commands = [v for _,v,_ in values if isinstance(v,str) and 'secure_agent.py' in v]
    run_same = len(commands)==1 and hashlib.sha256(commands[0].encode()).hexdigest()==baseline['run_hash']
    assert run_same
    preferences = json.loads((PROFILE/'desktop-window-state.json').read_text(encoding='utf-8'))
    settings = json.loads((PROFILE/'workbench/workbench-v1.json').read_text(encoding='utf-8'))
    report = {'utc': datetime.now(timezone.utc).isoformat(), 'ok': True,
        'candidate_files_matched': len(candidate), 'backup_files_verified': len(manifest['files']),
        'backup_manifest_sha256': expected_manifest, 'previous_install_files_missing': 0,
        'profile_original_files': len(before['profile']),
        'profile_original_files_missing': len(set(before['profile'])-set(profile)),
        'profile_original_files_changed_during_authorized_execution': sum(profile.get(k)!=v for k,v in before['profile'].items()),
        'profile_current_files': len(profile), 'window_preferences_valid': preferences['schema']==1,
        'automatic_tray_disabled': preferences['minimizeToTray'] is False,
        'history_enabled_by_test_ui': settings['history']['enabled'],
        'history_retention_hours': settings['history']['retentionHours'],
        'app_local_profile': settings['profile']['name'],
        'protected_config_and_certificate_files_unchanged': True,
        'database_quick_check_ok': True, 'grants': grants, 'pending_commands': pending,
        'hkcu_run_command_unchanged': run_same, 'credentials_decrypted': False,
        'nsis_sha256': sha(CANDIDATE/'Lone-Smart-Room-2.0.0-dev.8-x64-Setup-DEV.exe'),
        'portable_sha256': sha(CANDIDATE/'Lone-Smart-Room-2.0.0-dev.8-x64-Portable-DEV.exe')}
    (OUT/'integrity.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))
