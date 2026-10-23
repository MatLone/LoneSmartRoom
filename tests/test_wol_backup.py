"""Recovery parsing tests with synthetic data only; no ADB/device/file operations."""
import importlib.util
import json
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('wol_backup', ROOT / 'scripts/backup-wol-readonly.py')
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)
KEY = b'_file://\x00\x01lone-wol-settings-v1'
SETTINGS = {'mac': '02:00:00:00:00:01', 'broadcast': '172.31.250.255', 'port': 9}


def varstring(value):
    length = len(value)
    prefix = bytearray()
    while length >= 128:
        prefix.append((length & 127) | 128)
        length >>= 7
    prefix.append(length)
    return bytes(prefix) + value


def batch(sequence, value, key=KEY):
    operation = b'\x00' + varstring(key) if value is None else b'\x01' + varstring(key) + varstring(value)
    return struct.pack('<QI', sequence, 1) + operation


def record(payload, kind=1):
    crc = backup.crc32c(bytes([kind]) + payload)
    masked = (((crc >> 15) | (crc << 17)) + 0xa282ead8) & 0xffffffff
    return struct.pack('<IHB', masked, len(payload), kind) + payload


class WolBackupTests(unittest.TestCase):
    def test_crc32c_known_vector(self):
        self.assertEqual(backup.crc32c(b'123456789'), 0xe3069283)

    def test_latest_sequence_and_origin_filter(self):
        old = dict(SETTINGS, port=7)
        data = record(batch(1, b'\x01' + json.dumps(old).encode()))
        data += record(batch(5, b'\x01' + json.dumps(SETTINGS).encode()))
        data += record(batch(10, b'\x01{}', b'_https://other.example\x00\x01lone-wol-settings-v1'))
        self.assertEqual(backup.wol_from_log(data), SETTINGS)

    def test_fragments_and_utf16(self):
        payload = batch(1, b'\x00' + json.dumps(SETTINGS).encode('utf-16-le'))
        data = record(payload[:20], 2) + record(payload[20:40], 3) + record(payload[40:], 4)
        self.assertEqual(backup.wol_from_log(data), SETTINGS)

    def test_corrupt_incomplete_and_deleted_refused(self):
        data = record(batch(1, b'\x01' + json.dumps(SETTINGS).encode()))
        for corrupted in (data[:-1], bytes([data[0] ^ 1]) + data[1:], data + record(batch(2, None))):
            with self.subTest(case=len(corrupted)), self.assertRaises(ValueError):
                backup.wol_from_log(corrupted)

    def test_unexpected_schema_and_bad_count_refused(self):
        extra = dict(SETTINGS, unrelated='must never be exported')
        payload = batch(1, b'\x01' + json.dumps(SETTINGS).encode())
        bad_count = payload[:8] + struct.pack('<I', 2) + payload[12:]
        for data in (record(batch(1, b'\x01' + json.dumps(extra).encode())), record(bad_count)):
            with self.assertRaises(ValueError):
                backup.wol_from_log(data)
