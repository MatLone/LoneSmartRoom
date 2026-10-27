"""Finite mock-only adapter worker; no operational reader or repair capability."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def deny(event, args):
    if event.startswith(('socket.', 'winreg.')) or event in ('subprocess.Popen', 'os.system', 'os.startfile', 'os.startfile/2', 'ctypes.dlopen', 'ctypes.call_function'):
        raise RuntimeError('operational_access_forbidden')


def serve(input_stream, output_stream):
    from diagnostics.mock_evidence import reports
    from monitoring.ipc import _object, _reject_constant
    # All five adapters and their bounded EvidenceHub are executed, not verdict strings supplied by UI.
    catalogue = reports()
    names = {'overview':'online','healthy':'online','inactive':'inactive','offline':'offline',
        'listener-mismatch':'listener-mismatch','auth-failure':'auth-failure','pipe-absent':'reconnecting',
        'sensor-unavailable':'unsupported','stale':'stale','provider-error':'provider-error',
        'unverified':'startup-inconclusive','recovered':'recovery','startup-inconclusive':'startup-inconclusive'}
    while True:
        line = input_stream.readline(258)
        if not line: return
        if len(line) > 256 or not line.endswith(b'\n'): return
        try:
            q = json.loads(line, object_pairs_hook=_object, parse_constant=_reject_constant)
            if type(q) is not dict or set(q) != {'v','scenario'} or type(q['v']) is not int or q['v'] != 1 or q['scenario'] not in names:
                raise ValueError()
            item = catalogue[names[q['scenario']]]
            response = dict(v=1, scenario=q['scenario'], bundle=dict(schema_version=1,simulation=True,
                report=item['report'],security=item['audit']['security']))
            body = json.dumps(response, separators=(',',':'), allow_nan=False).encode()
            if len(body) > 24576: raise ValueError()
        except Exception:
            body = b'{"v":1,"error":"invalid_mock_query"}'
        output_stream.write(body + b'\n'); output_stream.flush()


if __name__ == '__main__':
    if sys.argv[1:]: raise ValueError('fixed_arguments_required')
    sys.addaudithook(deny)
    serve(sys.stdin.buffer, sys.stdout.buffer)
