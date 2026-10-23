"""Read only the existing WoL entry over ADB; save only three fields under DPAPI.

Supports the observed single-WAL LevelDB layout; refuses SSTs or ambiguous layouts.
Raw WebView bytes and unrelated entries stay in memory and are never logged/saved.
Format references: google/leveldb doc/log_format.md, db/write_batch.cc, util/crc32c.h;
Chromium local_storage_impl.cc schema. No LevelDB writer/database open is used.
"""
import argparse
import datetime
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'agent/windows'))
from secure_store import DPAPI

PACKAGE = 'com.lonesmartroom.app'
DIRECTORY = 'app_webview/Default/Local Storage/leveldb'
STORAGE_KEY = 'lone-wol-settings-v1'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def crc32c(data):
    crc = 0xffffffff
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ (0x82f63b78 if crc & 1 else 0)
    return crc ^ 0xffffffff


def records(data):
    """Reject incomplete/corrupt WAL data instead of guessing configuration values."""
    require(len(data) <= 4 * 1024 * 1024, 'WebView WAL exceeds supported limit')
    fragments = None
    offset = 0
    while offset < len(data):
        remaining = min(32768 - offset % 32768, len(data) - offset)
        if remaining < 7:
            require(not any(data[offset:offset + remaining]), 'Incomplete WAL header')
            offset += remaining
            continue
        checksum, length, kind = struct.unpack_from('<IHB', data, offset)
        require(kind in (1, 2, 3, 4) and length + 7 <= remaining, 'Unsupported/incomplete WAL record')
        payload = data[offset + 7:offset + 7 + length]
        crc = crc32c(bytes([kind]) + payload)
        masked = (((crc >> 15) | (crc << 17)) + 0xa282ead8) & 0xffffffff
        require(checksum == masked, 'WAL checksum mismatch')
        offset += 7 + length
        if kind == 1:
            require(fragments is None, 'Unexpected full WAL record')
            yield payload
        elif kind == 2:
            require(fragments is None, 'Unexpected WAL first fragment')
            fragments = bytearray(payload)
        else:
            require(fragments is not None, 'Missing WAL first fragment')
            fragments.extend(payload)
            if kind == 4:
                yield bytes(fragments)
                fragments = None
    require(fragments is None, 'Incomplete WAL fragments')


def entry(data, offset):
    length = 0
    for shift in range(0, 35, 7):
        require(offset < len(data), 'Incomplete WAL varint')
        byte = data[offset]
        offset += 1
        length |= (byte & 127) << shift
        if byte < 128:
            require(length <= 0xffffffff and offset + length <= len(data), 'Invalid WAL entry length')
            return data[offset:offset + length], offset + length
    raise ValueError('Invalid WAL varint')


def wol_from_log(data):
    # Only the original local file origin, never values from unrelated origins.
    keys = {b'_file://\x00\x01' + STORAGE_KEY.encode(),
            b'_file://\x00\x00' + STORAGE_KEY.encode('utf-16-le')}
    latest, value = -1, None
    for batch in records(data):
        require(len(batch) >= 12, 'Incomplete WriteBatch')
        sequence, count = struct.unpack_from('<QI', batch)
        offset = 12
        for index in range(count):
            require(offset < len(batch), 'Invalid WriteBatch count')
            kind = batch[offset]
            require(kind in (0, 1), 'Unsupported WriteBatch operation')
            key, offset = entry(batch, offset + 1)
            candidate = None
            if kind == 1:
                candidate, offset = entry(batch, offset)
            if key in keys and sequence + index > latest:
                latest, value = sequence + index, candidate
        require(offset == len(batch), 'WriteBatch count mismatch')
    require(value is not None and 0 < len(value) <= 1024, 'Saved WoL entry not found or deleted')
    require(value[0] in (0, 1), 'Unsupported WebView string encoding')
    text = value[1:].decode('latin-1' if value[0] == 1 else 'utf-16-le')
    try:
        settings = json.loads(text)
    except (ValueError, UnicodeError):
        raise ValueError('Invalid saved WoL JSON') from None
    require(isinstance(settings, dict) and set(settings) == {'mac', 'broadcast', 'port'}, 'Unexpected WoL schema')
    require(isinstance(settings['mac'], str) and re.fullmatch(r'(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}', settings['mac']), 'Invalid saved MAC')
    require(isinstance(settings['broadcast'], str), 'Invalid saved broadcast')
    try:
        ipaddress.IPv4Address(settings['broadcast'])
    except ipaddress.AddressValueError:
        raise ValueError('Invalid saved broadcast') from None
    require(type(settings['port']) is int and settings['port'] in (7, 9), 'Invalid saved UDP port')
    return settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adb', required=True, type=Path)
    parser.add_argument('--device', required=True)
    args = parser.parse_args()

    def adb_read(command, binary=False):
        # Commands here are fixed read-only operations, not arbitrary user input.
        result = subprocess.run([str(args.adb), '-s', args.device, 'exec-out', command], capture_output=True, timeout=20)
        require(result.returncode == 0, 'Read-only ADB operation failed')
        return result.stdout if binary else result.stdout.decode('utf-8').strip()

    listing = adb_read(f"run-as {PACKAGE} ls -1 '{DIRECTORY}'")
    names = listing.splitlines()
    logs = [name for name in names if re.fullmatch(r'[0-9]{6}\.log', name)]
    require(len(logs) == 1 and not any(name.endswith(('.ldb', '.sst')) for name in names), 'Unsupported LevelDB layout; stop for manual read-only review')
    command = f"run-as {PACKAGE} cat '{DIRECTORY}/{logs[0]}'"
    data = adb_read(command, binary=True)
    settings = wol_from_log(data)
    require(data == adb_read(command, binary=True) and listing == adb_read(f"run-as {PACKAGE} ls -1 '{DIRECTORY}'"),
            'WebView changed during read; stop and retry inspection')
    saved_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    payload = json.dumps({'schema': 1, 'package': PACKAGE, 'storageKey': STORAGE_KEY,
                          'origin': 'file://', 'savedAt': saved_at, 'settings': settings}, separators=(',', ':')).encode()
    protector = DPAPI()
    sealed = protector.seal(payload)
    require(protector.open(sealed) == payload, 'DPAPI recovery round-trip failed')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = ROOT / 'recovery/device-settings' / ('samsung-wol-' + stamp + '.dpapi')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as stream:
        stream.write(sealed)
    require(protector.open(output.read_bytes()) == payload, 'Saved DPAPI backup verification failed')
    receipt = {'savedAt': saved_at, 'package': PACKAGE, 'storageKey': STORAGE_KEY, 'origin': 'file://',
               'backupPath': output.relative_to(ROOT).as_posix(), 'backupSha256': hashlib.sha256(sealed).hexdigest(),
               'fields': ['mac', 'broadcast', 'port'], 'savedValuesValidated': True,
               'stableDoubleRead': True, 'walChecksumsVerified': True, 'dpapiRoundTripPassed': True,
               'plaintextWritten': False, 'unrelatedAppDataSaved': False, 'deviceFilesChanged': False,
               'appOpened': False, 'apkInstalled': False}
    receipt_path = ROOT / '.cache/validation/wol-backup-receipt.json'
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # Never emit raw DB content, JSON payloads or ADB output on errors.
        print('Read-only WoL backup failed: ' + type(error).__name__ + '; stop for review.', file=sys.stderr)
        raise SystemExit(1)
