"""Review the exact Git index; print paths, never potential credential values."""
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from preservation_rules import reviewed_version_update

root = Path(__file__).resolve().parents[1]
portable = root / '.tools/git/cmd/git.exe'
git = str(portable) if portable.is_file() else shutil.which('git')
if not git:
    raise SystemExit('Git is required.')


def run(*args):
    return subprocess.check_output([git, *args], cwd=root)


paths = run('diff', '--cached', '--name-only', '--diff-filter=ACM', '-z').decode().split('\0')
bad = []
for name in filter(None, paths):
    path = Path(name)
    forbidden_names = {'agent_config.json', 'local.properties', 'credentials.json', 'secrets.json'}
    if (path.parts[0] in {'recovery', '.tools', '.cache'} or path.name in forbidden_names
            or path.name.startswith('.env') and path.name != '.env.example'
            or path.suffix.lower() in {'.keystore', '.jks', '.pem', '.pfx', '.p12', '.key'}):
        bad.append(name)
        continue
    data = run('show', ':' + name)
    if re.search(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----', data):
        bad.append(name)
    if re.search(rb'''(?i)(?:secret_hex|api_key|password|access_token)\s*[:=]\s*["'][A-Za-z0-9_+/=.-]{24,}["']''', data):
        bad.append(name)

records = json.loads((root / 'docs/baseline-inventory.json').read_text())
integration_files = {
    'apps/android/app/src/main/java/com/lonesmartroom/app/MainActivity.kt',
    'apps/android/app/src/main/assets/index.html', 'apps/windows-ui/index.html',
    'apps/android/app/src/main/res/values/styles.xml',
}
for record in records:
    rel = Path(record['copy'])
    if rel.as_posix() in integration_files:
        continue
    if rel.parts[0] in {'apps', 'agent'} and rel.suffix in {'.kt', '.js', '.html', '.css', '.cjs', '.xml', '.py'}:
        current = run('show', ':' + rel.as_posix())
        if hashlib.sha256(current).hexdigest() != record['sha256']:
            baseline = run('show', 'ed0fdae90db78d721444b29ee7d9ac49c21f73df:' + rel.as_posix())
            if current != reviewed_version_update(rel.as_posix(), baseline):
                bad.append(rel.as_posix())
if bad:
    raise SystemExit('Index review failed (paths only):\n' + '\n'.join(sorted(set(bad))))
activity = 'apps/android/app/src/main/java/com/lonesmartroom/app/MainActivity.kt'
def wake_bridge(data):
    return data.split(b'    inner class WakeBridge {', 1)[1].split(b'    override fun onDestroy()', 1)[0]
if wake_bridge(run('show', ':' + activity)) != wake_bridge(run('show', 'ed0fdae90db78d721444b29ee7d9ac49c21f73df:' + activity)):
    raise SystemExit('Staged WakeBridge differs from the preserved baseline')
print(f'PASS: {len(list(filter(None, paths)))} staged files; no credential patterns; protected baseline sources and WakeBridge preserved.')
