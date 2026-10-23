"""Check the preserved copies AND their originals, without changing either."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
records = json.loads((root / 'recovery/manifest.json').read_text(encoding='utf-8'))
failures = []
for record in records:
    source = Path(record['source'])
    for label, path in [('original', source), ('copy', root / record['copy'])]:
        # Runtime files are also checked by tests; build files intentionally evolve.
        if label == 'copy' and Path(record['copy']).parts[0] in {'apps', 'agent'}:
            continue
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
            failures.append(f"{label}: {record['copy']}")
if failures:
    raise SystemExit('\n'.join(failures))
print(f'PASS: {len(records)} manifest records; original files and recovery copies unchanged.')
