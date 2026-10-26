"""Snapshot the already validated local CPython, stdlib and allowlisted monitoring code.

No downloads, pip, installs, sensors, Registry operations or generated EXE execution.
The new payload is never overwritten. Python source and binaries are hashed on copy.
"""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
MODULES=('__init__','contracts','collector','cache','ipc','pipe_protocol','winpipe','pipe_server',
         'windows_native','windows_basic','development_collector','lifetime','application_context',
         'adlx_provider','adlx_bridge','adlx_diagnostics','gpu_development')
BINARIES=('python.exe','python3.dll','python313.dll','vcruntime140.dll','vcruntime140_1.dll','LICENSE.txt')
EXTENSIONS=('_ctypes.pyd','libffi-8.dll','_decimal.pyd','_statistics.pyd','_queue.pyd',
            'select.pyd','unicodedata.pyd','zlib1.dll')
EXCLUDED={'site-packages','__pycache__','test','tests','idlelib','tkinter','turtledemo','ensurepip','venv',
          'sitecustomize.py','usercustomize.py','__phello__'}


def main():
    assert sys.version_info[:3]==(3,13,3),'Use the approved existing Python 3.13.3'
    base=Path(sys._base_executable).resolve().parent
    destination=ROOT/'.cache/windows-monitoring-runtime/dev7'
    if destination.exists():raise RuntimeError('Preserve earlier payload; destination already exists')
    destination.mkdir(parents=True)
    runtime=destination/'runtime';runtime.mkdir();(runtime/'DLLs').mkdir()
    copied={}
    def copy(source,target):
        target.parent.mkdir(parents=True,exist_ok=True)
        before=hashlib.sha256(source.read_bytes()).hexdigest();shutil.copyfile(source,target)
        assert before==hashlib.sha256(source.read_bytes()).hexdigest()==hashlib.sha256(target.read_bytes()).hexdigest()
        copied[target.relative_to(destination).as_posix()]=before
    for name in BINARIES:copy(base/name,runtime/name)
    for name in EXTENSIONS:
        source=base/'DLLs'/name
        if source.is_file():copy(source,runtime/'DLLs'/name)
        elif name not in ('_statistics.pyd',):raise RuntimeError('Required authorized runtime extension missing')
    archive=runtime/'python313.zip';count=0
    # Stored members avoid depending on zlib during isolated interpreter bootstrap.
    # NSIS/portable apply their normal outer archive compression afterwards.
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_STORED) as z:
        for file in sorted((base/'Lib').rglob('*.py')):
            relative=file.relative_to(base/'Lib')
            if any(part in EXCLUDED for part in relative.parts):continue
            if file.is_symlink():raise RuntimeError('Unexpected stdlib symlink')
            info=zipfile.ZipInfo(relative.as_posix(),date_time=(2025,4,8,0,0,0));info.compress_type=zipfile.ZIP_STORED
            info.external_attr=0o100644<<16
            z.writestr(info,file.read_bytes());count+=1
    # Isolated application-local search path, no import site, Registry or PYTHONPATH.
    (runtime/'python313._pth').write_text('python313.zip\nDLLs\n.\n',encoding='ascii',newline='\n')
    for name in MODULES:copy(ROOT/'monitoring'/(name+'.py'),destination/'code/monitoring'/(name+'.py'))
    for name in ('monitoring-pipe-client.py','monitoring-pipe-server.py'):copy(ROOT/'scripts'/name,destination/'code/scripts'/name)
    version=json.loads((ROOT/'apps/windows-ui/package.json').read_text())['version'];assert version=='2.0.0-dev.7'
    build=ROOT/'.cache/adlx-build'
    receipt=json.loads((build/'bridge-build.json').read_text())
    assert receipt['mock'] is False and receipt['verifyOnly'] is False
    assert receipt['sourceSha256']==hashlib.sha256((ROOT/'native/adlx/bridge.cpp').read_bytes()).hexdigest()
    assert receipt['exeSha256']==hashlib.sha256((build/'bridge.exe').read_bytes()).hexdigest()
    copy(build/'bridge.exe',destination/'code/native/adlx/bridge.exe')
    # Sanitize build machine paths; no SDK headers/helper or driver DLL distributed.
    receipt={k:v for k,v in receipt.items() if k not in ('exe','compiler')}
    (destination/'code/native/adlx/bridge-build.json').write_text(json.dumps(receipt,indent=2)+'\n')
    copy(ROOT/'third_party/adlx-v1.4/ADLX SDK License Agreement.pdf',destination/'licenses/AMD-ADLX-SDK-License.pdf')
    copy(ROOT/'docs/windows-dev7/THIRD-PARTY-NOTICES.txt',destination/'licenses/THIRD-PARTY-NOTICES.txt')
    (destination/'code/BUNDLED-MONITORING.json').write_text(json.dumps({'schema':1,'version':version,'realOnly':True,
        'gpuReadOnly':True,'nativeSha256':receipt['exeSha256']},indent=2)+'\n',encoding='utf-8')
    files={file.relative_to(destination).as_posix():hashlib.sha256(file.read_bytes()).hexdigest()
           for file in sorted(destination.rglob('*')) if file.is_file()}
    manifest={'schema':1,'version':version,'pythonVersion':'3.13.3','origin':'snapshot_of_existing_validated_local_CPython_no_download',
              'stdlibPythonFiles':count,'files':files}
    text=json.dumps(manifest,indent=2)+'\n';(destination/'manifest.json').write_text(text,encoding='utf-8',newline='\n')
    pin={'schema':1,'version':version,'pythonVersion':'3.13.3','manifestSha256':hashlib.sha256(text.encode()).hexdigest()}
    (ROOT/'apps/windows-ui/monitoring-package.json').write_text(json.dumps(pin,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'ok':True,'version':version,'pythonVersion':'3.13.3','files':len(files),'stdlibPythonFiles':count,
                      'bytes':sum(f.stat().st_size for f in destination.rglob('*') if f.is_file()),'manifestSha256':pin['manifestSha256'],
                      'dependenciesInstalled':False,'generatedExecutablesRun':False}))


if __name__=='__main__':main()
