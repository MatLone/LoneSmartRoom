"""Ensure local branding cannot introduce scripts or remote content in WebView."""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'apps/android/app/src/main/assets/brand'


class BrandAssetsTests(unittest.TestCase):
    def test_svg_is_local_static_artwork_without_embedded_code_or_fonts(self):
        for path in ASSETS.glob('*.svg'):
            with self.subTest(asset=path.name):
                tree = ET.fromstring(path.read_bytes())
                self.assertEqual(tree.tag, '{http://www.w3.org/2000/svg}svg')
                self.assertIn('viewBox', tree.attrib)
                for node in tree.iter():
                    self.assertNotIn(node.tag.split('}')[-1], {'script', 'foreignObject', 'image', 'text', 'style'})
                    self.assertFalse(any(key.lower().startswith('on') for key in node.attrib))
                    for key, value in node.attrib.items():
                        if key.split('}')[-1] == 'href':
                            self.assertTrue(value.startswith('#'))
                        self.assertNotIn('https:', value)
                        self.assertNotIn('http:', value)

    def test_reference_and_generated_asset_hashes_match_provenance(self):
        manifest = json.loads((ASSETS / 'brand-manifest.json').read_text(encoding='utf-8'))
        reference = ROOT / 'docs/design/brand/official-board-2026-10-24/reference/approved-board.png'
        self.assertEqual(manifest['referenceSha256'], hashlib.sha256(reference.read_bytes()).hexdigest())
        self.assertEqual(len(manifest['svgSha256']), 5)
        for name, digest in manifest['svgSha256'].items():
            self.assertEqual(hashlib.sha256((ASSETS / name).read_bytes()).hexdigest(), digest)

    def test_generator_import_has_no_side_effects_and_uses_geometric_contours(self):
        spec = importlib.util.spec_from_file_location('brand_generator', ROOT / 'scripts/build-official-brand.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        source = module.svg(390, 112, 'Lone Smart Room — marca principal', module.horizontal())
        self.assertEqual(source.encode(), (ASSETS / 'logo-horizontal.svg').read_bytes())

    def test_native_splash_is_resource_only_and_references_safe_artwork(self):
        res = ROOT / 'apps/android/app/src/main/res'
        ns = '{http://schemas.android.com/apk/res/android}'
        theme = ET.parse(res / 'values-v31/styles.xml').getroot().find('style')
        items = {node.get('name'): node.text for node in theme.findall('item')}
        self.assertEqual(items['android:windowSplashScreenAnimatedIcon'], '@drawable/lone_splash_safe')
        self.assertEqual(items['android:windowSplashScreenBackground'], '@color/ic_lone_background')
        launch = ET.parse(res / 'drawable/lone_launch_background.xml').getroot()
        self.assertEqual(launch.find('item').get(ns+'drawable'), '@color/ic_lone_background')

    def test_superseded_cube_not_referenced_by_active_brand_or_native_icons(self):
        html = (ASSETS.parent / 'index.html').read_text(encoding='utf-8')
        self.assertNotIn('nex-app-icon', html)
        self.assertNotIn('Hexágono NEX', html)
        for name in ('ic_launcher', 'ic_launcher_round'):
            xml = (ROOT / 'apps/android/app/src/main/res/mipmap-anydpi-v26' / (name+'.xml')).read_text()
            self.assertIn('@mipmap/ic_lone_foreground', xml)
            self.assertNotIn('ic_nex', xml)


if __name__ == '__main__':
    unittest.main()
