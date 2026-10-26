"""Print a clearly labeled simulated report; never examines the local machine."""
from datetime import datetime, timezone
import json
from .contracts import Component
from .engine import DiagnosticEngine
from .simulated import SimulatedProvider, healthy_fixture


def main():
    # Fixed clock and fixture values make the demonstration reproducible.
    now = datetime(2026, 10, 26, 12, tzinfo=timezone.utc)
    providers = [SimulatedProvider(c, [healthy_fixture(c, now, 100)]) for c in Component]
    print(json.dumps(DiagnosticEngine(providers).collect(now, 100), indent=2))


if __name__ == '__main__':
    main()
