"""Relay mocks only: no sensors, native loading, production requests or writes."""
import copy
import json
from pathlib import Path
import sys
import threading
import tempfile
import ssl
import http.client
import hmac
import hashlib
import secrets
import time
import unittest
from unittest.mock import Mock

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'agent/windows'),str(ROOT/'tests')]
from monitoring.ipc import PeerEvidence
from telemetry.broker import SnapshotBroker
from telemetry.relay import RelayReader,RelayServer,registered_peer,pipe_name,encode,REQUEST,MAX_BYTES
from telemetry_fixtures import snapshot
from telemetry_runtime import TelemetryStatusServer
from secure_protocol import Store,canonical
from secure_tls import create_identity,server_context
from secure_apps import AppRegistry
from test_remote_telemetry import TestProtector


class RelayTests(unittest.TestCase):
    def setUp(self):
        self.peer=dict(sid='S-1-5-21-123',session=1,elevated=False,pid=123,created=987,image='fixed-python')
        self.api=Mock();self.api.own=self.peer;self.api.identity.return_value=self.peer;self.api.alive.return_value=True
        self.api.connect.return_value=55;self.api.create_server.return_value=77
        self.api.client_token.return_value=PeerEvidence(self.peer['sid'],1,True,False)
        self.broker=SnapshotBroker(simulation=True);self.raw=snapshot(time.time());self.broker.publish(self.raw)
        self.api.read_frame.return_value=encode(self.broker.read())
        self.reader=RelayReader(self.api,'a'*32,11,self.peer,simulation=True)
    def test_read_same_snapshot_values_and_monotonic_age(self):
        body=self.reader.read();self.assertIsNotNone(body['snapshot'])
        origin={m['id']:m for m in self.broker.read()['snapshot']['metrics']}
        for m in body['snapshot']['metrics']:
            self.assertEqual(m['value'],origin[m['id']]['value']);self.assertGreaterEqual(m['age_seconds'],origin[m['id']]['age_seconds']-.01)
        self.api.inspect_dacl.assert_called_once_with(55);self.api.close.assert_called_once_with(55)
        self.assertEqual(self.api.write_frame.call_args.args[1],REQUEST)
    def test_disconnect_has_no_stale_fallback_and_keeps_generation(self):
        good=self.reader.read();self.api.connect.side_effect=OSError('private text')
        missing=self.reader.read();self.assertIsNone(missing['snapshot']);self.assertEqual(missing['generation'],good['generation'])
        self.assertNotIn('private text',str(missing));self.api.connect.side_effect=None
        self.assertIsNotNone(self.reader.read()['snapshot'])
    def test_future_old_or_injected_source_rejected(self):
        for mutate in (lambda b:b['snapshot'].update(generated_at='2099-01-01T00:00:00Z'),lambda b:b['snapshot'].update(generated_at='2000-01-01T00:00:00Z'),lambda b:b['snapshot']['metrics'][0].update(source='private.path')):
            body=copy.deepcopy(self.broker.read());mutate(body);self.api.read_frame.return_value=encode(body)
            self.assertIsNone(self.reader.read()['snapshot'])
    def test_unknown_envelope_duplicate_json_and_nonfinite_rejected(self):
        for payload in (b'{"ok":true,"ok":true}',b'{"ok":NaN}',b'[]',b'{"secret":"do not return"}'):
            self.api.read_frame.return_value=payload;value=self.reader.read()
            self.assertIsNone(value['snapshot']);self.assertNotIn('secret',str(value))
    def test_identity_pid_reuse_sid_session_and_elevation_rejected(self):
        for change in ({'created':1234},{'pid':456},{'sid':'S-1-5-21-456'},{'session':2},{'elevated':True},{'image':'other'}):
            self.api.identity.return_value={**self.peer,**change}
            with self.assertRaises(PermissionError):registered_peer(self.api,11,self.peer)
            self.assertIsNone(self.reader.read()['snapshot'])
    def test_acl_or_server_identity_failure_closes_only_owned_connection(self):
        self.api.inspect_dacl.side_effect=PermissionError('wrong acl')
        self.assertIsNone(self.reader.read()['snapshot']);self.api.close.assert_called_once_with(55)
    def test_no_collector_means_unavailable_without_starting_one(self):
        self.broker.clear();self.api.read_frame.return_value=encode(self.broker.read())
        self.assertIsNone(self.reader.read()['snapshot'])
    def test_null_zero_and_read_close(self):
        body=self.reader.read();m={m['id']:m for m in body['snapshot']['metrics']}
        self.assertEqual(m['gpu.adlx.fan_rpm']['value'],0)
        calls=self.api.connect.call_count;self.reader.close();self.assertIsNone(self.reader.read()['snapshot'])
        self.assertEqual(self.api.connect.call_count,calls)
    def test_response_and_endpoint_limits(self):
        with self.assertRaises(ValueError):encode({'data':'x'*(MAX_BYTES+1)})
        for s in ('invalid','a'*31,'a'*32+'\\else'):
            with self.assertRaises(ValueError):pipe_name(s)
    def server_once(self,payload=REQUEST,token=None,last=None):
        stop=threading.Event();server=RelayServer(self.api,self.broker,'b'*32,11,self.peer,stop)
        self.api.read_frame.return_value=payload
        if token is not None:self.api.client_token.return_value=token
        self.api.read_exact.return_value=b'\x06'
        self.api.k.DisconnectNamedPipe.side_effect=lambda _:stop.set()
        server.last=last
        server.open();server.serve();return server
    def test_server_rate_limit_does_not_read_cache(self):
        self.broker.read=Mock(wraps=self.broker.read)
        server=self.server_once(last=time.monotonic())
        self.assertEqual(server.counts['rate_limited'],1);self.broker.read.assert_not_called()
    def test_server_only_reads_cache_and_validates_native_token(self):
        server=self.server_once();self.assertEqual(server.counts['responses'],1)
        self.api.peer.assert_called_once_with(77,11,self.peer,server_side=True)
        self.api.close.assert_called_once_with(77)
    def test_server_rejects_commands_and_foreign_tokens(self):
        for payload,token in [(b'{"v":1,"op":"exec"}',None),(b'{"v":1,"op":"capabilities"}',None),(REQUEST,PeerEvidence('S-1-5-21-456',1,True,False)),(REQUEST,PeerEvidence(self.peer['sid'],1,True,True))]:
            self.setUp();server=self.server_once(payload,token);self.assertEqual(server.counts['responses'],0)
    def test_server_rejects_acl_failure_before_accept(self):
        server=RelayServer(self.api,self.broker,'b'*32,11,self.peer,threading.Event())
        self.api.inspect_dacl.side_effect=PermissionError('acl')
        with self.assertRaises(PermissionError):server.open()
        self.api.accept.assert_not_called();self.api.close.assert_called_once_with(77)


class RelayHttpsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();state=Path(self.temp.name);self.protector=TestProtector()
        create_identity(state,'127.0.0.1',self.protector)
        self.store=Store(state/'devices.db',self.protector);token,_=self.store.begin_pairing();self.device=self.store.pair(token,'simulated relay test')
        peer=dict(sid='S-1-5-21-123',session=1,elevated=False,pid=123,created=987,image='fixed-python')
        self.api=Mock();self.api.own=peer;self.api.identity.return_value=peer;self.api.alive.return_value=True;self.api.connect.return_value=55
        self.broker=SnapshotBroker(simulation=True);self.broker.publish(snapshot(time.time()))
        self.api.read_frame.side_effect=lambda *_:encode(self.broker.read())
        self.reader=RelayReader(self.api,'a'*32,11,peer,simulation=True)
        self.server=TelemetryStatusServer(('127.0.0.1',0),server_context(state,self.protector),self.store,'127.0.0.0/8',
            relay=self.reader,enabled=True,read_devices=[self.device['device_id']])
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.context=ssl.create_default_context(cafile=str(state/'server.crt'))
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.reader.close();self.temp.cleanup()
    def request(self,*,authenticated=True,path='/v2/telemetry'):
        stamp=str(int(time.time()));nonce=secrets.token_hex(16);device=self.device['device_id']
        signature=hmac.new(bytes.fromhex(self.device['secret']),canonical(stamp,nonce,device,'GET',path,b''),hashlib.sha256).hexdigest()
        headers=dict(zip(('X-Lone-Device','X-Lone-Timestamp','X-Lone-Nonce','X-Lone-Signature'),(device,stamp,nonce,signature))) if authenticated else {}
        connection=http.client.HTTPSConnection('127.0.0.1',self.server.server_port,context=self.context,timeout=2)
        try:
            connection.request('GET',path,headers=headers);response=connection.getresponse()
            return response.status,json.loads(response.read(32769))
        finally:connection.close()
    def test_authenticated_read_through_relay_is_separate_from_grants(self):
        self.assertEqual(self.request(authenticated=False)[0],401)
        status,body=self.request();self.assertEqual(status,200);self.assertEqual(len(body['snapshot']['metrics']),29)
        self.assertEqual(AppRegistry(self.store).permissions(self.device['device_id']),[])
        self.server.telemetry_readers=frozenset();self.assertEqual(self.request()[0],403)
    def test_disconnect_unavailable_recovery_and_original_status(self):
        self.api.connect.side_effect=OSError('do not expose')
        status,body=self.request();self.assertEqual(status,200);self.assertIsNone(body['snapshot']);self.assertNotIn('expose',str(body))
        self.api.connect.side_effect=None;self.assertIsNotNone(self.request()[1]['snapshot'])
        self.assertEqual(self.request(path='/v2/status')[1]['agent'],'online')
    def test_explicit_enable_flag_and_registered_source_required(self):
        with self.assertRaises(ValueError):TelemetryStatusServer(relay=self.reader,enabled='yes')
        with self.assertRaises(ValueError):TelemetryStatusServer(relay=object(),enabled=True)

if __name__=='__main__':unittest.main(verbosity=2)
