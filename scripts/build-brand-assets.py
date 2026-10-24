"""Build local SVG artwork traced from the user-approved reference, without fonts.

This is a vector recreation, not a recovered original master or original font.
No network, native bridge, credentials, device or application commands are used.
"""
from pathlib import Path
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'apps/android/app/src/main/assets/brand'

# Normalized angular contours from the large app-icon application in the image.
SYMBOL = ('M14 8 L14 84 L26 96 L92 96 L78 82 L43 82 L31 70 L31 25 Z',
          'M42 39 L42 64 L53 75 L70 75 Z')
# Geometric lettering reconstructed as contours; no dependency on installed fonts.
WORD = ('M0 0 H7 V31 H40 L47 38 H0 Z',
        'M68 0 H103 L110 7 V31 L103 38 H68 L61 31 V7 Z '
        'M71 7 L68 10 V28 L71 31 H100 L103 28 V10 L100 7 Z',
        'M124 38 V0 H131 L169 27 V0 H176 V38 H169 L131 11 V38 Z',
        'M197 0 H242 L238 7 H190 Z '
        'M190 14 H234 V21 H197 V31 H239 V38 H197 L190 31 Z')
LETTERS = {
    'S': 'M8 1 H1 V5 H7 V9 H0',
    'M': 'M0 10 V0 L4 6 L8 0 V10',
    'A': 'M0 10 L4 0 L8 10 M1.6 6 H6.4',
    'R': 'M0 10 V0 H6 L8 2 V4 L6 5 H0 M4 5 L8 10',
    'T': 'M0 0 H8 M4 0 V10',
    'O': 'M2 0 H6 L8 2 V8 L6 10 H2 L0 8 V2 Z',
}


def mark(transform=''):
    paths = ''.join(f'<path d="{p}"/>' for p in SYMBOL)
    return f'<g transform="{transform}" fill="none" stroke="#ff0033" stroke-width="2.2" stroke-linejoin="miter" stroke-miterlimit="5"><g filter="url(#neon)">{paths}</g>{paths}</g>'


def word(transform=''):
    return f'<g transform="{transform}" fill="#f5f5f7" fill-rule="evenodd">' + ''.join(f'<path d="{p}"/>' for p in WORD) + '</g>'


def subtitle(transform=''):
    positions = [('S', 0), ('M', 26), ('A', 52), ('R', 78), ('T', 104), ('R', 143), ('O', 169), ('O', 195), ('M', 221)]
    paths = ''.join(f'<path transform="translate({x} 0)" d="{LETTERS[c]}"/>' for c, x in positions)
    return f'<g transform="{transform}" fill="none" stroke="#ededf2" stroke-width="0.8" stroke-linejoin="round" stroke-linecap="round">{paths}</g>'


def horizontal():
    return mark('translate(10 4)') + word('translate(128 28)') + subtitle('translate(134.5 86)')


def compact(transform=''):
    return f'<g transform="{transform}">' + mark('translate(64 6) scale(1.08)') + word('translate(10 142) scale(0.91)') + subtitle('translate(17 198) scale(0.9)') + '</g>'


def artwork():
    return '''<defs>
  <filter id="neon" x="-50%" y="-50%" width="200%" height="200%" color-interpolation-filters="sRGB">
    <feGaussianBlur stdDeviation="1.35"/><feComponentTransfer><feFuncA type="linear" slope="0.6"/></feComponentTransfer>
  </filter>
  <linearGradient id="iconBase" x2="0.9" y2="1"><stop stop-color="#170b11"/><stop offset="0.6" stop-color="#09090d"/><stop offset="1" stop-color="#050609"/></linearGradient>
  <linearGradient id="iconEdge" x2="1" y2="1"><stop stop-color="#ff0033"/><stop offset="0.5" stop-color="#b20b2c"/><stop offset="1" stop-color="#ff1744"/></linearGradient>
</defs>'''


def svg(width, height, title, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
<title id="title">{title}</title>
<desc id="description">Lone Smart Room. Recriação vetorial baseada na referência aprovada; contorno angular vermelho neon e lettering geométrico.</desc>
{artwork()}
{body}
</svg>
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, help='Optional local reference to verify provenance; not copied by this script')
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    assets = {
        'logo-horizontal.svg': svg(390, 112, 'Lone Smart Room — logo horizontal', horizontal()),
        'logo-compact.svg': svg(240, 240, 'Lone Smart Room — logo compacta', compact()),
        'symbol.svg': svg(112, 112, 'Lone Smart Room — símbolo angular', mark('translate(3 2)')),
        'app-icon.svg': svg(256, 256, 'Lone Smart Room — ícone do aplicativo', '''<rect x="2" y="2" width="252" height="252" rx="57" fill="url(#iconBase)" stroke="url(#iconEdge)" stroke-width="2.5"/>
''' + mark('translate(38 30) scale(1.7)') + ''''''),
        'splash-screen.svg': svg(1080, 2400, 'Lone Smart Room — splash screen', '''<rect width="1080" height="2400" fill="#080a0d"/>
<g fill="none" stroke="#ff0033" stroke-width="2" opacity="0.65"><path d="M700 -80 L1110 330"/><path d="M-60 1850 L490 2400"/></g>
''' + compact('translate(132 755) scale(3.4)') + '''
<path d="M380 1640 H700" fill="none" stroke="#ff0033" stroke-width="3"/>'''),
    }
    for name, source in assets.items():
        (OUTPUT / name).write_text(source, encoding='utf-8', newline='\n')
    record = {'method': 'vector recreation from approved raster reference',
              'approval': 'reference approved; recreated assets awaiting visual approval',
              'primaryRed': '#ff0033', 'graphite': '#080a0d',
              'lettering': 'custom vector contours; original typeface not identified',
              'fontsRequired': False,
              'svgSha256': {name: hashlib.sha256((OUTPUT / name).read_bytes()).hexdigest() for name in assets}}
    if args.reference:
        record['referenceSha256'] = hashlib.sha256(args.reference.read_bytes()).hexdigest()
    (OUTPUT / 'brand-manifest.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print('Generated five SVG assets; no application or device operations performed.')


if __name__ == '__main__':
    main()
