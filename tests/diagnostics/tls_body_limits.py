"""Explicit opt-in transport experiment; never imports/runs an operational agent.

Run from the repository root with the existing Windows venv. All identities,
devices and servers belong to the existing disposable test fixture. Experimental
handlers live only here. No real executors, production grants or retries.
"""
from pathlib import Path
import argparse
import collections
import http.client
import importlib.util
import json
import ssl
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('transport_fixture', ROOT / 'tests/test_app_commands.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
from secure_http import Handler, StatusServer


class BoundedDiscardHandler(Handler):
    """Proposal only: discard at most 4096 clear-framed bytes, within 0.5 s."""
    def body(self):
        lengths = self.headers.get_all('Content-Length', [])
        types = self.headers.get_all('Content-Type', [])
        if (not self.headers.get('Transfer-Encoding') and len(lengths) == 1 and len(types) == 1
                and lengths[0].isascii() and lengths[0].isdecimal() and len(lengths[0]) <= 4
                and 1024 < int(lengths[0]) <= 4096
                and self.headers.get_content_type() == 'application/json'):
            self._body_read = True
            previous = self.connection.gettimeout()
            deadline = time.monotonic() + 0.5
            remaining = int(lengths[0])
            try:
                while remaining:
                    budget = deadline - time.monotonic()
                    if budget <= 0:
                        raise TimeoutError('Discard deadline')
                    self.connection.settimeout(budget)
                    raw = self.rfile.read1(remaining)
                    if not raw:
                        break
                    remaining -= len(raw)
                    self.server.transport_events['bounded_bytes_discarded'] += len(raw)
            except (OSError, ValueError):
                self.server.transport_events['discard_timeouts_or_io_errors'] += 1
            finally:
                self.connection.settimeout(previous)
            raise ValueError('Invalid request framing')
        return super().body()


class OrderlyCloseServer(StatusServer):
    """Proposal only: test a bounded TLS close handshake without body changes."""
    def process_request_thread(self, request, address):
        try:
            if self.private_guard is not None and not self.private_guard():
                return
            request.settimeout(5)
            with self.tls.wrap_socket(request, server_side=True) as secured:
                self.finish_request(secured, address)
                secured.settimeout(0.5)
                try:
                    raw = secured.unwrap()
                    self.transport_events['unwrap_completed'] += 1
                    raw.close()
                except (OSError, ValueError) as error:
                    self.transport_events['unwrap_' + type(error).__name__] += 1
        except (OSError, ValueError):
            pass
        finally:
            request.close()
            self.slots.release()
            self.transport_events['connections_finished'] += 1


def request(case, device, scenario):
    name, declared, sent, mode = scenario
    payload = b'x' * sent
    headers = case.headers(device, 'POST', '/v2/apps/commands', payload or b'x')
    result = {'case': name, 'declaredBytes': declared, 'sentBytes': sent,
              'status': None, 'complete': False}
    connection = http.client.HTTPSConnection('127.0.0.1', case.server.server_port,
                                            timeout=4, context=case.context)
    start = time.monotonic()
    stage = 'send'
    try:
        connection.putrequest('POST', '/v2/apps/commands')
        for key, value in headers.items():
            connection.putheader(key, value)
        connection.putheader('Content-Length', str(declared))
        if mode == 'duplicate':
            connection.putheader('Content-Length', str(declared))
        if mode == 'transfer':
            connection.putheader('Transfer-Encoding', 'chunked')
        if mode == 'drip':
            connection.endheaders(payload[:16])
            for offset in range(16, len(payload), 16):
                time.sleep(0.15)
                connection.send(payload[offset:offset+16])
        else:
            connection.endheaders(payload or None)
        stage = 'read-status'
        response = connection.getresponse()
        result['status'] = response.status
        stage = 'read-body'
        raw = response.read()
        result['complete'] = (response.status == 400 and json.loads(raw).get('ok') is False
                              and len(raw) == int(response.getheader('Content-Length')))
        result['responseBytes'] = len(raw)
    except (OSError, http.client.HTTPException, ValueError) as error:
        result.update(error=type(error).__name__, stage=stage,
                      winerror=getattr(error, 'winerror', None))
    finally:
        connection.close()
    result['seconds'] = round(time.monotonic() - start, 4)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rounds', type=int, default=12)
    args = parser.parse_args()
    if not 1 <= args.rounds <= 12:
        raise SystemExit('Use 1..12 independent rounds; no retries.')
    target = args.output.resolve()
    if not target.is_relative_to((ROOT / '.cache/validation').resolve()):
        raise SystemExit('Output must stay in the ignored validation workspace.')
    target.parent.mkdir(parents=True, exist_ok=True)
    scenarios = [(f'invalid-json-{size}', size, size, '') for size in (1, 1023, 1024)]
    scenarios += [(f'oversized-{size}', size, size, '') for size in (1025, 4096, 4097, 65536)]
    scenarios += [('oversized-header-only', 1025, 0, ''), ('oversized-partial', 1025, 17, ''),
                  ('oversized-drip-partial', 1025, 64, 'drip'),
                  ('duplicate-length', 1025, 1025, 'duplicate'),
                  ('transfer-and-length', 1025, 1025, 'transfer')]
    variants = [('operational-code-unmodified', StatusServer, Handler),
                ('proposal-bounded-discard', StatusServer, BoundedDiscardHandler),
                ('proposal-unwrap-only', OrderlyCloseServer, Handler)]
    results = {'python': sys.version.split()[0], 'openssl': ssl.OPENSSL_VERSION,
               'productionModified': False, 'retries': 0, 'rounds': args.rounds,
               'loopbackOnly': True, 'ephemeralFixtureOnly': True, 'variants': {}}
    Case = fixture.AppCommandTests
    Case.setUpClass()
    try:
        for name, server_class, handler_class in variants:
            case = Case('test_strict_json_duplicate_headers_and_limits')
            case.setUp()
            try:
                assert Path(case.temp.name).resolve().is_relative_to((ROOT / '.cache/tests').resolve())
                case.server.shutdown()
                case.server.server_close()
                case.thread.join(timeout=3)
                case.server = server_class(('127.0.0.1', 0), fixture.server_context(case.tls_path, fixture.DPAPI()),
                                           case.store, '127.0.0.0/8', apps=case.apps)
                case.server.RequestHandlerClass = handler_class
                case.server.transport_events = collections.Counter()
                case.thread = threading.Thread(target=case.server.serve_forever, daemon=True)
                case.thread.start()
                device = case.device()  # No app grant, even in the synthetic database.
                trials = []
                for index in range(args.rounds):
                    for scenario in scenarios:
                        result = request(case, device, scenario)
                        result['round'] = index + 1
                        trials.append(result)
                # Normal authenticated traffic and zero permissions still work.
                assert case.request('GET', '/v2/status', device)[0] == 200
                assert case.request('GET', '/v2/apps', device)[1]['allowed_apps'] == []
                assert case.post(device)[0][0] == 403
                assert not case.calls
                # Wait for any bounded experimental shutdown to finish before reporting.
                if server_class is OrderlyCloseServer:
                    deadline = time.monotonic() + 2
                    while (case.server.transport_events['connections_finished'] < len(trials) + 3
                           and time.monotonic() < deadline):
                        time.sleep(0.02)
                summary = {}
                for scenario in scenarios:
                    subset = [row for row in trials if row['case'] == scenario[0]]
                    summary[scenario[0]] = {
                        'requests': len(subset), 'complete400': sum(row['complete'] for row in subset),
                        'resets': sum(row.get('error') == 'ConnectionResetError' for row in subset),
                        'errors': dict(collections.Counter(row.get('error', 'none') for row in subset)),
                        'maxSeconds': max(row['seconds'] for row in subset),
                    }
                results['variants'][name] = {'summary': summary, 'trials': trials,
                    'transportEvents': dict(case.server.transport_events), 'fakeExecutorCalls': len(case.calls),
                    'statusAuthenticated': True, 'grantsEmpty': True, 'ungrantedCommandRejected': True}
                target.write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8', newline='\n')
                print(json.dumps({'variant': name, 'summary': summary, 'events': dict(case.server.transport_events)}, indent=2))
            finally:
                case.tearDown()
    finally:
        Case.tearDownClass()


if __name__ == '__main__':
    main()
