"""Inspect compiled official-brand resources; never reads devices or signing keys."""
from pathlib import Path
import argparse, hashlib, json, re, struct, subprocess, zipfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'.cache/validation/official-brand-dev5/apk-inspection.json')
    args=parser.parse_args()
    build=(ROOT/'apps/android/app/build.gradle.kts').read_text()
    code=re.search(r'versionCode\s*=\s*(\d+)',build)[1]
    version=re.search(r'versionName\s*=\s*"([^"]+)"',build)[1]
    apk=ROOT/f'.cache/artifacts/android/LoneSmartRoom-{version}-v{code}.apk'
    tool=args.sdk_root/'build-tools/35.0.0/aapt2.exe'
    def dump(*arguments):
        return subprocess.check_output([str(tool),'dump',*arguments,str(apk)],text=True)
    resources=dump('resources');manifest=dump('xmltree','--file','AndroidManifest.xml')
    names=('mipmap/ic_launcher','mipmap/ic_launcher_round','mipmap/ic_lone_foreground',
           'color/ic_lone_background','drawable/lone_splash_safe','drawable/lone_splash_lockup','drawable/lone_launch_background')
    ids={name:re.search(r'resource (0x[0-9a-f]+) '+re.escape(name)+r'\b',resources)[1] for name in names}
    assert re.search(r':icon\([^)]*\)=@'+ids['mipmap/ic_launcher'],manifest)
    assert re.search(r':roundIcon\([^)]*\)=@'+ids['mipmap/ic_launcher_round'],manifest)
    assert ':usesCleartextTraffic(0x010104ec)=false' in manifest
    assert ':allowBackup(0x01010280)=false' in manifest
    assert re.search(r':versionCode\([^)]*\)='+code+r'(?:\n|$)',manifest)
    assert re.search(r':versionName\([^)]*\)="'+re.escape(version)+'"',manifest)
    # AAPT2 prints framework attribute IDs (checked against local SDK android.R$attr),
    # while resolved app resource values are printed by name in the style table.
    theme=resources.split(' style/Theme.LoneSmartRoom',1)[1].split('\n    resource ',1)[0]
    v31=theme.split('(v31)',1)[1]
    assert '0x0101062c=@color/ic_lone_background' in v31
    assert '0x0101062d=@drawable/lone_splash_safe' in v31
    assert '0x01010630=@color/ic_lone_background' in v31
    assert theme.count('0x01010054=@drawable/lone_launch_background')==3
    assert '#ff141720' not in theme
    assert 'ic_nex_foreground' not in resources
    inspected=[]
    with zipfile.ZipFile(apk) as archive:
        for name in ('ic_launcher','ic_launcher_round'):
            rel='res/mipmap-anydpi-v26/'+name+'.xml';tree=dump('xmltree','--file',rel)
            assert 'E: adaptive-icon' in tree
            for ref in ('mipmap/ic_lone_foreground','color/ic_lone_background'):assert '@'+ids[ref] in tree
            inspected.append({'path':rel,'sha256':hashlib.sha256(archive.read(rel)).hexdigest()})
        for density,scale in (('mdpi',1),('hdpi',1.5),('xhdpi',2),('xxhdpi',3),('xxxhdpi',4)):
            for name,dp in (('ic_launcher',48),('ic_launcher_round',48),('ic_lone_foreground',108)):
                rel=f'res/mipmap-{density}-v4/{name}.png';raw=archive.read(rel)
                assert raw[:8]==b'\x89PNG\r\n\x1a\n'
                size=struct.unpack('>II',raw[16:24]);assert size==(int(dp*scale),int(dp*scale))
                inspected.append({'path':rel,'pixels':list(size),'sha256':hashlib.sha256(raw).hexdigest()})
        for name in ('lone_splash_safe','lone_splash_lockup'):
            rel=f'res/drawable-nodpi-v4/{name}.png'
            raw=archive.read(rel);assert raw.startswith(b'\x89PNG')
            inspected.append({'path':rel,'pixels':list(struct.unpack('>II',raw[16:24])),'sha256':hashlib.sha256(raw).hexdigest()})
        launch=dump('xmltree','--file','res/drawable/lone_launch_background.xml')
        assert '@'+ids['drawable/lone_splash_lockup'] in launch
        inspected.append({'path':'res/drawable/lone_launch_background.xml'})
        header=archive.read('assets/index.html')
        assert b'nex-app-icon' not in header and b'lone-app-icon.png' in header
        assert b'logo-header-small.svg' in header and b'logo-horizontal.svg' in header
    result={'ok':True,'version':version,'versionCode':int(code),'apkSha256':hashlib.sha256(apk.read_bytes()).hexdigest(),
            'compiledAdaptiveIconsAndNativeSplashVerified':True,'resourceIds':ids,'inspectedResources':inspected,
            'installedOnSamsung':False,'deviceAccess':False}
    out=args.output
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'PASS: {len(inspected)} compiled icon/splash resources and system splash attributes verified; no device access.')


if __name__=='__main__':main()
