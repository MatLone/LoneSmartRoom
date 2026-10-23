"""Bounded HTTPS server. The v2 listener has NO action routes or OS executors."""
import ipaddress
import json
import ssl
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class StatusServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, address, context, store, network, private_guard=None):
        self.tls, self.store = context, store
        self.network = ipaddress.ip_network(network)
        self.private_guard = private_guard
        self.slots = threading.BoundedSemaphore(12)
        self.rate_lock, self.rates = threading.Lock(), {}
        super().__init__(address, Handler)

    def process_request(self, request, address):
        if ipaddress.ip_address(address[0]) not in self.network or not self.slots.acquire(False):
            request.close()
            return
        try:
            super().process_request(request, address)
        except Exception:
            self.slots.release()
            request.close()
            raise

    def process_request_thread(self, request, address):
        try:
            if self.private_guard is not None and not self.private_guard():
                return
            request.settimeout(5)
            with self.tls.wrap_socket(request, server_side=True) as secured:
                self.finish_request(secured, address)
        except (OSError, ssl.SSLError, ValueError):
            pass
        finally:
            request.close()
            self.slots.release()

    def pair_allowed(self, ip):
        now = time.monotonic()
        with self.rate_lock:
            self.rates = {k: v for k, v in self.rates.items() if now - v[0] < 60}
            start, count = self.rates.get(ip, (now, 0))
            self.rates[ip] = (start, count + 1)
            return count < 5


class Handler(BaseHTTPRequestHandler):
    server_version = 'LoneSecure/2'
    sys_version = ''

    def log_message(self, *args):
        pass  # No request, authentication header, pair code or secret in logs.

    def reply(self, status, value):
        # Drain only bounded bodies before early rejections, avoiding TCP resets
        # that can discard the error response. Never consume an unbounded upload.
        length = self.headers.get('Content-Length', '0')
        if not getattr(self, '_body_read', False) and length.isascii() and length.isdecimal() and len(length) <= 4:
            if 0 < int(length) <= 4096:
                self.rfile.read(int(length))
            self._body_read = True
        body = json.dumps(value, separators=(',', ':')).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(body)
        self.close_connection = True

    def do_GET(self):
        if self.path != '/v2/status':
            return self.reply(404, {'ok': False})
        if self.headers.get('Transfer-Encoding') or self.headers.get('Content-Length', '0') != '0':
            return self.reply(400, {'ok': False})
        if not self.server.store.authenticate(self.headers, 'GET', self.path):
            return self.reply(401, {'ok': False, 'error': 'unauthorized'})
        self.reply(200, {'ok': True, 'agent': 'online', 'version': '2.0.0', 'scope': 'status'})

    def do_POST(self):
        if self.path != '/v2/pair':
            return self.reply(404, {'ok': False})
        if not self.server.pair_allowed(self.client_address[0]):
            return self.reply(429, {'ok': False})
        length = self.headers.get('Content-Length', '')
        if (self.headers.get('Transfer-Encoding') or not length.isascii() or not length.isdecimal()
                or len(length) > 4 or not 1 <= int(length) <= 1024
                or self.headers.get_content_type() != 'application/json'):
            return self.reply(400, {'ok': False})
        try:
            raw = self.rfile.read(int(length))
            self._body_read = True
            if len(raw) != int(length):
                return self.reply(400, {'ok': False})
            data = json.loads(raw)
            result = self.server.store.pair(data.get('code'), data.get('label')) if isinstance(data, dict) else None
        except (ValueError, UnicodeError):
            return self.reply(400, {'ok': False})
        self.reply(200 if result else 401, {'ok': bool(result), **(result or {})})
