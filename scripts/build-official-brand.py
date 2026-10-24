"""Recreate the approved 2026-10-24 board as deterministic, local SVG artwork.

No raster tracing service, fonts, devices, bridges or application commands.
The earlier recreations remain archived and reproducible with their old scripts.
"""
from pathlib import Path
import hashlib
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / 'apps/android/app/src/main/assets/brand'
DOCS = ROOT / 'docs/design/brand/official-board-2026-10-24'
REFERENCE = DOCS / 'reference/approved-board.png'
spec = importlib.util.spec_from_file_location('previous_brand', ROOT / 'scripts/build-brand-assets.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)

# New board, SYMBOL panel: square-ended 45-degree contours and chamfered bends.
# Coordinates normalized from the supplied board, not the superseded cube.
SYMBOL = ('M8 6 V96 L23 111 H106 L89 94 H41 L28 81 V27 Z',
          'M41 43 V73 L52 84 H75 Z')


def definitions():
    return '''<defs>
<linearGradient id="markRed" x1="0" y1="0" x2="1" y2="0.7"><stop stop-color="#ff3654"/><stop offset="0.32" stop-color="#ff6680"/><stop offset="0.48" stop-color="#ff173d"/><stop offset="1" stop-color="#ff0033"/></linearGradient>
<linearGradient id="wordWhite" x2="0" y2="1"><stop stop-color="#ffffff"/><stop offset="1" stop-color="#dedee4"/></linearGradient>
<radialGradient id="baseGlow"><stop stop-color="#360812"/><stop offset="0.68" stop-color="#100a0e"/><stop offset="1" stop-color="#080a0d"/></radialGradient>
<filter id="neon" x="-70%" y="-70%" width="240%" height="240%" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="2.1"/></filter>
</defs>'''


def mark(transform=''):
    paths = ''.join(f'<path d="{p}"/>' for p in SYMBOL)
    return f'<g transform="{transform}" fill="none" stroke="url(#markRed)" stroke-width="4.2" stroke-linejoin="miter" stroke-miterlimit="5"><g filter="url(#neon)" opacity="0.34">{paths}</g>{paths}</g>'


def word(transform=''):
    return f'<g transform="{transform}" fill="url(#wordWhite)" fill-rule="evenodd">' + ''.join(f'<path d="{p}"/>' for p in previous.WORD) + '</g>'


def subtitle(transform=''):
    return previous.subtitle(transform)


def horizontal():
    return mark('translate(0 0) scale(0.9)') + word('translate(125 25)') + subtitle('translate(131 84) scale(1 1.3)')


def small_header():
    return mark('translate(0 0) scale(0.78)') + word('translate(108 20) scale(0.98)') + subtitle('translate(114 75) scale(1 1.3)')


def stacked():
    return mark('translate(71 13) scale(1.07)') + word('translate(7 157)') + subtitle('translate(13 207) scale(1 1.3)')


def svg(width, height, title, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
<title id="title">{title}</title>
<desc id="description">Recriação vetorial baseada na prancha oficial aprovada em 24/10/2026; símbolo angular vermelho, LONE e SMART ROOM.</desc>
{definitions()}
{body}
</svg>
'''


def main():
    assert REFERENCE.is_file(), 'Approved board must be preserved before generation'
    BRAND.mkdir(parents=True, exist_ok=True)
    assets = {
        'logo-horizontal.svg': svg(390, 112, 'Lone Smart Room — marca principal', horizontal()),
        'logo-compact.svg': svg(256, 240, 'Lone Smart Room — composição vertical', stacked()),
        'symbol.svg': svg(116, 120, 'Lone Smart Room — símbolo angular', mark()),
        'app-icon.svg': svg(256, 256, 'Lone Smart Room — ícone Android', '<rect x="2" y="2" width="252" height="252" rx="55" fill="url(#baseGlow)" stroke="#ff0033" stroke-width="1.5"/>' + '<g transform="translate(16 12) scale(0.875)">' + stacked() + '</g>'),
        'splash-screen.svg': svg(1080, 2400, 'Lone Smart Room — splash completa', '<rect width="1080" height="2400" fill="#080a0d"/><g stroke="#ff0033" stroke-width="2" fill="none"><path d="M680 -30 L1080 370"/><path d="M-20 1890 L490 2400 M-20 1930 L450 2400"/></g><g transform="translate(270 905) scale(2.1)">' + stacked() + '</g><path d="M420 1610 H660" fill="none" stroke="#ff0033" stroke-width="3"/>'),
    }
    for name, source in assets.items():
        (BRAND / name).write_text(source, encoding='utf-8', newline='\n')
    header = svg(360, 100, 'Lone Smart Room — cabeçalho legível', small_header())
    (BRAND / 'logo-header-small.svg').write_text(header, encoding='utf-8', newline='\n')
    manifest = {'method': 'deterministic vector recreation from new official board',
                'reference': REFERENCE.relative_to(ROOT).as_posix(),
                'referenceSha256': hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),
                'approval': 'official board approved; derived exports awaiting visual inspection',
                'primaryRed': '#ff0033', 'graphite': '#080a0d', 'fontsRequired': False,
                'svgSha256': {name: hashlib.sha256(source.encode()).hexdigest() for name, source in assets.items()}}
    (BRAND / 'brand-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8', newline='\n')
    header_record = {'source': 'new official board', 'subtitleRetained': True, 'viewBox': [360, 100],
                     'subtitleHeightUnits': 13, 'renderedWidthCss': {'default': 244, 'narrow': 224},
                     'minimumSubtitleHeightCss': 13*224/360,
                     'variantSha256': hashlib.sha256(header.encode()).hexdigest(),
                     'olderVectorsArchivedAt': (DOCS/'previous-dev4').relative_to(ROOT).as_posix()}
    (BRAND / 'header-small-manifest.json').write_text(json.dumps(header_record,indent=2)+'\n',encoding='utf-8',newline='\n')
    (DOCS / 'android-adaptive-foreground.svg').write_text(svg(256,240,'Foreground adaptativo sem moldura',stacked()),encoding='utf-8',newline='\n')
    (DOCS / 'windows-icon.svg').write_text(svg(256,256,'Lone Smart Room — ícone Windows','<rect x="2" y="2" width="252" height="252" rx="26" fill="url(#baseGlow)" stroke="#ff234c" stroke-width="1.5"/>'+mark('translate(50 42) scale(1.4)')),encoding='utf-8',newline='\n')
    print('PASS: official board vectors, legible header, frame-free foreground and Windows icon generated.')


if __name__ == '__main__':
    main()
