"""Derive the small-header variant without rewriting the original brand files."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / 'apps/android/app/src/main/assets/brand'


def main():
    manifest = json.loads((BRAND / 'brand-manifest.json').read_text())
    originals = {name: hashlib.sha256((BRAND / name).read_bytes()).hexdigest()
                 for name in manifest['svgSha256']}
    if originals != manifest['svgSha256']:
        raise SystemExit('Original brand hashes differ; review before deriving a variant.')
    source = (BRAND / 'logo-horizontal.svg').read_text(encoding='utf-8')
    # Reuse the exact original symbol and word paths/styles; omit the fine subtitle.
    prefix, body = source.split('</defs>\n', 1)
    body = body.split('<g transform="translate(134.5 86)"', 1)[0]
    body = body.replace('translate(128 28)', 'translate(128 37)', 1)
    prefix = prefix.replace('Lone Smart Room — logo horizontal',
                            'Lone Smart Room — cabeçalho pequeno, símbolo e LONE')
    result = prefix + '</defs>\n' + body + '\n</svg>\n'
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    paths = lambda text: [p.attrib['d'] for p in ET.fromstring(text).findall('.//svg:path', ns)]
    assert paths(result) == paths(source)[:8]
    target = BRAND / 'logo-header-small.svg'
    target.write_text(result, encoding='utf-8', newline='\n')
    record = {
        'purpose': 'Small Android headers: symbol and LONE, no unreadable subtitle',
        'source': 'logo-horizontal.svg', 'sourceSha256': originals['logo-horizontal.svg'],
        'variantSha256': hashlib.sha256(target.read_bytes()).hexdigest(),
        'originalAssetsUnchanged': originals,
        'symbolGeometryChanged': False, 'wordGeometryChanged': False,
        'compositionChange': 'Remove subtitle and vertically center original word at y=37',
        'fullLogoRetainedFor': ['splash', 'larger layouts'],
    }
    (BRAND / 'header-small-manifest.json').write_text(
        json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
    assert originals == {name: hashlib.sha256((BRAND / name).read_bytes()).hexdigest()
                         for name in originals}
    print('PASS: small-header variant generated; original five vectors and symbol paths preserved.')


if __name__ == '__main__':
    main()
