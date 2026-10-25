"""Opt-in Windows named pipes. stdlib only; no DLL loaded on import.

One retained FIRST_PIPE_INSTANCE, explicit account-only DACL, remote rejection,
bounded overlapped I/O, OS token/session and exact spawned-process checks.
Same-account code injection/token theft is NOT isolated by these checks.
"""
import ctypes as ct
from ctypes import wintypes as w
import os
import time

from .ipc import PeerEvidence
from .pipe_protocol import CLIENT_RIGHTS, descriptor, frame, length, same_peer


class Overlapped(ct.Structure):
    _fields_ = [('Internal', ct.c_size_t), ('InternalHigh', ct.c_size_t),
                ('Offset', w.DWORD), ('OffsetHigh', w.DWORD), ('hEvent', w.HANDLE)]


class SecurityAttributes(ct.Structure):
    _fields_ = [('length', w.DWORD), ('descriptor', ct.c_void_p), ('inherit', w.BOOL)]


class Memory(ct.Structure):
    _fields_ = [('cb', w.DWORD), ('faults', w.DWORD)] + [(k, ct.c_size_t) for k in (
        'peak_working_set', 'working_set', 'peak_paged', 'paged', 'peak_nonpaged',
        'nonpaged', 'pagefile', 'peak_pagefile', 'private_commit')]


class AclInformation(ct.Structure):
    _fields_ = [('count', w.DWORD), ('used', w.DWORD), ('free', w.DWORD)]


def bind(dll, name, args, result):
    fn = getattr(dll, name); fn.argtypes = args; fn.restype = result
    return fn


def checked(ok):
    if not ok:
        raise OSError(ct.get_last_error(), 'local_pipe_operation_failed')
    return ok


def ticks(value):
    return (value.dwHighDateTime << 32) | value.dwLowDateTime


class WindowsPipeApi:
    def __init__(self):
        if os.name != 'nt' or ct.sizeof(ct.c_void_p) != 8:
            raise RuntimeError('windows_x64_required')
        self.k = ct.WinDLL('kernel32.dll', use_last_error=True, winmode=0x800)
        self.a = ct.WinDLL('advapi32.dll', use_last_error=True, winmode=0x800)
        k, a = self.k, self.a
        bind(k, 'GetCurrentProcess', [], w.HANDLE)
        bind(k, 'GetCurrentThread', [], w.HANDLE)
        bind(k, 'OpenProcess', [w.DWORD, w.BOOL, w.DWORD], w.HANDLE)
        bind(k, 'CloseHandle', [w.HANDLE], w.BOOL)
        bind(k, 'GetProcessId', [w.HANDLE], w.DWORD)
        bind(k, 'WaitForSingleObject', [w.HANDLE, w.DWORD], w.DWORD)
        bind(k, 'ProcessIdToSessionId', [w.DWORD, ct.POINTER(w.DWORD)], w.BOOL)
        bind(k, 'GetProcessTimes', [w.HANDLE] + [ct.POINTER(w.FILETIME)] * 4, w.BOOL)
        bind(k, 'QueryFullProcessImageNameW', [w.HANDLE, w.DWORD, w.LPWSTR, ct.POINTER(w.DWORD)], w.BOOL)
        bind(k, 'K32GetProcessMemoryInfo', [w.HANDLE, ct.POINTER(Memory), w.DWORD], w.BOOL)
        bind(k, 'CreateNamedPipeW', [w.LPCWSTR, w.DWORD, w.DWORD, w.DWORD, w.DWORD, w.DWORD,
                                   w.DWORD, ct.POINTER(SecurityAttributes)], w.HANDLE)
        bind(k, 'CreateFileW', [w.LPCWSTR, w.DWORD, w.DWORD, ct.c_void_p, w.DWORD, w.DWORD, w.HANDLE], w.HANDLE)
        bind(k, 'ConnectNamedPipe', [w.HANDLE, ct.POINTER(Overlapped)], w.BOOL)
        bind(k, 'DisconnectNamedPipe', [w.HANDLE], w.BOOL)
        bind(k, 'ReadFile', [w.HANDLE, ct.c_void_p, w.DWORD, ct.POINTER(w.DWORD), ct.POINTER(Overlapped)], w.BOOL)
        bind(k, 'WriteFile', [w.HANDLE, ct.c_void_p, w.DWORD, ct.POINTER(w.DWORD), ct.POINTER(Overlapped)], w.BOOL)
        bind(k, 'CreateEventW', [ct.c_void_p, w.BOOL, w.BOOL, w.LPCWSTR], w.HANDLE)
        bind(k, 'GetOverlappedResult', [w.HANDLE, ct.POINTER(Overlapped), ct.POINTER(w.DWORD), w.BOOL], w.BOOL)
        bind(k, 'CancelIoEx', [w.HANDLE, ct.POINTER(Overlapped)], w.BOOL)
        bind(k, 'GetNamedPipeClientProcessId', [w.HANDLE, ct.POINTER(w.ULONG)], w.BOOL)
        bind(k, 'GetNamedPipeServerProcessId', [w.HANDLE, ct.POINTER(w.ULONG)], w.BOOL)
        bind(k, 'LocalFree', [ct.c_void_p], ct.c_void_p)
        bind(a, 'OpenProcessToken', [w.HANDLE, w.DWORD, ct.POINTER(w.HANDLE)], w.BOOL)
        bind(a, 'OpenThreadToken', [w.HANDLE, w.DWORD, w.BOOL, ct.POINTER(w.HANDLE)], w.BOOL)
        bind(a, 'GetTokenInformation', [w.HANDLE, ct.c_int, ct.c_void_p, w.DWORD, ct.POINTER(w.DWORD)], w.BOOL)
        bind(a, 'ConvertSidToStringSidW', [ct.c_void_p, ct.POINTER(ct.c_void_p)], w.BOOL)
        bind(a, 'ConvertStringSecurityDescriptorToSecurityDescriptorW', [w.LPCWSTR, w.DWORD,
                          ct.POINTER(ct.c_void_p), ct.POINTER(w.ULONG)], w.BOOL)
        bind(a, 'ImpersonateNamedPipeClient', [w.HANDLE], w.BOOL)
        bind(a, 'RevertToSelf', [], w.BOOL)
        bind(a, 'GetSecurityInfo', [w.HANDLE, ct.c_int, w.DWORD] + [ct.POINTER(ct.c_void_p)] * 5, w.DWORD)
        bind(a, 'GetSecurityDescriptorControl', [ct.c_void_p, ct.POINTER(w.WORD), ct.POINTER(w.DWORD)], w.BOOL)
        bind(a, 'GetAclInformation', [ct.c_void_p, ct.c_void_p, w.DWORD, ct.c_int], w.BOOL)
        bind(a, 'GetAce', [ct.c_void_p, w.DWORD, ct.POINTER(ct.c_void_p)], w.BOOL)
        self.own = self.identity(self.k.GetCurrentProcess())
        if self.own['elevated']:
            raise PermissionError('elevated_monitoring_forbidden')

    def close(self, handle):
        if handle is not None and handle != ct.c_void_p(-1).value:
            checked(self.k.CloseHandle(handle))

    def token_identity(self, token):
        size = w.DWORD()
        self.a.GetTokenInformation(token, 1, None, 0, ct.byref(size))
        if not 8 <= size.value <= 65536:
            raise PermissionError('invalid_token')
        buffer = ct.create_string_buffer(size.value)
        checked(self.a.GetTokenInformation(token, 1, buffer, size, ct.byref(size)))
        sid_ptr = ct.cast(buffer, ct.POINTER(ct.c_void_p))[0]
        text = ct.c_void_p()
        checked(self.a.ConvertSidToStringSidW(sid_ptr, ct.byref(text)))
        try: sid = ct.wstring_at(text)
        finally: self.k.LocalFree(text)
        session, elevated = w.DWORD(), w.DWORD()
        checked(self.a.GetTokenInformation(token, 12, ct.byref(session), 4, ct.byref(size)))
        checked(self.a.GetTokenInformation(token, 20, ct.byref(elevated), 4, ct.byref(size)))
        return {'sid': sid, 'session': session.value, 'elevated': bool(elevated.value)}

    def hold_process(self, pid):
        if type(pid) is not int or pid <= 0:
            raise ValueError('invalid_process')
        return checked(self.k.OpenProcess(0x00101000, False, pid))  # query limited + synchronize, no control rights.

    def identity(self, handle):
        token = w.HANDLE()
        checked(self.a.OpenProcessToken(handle, 8, ct.byref(token)))
        try: identity = self.token_identity(token)
        finally: self.close(token)
        creation, exit_at, kernel, user = (w.FILETIME() for _ in range(4))
        checked(self.k.GetProcessTimes(handle, ct.byref(creation), ct.byref(exit_at), ct.byref(kernel), ct.byref(user)))
        image, size = ct.create_unicode_buffer(32768), w.DWORD(32768)
        checked(self.k.QueryFullProcessImageNameW(handle, 0, image, ct.byref(size)))
        return {**identity, 'pid': self.k.GetProcessId(handle), 'created': ticks(creation),
                'image': os.path.normcase(os.path.realpath(image.value))}

    def alive(self, handle):
        return self.k.WaitForSingleObject(handle, 0) == 258

    def resources(self, handle):
        creation, exit_at, kernel, user = (w.FILETIME() for _ in range(4))
        checked(self.k.GetProcessTimes(handle, ct.byref(creation), ct.byref(exit_at), ct.byref(kernel), ct.byref(user)))
        memory = Memory(); memory.cb = ct.sizeof(memory)
        checked(self.k.K32GetProcessMemoryInfo(handle, ct.byref(memory), ct.sizeof(memory)))
        return {'cpu_seconds': (ticks(kernel) + ticks(user)) / 10_000_000,
                'working_set_bytes': memory.working_set, 'private_commit_bytes': memory.private_commit}

    def create_server(self, name):
        sd = ct.c_void_p()
        checked(self.a.ConvertStringSecurityDescriptorToSecurityDescriptorW(
            descriptor(self.own['sid']), 1, ct.byref(sd), None))
        try:
            security = SecurityAttributes(ct.sizeof(SecurityAttributes), sd, False)
            handle = self.k.CreateNamedPipeW(name, 3 | 0x40000000 | 0x00080000,
                                            8, 1, 131076, 260, 2000, ct.byref(security))
            if handle == ct.c_void_p(-1).value:
                raise OSError(ct.get_last_error(), 'endpoint_unavailable')
            return handle
        finally: self.k.LocalFree(sd)

    def inspect_dacl(self, handle):
        owner, group, dacl, sacl, sd = (ct.c_void_p() for _ in range(5))
        code = self.a.GetSecurityInfo(handle, 1, 5, ct.byref(owner), ct.byref(group),
                                      ct.byref(dacl), ct.byref(sacl), ct.byref(sd))
        if code: raise OSError(code, 'pipe_acl_unreadable')
        try:
            control, revision, info = w.WORD(), w.DWORD(), AclInformation()
            checked(self.a.GetSecurityDescriptorControl(sd, ct.byref(control), ct.byref(revision)))
            checked(self.a.GetAclInformation(dacl, ct.byref(info), ct.sizeof(info), 2))
            if info.count != 1 or not control.value & 0x1000:
                raise PermissionError('unexpected_pipe_acl')
            ace = ct.c_void_p();checked(self.a.GetAce(dacl, 0, ct.byref(ace)))
            allowed = ct.cast(ace, ct.POINTER(ct.c_ubyte))[0] == 0
            mask = ct.cast(ace.value+4, ct.POINTER(w.DWORD))[0]
            text = ct.c_void_p()
            checked(self.a.ConvertSidToStringSidW(ace.value+8, ct.byref(text)))
            try: sid = ct.wstring_at(text)
            finally: self.k.LocalFree(text)
            if not allowed or mask != CLIENT_RIGHTS or sid != self.own['sid']:
                raise PermissionError('unexpected_pipe_acl')
            return {'protected':True,'aces':1,'account_only':True,'client_mask':int(mask),
                    'create_instance_granted':False}
        finally: self.k.LocalFree(sd)

    def _io(self, handle, operation, buffer, amount, deadline, stop):
        event = checked(self.k.CreateEventW(None, True, False, None))
        overlapped, count, pending = Overlapped(), w.DWORD(), False
        overlapped.hEvent = event
        try:
            if operation == 'connect':
                ok = self.k.ConnectNamedPipe(handle, ct.byref(overlapped))
            else:
                fn = self.k.ReadFile if operation == 'read' else self.k.WriteFile
                ok = fn(handle, buffer, amount, ct.byref(count), ct.byref(overlapped))
            code = ct.get_last_error() if not ok else 0
            if operation == 'connect' and code == 535:
                return 0
            if not ok and code != 997:
                raise OSError(code, 'pipe_disconnected')
            if not ok:
                pending = True
                while True:
                    if stop.is_set() or time.monotonic() >= deadline:
                        raise TimeoutError('pipe_deadline')
                    status = self.k.WaitForSingleObject(event, min(50, max(1, int((deadline-time.monotonic())*1000))))
                    if status == 0: break
                    if status != 258: raise OSError('pipe_wait_failed')
                checked(self.k.GetOverlappedResult(handle, ct.byref(overlapped), ct.byref(count), False))
                pending = False
            return count.value
        finally:
            if pending:
                # Buffers/OVERLAPPED stay alive until cancellation completion, never freed while pending.
                self.k.CancelIoEx(handle, ct.byref(overlapped))
                self.k.GetOverlappedResult(handle, ct.byref(overlapped), ct.byref(count), True)
            self.close(event)

    def accept(self, handle, deadline, stop):
        self._io(handle, 'connect', None, 0, deadline, stop)

    def read_exact(self, handle, size, deadline, stop):
        if not 1 <= size <= 131072:
            raise ValueError('frame_size')
        parts = bytearray()
        while len(parts) < size:
            buffer = ct.create_string_buffer(size-len(parts))
            count = self._io(handle, 'read', buffer, len(buffer), deadline, stop)
            if not count: raise OSError('pipe_disconnected')
            parts.extend(buffer.raw[:count])
        return bytes(parts)

    def read_frame(self, handle, limit, deadline, stop):
        size = length(self.read_exact(handle, 4, deadline, stop), limit)
        return self.read_exact(handle, size, deadline, stop)

    def write_frame(self, handle, payload, limit, deadline, stop):
        data = frame(payload, limit); sent = 0
        while sent < len(data):
            buffer = ct.create_string_buffer(data[sent:])
            count = self._io(handle, 'write', buffer, len(data)-sent, deadline, stop)
            if not count: raise OSError('pipe_disconnected')
            sent += count

    def peer(self, pipe, expected_handle, expected, *, server_side=False):
        pid = w.ULONG()
        fn = self.k.GetNamedPipeClientProcessId if server_side else self.k.GetNamedPipeServerProcessId
        checked(fn(pipe, ct.byref(pid)))
        if pid.value != expected['pid'] or not self.alive(expected_handle):
            raise PermissionError('unexpected_peer')
        actual = self.identity(expected_handle)
        if not same_peer(actual, expected) or any(actual[k] != self.own[k] for k in ('sid', 'session')):
            raise PermissionError('unexpected_peer')
        return actual

    def client_token(self, pipe):
        checked(self.a.ImpersonateNamedPipeClient(pipe))
        token = w.HANDLE()
        try:
            checked(self.a.OpenThreadToken(self.k.GetCurrentThread(), 8, True, ct.byref(token)))
            identity = self.token_identity(token)
            level, size = w.DWORD(), w.DWORD()
            checked(self.a.GetTokenInformation(token, 9, ct.byref(level), 4, ct.byref(size)))
            if level.value < 1 or identity['elevated'] or any(identity[k] != self.own[k] for k in ('sid', 'session')):
                raise PermissionError('unexpected_client_token')
            return PeerEvidence(identity['sid'], identity['session'], True, False)
        finally:
            try:
                if token.value: self.close(token)
            finally:
                # Fail closed; no application work is done under impersonation.
                if not self.a.RevertToSelf():
                    raise RuntimeError('revert_failed')

    def connect(self, name, expected_handle, expected, deadline, stop):
        while not stop.is_set() and time.monotonic() < deadline:
            handle = self.k.CreateFileW(name, CLIENT_RIGHTS, 0, None, 3,
                                       0x40000000 | 0x00100000 | 0x00010000, None)
            if handle != ct.c_void_p(-1).value:
                try:
                    self.peer(handle, expected_handle, expected)
                    return handle
                except Exception:
                    self.close(handle); raise
            code = ct.get_last_error()
            if code not in (2, 231): raise OSError(code, 'pipe_connect_failed')
            stop.wait(min(0.025, max(0, deadline-time.monotonic())))
        raise TimeoutError('pipe_connect_timeout')
