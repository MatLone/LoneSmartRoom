from dataclasses import replace
import json
from unittest.mock import patch
import unittest

from monitoring.catalog import DEFAULT_METRICS
from monitoring.collector import Collector
from monitoring.contracts import ContractError
from monitoring.ipc import (LocalAccessPolicy, LocalReadService, MAX_REQUEST_BYTES,
                            MAX_RESPONSE_BYTES, PeerEvidence, encode)
from monitoring_fakes import FakeClock, FakeProvider


SID = 'S-1-5-21-100000000-200000000-300000000-1001'  # Fixture only, no Windows account lookup.


class IpcTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.provider = FakeProvider(DEFAULT_METRICS)
        self.collector = Collector(DEFAULT_METRICS, [self.provider], clock=self.clock)
        self.policy = LocalAccessPolicy(SID, 1)
        self.peer = PeerEvidence(SID, 1, True, False)
        self.service = LocalReadService(self.collector, self.policy)
        self.addCleanup(self.collector.stop)

    def request(self, value=None, peer=None):
        frame = encode(value or {'v': 1, 'op': 'snapshot'})
        return json.loads(self.service.handle(frame, peer or self.peer))

    def test_read_snapshot_never_triggers_collection(self):
        result = self.request()
        self.assertTrue(result['ok'])
        self.assertFalse(result['snapshot']['contains_simulated'])
        self.assertTrue(all(m['value'] is None for m in result['snapshot']['metrics']))
        self.assertEqual(self.provider.call_count, 0)

    def test_simulated_data_cannot_look_like_real_data(self):
        self.collector.step()
        snapshot = self.request()['snapshot']
        self.assertTrue(snapshot['contains_simulated'])
        self.assertTrue(all(m['data_kind'] == 'simulated' for m in snapshot['metrics']))

    def test_capabilities_do_not_claim_sensor_detection_or_transport(self):
        result = self.request({'v': 1, 'op': 'capabilities'})
        self.assertEqual(result['transport'], 'not_implemented')
        self.assertEqual(result['hardware_inventory'], 'declared_slots_not_detected')
        self.assertFalse(result['real_providers_included'])
        self.assertEqual(len(result['metrics']), 22)

    def test_unauthenticated_other_user_other_session_and_remote_denied(self):
        for peer in (replace(self.peer, user_sid=SID + '0'), replace(self.peer, session_id=2),
                     replace(self.peer, authenticated=False), replace(self.peer, remote=True),
                     replace(self.peer, authenticated=1), replace(self.peer, remote=0),
                     replace(self.peer, session_id=True), {'user_sid': SID}, None):
            with self.subTest(peer=type(peer).__name__):
                result = json.loads(self.service.handle(b'{"v":1,"op":"snapshot"}', peer))
                self.assertEqual(result, {'ok': False, 'error': 'access_denied'})

    def test_identity_in_json_never_authenticates_peer(self):
        frame = encode({'v': 1, 'op': 'snapshot', 'user_sid': SID,
                        'authenticated': True, 'session_id': 1})
        self.assertEqual(json.loads(self.service.handle(frame, None))['error'], 'access_denied')
        self.assertEqual(json.loads(self.service.handle(frame, self.peer))['error'], 'invalid_request')

    def test_execution_configuration_and_lifecycle_operations_not_supported(self):
        for op in ('steam', 'cs2', 'start', 'stop', 'set_active', 'powershell',
                   'read_path', 'load_provider', 'history', 'subscribe'):
            self.clock.advance(1)
            self.assertEqual(self.request({'v': 1, 'op': op})['error'], 'invalid_request')
        self.assertEqual(self.provider.call_count, 0)
        self.assertEqual(self.collector.state, 'created')

    def test_unknown_fields_and_arbitrary_paths_rejected(self):
        for field, value in (('path', 'C:/private/file'), ('args', ['-applaunch', '730']),
                             ('metric', 'outside.allowlist'), ('url', 'https://example.com'),
                             ('source', 'ctypes'), ('grant', True)):
            self.clock.advance(1)
            result = self.request({'v': 1, 'op': 'snapshot', field: value})
            self.assertEqual(result['error'], 'invalid_request')

    def test_malformed_duplicate_nonfinite_and_wrong_types_rejected(self):
        frames = [b'', b'\xff', b'[]', b'null', b'{', b'{}',
                  b'{"v":1,"v":1,"op":"snapshot"}',
                  b'{"v":true,"op":"snapshot"}', b'{"v":2,"op":"snapshot"}',
                  b'{"v":1,"op":[]}', b'{"v":NaN,"op":"snapshot"}',
                  b'{"v":1,"op":"snapshot","x":Infinity}', b'[' * 200]
        for frame in frames:
            self.clock.advance(1)
            self.assertEqual(json.loads(self.service.handle(frame, self.peer))['error'], 'invalid_request')

    def test_request_limit_exact_boundary_and_excess(self):
        body = b'{"v":1,"op":"snapshot"}'
        for size, ok in ((MAX_REQUEST_BYTES - 1, True), (MAX_REQUEST_BYTES, True),
                         (MAX_REQUEST_BYTES + 1, False)):
            self.clock.advance(1)
            frame = body + b' ' * (size - len(body))
            self.assertEqual(json.loads(self.service.handle(frame, self.peer))['ok'], ok)

    def test_response_size_limit_and_error_sanitization(self):
        with patch.object(self.collector, 'snapshot', return_value={'too_large': 'x' * MAX_RESPONSE_BYTES}):
            self.assertEqual(self.request()['error'], 'response_too_large')
        for exception in (RuntimeError('PRIVATE TOKEN /path'), ValueError('PRIVATE KEY')):
            self.clock.advance(1)
            with patch.object(self.collector, 'snapshot', side_effect=exception):
                result = self.request()
            self.assertEqual(result, {'ok': False, 'error': 'service_unavailable'})

    def test_global_rate_limit_refill_and_unauthorized_not_counted(self):
        for _ in range(20):
            self.service.handle(b'anything', None)
        for _ in range(4):
            self.assertTrue(self.request()['ok'])
        self.assertEqual(self.request()['error'], 'rate_limited')
        self.clock.advance(0.5)
        self.assertTrue(self.request()['ok'])
        self.assertEqual(self.request()['error'], 'rate_limited')

    def test_stopped_or_stopping_collector_does_not_publish_as_live(self):
        self.collector.request_stop()
        self.assertEqual(self.request()['error'], 'collector_stopped')
        self.collector.stop()
        self.clock.advance(1)
        self.assertEqual(self.request()['error'], 'collector_stopped')

    def test_invalid_local_policy_is_rejected(self):
        for sid, session in (('', 1), ('Everyone', 1), (SID, -1), (SID, True), (SID, 2**32)):
            with self.assertRaises(ContractError):
                LocalAccessPolicy(sid, session)
        with self.assertRaises(ContractError):
            LocalReadService(self.collector, None)

    def test_clock_regression_cannot_refill_bucket(self):
        self.clock.advance(2)
        self.assertTrue(self.request()['ok'])
        self.clock.now = 1
        self.assertEqual(self.request()['error'], 'rate_limited')

    def test_thread_safe_snapshot_and_rate_admission(self):
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(lambda _: self.request(), range(16)))
        self.assertEqual(sum(r['ok'] for r in results), 4)
        self.assertTrue(all(r.get('ok') or r.get('error') == 'rate_limited' for r in results))
