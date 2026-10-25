"""Opt-in lifecycle adapters. Existing handler/TLS/HMAC/executors stay unchanged."""
import ipaddress
import queue
from socketserver import ThreadingMixIn
import threading
from secure_apps import AppDispatcher
from secure_http import StatusServer
from launcher_logs import error_code


class DrainingServer(StatusServer):
    def __init__(self, *args, **kwargs):
        self.admission = threading.Condition()
        self.accepting, self.active_requests = True, 0
        super().__init__(*args, **kwargs)

    def stop_admission(self):
        with self.admission:
            self.accepting = False

    def process_request(self, request, address):
        # Same LAN/slot policy as StatusServer, plus a serialized admission gate.
        with self.admission:
            if (not self.accepting or ipaddress.ip_address(address[0]) not in self.network
                    or not self.slots.acquire(False)):
                request.close()
                return
            self.active_requests += 1  # Count before a request thread can start.
            try:
                ThreadingMixIn.process_request(self, request, address)
            except BaseException:
                self.slots.release()
                self.active_requests -= 1
                self.admission.notify_all()
                request.close()
                raise

    def process_request_thread(self, request, address):
        try:
            # Original private-profile guard, TLS, timeout, handler and cleanup.
            super().process_request_thread(request, address)
        finally:
            with self.admission:
                self.active_requests -= 1
                self.admission.notify_all()

    def wait_drained(self):
        with self.admission:
            while self.active_requests:
                self.admission.wait(0.1)


class DrainingDispatcher(AppDispatcher):
    """Original submit/authorization; queued jobs cancel, claimed job completes."""
    def _cancel(self, device, request_id):
        with self.registry.store.connect() as db:
            db.execute('''UPDATE app_commands SET state='failed',updated=?,error='agent_stopping'
                WHERE device=? AND request_id=? AND state='accepted' ''',
                (int(self.registry.store.clock()), device, request_id))

    def quiesce(self):
        with self.lock:
            self.stopped.set()  # Inherited submit now refuses new work with 503.
            while True:
                try:
                    item = self.queue.get_nowait()
                except queue.Empty:
                    break
                try:
                    self._cancel(*item)
                finally:
                    self.queue.task_done()

    def _work(self):
        while not self.stopped.is_set():
            try:
                device, request_id = self.queue.get(timeout=0.1)
            except queue.Empty:
                continue
            try:
                with self.lock:
                    if self.stopped.is_set():
                        self._cancel(device, request_id)
                        continue
                    try:
                        private = self.private_guard()
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

    def wait_drained(self):
        self.queue.join()
        self.worker.join()  # No two-second cutoff and no forced cancellation.

    def close(self):
        self.quiesce()
        self.wait_drained()


class Shutdown:
    """One cleanup owner. Deadline is a warning, never permission to kill/release."""
    def __init__(self, server, apps, serving, log, grace=15):
        if not 0 < grace <= 60:
            raise ValueError('invalid_grace')
        self.server, self.apps, self.serving, self.log, self.grace = server, apps, serving, log, grace
        self.lock, self.done = threading.Lock(), threading.Event()
        self.started, self.expired = False, False
        self.logs_healthy = True

    def emit(self, event, **metadata):
        try:
            self.log.emit(event, **metadata)
        except Exception:
            # A full/unavailable log must not skip socket/thread cleanup.
            self.logs_healthy = False

    def _deadline(self):
        if not self.done.wait(self.grace):
            self.expired = True
            self.emit('shutdown_deadline_exceeded', phase='worker')

    def stop(self):
        with self.lock:
            owner = not self.started
            self.started = True
        if not owner:
            self.done.wait()
            return self.logs_healthy
        watchdog = threading.Thread(target=self._deadline, name='lsr-stop-deadline', daemon=True)
        watchdog.start()
        self.emit('shutdown_requested', phase='worker')
        # Errors fail closed: never acknowledge completion or release the mutex
        # while cleanup cannot be proved. A later authorized diagnosis is needed.
        try:
            self.server.stop_admission()
            self.apps.quiesce()
            if self.serving.is_alive():
                self.server.shutdown()  # Called outside the serve_forever thread.
            self.serving.join()
            self.server.server_close()
            self.emit('listener_closed', phase='worker')
            self.server.wait_drained()
            self.apps.wait_drained()
        except BaseException as error:
            self.emit('shutdown_failed', phase='worker', code=error_code(error))
            # Deliberately stay alive/quiesced; do not turn cleanup failure into
            # successful exit with live daemon threads or a released lease.
            self.done.wait()
            return
        self.emit('shutdown_complete', phase='worker')
        self.done.set()
        watchdog.join()
        return self.logs_healthy


def serve(config, store, channel, log, *, private_guard, context_factory,
          registry_factory, executor, server_factory=DrainingServer,
          dispatcher_factory=DrainingDispatcher):
    """Same secure configuration; only a future opt-in worker calls this runtime."""
    while not channel.wait_stop(0):
        if not private_guard():
            channel.wait_stop(1)
            continue
        context = context_factory()
        if channel.wait_stop(0):
            break
        server = server_factory((config['host'], config['port']), context, store,
                                config['network'], private_guard=private_guard)
        apps = None
        serving = None
        started = False
        reason = 'server_failure'
        try:
            apps = dispatcher_factory(registry_factory(store), executor, private_guard)
            server.apps = apps
            serving = threading.Thread(target=server.serve_forever, kwargs={'poll_interval':0.1},
                                       name='lsr-https', daemon=True)
            serving.start()
            started = True
            while serving.is_alive():
                if channel.wait_stop(0.2):
                    reason = 'local_stop'
                    break
                if not private_guard():
                    reason = 'network_change'
                    break
        finally:
            if started:
                if not Shutdown(server, apps, serving, log).stop():
                    return 26  # Resources drained, but no successful log receipt.
            else:
                server.stop_admission()
                server.server_close()
                if apps is not None:
                    apps.close()
        if reason == 'server_failure' and not channel.wait_stop(0):
            # An unexpected serve thread exit is not silently relaunched.
            raise RuntimeError('serve_loop_exited')
    return 0
