"""Offline payload + imports through the EXISTING interpreter; no bundled EXE runs.

The audit hook rejects native sensor calls, sockets, Registry and process creation.
This is not a physical validation of the packaged interpreter/application.
"""
import ctypes  # Known standard-library bootstrap only, before audit hook.
import hashlib
import importlib
import json
from pathlib import Path
import runpy
import struct
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
PAYLOAD=ROOT/'.cache/windows-monitoring-runtime/dev8'


def main():
    checks=0
    def check(value):
        nonlocal checks
        assert value
        checks+=1
    manifest=json.loads((PAYLOAD/'manifest.json').read_text())
    pin=json.loads((ROOT/'apps/windows-ui/monitoring-package.json').read_text())
    check(hashlib.sha256((PAYLOAD/'manifest.json').read_bytes()).hexdigest()==pin['manifestSha256'])
    check(manifest['version']==pin['version']=='2.0.0-dev.8')
    check(manifest['pythonVersion']==pin['pythonVersion']=='3.13.3')
    check(set(manifest['files'])=={p.relative_to(PAYLOAD).as_posix() for p in PAYLOAD.rglob('*') if p.is_file() and p.name!='manifest.json'})
    native=[]
    for name,digest in manifest['files'].items():
        file=PAYLOAD/name;data=file.read_bytes()
        check(hashlib.sha256(data).hexdigest()==digest)
        check(not file.is_symlink() and not {'..','tests','site-packages','agent','.runtime','.git'}&set(Path(name).parts))
        check(file.suffix.lower() not in ('.pem','.key','.crt','.pfx','.p12','.db','.keystore','.jks'))
        if file.suffix in ('.exe','.dll','.pyd'):
            pe=struct.unpack_from('<I',data,0x3c)[0]
            check(data[pe:pe+4]==b'PE\0\0' and struct.unpack_from('<H',data,pe+4)[0]==0x8664)
            native.append(name)
        if name.startswith('code/'):
            check(not any(s in data for s in (b'BEGIN PRIVATE KEY',b'BEGIN RSA PRIVATE KEY')))
            source=ROOT/('/'.join(Path(name).parts[1:]))
            if source.is_file():check(hashlib.sha256(source.read_bytes()).hexdigest()==digest)
    base=Path(sys._base_executable).resolve().parent
    for name in [n for n in native if n.startswith('runtime/')]+['runtime/LICENSE.txt']:
        original=base/Path(name).relative_to('runtime')
        check(original.is_file() and original.read_bytes()==(PAYLOAD/name).read_bytes())
    check((PAYLOAD/'runtime/python313._pth').read_text()=='python313.zip\nDLLs\n.\n')
    receipt=json.loads((PAYLOAD/'code/native/adlx/bridge-build.json').read_text())
    check(receipt['sourceSha256']==hashlib.sha256((ROOT/'native/adlx/bridge.cpp').read_bytes()).hexdigest())
    check(receipt['exeSha256']==hashlib.sha256((PAYLOAD/'code/native/adlx/bridge.exe').read_bytes()).hexdigest())
    check((PAYLOAD/'code/native/adlx/bridge.exe').read_bytes()==(ROOT/'.cache/adlx-build/bridge.exe').read_bytes())
    check(not any('amdadlx64.dll' in p.lower() or p.endswith('.h') for p in manifest['files']))
    check((PAYLOAD/'licenses/AMD-ADLX-SDK-License.pdf').read_bytes()==(ROOT/'third_party/adlx-v1.4/ADLX SDK License Agreement.pdf').read_bytes())
    members=0
    with zipfile.ZipFile(PAYLOAD/'runtime/python313.zip') as archive:
        check(archive.testzip() is None)
        for info in archive.infolist():
            check(info.compress_type==zipfile.ZIP_STORED and info.filename.endswith('.py'))
            check(not {'tests','test','site-packages','__pycache__','ensurepip','venv','idlelib','tkinter'}&set(Path(info.filename).parts))
            check(not Path(info.filename).is_absolute() and '..' not in Path(info.filename).parts)
            data=archive.read(info)
            check(data==(base/'Lib'/info.filename).read_bytes())
            compile(data,info.filename,'exec');members+=1
    check(members==manifest['stdlibPythonFiles'])
    # No vendor executable is invoked: use this existing Python with staged search paths.
    sys.path[:]=[str(PAYLOAD/'code'),str(PAYLOAD/'runtime/python313.zip'),str(PAYLOAD/'runtime/DLLs'),str(PAYLOAD/'runtime')]
    def deny(event,args):
        if event.startswith(('socket.','winreg.')) or event in ('subprocess.Popen','os.system','os.startfile','os.startfile/2',
                'ctypes.dlopen','ctypes.call_function','os.posix_spawn','os.exec'):
            raise RuntimeError('Physical operations forbidden in package inspection')
    sys.addaudithook(deny)
    modules=[]
    for file in sorted((PAYLOAD/'code/monitoring').glob('*.py')):
        if file.stem=='__init__':continue
        module=importlib.import_module('monitoring.'+file.stem)
        check(Path(module.__file__).is_relative_to(PAYLOAD));modules.append(module.__name__)
    for file in sorted((PAYLOAD/'code/scripts').glob('*.py')):
        runpy.run_path(str(file),run_name='__package_inspection__');checks+=1
    from monitoring.gpu_development import validate_gpu_mode
    validate_gpu_mode(PAYLOAD/'code',True,True,False,None);checks+=1
    result={'ok':True,'checks':checks,'files':len(manifest['files']),'pythonVersion':manifest['pythonVersion'],
        'version':manifest['version'],'stdlibPythonFiles':members,'importedMonitoringModules':modules,
        'manifestSha256':pin['manifestSha256'],'packagedExecutablesRun':False,'realSensors':False,
        'dependenciesInstalled':False,'nativeCallsAllowed':False}
    out=ROOT/'.cache/validation/windows-dev8/runtime-inspection.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))


if __name__=='__main__':main()
