"""Opt-in development composition. Original operational server/launcher unchanged."""
import json
import threading
import time

from secure_http import Handler, StatusServer

PATH = '/v2/telemetry'
MAX_RESPONSE_BYTES = 32768


class TelemetryHandler(Handler):
    def do_GET(self):
        if self.path != PATH: return super().do_GET()
        if self.server.telemetry is None: return self.reply(404, {'ok': False})
        if (self.headers.get('Transfer-Encoding') or self.headers.get('Content-Length', '0') != '0'
                or len(self.headers.get_all('Content-Length', [])) > 1):
            self._body_read = True
            return self.reply(400, {'ok': False})
        if not self.authenticated('GET'): return self.reply(401, {'ok': False, 'error': 'unauthorized'})
        if not self.server.telemetry_admit(): return self.reply(429, {'ok': False, 'error': 'rate_limited'})
        try:
            value = self.server.telemetry.read()
            if len(json.dumps(value, allow_nan=False).encode()) > MAX_RESPONSE_BYTES: raise ValueError()
            return self.reply(200, value)
        except Exception:
            return self.reply(503, {'ok': False, 'error': 'telemetry_unavailable'})


class DevelopmentTelemetryServer(StatusServer):
    """Authenticated read scope follows existing pairing; grants remain launch-only.

    Default disabled. Source must be an already-owned trusted cache adapter, never
    a renderer-supplied path or command. Rate bucket is global (bounded memory).
    """
    def __init__(self, *args, telemetry=None, development_enabled=False, clock=time.monotonic, **kwargs):
        self.telemetry = telemetry if development_enabled else None
        self.telemetry_clock = clock
        self.telemetry_lock = threading.Lock()
        self.telemetry_tokens, self.telemetry_at = 4., clock()
        super().__init__(*args, **kwargs)
        self.RequestHandlerClass = TelemetryHandler

    def telemetry_admit(self):
        with self.telemetry_lock:
            now = self.telemetry_clock()
            if now < self.telemetry_at: return False
            self.telemetry_tokens = min(4., self.telemetry_tokens + (now - self.telemetry_at) * 2)
            self.telemetry_at = now
            if self.telemetry_tokens < 1: return False
            self.telemetry_tokens -= 1
            return True
