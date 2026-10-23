"""Verify and preserve an opt-in signed APK. Never accesses a device or keystore."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import zipfile
from preservation_rules import version_only_update

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = '02c5b46ab301cdfb7a1d858588b1122eb00be1bfd12349ea9f0d1e40a53d1bc8'
BASE_HASH = 'ea0c3a74f859f97e7d4e3a80d23525e2137a3d1add94f21d09e1746611e245d7'


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk-root', required=True, type=Path)
    args = parser.parse_args()
    tools = args.sdk_root / 'build-tools/35.0.0'
    apk = ROOT / 'apps/android/app/build/outputs/apk/debug/app-debug.apk'
    recovery = ROOT / 'recovery/artifacts/android/intermediates/apk/debug/app-debug.apk'
    android = ROOT / 'apps/android/app/src/main'
    baseline = ROOT / 'recovery/sources/android-working/app/src/main'

    def certificate(path):
        result = subprocess.run([str(tools / 'apksigner.bat'), 'verify', '--verbose', '--print-certs', str(path)],
                                capture_output=True, text=True)
        require(result.returncode == 0, 'APK signature verification failed')
        pins = re.findall(r'Signer #\d+ certificate SHA-256 digest: ([0-9a-f]{64})', result.stdout)
        require(pins == [EXPECTED], 'Signer mismatch: incompatible APK; do not install')
        return result.stdout

    verification = certificate(apk)
    v2_verified = 'Verified using v2 scheme (APK Signature Scheme v2): true' in verification
    require(v2_verified, 'APK v2 signature required for the supported Android versions')
    certificate(recovery)
    require(digest(recovery) == BASE_HASH, 'Functional recovery APK changed')
    result = subprocess.run([str(tools / 'aapt.exe'), 'dump', 'badging', str(apk)],
                            capture_output=True, text=True)
    require(result.returncode == 0, 'Cannot inspect APK manifest')
    package = re.search(r"package: name='([^']+)' versionCode='([^']+)' versionName='([^']+)'", result.stdout)
    require(package is not None, 'Missing APK package metadata')
    build = (ROOT / 'apps/android/app/build.gradle.kts').read_text()
    version_code = re.search(r'versionCode\s*=\s*(\d+)', build)[1]
    version_name = re.search(r'versionName\s*=\s*"([0-9][0-9A-Za-z.+_-]{0,63})"', build)[1]
    require(package.groups() == ('com.lonesmartroom.app', version_code, version_name) and int(version_code) > 15, 'Unexpected package/version')
    for rel in ('java/com/lonesmartroom/app/WakeOnLan.kt', 'AndroidManifest.xml'):
        require((android / rel).read_bytes() == (baseline / rel).read_bytes(), 'Preservation mismatch: ' + rel)
    require((android / 'assets/app.js').read_bytes() == version_only_update((baseline / 'assets/app.js').read_bytes()),
            'Legacy JavaScript changed beyond the two reviewed version labels')
    activity = (android / 'java/com/lonesmartroom/app/MainActivity.kt').read_bytes()
    original = (baseline / 'java/com/lonesmartroom/app/MainActivity.kt').read_bytes()
    for marker in (b'private val assetsPrefix = "file:///android_asset/"',
                   b'webView.loadUrl(assetsPrefix + "index.html")',
                   b'webView.settings.domStorageEnabled = true'):
        require(marker in activity and marker in original, 'WebView origin/storage compatibility changed')
    require(b'setDataDirectorySuffix' not in activity, 'WebView data directory changed')
    with zipfile.ZipFile(apk) as archive:
        for name in ('app.js', 'index.html', 'styles.css', 'agent-status.js', 'app-version.js', 'app-launch.js'):
            require(archive.read('assets/' + name) == (android / 'assets' / name).read_bytes(),
                    'Packaged asset differs from reviewed source: ' + name)
        require(b'lone-wol-settings-v1' in archive.read('assets/app.js'), 'WoL storage key changed')

    output = ROOT / f'.cache/artifacts/android/LoneSmartRoom-{version_name}-v{version_code}.apk'
    output.parent.mkdir(parents=True, exist_ok=True)
    # Preserve every previously prepared candidate if future builds differ.
    if output.exists():
        require(digest(output) == digest(apk), 'Candidate already exists with different contents; preserve it and use a new version')
    else:
        shutil.copy2(apk, output)
    require(digest(output) == digest(apk), 'Candidate copy verification failed')
    receipt = {
        'package': package[1], 'versionCode': int(package[2]), 'versionName': package[3],
        'artifact': output.relative_to(ROOT).as_posix(), 'apkSha256': digest(output),
        'certificateSha256': EXPECTED, 'signatureVerified': True,
        'v2SignatureVerified': v2_verified,
        'recoveryApk': recovery.relative_to(ROOT).as_posix(), 'recoveryApkSha256': BASE_HASH,
        'recoverySignatureVerified': True, 'packagedAssetsVerified': True,
        'webViewOriginAndStorageSourceCompatible': True,
        'installedOnSamsung': False, 'deviceDataAccessed': False,
        'androidKeystoreRuntimeTestedOnSamsung': False,
    }
    path = ROOT / '.cache/validation/compatible-apk.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
