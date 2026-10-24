"""Inspect compiled launcher resources without ADB, installation or signing keys."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import struct
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk-root', type=Path, required=True)
    args = parser.parse_args()
    tool = args.sdk_root / 'build-tools/35.0.0/aapt2.exe'
    apk = ROOT / '.cache/artifacts/android/LoneSmartRoom-2.0.0-dev.4-v18.apk'
    def dump(*arguments):
        return subprocess.check_output([str(tool), 'dump', *arguments, str(apk)], text=True)
    resources = dump('resources')
    manifest = dump('xmltree', '--file', 'AndroidManifest.xml')
    ids = {name: re.search(r'resource (0x[0-9a-f]+) ' + re.escape(name) + r'\b', resources)[1]
           for name in ('mipmap/ic_launcher', 'mipmap/ic_launcher_round',
                        'mipmap/ic_nex_foreground', 'color/ic_nex_background')}
    assert re.search(r':icon\([^)]*\)=@' + ids['mipmap/ic_launcher'], manifest)
    assert re.search(r':roundIcon\([^)]*\)=@' + ids['mipmap/ic_launcher_round'], manifest)
    assert ':usesCleartextTraffic(0x010104ec)=false' in manifest
    assert ':allowBackup(0x01010280)=false' in manifest
    assert re.search(r':versionCode\([^)]*\)=18(?:\n|$)', manifest)
    assert re.search(r':versionName\([^)]*\)="2\.0\.0-dev\.4"', manifest)
    assert '#ff080a0d' in resources
    inspected = []
    with zipfile.ZipFile(apk) as archive:
        for name in ('ic_launcher', 'ic_launcher_round'):
            rel = 'res/mipmap-anydpi-v26/' + name + '.xml'
            tree = dump('xmltree', '--file', rel)
            assert 'E: adaptive-icon' in tree
            assert '@' + ids['mipmap/ic_nex_foreground'] in tree
            assert '@' + ids['color/ic_nex_background'] in tree
            inspected.append({'path': rel, 'sha256': hashlib.sha256(archive.read(rel)).hexdigest()})
        for density, scale in (('mdpi', 1), ('hdpi', 1.5), ('xhdpi', 2), ('xxhdpi', 3), ('xxxhdpi', 4)):
            for name, dp in (('ic_launcher', 48), ('ic_launcher_round', 48), ('ic_nex_foreground', 108)):
                rel = f'res/mipmap-{density}-v4/{name}.png'
                raw = archive.read(rel)
                assert raw[:8] == b'\x89PNG\r\n\x1a\n'
                size = struct.unpack('>II', raw[16:24])
                assert size == (int(dp*scale), int(dp*scale))
                inspected.append({'path': rel, 'pixels': list(size), 'sha256': hashlib.sha256(raw).hexdigest()})
        # The source house drawable stays recoverable, but neither manifest icon references it.
        header = archive.read('assets/index.html').split(b'<header', 1)[1].split(b'</header>', 1)[0]
        assert b'logo-header-small.svg' in header and b'logo-horizontal.svg' in header
    result = {'ok': True, 'apkSha256': hashlib.sha256(apk.read_bytes()).hexdigest(),
              'compiledManifestUsesNexMipmaps': True, 'headerLogoPreserved': True,
              'resourceIds': ids, 'inspectedResources': inspected, 'installedOnSamsung': False}
    output = ROOT / '.cache/validation/nex-icon-dev4/apk-icon-inspection.json'
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('PASS: 17 compiled launcher resources, five densities, adaptive references and original header verified in signed APK.')


if __name__ == '__main__':
    main()
