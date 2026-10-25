"""Build only with existing MSVC/Windows SDK. Never loads ADLX or runs output."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
MSVC=Path('C:/Program Files (x86)/Microsoft Visual Studio/2019/BuildTools/VC/Tools/MSVC/14.29.30133')
SDK=Path('C:/Program Files (x86)/Windows Kits/10');VERSION='10.0.19041.0'


def main():
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group();group.add_argument('--mock',action='store_true');group.add_argument('--verify',action='store_true');args=parser.parse_args()
    third=ROOT/'third_party/adlx-v1.4';manifest=json.loads((third/'manifest.json').read_text())
    assert manifest['commit']=='66557d410ce4c463f5f7106597d94f53dd84bc82'
    for name,entry in manifest['files'].items():
        assert hashlib.sha256((third/name).read_bytes()).hexdigest()==entry['sha256'],'SDK integrity mismatch'
    compiler=MSVC/'bin/Hostx64/x64/cl.exe';assert compiler.is_file(),'No compiler; installation not authorized'
    out=ROOT/'.cache/adlx-build';out.mkdir(parents=True,exist_ok=True);stem='bridge-mock' if args.mock else 'bridge-verify' if args.verify else 'bridge';target=out/(stem+'.exe')
    env=dict(os.environ);env['INCLUDE']=';'.join(map(str,[MSVC/'include']+[SDK/'Include'/VERSION/n for n in ('ucrt','shared','um')]))
    env['LIB']=';'.join(map(str,[MSVC/'lib/x64']+[SDK/'Lib'/VERSION/n/'x64' for n in ('ucrt','um')]))
    command=[str(compiler),'/nologo','/std:c++17','/EHsc','/MT','/W4','/WX','/external:W0',
        '/external:I'+str(third/'SDK/Include'),'/I'+str(third/'SDK/Include'),'/Fo'+str(out/(stem+'.obj')),'/Fe'+str(target),str(ROOT/'native/adlx/bridge.cpp')]
    if args.mock:command.append('/DLONE_ADLX_MOCK')
    if args.verify:command.append('/DLONE_ADLX_VERIFY')
    command+=['/link','/DYNAMICBASE','/NXCOMPAT','/HIGHENTROPYVA','/DEPENDENTLOADFLAG:0x800','/MACHINE:X64','wintrust.lib','bcrypt.lib','psapi.lib','advapi32.lib']
    result=subprocess.run(command,cwd=out,env=env,text=True,capture_output=True,shell=False)
    (out/(stem+'-build.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
    if result.returncode:print(result.stdout+result.stderr);return result.returncode
    receipt={'ok':True,'mock':args.mock,'verifyOnly':args.verify,'exe':str(target),'exeSha256':hashlib.sha256(target.read_bytes()).hexdigest(),
        'sourceSha256':hashlib.sha256((ROOT/'native/adlx/bridge.cpp').read_bytes()).hexdigest(),'sdkCommit':manifest['commit'],
        'compiler':str(compiler),'newDependenciesInstalled':False,'outputExecuted':False}
    (out/(stem+'-build.json')).write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt));return 0


if __name__=='__main__':raise SystemExit(main())
