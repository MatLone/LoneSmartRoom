"""Two explicit application IDs, local per-device grants, durable command results.

No path, URI, arguments or shell text is accepted from the network. The existing
v1.5 executor is reached only through launch_allowed after allowlist validation.
"""
import queue
import re
import threading
import ctypes
import os

APPS = frozenset(('steam', 'cs2'))
ID = re.compile(r'[0-9a-f]{32}')


class AppError(Exception):
    def __init__(self, status, code):
        self.status, self.code = status, code
        super().__init__(code)


def require_interactive_user():
    if os.name != 'nt' or ctypes.windll.shell32.IsUserAnAdmin():
        raise PermissionError('Launch requires a non-elevated Windows user')
    session = ctypes.c_uint()
    if not ctypes.windll.kernel32.ProcessIdToSessionId(os.getpid(), ctypes.byref(session)) or session.value == 0:
        raise PermissionError('Launch requires an interactive user session')


def launch_allowed(app):
    if app not in APPS:
        raise ValueError('Application is not allowlisted')
    require_interactive_user()
    from agent import execute_action
    return execute_action(app)


class AppRegistry:
    def __init__(self, store):
        self.store = store
        with store.connect() as db:
            db.executescript('''
              CREATE TABLE IF NOT EXISTS app_permissions(
                device TEXT NOT NULL,app TEXT NOT NULL CHECK(app IN ('steam','cs2')),
                PRIMARY KEY(device,app));
              CREATE TABLE IF NOT EXISTS app_commands(
                device TEXT NOT NULL,request_id TEXT NOT NULL,app TEXT NOT NULL CHECK(app IN ('steam','cs2')),
                state TEXT NOT NULL,created INTEGER NOT NULL,updated INTEGER NOT NULL,error TEXT,
                PRIMARY KEY(device,request_id));
            ''')

    def permissions(self, device):
        with self.store.connect() as db:
            return [r[0] for r in db.execute('''SELECT app FROM app_permissions WHERE device=?
                AND EXISTS(SELECT 1 FROM devices WHERE id=? AND revoked=0) ORDER BY app''', (device, device))]

    def set_permission(self, device, apps, allowed):
        if not ID.fullmatch(device) or not apps or any(app not in APPS for app in apps):
            raise ValueError('Invalid explicit device/application permission')
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if not db.execute('SELECT 1 FROM devices WHERE id=? AND revoked=0', (device,)).fetchone():
                raise ValueError('Unknown or revoked device')
            for app in apps:
                if allowed:
                    db.execute('INSERT OR IGNORE INTO app_permissions VALUES (?,?)', (device, app))
                else:
                    db.execute('DELETE FROM app_permissions WHERE device=? AND app=?', (device, app))

    @staticmethod
    def public(row):
        if row is None:
            return None
        request_id, app, state, created, updated, error = row
        return {'ok': True, 'request_id': request_id, 'app': app,
                'state': 'accepted' if state == 'dispatching' else state,
                'in_progress': state == 'dispatching', 'created': created, 'updated': updated,
                'error': error, 'process_running_verified': False}

    def result(self, device, request_id):
        with self.store.connect() as db:
            return self.public(db.execute('''SELECT request_id,app,state,created,updated,error
                FROM app_commands WHERE device=? AND request_id=?''', (device, request_id)).fetchone())

    def accept(self, device, request_id, app):
        now = int(self.store.clock())
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if not db.execute('''SELECT 1 FROM devices d JOIN app_permissions p ON p.device=d.id
                WHERE d.id=? AND d.revoked=0 AND p.app=?''', (device, app)).fetchone():
                raise AppError(403, 'app_not_authorized')
            row = db.execute('''SELECT request_id,app,state,created,updated,error FROM app_commands
                WHERE device=? AND request_id=?''', (device, request_id)).fetchone()
            if row:
                if row[1] != app:
                    raise AppError(409, 'request_id_conflict')
                return self.public(row), False
            count = db.execute('SELECT count(*) FROM app_commands WHERE device=?', (device,)).fetchone()[0]
            if count >= 1000:
                raise AppError(429, 'command_history_full')
            recent = db.execute('SELECT count(*) FROM app_commands WHERE device=? AND created>=?', (device, now-60)).fetchone()[0]
            if recent >= 6:
                raise AppError(429, 'app_rate_limited')
            db.execute('INSERT INTO app_commands VALUES (?,?,?,?,?,?,NULL)',
                       (device, request_id, app, 'accepted', now, now))
            return self.public((request_id, app, 'accepted', now, now, None)), True

    def claim(self, device, request_id, private_network):
        now = int(self.store.clock())
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT app,created,state FROM app_commands WHERE device=? AND request_id=?',
                             (device, request_id)).fetchone()
            if not row or row[2] != 'accepted':
                return None
            permitted = db.execute('''SELECT 1 FROM devices d JOIN app_permissions p ON p.device=d.id
                WHERE d.id=? AND d.revoked=0 AND p.app=?''', (device, row[0])).fetchone()
            error = ('network_not_private' if not private_network else 'authorization_revoked' if not permitted
                     else 'command_expired' if not 0 <= now-row[1] <= 30 else None)
            if error:
                db.execute('UPDATE app_commands SET state=?,updated=?,error=? WHERE device=? AND request_id=?',
                           ('failed', now, error, device, request_id))
                return None
            # Durable claim BEFORE handing anything to Windows. Never auto-repeat
            # this dispatch after a crash or a lost network response.
            db.execute('UPDATE app_commands SET state=?,updated=? WHERE device=? AND request_id=?',
                       ('dispatching', now, device, request_id))
            return row[0]

    def finish(self, device, request_id, error=None):
        with self.store.connect() as db:
            db.execute('''UPDATE app_commands SET state=?,updated=?,error=?
                WHERE device=? AND request_id=? AND state='dispatching' ''',
                       ('failed' if error else 'executed', int(self.store.clock()), error, device, request_id))

    def abandon_on_start(self):
        with self.store.connect() as db:
            db.execute('''UPDATE app_commands SET error=CASE WHEN state='dispatching'
                THEN 'execution_uncertain' ELSE 'agent_restarted' END,state='failed',updated=?
                WHERE state IN ('accepted','dispatching')''', (int(self.store.clock()),))


class AppDispatcher:
    """Single bounded worker; an injected executor is mandatory (no test fallback)."""
    def __init__(self, registry, executor, private_guard, capacity=8):
        self.registry, self.executor, self.private_guard = registry, executor, private_guard
        self.queue = queue.Queue(maxsize=capacity)
        self.lock, self.stopped = threading.Lock(), threading.Event()
        self.registry.abandon_on_start()
        self.worker = threading.Thread(target=self._work, name='lsr-app-launch', daemon=True)
        self.worker.start()

    def submit(self, device, payload):
        if (not isinstance(payload, dict) or set(payload) != {'request_id', 'app', 'confirmed'}
                or not isinstance(payload['request_id'], str) or not ID.fullmatch(payload['request_id'])
                or not isinstance(payload['app'], str) or payload['app'] not in APPS
                or payload['confirmed'] is not True):
            raise AppError(400, 'invalid_app_request')
        with self.lock:
            if self.stopped.is_set():
                raise AppError(503, 'agent_stopping')
            existing = self.registry.result(device, payload['request_id'])
            if self.queue.full() and existing is None:
                raise AppError(429, 'app_queue_full')
            result, created = self.registry.accept(device, payload['request_id'], payload['app'])
            if created:
                self.queue.put_nowait((device, payload['request_id']))
            return result

    def _work(self):
        while not self.stopped.is_set():
            try:
                device, request_id = self.queue.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                try:
                    private = not self.stopped.is_set() and self.private_guard()
                except Exception:
                    private = False
                app = self.registry.claim(device, request_id, private)
                if app is not None:
                    try:
                        self.executor(app)
                    except Exception:
                        self.registry.finish(device, request_id, 'launcher_failed')
                    else:
                        self.registry.finish(device, request_id)
            finally:
                self.queue.task_done()

    def close(self):
        self.stopped.set()
        self.worker.join(timeout=2)
        # Accepted work is never carried to a new process. An already-dispatched
        # Windows request cannot be cancelled by closing/revoking the agent.
