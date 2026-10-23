"""HTTPS app control with injected fake executors only. Never launches a real app."""
import concurrent.futures
import hashlib
import hmac
import http.client
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
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'agent/windows'))
from secure_apps import AppRegistry, AppDispatcher, launch_allowed, require_interactive_user
from secure_http import StatusServer
from secure_protocol import Store, canonical
from secure_store import DPAPI
from secure_tls import create_identity, server_context, fingerprint


class AppCommandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / '.cache/tests').mkdir(parents=True, exist_ok=True)
        cls.identity = tempfile.TemporaryDirectory(dir=ROOT / '.cache/tests')
        cls.tls_path = Path(cls.identity.name)
        create_identity(cls.tls_path, '127.0.0.1', DPAPI())
        cls.context = ssl.create_default_context(cafile=str(cls.tls_path / 'server.crt'))

    @classmethod
    def tearDownClass(cls):
        cls.identity.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / '.cache/tests')
        self.store = Store(Path(self.temp.name) / 'devices.db', DPAPI())
        self.registry = AppRegistry(self.store)
        self.calls, self.block, self.launch_fail, self.private = [], False, False, True
        self.started, self.release = threading.Event(), threading.Event()
        def fake(app):
            self.calls.append(app)
            self.started.set()
            if self.block:
                self.release.wait(timeout=10)
            if self.launch_fail:
                raise OSError('synthetic launch failure; never passed to network')
        self.fake = fake
        self.apps = AppDispatcher(self.registry, fake, lambda: self.private, capacity=1)
        self.server = StatusServer(('127.0.0.1', 0), server_context(self.tls_path, DPAPI()), self.store,
                                   '127.0.0.0/8', apps=self.apps)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.release.set()
        self.apps.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.temp.cleanup()

    def device(self, apps=()):
        code, _ = self.store.begin_pairing()
        result = self.store.pair(code, 'Synthetic app test')
        if apps:
            self.registry.set_permission(result['device_id'], list(apps), True)
        return result

    def headers(self, device, method, path, body=b'', offset=0, secret=None):
        stamp, nonce = str(int(time.time()) + offset), secrets.token_hex(16)
        signature = hmac.new(bytes.fromhex(secret or device['secret']),
            canonical(stamp, nonce, device['device_id'], method, path, body), hashlib.sha256).hexdigest()
        result = {'X-Lone-Device': device['device_id'], 'X-Lone-Timestamp': stamp,
                  'X-Lone-Nonce': nonce, 'X-Lone-Signature': signature}
        if body:
            result['Content-Type'] = 'application/json'
        return result

    def request(self, method, path, device=None, body=b'', headers=None):
        connection = http.client.HTTPSConnection('127.0.0.1', self.server.server_port, timeout=4, context=self.context)
        try:
            connection.request(method, path, body=body or None,
                               headers=headers if headers is not None else self.headers(device, method, path, body))
            response = connection.getresponse()
            return response.status, json.loads(response.read())
        finally:
            connection.close()

    def post(self, device, app='steam', request_id=None, **extra):
        data = {'request_id': request_id or secrets.token_hex(16), 'app': app, 'confirmed': True, **extra}
        body = json.dumps(data, separators=(',', ':')).encode()
        return self.request('POST', '/v2/apps/commands', device, body), data['request_id']

    def terminal(self, device, request_id):
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline:
            result = self.registry.result(device['device_id'], request_id)
            if result and result['state'] in ('executed', 'failed'):
                return result
            time.sleep(0.02)
        self.fail('Synthetic command did not terminate')

    def drain(self):
        deadline = time.monotonic()+4
        while self.apps.queue.unfinished_tasks and time.monotonic()<deadline:
            time.sleep(0.02)
        self.assertEqual(self.apps.queue.unfinished_tasks, 0, 'Synthetic queue did not drain')

    def test_pairing_is_not_permission_and_migration_preserves_status(self):
        device = self.device()
        reopened = AppRegistry(Store(self.store.path, DPAPI()))
        self.assertEqual(reopened.permissions(device['device_id']), [])
        self.assertEqual(self.request('GET', '/v2/status', device)[0], 200)
        self.assertEqual(self.request('GET', '/v2/apps', device)[1]['allowed_apps'], [])
        self.assertEqual(self.post(device)[0][0], 403)
        self.assertEqual(self.calls, [])

    def test_requested_accepted_executed_and_duplicate_not_reexecuted(self):
        device = self.device(('steam', 'cs2'))
        self.block = True
        response, rid = self.post(device)
        self.assertEqual(response[0], 202)
        self.assertEqual(response[1]['state'], 'accepted')
        self.assertTrue(self.started.wait(2))
        self.assertEqual(self.post(device, request_id=rid)[0][0], 202)
        self.assertEqual(self.post(device, app='cs2', request_id=rid)[0][0], 409)
        self.release.set()
        result = self.terminal(device, rid)
        self.assertEqual(result['state'], 'executed')
        self.assertFalse(result['process_running_verified'])
        self.assertEqual(self.post(device, request_id=rid)[0][1]['state'], 'executed')
        self.assertEqual(self.calls, ['steam'])

    def test_wrong_credentials_replay_expiry_and_body_tampering(self):
        device = self.device(('steam', 'cs2'))
        path = '/v2/apps/commands'
        body = json.dumps({'request_id': secrets.token_hex(16), 'app': 'steam', 'confirmed': True}).encode()
        self.assertEqual(self.request('POST', path, body=body, headers={'Content-Type': 'application/json'})[0], 401)
        bad = self.headers(device, 'POST', path, body, secret='00'*32)
        self.assertEqual(self.request('POST', path, body=body, headers=bad)[0], 401)
        expired = self.headers(device, 'POST', path, body, offset=-90)
        self.assertEqual(self.request('POST', path, body=body, headers=expired)[0], 401)
        headers = self.headers(device, 'POST', path, body)
        self.assertEqual(self.request('POST', path, body=body.replace(b'steam', b'cs2'), headers=headers)[0], 401)
        headers = self.headers(device, 'POST', path, body)
        self.assertEqual(self.request('POST', path, body=body, headers=headers)[0], 202)
        self.assertEqual(self.request('POST', path, body=body, headers=headers)[0], 401)
        self.assertEqual(self.terminal(device, json.loads(body)['request_id'])['state'], 'executed')
        self.assertEqual(self.calls, ['steam'])

    def test_unknown_apps_shell_power_and_extra_arguments_rejected(self):
        device = self.device(('steam', 'cs2'))
        for app in ('shutdown', 'restart', 'sleep', 'cancel_shutdown', 'powershell', 'cmd.exe',
                    'steam://run/1', 'steam; calc', '../steam.exe', '', 'STEAM'):
            with self.subTest(app=app):
                self.assertEqual(self.post(device, app=app)[0][0], 400)
        for extra in ({'args': []}, {'path': 'steam.exe'}, {'command': 'ignored'}, {'scope': 'admin'}, {'confirmed': 1}, {'confirmed': False}):
            self.assertEqual(self.post(device, **extra)[0][0], 400)
        for path in ('/v1/action', '/v2/action', '/v2/apps/grant', '/v2/apps/permissions', '/v2/apps/commands?app=steam', '/v2/apps/commands/../steam'):
            self.assertEqual(self.request('POST', path, device, b'{}')[0], 404)
        self.assertEqual(self.calls, [])

    def test_strict_json_duplicate_headers_and_limits(self):
        device = self.device(('steam',))
        path = '/v2/apps/commands'
        for body in (b'{}', b'[]', b'{bad', b'{"app":"steam","app":"cs2"}', b'{"value":NaN}', b'x'*1025):
            self.assertEqual(self.request('POST', path, device, body)[0], 400)
        body = json.dumps({'request_id': secrets.token_hex(16), 'app': 'steam', 'confirmed': True}).encode()
        headers = self.headers(device, 'POST', path, body)
        connection = http.client.HTTPSConnection('127.0.0.1', self.server.server_port, timeout=4, context=self.context)
        try:
            connection.putrequest('POST', path)
            for key, value in headers.items():
                connection.putheader(key, value)
            connection.putheader('X-Lone-Device', device['device_id'])
            connection.putheader('Content-Length', str(len(body)))
            connection.endheaders(body)
            response = connection.getresponse()
            self.assertEqual(response.status, 401)
            response.read()
        finally:
            connection.close()
        self.assertEqual(self.calls, [])

    def test_results_are_device_scoped(self):
        owner, other = self.device(('steam',)), self.device(('steam',))
        _, rid = self.post(owner)
        self.terminal(owner, rid)
        self.assertEqual(self.request('GET', '/v2/apps/commands/'+rid, other)[0], 404)
        self.assertEqual(self.request('GET', '/v2/apps/commands/'+rid, owner)[1]['state'], 'executed')

    def test_app_permission_revoked_while_queued(self):
        device = self.device(('steam', 'cs2'))
        self.block = True
        _, first = self.post(device)
        self.assertTrue(self.started.wait(2))
        _, second = self.post(device, 'cs2')
        self.registry.set_permission(device['device_id'], ['cs2'], False)
        self.release.set()
        self.assertEqual(self.terminal(device, second)['error'], 'authorization_revoked')
        self.assertEqual(self.calls, ['steam'])
        self.assertEqual(self.request('GET', '/v2/status', device)[0], 200)

    def test_device_revoked_while_queued(self):
        device = self.device(('steam', 'cs2'))
        self.block = True
        self.post(device)
        self.assertTrue(self.started.wait(2))
        _, second = self.post(device, 'cs2')
        self.store.revoke(device['device_id'])
        self.release.set()
        self.assertEqual(self.terminal(device, second)['error'], 'authorization_revoked')
        self.assertEqual(self.request('GET', '/v2/apps', device)[0], 401)
        self.assertEqual(self.calls, ['steam'])

    def test_private_profile_and_expiration_rechecked_before_dispatch(self):
        device = self.device(('steam', 'cs2'))
        self.block = True
        self.post(device)
        self.assertTrue(self.started.wait(2))
        _, second = self.post(device, 'cs2')
        self.private = False
        self.release.set()
        self.assertEqual(self.terminal(device, second)['error'], 'network_not_private')
        self.assertEqual(self.calls, ['steam'])
        self.private = True
        result, _ = self.registry.accept(device['device_id'], secrets.token_hex(16), 'cs2')
        now = self.store.clock()
        self.store.clock = lambda: now+31
        self.assertIsNone(self.registry.claim(device['device_id'], result['request_id'], True))
        self.assertEqual(self.registry.result(device['device_id'], result['request_id'])['error'], 'command_expired')

    def test_executor_failure_is_safe_and_not_retried(self):
        device = self.device(('steam',))
        self.launch_fail = True
        _, rid = self.post(device)
        result = self.terminal(device, rid)
        self.assertEqual(result['state'], 'failed')
        self.assertEqual(result['error'], 'launcher_failed')
        self.post(device, request_id=rid)
        self.assertEqual(self.calls, ['steam'])

    def test_restart_does_not_redispatch_uncertain_or_queued_work(self):
        self.apps.close()
        device = self.device(('steam',))
        first, _ = self.registry.accept(device['device_id'], secrets.token_hex(16), 'steam')
        second, _ = self.registry.accept(device['device_id'], secrets.token_hex(16), 'steam')
        rid1, rid2 = first['request_id'], second['request_id']
        self.registry.claim(device['device_id'], rid1, True)
        reopened = AppRegistry(Store(self.store.path, DPAPI()))
        self.apps = AppDispatcher(reopened, self.fake, lambda: True)
        self.server.apps = self.apps
        self.assertEqual(reopened.result(device['device_id'], rid1)['error'], 'execution_uncertain')
        self.assertEqual(reopened.result(device['device_id'], rid2)['error'], 'agent_restarted')
        self.assertEqual(self.post(device, request_id=rid1)[0][1]['state'], 'failed')
        self.assertEqual(self.calls, [])

    def test_bounded_queue_rate_and_history_limits(self):
        device = self.device(('steam',))
        self.block = True
        self.post(device)
        self.assertTrue(self.started.wait(2))
        self.post(device)
        self.assertEqual(self.post(device)[0][1]['error'], 'app_queue_full')
        self.release.set()
        self.drain()
        self.block = False
        for _ in range(4):
            _, rid = self.post(device)
            self.terminal(device, rid)
        self.assertEqual(self.post(device)[0][1]['error'], 'app_rate_limited')
        with self.store.connect() as db:
            db.executemany('INSERT INTO app_commands VALUES (?,?,?,?,?,?,NULL)',
                [(device['device_id'], f'{i:032x}', 'steam', 'executed', 1, 1) for i in range(1000)])
        self.assertEqual(self.post(device)[0][1]['error'], 'command_history_full')

    def test_concurrent_duplicate_is_dispatched_once(self):
        device = self.device(('steam',))
        self.block = True
        rid = secrets.token_hex(16)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.post(device, request_id=rid)[0][0], range(2)))
        self.assertEqual(results, [202, 202])
        self.release.set()
        self.terminal(device, rid)
        self.assertEqual(self.calls, ['steam'])

    def test_adapter_steam_direct_cs2_legacy_and_no_arbitrary_action(self):
        import agent
        with patch('steam_launcher.launch_steam', return_value='dispatch only') as direct, \
                patch.object(agent.os, 'startfile', create=True) as start, patch.object(agent.subprocess, 'run') as shell:
            launch_allowed('steam')
            launch_allowed('cs2')
            for app in ('shutdown', 'restart', 'sleep', 'powershell', 'steam://open/other'):
                with self.assertRaises(ValueError):
                    launch_allowed(app)
            direct.assert_called_once_with()
            self.assertEqual([call.args[0] for call in start.call_args_list], ['steam://rungameid/730'])
            shell.assert_not_called()

    def test_https_production_adapter_requires_grant_and_dispatches_direct_once(self):
        import steam_launcher
        self.apps.executor = launch_allowed
        device = self.device()
        executable = Path(self.temp.name)/'steam.exe'
        with patch('secure_apps.require_interactive_user'), \
                patch.object(steam_launcher, 'validated_steam_executable', return_value=executable) as resolver, \
                patch.object(steam_launcher, '_canonical_executable', return_value=executable), \
                patch.object(steam_launcher.subprocess, 'Popen') as process, patch('os.startfile') as uri:
            self.assertEqual(self.post(device)[0][0], 403)
            resolver.assert_not_called(); process.assert_not_called()
            self.registry.set_permission(device['device_id'], ['steam'], True)
            response, rid = self.post(device)
            self.assertEqual(response[0], 202)
            result = self.terminal(device, rid)
            self.assertEqual(result['state'], 'executed')
            self.assertFalse(result['process_running_verified'])
            self.assertEqual(self.post(device, request_id=rid)[0][1]['state'], 'executed')
            self.assertEqual(self.post(device, app='cs2')[0][0], 403)
            process.assert_called_once()
            self.assertEqual(process.call_args.args, ([str(executable)],))
            self.assertEqual(process.call_args.kwargs['cwd'], str(executable.parent))
            self.assertFalse(process.call_args.kwargs['shell'])
            uri.assert_not_called()

    def test_https_production_adapter_missing_executable_is_failure_without_retry(self):
        import steam_launcher
        self.apps.executor = launch_allowed
        device = self.device(('steam',))
        with patch('secure_apps.require_interactive_user'), \
                patch.object(steam_launcher, 'validated_steam_executable', side_effect=FileNotFoundError) as resolver, \
                patch.object(steam_launcher.subprocess, 'Popen') as process, patch('os.startfile') as uri:
            _, rid = self.post(device)
            result = self.terminal(device, rid)
            self.assertEqual((result['state'], result['error']), ('failed', 'launcher_failed'))
            self.post(device, request_id=rid)
            resolver.assert_called_once()
            process.assert_not_called(); uri.assert_not_called()

    def test_admin_and_noninteractive_sessions_cannot_launch(self):
        import ctypes
        import agent
        with patch.object(ctypes.windll.shell32, 'IsUserAnAdmin', return_value=1), patch.object(agent.os, 'startfile') as start:
            with self.assertRaises(PermissionError):
                launch_allowed('steam')
            start.assert_not_called()
        def session_zero(pid, output):
            output._obj.value = 0
            return 1
        with patch.object(ctypes.windll.shell32, 'IsUserAnAdmin', return_value=0), patch.object(ctypes.windll.kernel32, 'ProcessIdToSessionId', side_effect=session_zero):
            with self.assertRaises(PermissionError):
                require_interactive_user()

    def test_android_production_post_hmac_interoperability(self):
        device = self.device(('steam', 'cs2'))
        jdk = Path('C:/Program Files/Android/Android Studio/jbr/bin')
        classes = ROOT / 'apps/android/app/build/tmp/kotlin-classes/debug'
        stdlib = next((ROOT / '.cache/gradle/caches/modules-2/files-2.1/org.jetbrains.kotlin/kotlin-stdlib/2.0.21').rglob('kotlin-stdlib-2.0.21.jar'))
        output = Path(self.temp.name) / 'java';output.mkdir()
        classpath = str(classes)+';'+str(stdlib)
        subprocess.run([str(jdk/'javac.exe'), '-encoding', 'UTF-8', '-classpath', classpath, '-d', str(output),
            str(ROOT/'apps/android/app/src/main/java/com/lonesmartroom/app/PinnedTls.java'),
            str(ROOT/'tests/AndroidAppAuthTest.java')], capture_output=True, check=True)
        result = subprocess.run([str(jdk/'java.exe'), '-classpath', str(output)+';'+classpath, 'AndroidAppAuthTest',
            str(self.server.server_port), fingerprint(self.tls_path)], input=device['device_id']+'\n'+device['secret']+'\n',
            capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.drain()
        self.assertEqual(self.calls, ['steam'])
