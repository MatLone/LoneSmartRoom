"""Development-only replacement for the existing owned monitoring intermediary.

Uses the same collector + native pipe, with an in-memory HTTPS fan-out. Does not
load the operational agent's config/store/certificates. Never installed/packaged.
Requires a separately prepared loopback test identity; creates nothing on startup.
"""
import importlib.util
from pathlib import Path
import re
import ssl
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'agent/windows'))


def development_state(root, session):
    if not re.fullmatch('[a-f0-9]{32}', session): raise ValueError('invalid_session')
    state = Path(root).resolve() / '.cache/telemetry-development' / session
    if not state.is_dir() or state.resolve() != state or state.is_symlink() or state.is_junction():
        raise ValueError('development_identity_required')
    for name in ('DEVELOPMENT-TELEMETRY', 'server.crt', 'server.key', 'tls.dpapi', 'devices.db'):
        p = state / name
        if not p.is_file() or p.is_symlink() or p.resolve() != p or p.stat().st_nlink != 1:
            raise ValueError('development_identity_required')
    if (state / 'DEVELOPMENT-TELEMETRY').read_bytes() != b'LSR-TELEMETRY-DEV-LOOPBACK-v1\n':
        raise ValueError('development_identity_required')
    return state


def development_context(state, protector):
    # Same existing TLS minimum/chain policy, without certificate generation or
    # a third-party import: monitoring's -I -S runtime intentionally has no site.
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(state / 'server.crt', state / 'server.key',
        password=lambda: protector.open((state / 'tls.dpapi').read_bytes()))
    return context


def run():
    if '--application' in sys.argv or '--session' not in sys.argv:
        raise ValueError('development_only')
    session = sys.argv[sys.argv.index('--session') + 1]
    if not re.fullmatch('[a-f0-9]{32}', session): raise ValueError('invalid_session')
    state = development_state(ROOT, session)
    # All credentials/certs here must be synthetic or separately authorized DEV identities.
    from secure_store import DPAPI
    from secure_protocol import Store
    from development_telemetry_http import DevelopmentTelemetryServer
    from telemetry.broker import SnapshotBroker
    broker = SnapshotBroker(simulation='--simulated' in sys.argv)
    # Ephemeral loopback only. Future LAN deployment requires separate approval.
    protector = DPAPI()
    server = DevelopmentTelemetryServer(('127.0.0.1', 0), development_context(state, protector),
        Store(state / 'devices.db', protector), '127.0.0.0/8', telemetry=broker, development_enabled=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    try:
        module_spec = importlib.util.spec_from_file_location('owned_pipe_client', ROOT / 'scripts/monitoring-pipe-client.py')
        module = importlib.util.module_from_spec(module_spec); module_spec.loader.exec_module(module)
        thread.start()
        return module.main(snapshot_sink=broker.publish)
    finally:
        if thread.is_alive(): server.shutdown()
        server.server_close()
        if thread.ident is not None: thread.join(timeout=2)
        broker.clear()


if __name__ == '__main__': raise SystemExit(run())
