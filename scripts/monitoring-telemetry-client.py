"""Development-only replacement for the existing owned monitoring intermediary.

Uses the same collector + native pipe, with an in-memory HTTPS fan-out. Does not
load the operational agent's config/store/certificates. Never installed/packaged.
Requires a separately prepared loopback test identity; creates nothing on startup.
"""
import importlib.util
import json
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
    for name in ('DEVELOPMENT-TELEMETRY', 'server.crt', 'server.key', 'tls.dpapi', 'devices.db', 'telemetry-readers.json'):
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


def traced_publisher(broker, emit, *, enabled=False):
    """Bounded opt-in stage receipts, never a raw snapshot or exception string."""
    count = 0
    def publish(snapshot):
        nonlocal count
        accepted = False
        before = broker.diagnostics()['rejected']
        try:
            accepted = broker.publish(snapshot)
            return accepted
        finally:
            if enabled and count < 40:
                count += 1
                diagnostics = broker.diagnostics()
                sequence = snapshot.get('sequence') if type(snapshot) is dict else None
                if type(sequence) is not int or not 0 <= sequence <= 2**53 - 1:
                    sequence = None
                emit({'v':1,'event':'telemetry_publication','sequence':sequence,
                    'accepted':accepted is True,'rejected':diagnostics['rejected'] > before,
                    'rule':diagnostics['last_rule'] if diagnostics['rejected'] > before else None})
    return publish


def run():
    if '--application' in sys.argv or '--session' not in sys.argv:
        raise ValueError('development_only')
    session = sys.argv[sys.argv.index('--session') + 1]
    if not re.fullmatch('[a-f0-9]{32}', session): raise ValueError('invalid_session')
    state = development_state(ROOT, session)
    trace = '--validation-trace' in sys.argv
    if trace:
        sys.argv.remove('--validation-trace')
    # All credentials/certs here must be synthetic or separately authorized DEV identities.
    from secure_store import DPAPI
    from secure_protocol import Store
    from development_telemetry_http import DevelopmentTelemetryServer
    from telemetry.broker import SnapshotBroker
    broker = SnapshotBroker(simulation='--simulated' in sys.argv)
    # Ephemeral loopback only. Future LAN deployment requires separate approval.
    protector = DPAPI()
    readers_file = state / 'telemetry-readers.json'
    if readers_file.stat().st_size > 2048: raise ValueError('invalid_telemetry_read_scope')
    readers = json.loads(readers_file.read_bytes())
    if type(readers) is not list: raise ValueError('invalid_telemetry_read_scope')
    server = DevelopmentTelemetryServer(('127.0.0.1', 0), development_context(state, protector),
        Store(state / 'devices.db', protector), '127.0.0.0/8', telemetry=broker, development_enabled=True, telemetry_readers=readers)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    publish = traced_publisher(broker, lambda value:print(json.dumps(value),flush=True), enabled=trace)
    try:
        module_spec = importlib.util.spec_from_file_location('owned_pipe_client', ROOT / 'scripts/monitoring-pipe-client.py')
        module = importlib.util.module_from_spec(module_spec); module_spec.loader.exec_module(module)
        thread.start()
        # Discovery for the fixed local test harness/main only; no credential output.
        print(json.dumps({'v':1,'event':'telemetry_ready','host':'127.0.0.1',
                          'port':server.server_port,'generation':broker.generation}),flush=True)
        return module.main(snapshot_sink=publish)
    finally:
        if thread.is_alive(): server.shutdown()
        server.server_close()
        if thread.ident is not None: thread.join(timeout=2)
        print(json.dumps({'v':1,'event':'telemetry_diagnostics',**broker.diagnostics()}),flush=True)
        broker.clear()


if __name__ == '__main__': raise SystemExit(run())
