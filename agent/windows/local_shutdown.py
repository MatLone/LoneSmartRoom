"""Local Windows stop/completion events, current-account ACL; no network or PID kill."""
import ctypes as c
from ctypes import wintypes as w
import hashlib
import re
from launcher_win32 import Attributes, SecurityError

NAME = re.compile(r'Global\\LoneSmartRoom\.(?:Graceful\.v1\.[0-9a-f]{64}|GracefulTests\.[0-9a-f]{32})')


def identity(root, sid):
    value = sid + '|' + str(root).casefold()
    return 'Global\\LoneSmartRoom.Graceful.v1.' + hashlib.sha256(value.encode('utf-8')).hexdigest()


class Channel:
    def __init__(self, api, stop, done):
        self.api, self.stop, self.done = api, stop, done

    def wait_stop(self, seconds=0):
        return self.api.wait(self.stop, seconds)

    def complete(self):
        self.api.win._ok(self.api.win.k.SetEvent(self.done))

    def close(self):
        for name in ('stop', 'done'):
            handle = getattr(self, name)
            if handle:
                self.api.win.k.CloseHandle(handle)
                setattr(self, name, None)


class LocalEvents:
    def __init__(self, windows):
        self.win = windows
        k = windows.k
        k.CreateEventW.argtypes = [c.POINTER(Attributes), w.BOOL, w.BOOL, w.LPCWSTR]
        k.CreateEventW.restype = w.HANDLE
        k.OpenEventW.argtypes = [w.DWORD, w.BOOL, w.LPCWSTR]
        k.OpenEventW.restype = w.HANDLE
        k.SetEvent.argtypes = [w.HANDLE]; k.SetEvent.restype = w.BOOL

    @staticmethod
    def validate(name):
        if not isinstance(name, str) or not NAME.fullmatch(name):
            raise SecurityError('invalid_local_channel')

    def _create(self, name):
        descriptor = w.LPVOID()
        # Explicit EVENT_ALL_ACCESS, protected owner-only DACL, non-inheritable.
        sddl = f'O:{self.win.sid}D:P(A;;0x001f0003;;;{self.win.sid})'
        self.win._ok(self.win.a.ConvertStringSecurityDescriptorToSecurityDescriptorW(
            sddl, 1, c.byref(descriptor), None))
        try:
            attributes = Attributes(c.sizeof(Attributes), descriptor, False)
            c.set_last_error(0)
            handle = self.win.k.CreateEventW(c.byref(attributes), True, False, name)
            error = c.get_last_error()
        finally:
            self.win.k.LocalFree(descriptor)
        self.win._ok(handle)
        try:
            if error == 183:
                # Never reset another session's event or adopt a stale signal.
                raise SecurityError('channel_exists')
            self.win._verify(handle, kernel=True)
            return handle
        except BaseException:
            self.win.k.CloseHandle(handle)
            raise

    def create(self, name):
        self.validate(name)
        stop = self._create(name + '.stop')
        try:
            return Channel(self, stop, self._create(name + '.done'))
        except BaseException:
            self.win.k.CloseHandle(stop)
            raise

    def _open(self, name, access):
        handle = self.win.k.OpenEventW(access | 0x20000, False, name)  # READ_CONTROL
        if not handle:
            error = c.get_last_error()
            if error == 2:
                return None
            raise c.WinError(error)
        try:
            self.win._verify(handle, kernel=True)
            return handle
        except BaseException:
            self.win.k.CloseHandle(handle)
            raise

    def wait(self, handle, seconds):
        if not 0 <= seconds <= 60:
            raise ValueError('invalid_wait')
        result = self.win.k.WaitForSingleObject(handle, int(seconds * 1000))
        if result not in (0, 0x102):
            raise c.WinError(c.get_last_error())
        return result == 0

    def request(self, name, seconds=30):
        self.validate(name)
        if not 0 <= seconds <= 60:
            raise ValueError('invalid_wait')
        done = self._open(name + '.done', 0x100000)  # SYNCHRONIZE, not modify
        if done is None:
            return 'not_running'
        stop = None
        try:
            stop = self._open(name + '.stop', 2)  # EVENT_MODIFY_STATE, not create
            if stop is None:
                return 'not_running'
            self.win._ok(self.win.k.SetEvent(stop))
            return 'completed' if self.wait(done, seconds) else 'timed_out'
        finally:
            if stop:
                self.win.k.CloseHandle(stop)
            self.win.k.CloseHandle(done)
