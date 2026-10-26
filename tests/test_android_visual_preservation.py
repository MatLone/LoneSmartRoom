"""UI-only migration must not mutate the installed app's native/security contract."""
import hashlib
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]

class AndroidVisualPreservation(unittest.TestCase):
    def test_functional_sources_resources_and_brand_match_pre_migration_checkpoint(self):
        pins=json.loads((ROOT/'tests/fixtures/android-functional-baseline.json').read_text(encoding='utf-8'))
        self.assertEqual(pins['checkpoint'],'29d12a6')
        for name,digest in pins['files'].items():
            with self.subTest(file=name):
                self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest)

    def test_native_identity_and_network_policy_unchanged(self):
        manifest=ET.parse(ROOT/'apps/android/app/src/main/AndroidManifest.xml').getroot()
        android='{http://schemas.android.com/apk/res/android}'
        application=manifest.find('application')
        self.assertEqual(application.get(android+'usesCleartextTraffic'),'false')
        source=(ROOT/'apps/android/app/build.gradle.kts').read_text(encoding='utf-8')
        self.assertIn('applicationId = "com.lonesmartroom.app"',source)
        html=(ROOT/'apps/android/app/src/main/assets/index.html').read_text(encoding='utf-8')
        self.assertIn("connect-src 'none'",html)
        self.assertIn('href="windows-family.css"',html)
        self.assertNotIn('diagnostics',html)

    def test_offline_mobile_sensors_are_not_fabricated(self):
        shell=(ROOT/'apps/android/app/src/main/assets/mobile-shell.js').read_text(encoding='utf-8')
        self.assertIn('Indisponível no Android',shell)
        self.assertIn('const unavailableRow',shell)
        self.assertNotIn('Math.random',shell)
        self.assertNotIn('fetch(',shell)
        self.assertNotIn('WebSocket',shell)

if __name__=='__main__':unittest.main()
