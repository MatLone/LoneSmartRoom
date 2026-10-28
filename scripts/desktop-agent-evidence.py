"""Fixed one-shot metadata reader; only a future explicit development flag uses it."""
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    if sys.argv[1:]: return 20
    from diagnostics.desktop_evidence import collect
    from diagnostics.windows_readers import WindowsReaders
    try:
        report = collect(WindowsReaders(candidate=True))
        payload = json.dumps(report, allow_nan=False, separators=(',', ':')).encode()
        if len(payload) > 16384: return 21
        sys.stdout.buffer.write(payload+b'\n');sys.stdout.buffer.flush()
        return 0
    except Exception: return 21  # No raw paths, exception strings or secrets.


if __name__ == '__main__': raise SystemExit(main())
