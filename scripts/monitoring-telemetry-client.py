"""Development-only replacement for the existing owned monitoring intermediary.

Uses the same collector + native pipe, with an in-memory HTTPS fan-out. Does not
load the operational agent's config/store/certificates. Never installed/packaged.
Requires a separately prepared loopback test identity; creates nothing on startup.
"""
import importlib.util
from pathlib import Path
import re
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'agent/windows'))


def run():
    if '--application' in sys.argv or '--session' not in sys.argv:
        raise ValueError('development_only')
    session = sys.argv[sys.argv.index('--session') + 1]
    if not re.fullmatch('[a-f0-9]{32}', session): raise ValueError('invalid_session')
    state = ROOT / '.cache/telemetry-development' / session
    # All credentials/certs here must be synthetic or separately authorized DEV identities.
    if not state.is_dir() or state.is_symlink(): raise ValueError('development_identity_required')
    from secure_store import DPAPI
    from secure_protocol import Store
    from secure_tls import server_context
    from development_telemetry_http import DevelopmentTelemetryServer
    from telemetry.broker import SnapshotBroker
    broker = SnapshotBroker(simulation='--simulated' in sys.argv)
    # Ephemeral loopback only. Future LAN deployment requires separate approval.
    protector = DPAPI()
    server = DevelopmentTelemetryServer(('127.0.0.1', 0), server_context(state, protector),
        Store(state / 'devices.db', protector), '127.0.0.0/8', telemetry=broker, development_enabled=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    module_spec = importlib.util.spec_from_file_location('owned_pipe_client', ROOT / 'scripts/monitoring-pipe-client.py')
    module = importlib.util.module_from_spec(module_spec); module_spec.loader.exec_module(module)
    thread.start()
    try:
        return module.main(snapshot_sink=broker.publish)
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2); broker.clear()


if __name__ == '__main__': raise SystemExit(run())
