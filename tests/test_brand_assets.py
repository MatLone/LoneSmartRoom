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
        reference = ROOT / 'docs/design/brand/reference/approved-reference.png'
        self.assertEqual(manifest['referenceSha256'], hashlib.sha256(reference.read_bytes()).hexdigest())
        self.assertEqual(len(manifest['svgSha256']), 5)
        for name, digest in manifest['svgSha256'].items():
            self.assertEqual(hashlib.sha256((ASSETS / name).read_bytes()).hexdigest(), digest)

    def test_generator_import_has_no_side_effects_and_uses_geometric_contours(self):
        spec = importlib.util.spec_from_file_location('brand_generator', ROOT / 'scripts/build-brand-assets.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        source = module.svg(390, 112, 'Lone Smart Room — logo horizontal', module.horizontal())
        self.assertEqual(source.encode(), (ASSETS / 'logo-horizontal.svg').read_bytes())


if __name__ == '__main__':
    unittest.main()
