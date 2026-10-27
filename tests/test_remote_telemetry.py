"""Isolated cache/HTTPS tests; synthetic identity and store, ephemeral loopback only."""
import copy
import hashlib
import hmac
import http.client
import importlib.util
import json
from pathlib import Path
import secrets
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'agent/windows'), str(ROOT/'tests')]
from telemetry.broker import SnapshotBroker
from telemetry.contract import project
from telemetry_fixtures import snapshot
from development_telemetry_http import DevelopmentTelemetryServer
from secure_http import StatusServer
from secure_protocol import Store, canonical
from secure_tls import create_identity, server_context, fingerprint


class TestProtector:
    def seal(self, value): return b'fixture:' + value
    def open(self, value):
        if not value.startswith(b'fixture:'): raise ValueError()
        return value[8:]


class BrokerTests(unittest.TestCase):
    def setUp(self):
        self.wall, self.mono = 1800000000., 100.
        self.broker = SnapshotBroker(simulation=True, utc=lambda:self.wall, monotonic=lambda:self.mono)
        self.raw = snapshot(self.wall)

    def test_pipeline_cache_values_zero_null_expiry(self):
        self.assertTrue(self.broker.publish(self.raw))
        metrics = self.broker.read()['snapshot']['metrics']
        self.assertEqual(next(m for m in metrics if m['id']=='gpu.adlx.fan_rpm')['value'], 0)
        self.mono += 3
        expired = {m['id']:m for m in self.broker.read()['snapshot']['metrics']}
        self.assertIsNone(expired['cpu.utilization']['value'])
        self.assertEqual(expired['cpu.utilization']['state'], 'stale')
        self.assertFalse(self.broker.publish(self.raw))
        self.assertTrue(expired['storage.c.total']['valid'])

    def test_future_old_versions_simulation_and_injections(self):
        for mutate in [lambda s:s.update(schema_version=2), lambda s:s.update(contains_simulated=False),
            lambda s:s.update(generated_at='2099-01-01T00:00:00Z'), lambda s:s.update(generated_at='2000-01-01T00:00:00Z'),
            lambda s:s['metrics'][0].update(id='execute.shell'), lambda s:s['metrics'][0].update(value=float('nan')),
            lambda s:s['metrics'][0].update(value=None), lambda s:s['metrics'][0].update(source='secret.path'),
            lambda s:s['metrics'][0].update(age_seconds=-1), lambda s:s['metrics'][0].update(unit='watts'),
            lambda s:s['metrics'][0].update(valid='true'), lambda s:s['metrics'][0].update(ingress_age_seconds=1.51)]:
            value = copy.deepcopy(self.raw); mutate(value)
            with self.assertRaises(ValueError): self.broker.publish(value)
        with self.assertRaises(ValueError): project(self.raw, simulation=False, now=self.wall)

    def test_projection_drops_private_fields_and_clone(self):
        self.raw['secret'] = 'NEVER PUBLIC'; self.raw['metrics'][0]['path'] = 'NEVER PUBLIC'
        self.broker.publish(self.raw)
        self.assertNotIn('NEVER PUBLIC', json.dumps(self.broker.read()))
        public = self.broker.read(); public['snapshot']['metrics'].clear()
        self.assertEqual(len(self.broker.read()['snapshot']['metrics']), 29)

    def test_empty_disconnect_generation_and_real_source(self):
        self.assertIsNone(self.broker.read()['snapshot'])
        self.broker.publish(self.raw); old = self.broker.generation; self.broker.clear()
        self.assertNotEqual(old, self.broker.generation); self.assertIsNone(self.broker.read()['snapshot'])
        from telemetry.contract import source_for
        self.raw['contains_simulated'] = False
        for m in self.raw['metrics']: m.update(data_kind='real',source=source_for(m['id']))
        self.assertEqual(project(self.raw, now=self.wall)['metrics'][0]['value'], 0.025)

    def test_temporal_limits_and_missing_gpu(self):
        self.raw['metrics'] = [m for m in self.raw['metrics'] if not m['id'].startswith('gpu.')]
        self.broker.publish(self.raw)
        self.assertEqual(len(self.broker.read()['snapshot']['metrics']), 21)
        self.mono -= 1; self.assertIsNone(self.broker.read()['snapshot'])

    def test_inconsistent_ratios_and_unsafe_integers(self):
        for key, value in [('ram.utilization', 0), ('storage.c.occupation', 100), ('ram.total', 2**53)]:
            raw = copy.deepcopy(self.raw)
            next(m for m in raw['metrics'] if m['id'] == key)['value'] = value
            with self.assertRaises(ValueError): self.broker.publish(raw)

    def test_development_composition_cannot_use_production_state(self):
        spec=importlib.util.spec_from_file_location('telemetry_development_composition',ROOT/'scripts/monitoring-telemetry-client.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory(dir=ROOT/'.cache') as temp:
            root=Path(temp);session='a'*32;state=root/'.cache/telemetry-development'/session;state.mkdir(parents=True)
            with self.assertRaises(ValueError):module.development_state(root,session)
            for name in ('server.crt','server.key','tls.dpapi','devices.db','telemetry-readers.json'):(state/name).write_bytes(b'synthetic fixture only')
            (state/'DEVELOPMENT-TELEMETRY').write_bytes(b'LSR-TELEMETRY-DEV-LOOPBACK-v1\n')
            self.assertEqual(module.development_state(root,session),state)
            (state/'DEVELOPMENT-TELEMETRY').write_bytes(b'operational')
            with self.assertRaises(ValueError):module.development_state(root,session)


class HttpsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(dir=ROOT/'.cache')
        cls.state = Path(cls.temp.name); cls.protector = TestProtector()
        create_identity(cls.state, '127.0.0.1', cls.protector)
        cls.store = Store(cls.state/'isolated.db', cls.protector)
        code,_ = cls.store.begin_pairing(); cls.device = cls.store.pair(code, 'SYNTHETIC ANDROID')
        cls.broker = SnapshotBroker(simulation=True)
        cls.broker.publish(snapshot(time.time()))
        spec=importlib.util.spec_from_file_location('development_telemetry_composition',ROOT/'scripts/monitoring-telemetry-client.py')
        composition=importlib.util.module_from_spec(spec);spec.loader.exec_module(composition)
        cls.server = DevelopmentTelemetryServer(('127.0.0.1', 0), composition.development_context(cls.state,cls.protector), cls.store,
            '127.0.0.0/8', telemetry=cls.broker, development_enabled=True, telemetry_readers=[cls.device['device_id']])
        cls.thread = threading.Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()
        cls.context = ssl.create_default_context(cafile=str(cls.state/'server.crt'))

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(2); cls.temp.cleanup()

    def headers(self, path='/v2/telemetry', device=None):
        device=device or self.device; stamp=str(int(time.time())); nonce=secrets.token_hex(16)
        signature=hmac.new(bytes.fromhex(device['secret']),canonical(stamp,nonce,device['device_id'],'GET',path,b''),hashlib.sha256).hexdigest()
        return dict(zip(('X-Lone-Device','X-Lone-Timestamp','X-Lone-Nonce','X-Lone-Signature'),(device['device_id'],stamp,nonce,signature)))

    def request(self,path='/v2/telemetry',headers=None,context=None):
        c=http.client.HTTPSConnection('127.0.0.1',self.server.server_port,context=context or self.context,timeout=2)
        try:
            c.request('GET',path,headers=headers or {}); r=c.getresponse(); body=r.read(32769)
            self.assertLessEqual(len(body),32768)
            return r.status,json.loads(body)
        finally:c.close()

    def setUp(self): self.server.telemetry_tokens=4

    def test_https_to_android_contract(self):
        self.broker.clear(); self.broker.publish(snapshot(time.time()))
        code,body=self.request(headers=self.headers());self.assertEqual(code,200)
        self.assertTrue(body['snapshot']['contains_simulated'])
        out=ROOT/'.cache/telemetry-tests';out.mkdir(parents=True,exist_ok=True)
        (out/'https-frame.json').write_text(json.dumps(body),encoding='utf-8')
        # Explicit simulation is preserved all the way to the renderer test input.
        self.assertEqual(len(body['snapshot']['metrics']),29)
        self.assertEqual(fingerprint(self.state),hashlib.sha256(ssl.PEM_cert_to_DER_cert((self.state/'server.crt').read_text())).hexdigest())

    def test_hmac_replay_revocation_wrong_path_and_no_grants(self):
        self.assertEqual(self.request()[0],401)
        headers=self.headers();self.assertEqual(self.request(headers=headers)[0],200);self.assertEqual(self.request(headers=headers)[0],401)
        self.assertEqual(self.request(headers=self.headers('/v2/status'))[0],401)
        self.assertEqual(self.request('/v2/telemetry?command=shutdown',self.headers())[0],404)
        code,_=self.store.begin_pairing();d=self.store.pair(code,'REVOKED FIXTURE');self.store.revoke(d['device_id'])
        self.assertEqual(self.request(headers=self.headers(device=d))[0],401)

    def test_rate_disabled_scope_and_status_regression(self):
        for _ in range(4):self.assertEqual(self.request(headers=self.headers())[0],200)
        self.assertEqual(self.request(headers=self.headers())[0],429)
        self.assertEqual(self.request('/v2/status',self.headers('/v2/status'))[0],200)
        self.server.telemetry=None
        try:self.assertEqual(self.request(headers=self.headers())[0],404)
        finally:self.server.telemetry=self.broker
        self.assertNotIn('telemetry',StatusServer.__init__.__code__.co_varnames)

    def test_tls_hostname_and_untrusted_cert(self):
        with self.assertRaises(ssl.SSLCertVerificationError):self.request(context=ssl.create_default_context())
        self.assertTrue(self.context.check_hostname)
        self.assertNotEqual(fingerprint(self.state),'00'*32)

    def test_pairing_alone_does_not_grant_telemetry_read(self):
        code,_=self.store.begin_pairing();other=self.store.pair(code,'NO READ SCOPE FIXTURE')
        self.assertEqual(self.request(headers=self.headers(device=other))[0],403)
        self.assertEqual(self.request('/v2/status',self.headers('/v2/status',device=other))[0],200)

    def test_source_failure_is_sanitized(self):
        class Broken:
            def read(self):raise ValueError('private token path')
        self.server.telemetry=Broken()
        try:
            status,body=self.request(headers=self.headers());self.assertEqual(status,503);self.assertNotIn('private',json.dumps(body))
        finally:self.server.telemetry=self.broker

    def test_oversized_response_is_rejected(self):
        class Oversized:
            def read(self): return {'ok':True,'unexpected':'x'*40000}
        self.server.telemetry=Oversized()
        try: self.assertEqual(self.request(headers=self.headers())[0],503)
        finally: self.server.telemetry=self.broker

    def test_android_production_pin_and_hmac(self):
        jdk=Path('C:/Program Files/Android/Android Studio/jbr/bin')
        classes=ROOT/'apps/android/app/build/tmp/kotlin-classes/debug'
        stdlib=next((ROOT/'.cache/gradle/caches/modules-2/files-2.1/org.jetbrains.kotlin/kotlin-stdlib/2.0.21').rglob('kotlin-stdlib-2.0.21.jar'))
        output=self.state/'jvm';output.mkdir(exist_ok=True)
        cp=str(classes)+';'+str(stdlib)
        subprocess.run([str(jdk/'javac.exe'),'-encoding','UTF-8','-classpath',cp,'-d',str(output),
            str(ROOT/'apps/android/app/src/main/java/com/lonesmartroom/app/PinnedTls.java'),str(ROOT/'tests/AndroidTelemetryTlsTest.java')],check=True,capture_output=True,timeout=15)
        self.broker.clear();self.broker.publish(snapshot(time.time()))
        target=ROOT/'.cache/telemetry-tests/jvm-frame.json';target.parent.mkdir(exist_ok=True,parents=True)
        result=subprocess.run([str(jdk/'java.exe'),'-classpath',str(output)+';'+cp,'AndroidTelemetryTlsTest',
            str(self.server.server_port),fingerprint(self.state),str(target)],input=self.device['device_id']+'\n'+self.device['secret']+'\n',
            capture_output=True,text=True,timeout=15)
        (ROOT/'.cache/telemetry-tests/jvm-error.log').write_text(result.stderr,encoding='utf-8')
        self.assertEqual(result.returncode,0,'Isolated Android pin/HMAC JVM regression failed')
        self.assertEqual(json.loads(target.read_bytes())['telemetry_version'],1)


if __name__=='__main__':unittest.main(verbosity=2)
