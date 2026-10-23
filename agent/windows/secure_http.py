"""Bounded HTTPS: pairing/status plus explicitly granted Steam/CS2 requests only."""
import ipaddress
import json
import re
import ssl
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from secure_apps import AppError


class StatusServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, address, context, store, network, private_guard=None, apps=None):
        self.tls, self.store = context, store
        self.network = ipaddress.ip_network(network)
        self.private_guard = private_guard
        self.apps = apps
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

    def authenticated(self, method, body=b''):
        names = ('X-Lone-Device', 'X-Lone-Timestamp', 'X-Lone-Nonce', 'X-Lone-Signature')
        return (all(len(self.headers.get_all(name, [])) == 1 for name in names)
                and self.server.store.authenticate(self.headers, method, self.path, body))

    def body(self):
        lengths = self.headers.get_all('Content-Length', [])
        types = self.headers.get_all('Content-Type', [])
        if (self.headers.get('Transfer-Encoding') or len(lengths) != 1 or len(types) != 1
                or not lengths[0].isascii() or not lengths[0].isdecimal() or len(lengths[0]) > 4
                or not 1 <= int(lengths[0]) <= 1024 or self.headers.get_content_type() != 'application/json'):
            self._body_read = True  # Never drain ambiguous/oversized framing.
            raise ValueError('Invalid request framing')
        raw = self.rfile.read(int(lengths[0]))
        self._body_read = True
        if len(raw) != int(lengths[0]):
            raise ValueError('Incomplete request')
        return raw

    @staticmethod
    def json_body(raw):
        def pairs(items):
            result = {}
            for key, value in items:
                if key in result:
                    raise ValueError('Duplicate JSON field')
                result[key] = value
            return result
        def constant(value):
            raise ValueError('Invalid JSON constant')
        return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant)

    def reply(self, status, value):
        # Drain only bounded bodies before early rejections, avoiding TCP resets
        # that can discard the error response. Never consume an unbounded upload.
        length = self.headers.get('Content-Length', '0')
        if (not getattr(self, '_body_read', False) and len(self.headers.get_all('Content-Length', [])) <= 1
                and length.isascii() and length.isdecimal() and len(length) <= 4):
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
        command = re.fullmatch(r'/v2/apps/commands/([0-9a-f]{32})', self.path)
        if self.path not in ('/v2/status', '/v2/apps') and command is None:
            return self.reply(404, {'ok': False})
        if (self.headers.get('Transfer-Encoding') or self.headers.get('Content-Length', '0') != '0'
                or len(self.headers.get_all('Content-Length', [])) > 1):
            self._body_read = True
            return self.reply(400, {'ok': False})
        if not self.authenticated('GET'):
            return self.reply(401, {'ok': False, 'error': 'unauthorized'})
        if self.path != '/v2/status':
            if self.server.apps is None:
                return self.reply(503, {'ok': False, 'error': 'apps_unavailable'})
            device = self.headers['X-Lone-Device']
            if command:
                result = self.server.apps.registry.result(device, command[1])
                return self.reply(200 if result else 404, result or {'ok': False, 'error': 'command_not_found'})
            return self.reply(200, {'ok': True, 'allowed_apps': self.server.apps.registry.permissions(device)})
        self.reply(200, {'ok': True, 'agent': 'online', 'version': '2.0.0', 'scope': 'status'})

    def do_POST(self):
        if self.path not in ('/v2/pair', '/v2/apps/commands'):
            return self.reply(404, {'ok': False})
        if self.path == '/v2/apps/commands':
            try:
                raw = self.body()
                if not self.authenticated('POST', raw):
                    return self.reply(401, {'ok': False, 'error': 'unauthorized'})
                if self.server.apps is None:
                    return self.reply(503, {'ok': False, 'error': 'apps_unavailable'})
                result = self.server.apps.submit(self.headers['X-Lone-Device'], self.json_body(raw))
                return self.reply(202 if result['state'] == 'accepted' else 200, result)
            except AppError as error:
                return self.reply(error.status, {'ok': False, 'error': error.code})
            except (ValueError, UnicodeError, RecursionError):
                return self.reply(400, {'ok': False, 'error': 'invalid_app_request'})
        if not self.server.pair_allowed(self.client_address[0]):
            return self.reply(429, {'ok': False})
        try:
            raw = self.body()
            data = self.json_body(raw)
            result = self.server.store.pair(data.get('code'), data.get('label')) if isinstance(data, dict) else None
        except (ValueError, UnicodeError, RecursionError):
            return self.reply(400, {'ok': False})
        self.reply(200 if result else 401, {'ok': bool(result), **(result or {})})
