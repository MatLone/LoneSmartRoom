"""Existing draining server + read-only relay, without operational activation.

Bootstrap supplies a retained/verified RelayReader. No publisher means no route;
read scope never comes from command grants or remote requests. No collector is
created here and no certificate/pairing is generated or migrated.
"""
import json
from graceful_runtime import DrainingServer, ServerExited, serve
from telemetry_runtime import TelemetryStatusServer

RECOVERABLE_EXIT = 71


class DrainingTelemetryServer(DrainingServer, TelemetryStatusServer):
    """One listener: original admission/drain and existing telemetry handler."""


def run_candidate(layout, channel, log, *, bound=lambda: None, relay=None,
                  read_devices=()):
    from secure_store import DPAPI
    from secure_protocol import Store, validate_lan
    from secure_tls import server_context
    from secure_startup import private_profile
    from secure_apps import AppRegistry, launch_allowed
    state = layout.root / '.runtime/secure-agent'
    protector = DPAPI()
    config = json.loads(protector.open((state/'config.dpapi').read_bytes()))
    validate_lan(config['host'], config['network'])
    store = Store(state/'devices.db', protector)
    def factory(*args, **kwargs):
        server = DrainingTelemetryServer(*args, relay=relay,
            read_devices=read_devices, enabled=relay is not None, **kwargs)
        # Bound + TLS configured is NOT authenticated health.
        try: bound()
        except BaseException:
            server.stop_admission()
            server.server_close()
            raise
        return server
    try:
        try:
            return serve(config, store, channel, log,
                private_guard=lambda: private_profile(config['host']),
                context_factory=lambda: server_context(state, protector),
                registry_factory=AppRegistry, executor=launch_allowed,
                server_factory=factory)
        except ServerExited:
            # Runtime guarantees cleanup before this typed failure.
            return RECOVERABLE_EXIT
    finally:
        if relay is not None: relay.close()
