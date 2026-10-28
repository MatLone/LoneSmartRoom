"""x86 NSIS -> native x64 helper integration, disposable file fixtures ONLY.

No production installer, registry entry, service, application or agent is run.
The real macro/helper operate on one .cache fixture; its journal is preserved.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
ROOT=Path(__file__).resolve().parents[1]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    base=ROOT/'.cache/runtime-preservation-nsis-test'/uuid.uuid4().hex
    source=base/'fixture-app';resources=base/'resources';resources.mkdir(parents=True);source.mkdir()
    assert source.resolve().is_relative_to((ROOT/'.cache/runtime-preservation-nsis-test').resolve())
    helper=ROOT/'apps/windows-ui/build/preserve-runtime.ps1'
    macro=ROOT/'apps/windows-ui/build/runtime-preservation.nsh'
    for name in ('preserve-runtime.ps1','package-files.txt','package-remove.nsh'):
        shutil.copyfile(ROOT/'apps/windows-ui/build'/name,resources/name)
    text=macro.read_text()
    # Only suppress modal rendering in this disposable test copy. Failure
    # conditions, nonzero exit, host selection and actual helper are unchanged.
    text='\n'.join('    DetailPrint "fixture aborted"' if line.lstrip().startswith('MessageBox ') else line for line in text.splitlines())+'\n'
    text=text.replace('  Pop $1','  Pop $1\n  FileOpen $2 "$INSTDIR\\probe-diagnostic.txt" a\n  FileWrite $2 "$0$\\r$\\n$1$\\r$\\n"\n  FileClose $2')
    (resources/'runtime-preservation.nsh').write_text(text)
    (source/'Lone Smart Room.exe').write_bytes(b'NOT AN EXECUTABLE: fixture marker only')
    log=source/'debug.log';log.write_text('owned NSIS fixture, preserve exactly\n')
    original=sha(log);binary=base/'fixture-probe.exe';result=base/'result.txt'
    script='''Unicode true
Name "LSR file preservation TEST ONLY"
OutFile "@@BINARY@@"
SilentInstall silent
RequestExecutionLevel user
!define BUILD_RESOURCES_DIR "@@RESOURCES@@"
!include "@@RESOURCES@@\\runtime-preservation.nsh"
Function instFilesPre
  StrCpy $INSTDIR "@@SOURCE@@"
FunctionEnd
Section
  Call lonePreserveBeforeInstall
  ; Delete ONLY the fixed disposable fixture file, never an installed app.
  Delete "$INSTDIR\\debug.log"
  !insertmacro customInstall
  FileOpen $2 "@@RESULT@@" w
  FileWrite $2 "$loneRuntimePowerShell$\\r$\\n$loneRuntimeJournal"
  FileClose $2
SectionEnd
'''
    for tag,value in [('BINARY',binary),('RESOURCES',resources),('SOURCE',source),('RESULT',result)]:script=script.replace('@@'+tag+'@@',str(value))
    nsi=base/'probe.nsi';nsi.write_text(script)
    compiler=ROOT/'.cache/electron-builder/nsis-3.0.4.1/nsis-3.0.4.1-1mx3n/Bin/makensis.exe'
    built=subprocess.run([str(compiler),'-V2',str(nsi)],shell=False,cwd=base,capture_output=True)
    if built.returncode:raise RuntimeError(built.stdout.decode(errors='replace')+built.stderr.decode(errors='replace'))
    # The script above contains only fixture file operations. This is not the
    # application's NSIS, has no production target and never runs its binaries.
    child=subprocess.Popen([str(binary)],cwd=base,shell=False,creationflags=0x08000000)
    try:code=child.wait(timeout=30)
    except subprocess.TimeoutExpired:raise RuntimeError('fixture_still_running_no_force') from None
    if code or not result.exists():
        diagnostic=source/'probe-diagnostic.txt'
        raise RuntimeError('native_fixture_failed_'+str(code)+' '+(diagnostic.read_text() if diagnostic.exists() else 'no_helper_receipt'))
    lines=result.read_text().splitlines();journal=Path(lines[-1]);manifest=json.loads((journal/'manifest.json').read_text(encoding='utf-8-sig'))
    assert 'Sysnative' in lines[0] and manifest['helper_architecture_bits']==64
    assert Path(manifest['source']).resolve()==source.resolve()
    assert sha(log)==original and sha(journal/'data/debug.log')==original
    assert len(manifest['files'])==1 and manifest['complete'] is True
    receipt=dict(ok=True,checks=7,nsis_architecture_bits=32,helper_architecture_bits=64,
        compiler_sha256=sha(compiler),macro_sha256=sha(macro),helper_sha256=sha(helper),
        debug_log_restored=True,fixture_exit_code=code,production_files_touched=False,
        production_installer_run=False,execution_policy_changed=False,execution_policy_override=False,
        fixture_retained=True,journal_preserved=True,fixture=str(base))
    out=ROOT/'.cache/validation/windows-dev9-installation';out.mkdir(parents=True,exist_ok=True)
    (out/'nsis-host-integration.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))
if __name__=='__main__':main()
