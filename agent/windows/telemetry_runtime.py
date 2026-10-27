"""Opt-in HTTPS composition for a future safely stopped/restarted agent.

No operational config/database/credential access or startup on import. The active
legacy launcher and secure_agent.py are deliberately untouched. A trusted local
bootstrap supplies the exact registered publisher handle and explicit read scope.
"""
from development_telemetry_http import DevelopmentTelemetryServer
from telemetry.relay import RelayReader


class TelemetryStatusServer(DevelopmentTelemetryServer):
    def __init__(self,*args,relay=None,read_devices=(),enabled=False,**kwargs):
        if type(enabled) is not bool:raise ValueError('explicit_telemetry_flag_required')
        if relay is not None and not isinstance(relay,RelayReader):
            raise ValueError('registered_local_relay_required')
        if enabled and relay is None:raise ValueError('registered_local_relay_required')
        super().__init__(*args,telemetry=relay,telemetry_readers=read_devices,
            development_enabled=enabled,**kwargs)
