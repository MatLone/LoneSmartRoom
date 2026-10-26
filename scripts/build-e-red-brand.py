"""Authorized color-only wordmark update; Windows icon remains the exact source.

Reference masters are archived at checkpoint 098d1a2. No fonts are reconstructed,
geometry edited, device accessed, or historical generator/export rewritten.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs/design/brand/e-red-windows-icon-2026-10-26'
REF=DOCS/'reference'
BRAND=ROOT/'apps/android/app/src/main/assets/brand'
WINDOWS=ROOT/'apps/windows-ui/assets/brand'
RED='#ff153f'
E_PATH=('M197 0 H242 L238 7 H190 Z '
        'M190 14 H234 V21 H197 V31 H239 V38 H197 L190 31 Z')


def red_e(source):
    original=f'<path d="{E_PATH}"/>'
    if source.count(original)!=1:
        raise ValueError('expected_one_original_E')
    return source.replace(original,f'<path fill="{RED}" d="{E_PATH}"/>',1)


def main():
    pins=json.loads((REF/'before-sha256.json').read_text(encoding='utf-8'))
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    for name in ('windows-icon.svg','windows-icon.png','windows-icon.ico'):
        assert digest(WINDOWS/name)==pins[(WINDOWS/name).relative_to(ROOT).as_posix()]
    for name in ('logo-horizontal.svg','logo-header-small.svg','logo-compact.svg','splash-screen.svg'):
        result=red_e((REF/name).read_text(encoding='utf-8'))
        (BRAND/name).write_text(result,encoding='utf-8',newline='\n')
        if (WINDOWS/name).is_file():
            (WINDOWS/name).write_text(result,encoding='utf-8',newline='\n')
    # The active Android icon is an exact copy of the existing Windows source.
    shutil.copyfile(WINDOWS/'windows-icon.svg',BRAND/'app-icon.svg')
    shutil.copyfile(WINDOWS/'windows-icon.png',BRAND/'lone-app-icon.png')
    manifest=json.loads((REF/'brand-manifest.json').read_text(encoding='utf-8'))
    manifest.update({'wordColors':{'L':'original_white','O':'original_white','N':'original_white','E':RED},
                     'primaryRed':RED,'symbolGeometryChanged':False,
                     'iconSource':'apps/windows-ui/assets/brand/windows-icon.svg',
                     'iconSourceSha256':digest(WINDOWS/'windows-icon.svg'),
                     'approval':'user-authorized E-only color and exact Windows icon; exports awaiting visual review'})
    manifest['svgSha256']={name:digest(BRAND/name) for name in manifest['svgSha256']}
    (BRAND/'brand-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
    header=json.loads((REF/'header-small-manifest.json').read_text(encoding='utf-8'))
    header.update({'variantSha256':digest(BRAND/'logo-header-small.svg'),'wordEColor':RED,'geometryChanged':False})
    (BRAND/'header-small-manifest.json').write_text(json.dumps(header,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('PASS: only E recolored in four wordmarks; Windows headers synchronized; original Windows icon copied exactly.')


if __name__=='__main__':main()
