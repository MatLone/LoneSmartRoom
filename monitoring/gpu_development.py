"""Bounded development-only GPU ownership/lifetime. No native calls on import."""
import hashlib
from subprocess import TimeoutExpired
import time


def validate_gpu_mode(root, enabled, application, simulated, duration):
    if type(enabled) is not bool:
        raise ValueError('boolean_required')
    if enabled and (application or simulated or (root/'BUNDLED-MONITORING.json').exists()
                    or type(duration) is not int or not 1<=duration<=70):
        raise PermissionError('gpu_requires_bounded_real_development')


def claim_gpu_owner(api):
    # A retained FIRST_PIPE_INSTANCE handle, not a lock file or a command endpoint.
    # Existing pipe implementation enforces the account DACL and rejects remote clients.
    # launch_native inherits only this lease (plus stdio) into the owned bridge,
    # keeping name ownership until native exit even if the Python parent dies.
    sid=api.own['sid']
    from .pipe_protocol import descriptor
    descriptor(sid)
    if api.own['elevated']:
        raise PermissionError('elevated_monitoring_forbidden')
    name=r'\\.\pipe\LoneSmartRoom.Monitoring.Gpu.Dev.Owner.'+hashlib.sha256(sid.encode('ascii')).hexdigest()
    handle=api.create_server(name)
    try:
        api.inspect_dacl(handle)
        return handle
    except Exception:
        api.close(handle)
        raise


def finish_gpu(adapter, pending=lambda:None):
    """Wait for owned cooperative exit. No kill, restart or false timeout success.

    Called after Collector.stop: its reading thread has stopped. If the native
    process has not finished, keep its owner/IPC supervisor alive and report pending.
    The bridge also has its existing bounded watchdog and EOF exit mechanism.
    """
    reported=False
    while True:
        try:
            adapter.close()
        except Exception:
            pass  # Diagnostics remain fixed codes in the adapter, never exception text.
        process=adapter.transport.process
        try:
            if process is None or process.poll() is not None:
                return adapter.clean is True
        except OSError:
            pass  # Cannot confirm exit: retain ownership and keep reporting pending.
        if not reported:
            pending()
            reported=True
        # Wait only on this owned child. Timeout is not termination or a new read.
        try:
            process.wait(timeout=.25)
        except TimeoutExpired:
            pass
        except OSError:
            time.sleep(.25)


class ReadActivity:
    """Infer UI demand from authenticated cache reads; no new wire operations.

    Foreground polls at 1 s, background at 10 s. After 4 s without an authorized
    snapshot, use inactive cadences. Unauthorized clients cannot change demand.
    """
    def __init__(self,collector,now):
        self.collector,self.now=collector,now
        self.last=now();self.active=True

    def _set(self,active):
        if active!=self.active:
            self.active=active;self.collector.set_active(active)

    def tick(self):
        if self.now()-self.last>=4:self._set(False)

    def read(self):
        now=self.now();self._set(now-self.last<4);self.last=now
