"""Status-only v2 protocol. Durable replay prevention and one-use pairing."""
import hashlib
import hmac
import ipaddress
import json
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

RFC1918 = tuple(ipaddress.ip_network(n) for n in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16'))


def validate_lan(host, network):
    address = ipaddress.IPv4Address(host)
    subnet = ipaddress.IPv4Network(network, strict=True)
    if not any(subnet.subnet_of(n) for n in RFC1918) or subnet.prefixlen < 24:
        raise ValueError('Use an explicit RFC1918 LAN subnet /24 or narrower')
    if address not in subnet or address in (subnet.network_address, subnet.broadcast_address):
        raise ValueError('Host must be a usable address in the authorized LAN')
    return address, subnet


def canonical(stamp, nonce, device, method, path, body):
    return f'LSR2\n{device}\n{stamp}\n{nonce}\n{method}\n{path}\n'.encode('ascii') + body


class Store:
    def __init__(self, path, protector, clock=time.time):
        self.path, self.protector, self.clock = Path(path), protector, clock
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
              CREATE TABLE IF NOT EXISTS devices(id TEXT PRIMARY KEY,label TEXT NOT NULL,
                secret BLOB NOT NULL,revoked INTEGER NOT NULL DEFAULT 0);
              CREATE TABLE IF NOT EXISTS nonces(device TEXT NOT NULL,nonce TEXT NOT NULL,
                expires INTEGER NOT NULL,PRIMARY KEY(device,nonce));
              CREATE TABLE IF NOT EXISTS pairing(hash TEXT PRIMARY KEY,expires INTEGER NOT NULL);
            ''')

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=5)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def begin_pairing(self, ttl=180):
        if not 30 <= ttl <= 300:
            raise ValueError('Pairing lifetime must be 30..300 seconds')
        token, expires = secrets.token_urlsafe(24), int(self.clock()) + ttl
        with self.connect() as db:
            db.execute('DELETE FROM pairing')
            db.execute('INSERT INTO pairing VALUES (?,?)', (hashlib.sha256(token.encode()).hexdigest(), expires))
        return token, expires

    def pair(self, token, label):
        if not isinstance(token, str) or not re.fullmatch(r'[A-Za-z0-9_-]{32}', token):
            return None
        if not isinstance(label, str) or not 1 <= len(label) <= 40 or not label.isprintable():
            return None
        device, secret = secrets.token_hex(16), secrets.token_bytes(32)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            digest = hashlib.sha256(token.encode()).hexdigest()
            row = db.execute('SELECT expires FROM pairing WHERE hash=?', (digest,)).fetchone()
            if not row or row[0] <= self.clock():
                return None
            db.execute('DELETE FROM pairing WHERE hash=?', (digest,))
            db.execute('INSERT INTO devices(id,label,secret) VALUES (?,?,?)',
                       (device, label, self.protector.seal(secret)))
        return {'device_id': device, 'secret': secret.hex()}

    def devices(self):
        with self.connect() as db:
            return db.execute('SELECT id,label,revoked FROM devices ORDER BY id').fetchall()

    def revoke(self, device):
        with self.connect() as db:
            return db.execute('UPDATE devices SET revoked=1 WHERE id=?', (device,)).rowcount == 1

    def authenticate(self, headers, method, path, body=b''):
        device, stamp, nonce, signature = [headers.get(k, '') for k in
            ('X-Lone-Device', 'X-Lone-Timestamp', 'X-Lone-Nonce', 'X-Lone-Signature')]
        if not re.fullmatch(r'[0-9a-f]{32}', device) or not re.fullmatch(r'[0-9]{10,11}', stamp):
            return False
        if not re.fullmatch(r'[0-9a-f]{32}', nonce) or not re.fullmatch(r'[0-9a-f]{64}', signature):
            return False
        now = int(self.clock())
        if abs(now - int(stamp)) > 60:
            return False
        with self.connect() as db:
            # The write transaction serializes revocation and nonce consumption.
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT secret FROM devices WHERE id=? AND revoked=0', (device,)).fetchone()
            if not row:
                return False
            expected = hmac.new(self.protector.open(row[0]), canonical(stamp, nonce, device, method, path, body),
                                hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected):
                return False
            db.execute('DELETE FROM nonces WHERE expires < ?', (now,))
            try:
                db.execute('INSERT INTO nonces VALUES (?,?,?)', (device, nonce, int(stamp) + 61))
            except sqlite3.IntegrityError:
                return False
        return True
