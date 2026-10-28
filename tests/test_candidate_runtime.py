"""Synthetic loopback identities ONLY. Tests composed drain+telemetry+HMAC."""
from pathlib import Path
import sys
import tempfile
import threading
import time
import ssl
import unittest
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'agent/windows'),str(ROOT/'agent/development'),str(ROOT/'tests')]
from candidate_runtime import DrainingTelemetryServer,run_candidate,RECOVERABLE_EXIT
from graceful_runtime import DrainingServer,ServerExited
from telemetry.relay import RelayReader
from telemetry.broker import SnapshotBroker
import test_remote_telemetry as remote
from telemetry_fixtures import snapshot
from secure_protocol import Store
from secure_tls import create_identity,server_context

class ComposedServerTests(unittest.TestCase):
    headers=remote.HttpsTests.headers
    request=remote.HttpsTests.request
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(dir=ROOT/'.cache');cls.state=Path(cls.temp.name)
        cls.protector=remote.TestProtector();create_identity(cls.state,'127.0.0.1',cls.protector)
        cls.store=Store(cls.state/'fixture.db',cls.protector)
        token,_=cls.store.begin_pairing();cls.device=cls.store.pair(token,'SYNTHETIC')
        cls.broker=SnapshotBroker(simulation=True)
        cls.relay=object.__new__(RelayReader);cls.relay.read=cls.broker.read
        cls.server=DrainingTelemetryServer(('127.0.0.1',0),server_context(cls.state,cls.protector),cls.store,
            '127.0.0.0/8',relay=cls.relay,enabled=True,read_devices=[cls.device['device_id']])
        cls.thread=threading.Thread(target=cls.server.serve_forever,kwargs={'poll_interval':.02},daemon=True);cls.thread.start()
        cls.context=ssl.create_default_context(cafile=str(cls.state/'server.crt'))
    @classmethod
    def tearDownClass(cls):
        cls.server.stop_admission();cls.server.shutdown();cls.server.server_close()
        cls.server.wait_drained();cls.thread.join(1);cls.temp.cleanup()
    def setUp(self):
        self.server.telemetry_tokens=4
        self.broker.clear();self.broker.publish(snapshot(time.time()))
    def test_existing_authenticated_route_with_null_zero_distinction(self):
        self.assertIsInstance(self.server,DrainingServer)
        status,body=self.request(headers=self.headers())
        self.assertEqual(status,200);self.assertIsNotNone(body['snapshot'])
        metrics={m['id']:m for m in body['snapshot']['metrics']}
        self.assertEqual(metrics['gpu.adlx.fan_rpm']['value'],0)
        self.assertTrue(body['snapshot']['contains_simulated'])
        self.server.wait_drained()
        self.assertEqual(self.server.active_requests,0)
    def test_no_auth_and_no_scope_fail_closed(self):
        self.assertEqual(self.request()[0],401)
        allowed=self.server.telemetry_readers
        try:
            self.server.telemetry_readers=frozenset()
            self.assertEqual(self.request(headers=self.headers())[0],403)
        finally:self.server.telemetry_readers=allowed
    def test_route_disabled_without_registered_reader(self):
        relay=self.server.telemetry
        try:
            self.server.telemetry=None
            self.assertEqual(self.request(headers=self.headers())[0],404)
        finally:self.server.telemetry=relay
    def test_replay_still_rejected(self):
        headers=self.headers()
        self.assertEqual(self.request(headers=headers)[0],200)
        self.assertEqual(self.request(headers=headers)[0],401)

class RuntimeClassificationTests(unittest.TestCase):
    def test_only_cleaned_server_exit_is_recoverable(self):
        # No DPAPI, operational config, credentials, socket or collector.
        layout=Mock();layout.root=ROOT
        relay=Mock()
        for failure,recoverable in [(ServerExited('serve_loop_exited'),True),(ValueError('private cert error'),False)]:
            with patch('secure_store.DPAPI',return_value=Mock(open=Mock(return_value=b'{"host":"127.0.0.1","port":0,"network":"127.0.0.0/8"}'))),patch('pathlib.Path.read_bytes',return_value=b'synthetic'),patch('secure_protocol.validate_lan'),patch('secure_protocol.Store'),patch('candidate_runtime.serve',side_effect=failure):
                if recoverable:self.assertEqual(run_candidate(layout,Mock(),Mock(),relay=relay),RECOVERABLE_EXIT)
                else:
                    with self.assertRaises(ValueError):run_candidate(layout,Mock(),Mock(),relay=relay)
            self.assertTrue(relay.close.called)

if __name__=='__main__':unittest.main()
