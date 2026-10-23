"""Regression guards for preserved behavior; no device or OS command execution."""
import hashlib
import json
import unittest
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from preservation_rules import reviewed_version_update


class BaselinePreservation(unittest.TestCase):
    def test_functional_sources_unchanged(self):
        records = json.loads((ROOT / 'docs/baseline-inventory.json').read_text())
        # Only explicitly reviewed integration/resource files may evolve in stage 2.
        integration_files = {
            'apps/android/app/src/main/java/com/lonesmartroom/app/MainActivity.kt',
            'apps/android/app/src/main/assets/index.html', 'apps/windows-ui/index.html',
            'apps/android/app/src/main/res/values/styles.xml',
        }
        extensions = {'.kt', '.js', '.html', '.css', '.cjs', '.xml', '.py'}
        for record in records:
            rel = Path(record['copy'])
            if rel.parts[0] not in {'apps', 'agent'} or rel.suffix not in extensions:
                continue
            if rel.as_posix() in integration_files:
                continue
            with self.subTest(file=str(rel)):
                current = (ROOT / rel).read_bytes()
                if hashlib.sha256(current).hexdigest() == record['sha256']:
                    continue
                originals = {
                    'apps/windows-ui/app.js': 'recovery/sources/electron-v1.4/app.js',
                    'apps/windows-ui/main.cjs': 'recovery/sources/electron-v1.4/main.cjs',
                    'apps/windows-ui/preload.cjs': 'recovery/sources/electron-v1.4/preload.cjs',
                    'apps/android/app/src/main/assets/app.js': 'recovery/sources/android-working/app/src/main/assets/app.js',
                }
                self.assertIn(rel.as_posix(), originals)
                baseline = (ROOT / originals[rel.as_posix()]).read_bytes()
                self.assertEqual(hashlib.sha256(baseline).hexdigest(), record['sha256'])
                self.assertEqual(current, reviewed_version_update(rel.as_posix(), baseline))

    def test_shared_ui_has_not_diverged(self):
        for name in ('app.js', 'index.html', 'styles.css', 'app-version.js', 'app-launch.js', 'agent-status.js'):
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

    def test_native_wake_bridge_unchanged(self):
        source = (ROOT / 'apps/android/app/src/main/java/com/lonesmartroom/app/MainActivity.kt').read_bytes()
        bridge = source.split(b'    inner class WakeBridge {', 1)[1].split(b'    override fun onDestroy()', 1)[0]
        reference = json.loads((ROOT / 'docs/wol-preservation.json').read_text())
        self.assertEqual(hashlib.sha256(bridge).hexdigest(), reference['wakeBridgeSha256'])


if __name__ == '__main__':
    unittest.main()
