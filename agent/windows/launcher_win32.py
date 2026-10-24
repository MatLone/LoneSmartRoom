"""Windows-only primitives for the isolated startup launcher; no agent imports."""
import ctypes as c
from ctypes import wintypes as w
from contextlib import contextmanager
import os
from pathlib import Path
import stat


class SecurityError(OSError):
    pass


class BusyError(OSError):
    pass


class Attributes(c.Structure):
    _fields_ = [('length', w.DWORD), ('descriptor', w.LPVOID), ('inherit', w.BOOL)]


class AclInfo(c.Structure):
    _fields_ = [('count', w.DWORD), ('used', w.DWORD), ('free', w.DWORD)]


def checked_path(path):
    """Local absolute path only; reject links/junctions in every existing component."""
    path = Path(path)
    if not path.is_absolute() or not path.drive or path.drive.startswith('\\'):
        raise SecurityError('local_absolute_required')
    if any(x in str(path) for x in ('\x00', '\n', '\r', '"', '%')):
        raise SecurityError('invalid_path')
    if '..' in path.parts or ':' in str(path)[2:]:
        raise SecurityError('invalid_path')
    for part in reversed((path, *path.parents)):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise SecurityError('reparse_point')
    return path


class Windows:
    def __init__(self):
        if os.name != 'nt':
            raise SecurityError('windows_required')
        self.k = c.WinDLL('kernel32', use_last_error=True, winmode=0x800)
        self.a = c.WinDLL('advapi32', use_last_error=True, winmode=0x800)
        declarations = [
            (self.k, 'GetCurrentProcess', [], w.HANDLE),
            (self.k, 'GetSystemDirectoryW', [w.LPWSTR, w.UINT], w.UINT),
            (self.k, 'CloseHandle', [w.HANDLE], w.BOOL),
            (self.k, 'LocalFree', [w.LPVOID], w.LPVOID),
            (self.k, 'CreateMutexW', [c.POINTER(Attributes), w.BOOL, w.LPCWSTR], w.HANDLE),
            (self.k, 'WaitForSingleObject', [w.HANDLE, w.DWORD], w.DWORD),
            (self.k, 'ReleaseMutex', [w.HANDLE], w.BOOL),
            (self.k, 'CreateDirectoryW', [w.LPCWSTR, c.POINTER(Attributes)], w.BOOL),
            (self.k, 'CreateFileW', [w.LPCWSTR, w.DWORD, w.DWORD, c.POINTER(Attributes),
                                    w.DWORD, w.DWORD, w.HANDLE], w.HANDLE),
            (self.a, 'OpenProcessToken', [w.HANDLE, w.DWORD, c.POINTER(w.HANDLE)], w.BOOL),
            (self.a, 'GetTokenInformation', [w.HANDLE, c.c_int, w.LPVOID, w.DWORD,
                                             c.POINTER(w.DWORD)], w.BOOL),
            (self.a, 'ConvertSidToStringSidW', [w.LPVOID, c.POINTER(w.LPWSTR)], w.BOOL),
            (self.a, 'ConvertStringSecurityDescriptorToSecurityDescriptorW',
             [w.LPCWSTR, w.DWORD, c.POINTER(w.LPVOID), c.POINTER(w.DWORD)], w.BOOL),
            (self.a, 'GetNamedSecurityInfoW', [w.LPWSTR, c.c_int, w.DWORD,
             c.POINTER(w.LPVOID), c.POINTER(w.LPVOID), c.POINTER(w.LPVOID),
             c.POINTER(w.LPVOID), c.POINTER(w.LPVOID)], w.DWORD),
            (self.a, 'GetSecurityInfo', [w.HANDLE, c.c_int, w.DWORD,
             c.POINTER(w.LPVOID), c.POINTER(w.LPVOID), c.POINTER(w.LPVOID),
             c.POINTER(w.LPVOID), c.POINTER(w.LPVOID)], w.DWORD),
            (self.a, 'GetSecurityDescriptorControl',
             [w.LPVOID, c.POINTER(w.WORD), c.POINTER(w.DWORD)], w.BOOL),
            (self.a, 'GetAclInformation', [w.LPVOID, w.LPVOID, w.DWORD, c.c_int], w.BOOL),
            (self.a, 'GetAce', [w.LPVOID, w.DWORD, c.POINTER(w.LPVOID)], w.BOOL),
        ]
        for library, name, args, result in declarations:
            fn = getattr(library, name)
            fn.argtypes, fn.restype = args, result
        system = c.create_unicode_buffer(32768)
        length = self.k.GetSystemDirectoryW(system, len(system))
        if not length or length >= len(system):
            raise SecurityError('system_directory_unavailable')
        self.system_directory = checked_path(system.value)
        token = w.HANDLE()
        self._ok(self.a.OpenProcessToken(self.k.GetCurrentProcess(), 8, c.byref(token)))
        try:
            size = w.DWORD()
            self.a.GetTokenInformation(token, 1, None, 0, c.byref(size))
            data = c.create_string_buffer(size.value)
            self._ok(self.a.GetTokenInformation(token, 1, data, size, c.byref(size)))
            self.sid = self._sid(c.cast(data, c.POINTER(w.LPVOID))[0])
            elevated = w.DWORD()
            self._ok(self.a.GetTokenInformation(token, 20, c.byref(elevated),
                                                c.sizeof(elevated), c.byref(size)))
            self.elevated = bool(elevated.value)
        finally:
            self.k.CloseHandle(token)

    @staticmethod
    def _ok(value):
        if not value:
            raise c.WinError(c.get_last_error())

    def _sid(self, pointer):
        value = w.LPWSTR()
        self._ok(self.a.ConvertSidToStringSidW(pointer, c.byref(value)))
        try:
            return value.value
        finally:
            self.k.LocalFree(c.cast(value, w.LPVOID))

    @contextmanager
    def attributes(self, directory=False, kernel=False):
        descriptor = w.LPVOID()
        # Kernel-object DACLs need the concrete MUTEX_ALL_ACCESS mask; generic
        # GA in a newly supplied descriptor is not reliably mapped on reopening.
        flags, rights = ('OICI' if directory else ''), ('0x001f0001' if kernel else 'FA')
        sddl = f'O:{self.sid}D:P(A;{flags};{rights};;;{self.sid})'
        self._ok(self.a.ConvertStringSecurityDescriptorToSecurityDescriptorW(
            sddl, 1, c.byref(descriptor), None))
        try:
            yield Attributes(c.sizeof(Attributes), descriptor, False)
        finally:
            self.k.LocalFree(descriptor)

    def _verify(self, target, kernel=False):
        owner, dacl, descriptor = w.LPVOID(), w.LPVOID(), w.LPVOID()
        args = (target, 6 if kernel else 1, 5, c.byref(owner), None,
                c.byref(dacl), None, c.byref(descriptor))
        error = (self.a.GetSecurityInfo if kernel else self.a.GetNamedSecurityInfoW)(*args)
        if error:
            raise c.WinError(error)
        try:
            if not owner.value or self._sid(owner) != self.sid or not dacl.value:
                raise SecurityError('owner_or_dacl')
            control, revision = w.WORD(), w.DWORD()
            self._ok(self.a.GetSecurityDescriptorControl(descriptor, c.byref(control), c.byref(revision)))
            if not control.value & 0x1000:
                raise SecurityError('unprotected_dacl')
            info = AclInfo()
            self._ok(self.a.GetAclInformation(dacl, c.byref(info), c.sizeof(info), 2))
            if info.count != 1:
                raise SecurityError('nonexclusive_acl')
            ace = w.LPVOID()
            self._ok(self.a.GetAce(dacl, 0, c.byref(ace)))
            header = (c.c_ubyte * 4).from_address(ace.value)
            if header[0] != 0 or header[1] & 0x18 or self._sid(ace.value + 8) != self.sid:
                raise SecurityError('nonexclusive_acl')
        finally:
            self.k.LocalFree(descriptor)

    def verify_private(self, path):
        self._verify(str(checked_path(path)))

    def private_directory(self, path):
        path = checked_path(path)
        if not path.parent.is_dir():
            raise SecurityError('parent_missing')
        with self.attributes(directory=True) as attributes:
            if not self.k.CreateDirectoryW(str(path), c.byref(attributes)):
                if c.get_last_error() != 183:
                    raise c.WinError(c.get_last_error())
        if not path.is_dir():
            raise SecurityError('not_directory')
        self.verify_private(path)  # Existing broad ACLs are rejected, never repaired.

    def private_file(self, path):
        path = checked_path(path)
        self.verify_private(path.parent)
        with self.attributes() as attributes:
            handle = self.k.CreateFileW(str(path), 0x40000000, 0, c.byref(attributes),
                                        1, 0x00200000, None)  # CREATE_NEW, no reparse traversal
        if handle == c.c_void_p(-1).value:
            if c.get_last_error() not in (80, 183):
                raise c.WinError(c.get_last_error())
        else:
            self.k.CloseHandle(handle)
        if not path.is_file() or path.stat().st_nlink != 1:
            raise SecurityError('unsafe_log_file')
        self.verify_private(path)

    @contextmanager
    def mutex(self, name, timeout=0):
        with self.attributes(kernel=True) as attributes:
            handle = self.k.CreateMutexW(c.byref(attributes), False, name)
        self._ok(handle)
        acquired = False
        try:
            self._verify(handle, kernel=True)
            result = self.k.WaitForSingleObject(handle, timeout)
            if result == 0x102:
                raise BusyError('busy')
            if result not in (0, 0x80):
                raise c.WinError(c.get_last_error())
            acquired = True
            yield result == 0x80
        finally:
            if acquired:
                self.k.ReleaseMutex(handle)
            self.k.CloseHandle(handle)
