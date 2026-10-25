"""Bounded read-only wire contract. No native calls or collection on import."""
import json
import re
import struct

from .ipc import MAX_REQUEST_BYTES, MAX_RESPONSE_BYTES, _object, _reject_constant

PREFIX = '\\\\.\\pipe\\LoneSmartRoom.Monitoring.Dev.v1.'
CLIENT_RIGHTS = 0x00120183  # read/write DATA + attributes + READ_CONTROL/SYNCHRONIZE; NOT append/create-instance.


def pipe_name(session):
    if type(session) is not str or not re.fullmatch('[a-f0-9]{32}', session):
        raise ValueError('invalid_development_session')
    return PREFIX + session


def descriptor(sid):
    if type(sid) is not str or not re.fullmatch(r'S-1-(?:[0-9]+-)+[0-9]+', sid):
        raise ValueError('invalid_sid')
    return 'O:' + sid + 'G:' + sid + 'D:P(A;;0x00120183;;;' + sid + ')'


def frame(payload, limit):
    if type(payload) is not bytes or not 1 <= len(payload) <= limit:
        raise ValueError('frame_size')
    return struct.pack('!I', len(payload)) + payload


def length(header, limit):
    if type(header) is not bytes or len(header) != 4:
        raise ValueError('invalid_header')
    size, = struct.unpack('!I', header)
    if not 1 <= size <= limit:
        raise ValueError('frame_size')
    return size


def request(payload):
    if type(payload) is not bytes or not 1 <= len(payload) <= MAX_REQUEST_BYTES:
        raise ValueError('invalid_request')
    value = json.loads(payload.decode('utf-8'), object_pairs_hook=_object, parse_constant=_reject_constant)
    if (type(value) is not dict or set(value) != {'v', 'op'} or type(value['v']) is not int
            or value['v'] != 1 or value['op'] not in ('snapshot', 'capabilities')):
        raise ValueError('invalid_request')
    return value


def same_peer(actual, expected):
    """Expected identity comes from held, spawned-process handles, never JSON."""
    return (type(actual) is dict and type(expected) is dict
            and all(actual.get(k) == expected.get(k) for k in ('pid', 'created', 'sid', 'session', 'image'))
            and actual.get('elevated') is False and expected.get('elevated') is False)
