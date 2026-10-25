"""Source receipts for the simulated gate; no hardware imports or collection."""
import hashlib
from pathlib import Path


def source_hashes(root):
    root = Path(root)
    paths = sorted(list((root / 'monitoring').glob('*.py'))
                   + list((root / 'tests/monitoring').glob('*.py'))
                   + [root / 'scripts/test-monitoring-isolated.py',
                      root / 'scripts/test-monitoring-basic-isolated.py',
                      root / 'scripts/monitoring-basic-session.py'])
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
