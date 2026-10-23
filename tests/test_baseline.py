"""Regression guards for preserved behavior; no device or OS command execution."""
import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BaselinePreservation(unittest.TestCase):
    def test_functional_sources_unchanged(self):
        records = json.loads((ROOT / 'docs/baseline-inventory.json').read_text())
        # Build configuration may evolve; preserve every runtime source byte.
        extensions = {'.kt', '.js', '.html', '.css', '.cjs', '.xml', '.py'}
        for record in records:
            rel = Path(record['copy'])
            if rel.parts[0] not in {'apps', 'agent'} or rel.suffix not in extensions:
                continue
            with self.subTest(file=str(rel)):
                self.assertEqual(hashlib.sha256((ROOT / rel).read_bytes()).hexdigest(), record['sha256'])

    def test_shared_ui_has_not_diverged(self):
        for name in ('app.js', 'index.html', 'styles.css'):
            self.assertEqual((ROOT / 'apps/windows-ui' / name).read_bytes(),
                             (ROOT / 'apps/android/app/src/main/assets' / name).read_bytes())

    def test_android_identity_and_security(self):
        build = (ROOT / 'apps/android/app/build.gradle.kts').read_text()
        self.assertIn('applicationId = "com.lonesmartroom.app"', build)
        manifest = ET.parse(ROOT / 'apps/android/app/src/main/AndroidManifest.xml').getroot()
        ns = '{http://schemas.android.com/apk/res/android}'
        self.assertEqual(manifest.find('application').get(ns + 'usesCleartextTraffic'), 'false')
        self.assertEqual(manifest.find('application').get(ns + 'allowBackup'), 'false')

    def test_wol_storage_contract_preserved(self):
        source = (ROOT / 'apps/android/app/src/main/assets/app.js').read_text(encoding='utf-8')
        self.assertIn('lone-wol-settings-v1', source)
        self.assertIn('window.LoneAndroid.sendWake', source)
        self.assertIn('window.onLoneWakeResult', source)


if __name__ == '__main__':
    unittest.main()
