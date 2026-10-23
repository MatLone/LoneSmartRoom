"""Review the exact Git index; print paths, never potential credential values."""
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

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
for record in records:
    rel = Path(record['copy'])
    if rel.parts[0] in {'apps', 'agent'} and rel.suffix in {'.kt', '.js', '.html', '.css', '.cjs', '.xml', '.py'}:
        if hashlib.sha256(run('show', ':' + rel.as_posix())).hexdigest() != record['sha256']:
            bad.append(rel.as_posix())
if bad:
    raise SystemExit('Index review failed (paths only):\n' + '\n'.join(sorted(set(bad))))
print(f'PASS: {len(list(filter(None, paths)))} staged files; no credential patterns; runtime bytes preserved in Git.')
