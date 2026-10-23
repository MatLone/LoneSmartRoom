"""HTTPS loopback integration tests; no power/app executor is imported or called."""
import hashlib
import hmac
import http.client
import json
from pathlib import Path
import secrets
import socket
import ssl
import sys
import tempfile
import threading
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'agent/windows'))
from secure_protocol import Store, canonical, validate_lan
from secure_store import DPAPI
from secure_tls import create_identity, fingerprint, server_context
from secure_http import StatusServer


class SecureAgentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cache = ROOT / '.cache/tests'
        cache.mkdir(parents=True, exist_ok=True)
        cls.temp = tempfile.TemporaryDirectory(dir=cache)
        cls.directory = Path(cls.temp.name)
        cls.protector = DPAPI()
        create_identity(cls.directory, '127.0.0.1', cls.protector)
        cls.store = Store(cls.directory / 'state.db', cls.protector)
        cls.server = StatusServer(('127.0.0.1', 0), server_context(cls.directory, cls.protector), cls.store, '127.0.0.0/8')
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_port
        cls.context = ssl.create_default_context(cafile=str(cls.directory / 'server.crt'))

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        cls.temp.cleanup()

    def device(self):
        token, _ = self.store.begin_pairing()
        result = self.store.pair(token, 'Test Android')
        self.assertIsNotNone(result)
        return result

    def headers(self, device, path='/v2/status', nonce=None, offset=0, secret=None):
        stamp = str(int(time.time()) + offset)
        nonce = nonce or secrets.token_hex(16)
        signature = hmac.new(bytes.fromhex(secret or device['secret']),
            canonical(stamp, nonce, device['device_id'], 'GET', path, b''), hashlib.sha256).hexdigest()
        return {'X-Lone-Device': device['device_id'], 'X-Lone-Timestamp': stamp,
                'X-Lone-Nonce': nonce, 'X-Lone-Signature': signature}

    def request(self, method='GET', path='/v2/status', headers=None, body=None, context=None):
        connection = http.client.HTTPSConnection('127.0.0.1', self.port, timeout=3, context=context or self.context)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            result = connection.getresponse()
            return result.status, json.loads(result.read())
        finally:
            connection.close()

    def test_https_status_and_encrypted_secret(self):
        device = self.device()
        status, result = self.request(headers=self.headers(device))
        self.assertEqual(status, 200)
        self.assertEqual(result['scope'], 'status')
        self.assertNotIn(bytes.fromhex(device['secret']), (self.directory / 'state.db').read_bytes())
        encrypted = self.protector.seal(b'isolated test credential')
        self.assertEqual(self.protector.open(encrypted), b'isolated test credential')

    def test_wrong_and_missing_credentials(self):
        device = self.device()
        self.assertEqual(self.request()[0], 401)
        self.assertEqual(self.request(headers=self.headers(device, secret='00' * 32))[0], 401)

    def test_replay_survives_store_restart(self):
        device = self.device()
        headers = self.headers(device)
        self.assertEqual(self.request(headers=headers)[0], 200)
        restarted = Store(self.directory / 'state.db', self.protector)
        self.assertFalse(restarted.authenticate(headers, 'GET', '/v2/status'))
        self.assertEqual(self.request(headers=headers)[0], 401)

    def test_revocation_and_individual_identities(self):
        first, second = self.device(), self.device()
        self.assertNotEqual(first['device_id'], second['device_id'])
        self.assertTrue(self.store.revoke(first['device_id']))
        self.assertEqual(self.request(headers=self.headers(first))[0], 401)
        self.assertEqual(self.request(headers=self.headers(second))[0], 200)

    def test_expired_and_single_use_pairing(self):
        now = [1000]
        store = Store(self.directory / 'expiry.db', self.protector, clock=lambda: now[0])
        token, _ = store.begin_pairing(30)
        now[0] = 1030
        self.assertIsNone(store.pair(token, 'Expired'))
        token, _ = store.begin_pairing(30)
        self.assertIsNotNone(store.pair(token, 'One use'))
        self.assertIsNone(store.pair(token, 'Second use'))
        self.assertIsNone(store.pair('invalid', 'Wrong'))

    def test_pair_over_https(self):
        self.server.rates.clear()
        token, _ = self.store.begin_pairing()
        body = json.dumps({'code': token, 'label': 'Paired over HTTPS'})
        code, result = self.request('POST', '/v2/pair', {'Content-Type': 'application/json'}, body)
        self.assertEqual(code, 200)
        self.assertEqual(self.request(headers=self.headers(result))[0], 200)
        self.assertEqual(self.request('POST', '/v2/pair', {'Content-Type': 'application/json'}, body)[0], 401)

    def test_pair_rate_limit_and_request_limit(self):
        self.server.rates.clear()
        for _ in range(5):
            self.assertEqual(self.request('POST', '/v2/pair', {'Content-Type': 'application/json'}, '{}')[0], 401)
        self.assertEqual(self.request('POST', '/v2/pair', {'Content-Type': 'application/json'}, '{}')[0], 429)
        self.server.rates.clear()
        self.assertEqual(self.request('POST', '/v2/pair', {'Content-Type': 'application/json'}, 'x' * 1025)[0], 400)

    def test_invalid_certificate_rejected(self):
        with self.assertRaises(ssl.SSLCertVerificationError):
            self.request(context=ssl.create_default_context())
        wrong = self.directory / 'other'
        create_identity(wrong, '127.0.0.1', self.protector)
        with self.assertRaises(ssl.SSLCertVerificationError):
            self.request(context=ssl.create_default_context(cafile=str(wrong / 'server.crt')))

    def test_expired_request_tampering_and_no_actions(self):
        device = self.device()
        self.assertEqual(self.request(headers=self.headers(device, offset=-90))[0], 401)
        self.assertFalse(self.store.authenticate(self.headers(device), 'GET', '/different'))
        for path in ('/v1/action', '/v2/action', '/v2/status?command=shutdown'):
            self.assertEqual(self.request('POST', path, body='{}')[0], 404)
        self.assertEqual(self.request(headers={**self.headers(device), 'X-Lone-Timestamp': '9' * 100})[0], 401)

    def test_unavailable_connection(self):
        listener = socket.socket()
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
        # Bound but deliberately not listening: reliable refused local connection.
        try:
            with self.assertRaises(OSError):
                connection = http.client.HTTPSConnection('127.0.0.1', port, timeout=1, context=self.context)
                try: connection.request('GET', '/v2/status')
                finally: connection.close()
        finally:
            listener.close()

    def test_lan_validation(self):
        validate_lan('172.31.250.8', '172.31.250.0/24')
        for host, subnet in [('0.0.0.0', '0.0.0.0/0'), ('8.8.8.8', '8.8.8.0/24'),
                             ('127.0.0.1', '127.0.0.0/24'), ('172.31.250.8', '192.168.4.0/24')]:
            with self.assertRaises(ValueError): validate_lan(host, subnet)

    def test_tls_only_and_identity_stable(self):
        old = fingerprint(self.directory)
        with self.assertRaises(FileExistsError): create_identity(self.directory, '127.0.0.1', self.protector)
        self.assertEqual(old, fingerprint(self.directory))
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=2)
        with self.assertRaises((OSError, http.client.HTTPException)):
            try:
                connection.request('GET', '/v2/status')
                connection.getresponse()
            finally: connection.close()


if __name__ == '__main__':
    unittest.main()
