"""Exact development source receipt. Import/hash only, no sensors, pipe or process."""
import hashlib
from .basic_validation import source_hashes as basic_hashes


def source_hashes(root):
    result=basic_hashes(root)
    paths=list((root/'apps/windows-ui').glob('monitoring*'))
    paths+=list((root/'scripts').glob('monitoring-*.py'))
    paths+=list((root/'tests').glob('electron-monitoring*.cjs'))
    paths+=[root/'apps/windows-ui'/name for name in ('main.cjs','preload.cjs','desktop-main.cjs',
             'desktop-policy.cjs','desktop-window.cjs','desktop-preferences.cjs','desktop.js','desktop.css','index.html','package.json')]
    paths+=[root/'scripts'/name for name in ('test-monitoring-pipe-isolated.py','preservation_rules.py')]
    paths+=[root/'tests'/name for name in ('electron-tray.cjs','electron-window-policy.cjs')]
    for path in paths:
        if path.is_file():result[path.relative_to(root).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(sorted(result.items()))
