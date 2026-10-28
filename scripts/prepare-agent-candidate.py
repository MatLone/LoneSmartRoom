"""Prepare a source-only agent candidate; never copies state or runs its entry."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.cache/artifacts/agent/agent-reliability-dev9-r1'

def main():
    OUT.mkdir(parents=True,exist_ok=False)
    files=[]
    for folder in ('agent/windows','agent/development','telemetry','monitoring','diagnostics'):
        files.extend((ROOT/folder).glob('*.py'))
    files.extend([ROOT/'diagnostics/windows-census.ps1',ROOT/'scripts/desktop-agent-evidence.py'])
    payload={}
    for file in sorted(set(files)):
        if file.is_symlink() or file.resolve()!=file or file.stat().st_nlink!=1:raise ValueError('source_link_rejected')
        name=file.relative_to(ROOT).as_posix();data=file.read_bytes()
        if len(data)>262144 or b'-----BEGIN PRIVATE KEY-----' in data or b'-----BEGIN ENCRYPTED PRIVATE KEY-----' in data:raise ValueError('source_limit')
        payload[name]=data
    manifest=dict(v=1,kind='source_only_candidate',activated=False,registry_changed=False,
        future_entry='agent/development/reliable_bootstrap.py',maximum_attempts=3,
        recoverable_exit_codes=[71],unknown_failures_terminal=True,
        telemetry_registration_required=True,telemetry_enabled_by_default=False,
        authenticated_desktop_identity_provisioned=False,requires_existing_venv=True,
        operational_readiness_proven=False,
        existing_dependency_versions={name:importlib.metadata.version(name) for name in ('cryptography','cffi')},
        files_sha256={name:hashlib.sha256(data).hexdigest() for name,data in payload.items()})
    encoded=(json.dumps(manifest,indent=2)+'\n').encode()
    with zipfile.ZipFile(OUT/'agent-candidate-sources.zip','x',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,data in payload.items():archive.writestr(name,data)
        archive.writestr('candidate-manifest.json',encoded)
    (OUT/'candidate-manifest.json').write_bytes(encoded)
    with zipfile.ZipFile(OUT/'agent-candidate-sources.zip') as archive:
        assert archive.testzip() is None
        assert set(archive.namelist())==set(payload)|{'candidate-manifest.json'}
        for name,data in payload.items():assert archive.read(name)==data
    checksums=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(OUT.iterdir()))
    (OUT/'SHA256SUMS.txt').write_text(checksums)
    print(json.dumps(dict(ok=True,source_files=len(payload),credentials_included=False,executed=False,artifact=str(OUT/'agent-candidate-sources.zip'))))
if __name__=='__main__':main()
