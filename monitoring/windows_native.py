"""Explicit Windows x64 READ APIs only. Import does not load DLLs or collect.

Native construction is reserved for the separately authorized single-session runner.
No process creation, writable device handles, control APIs, sensors or network.
"""
import ctypes as ct
from ctypes import wintypes as w
import os

from .contracts import Availability as A
from .windows_basic import DiskCounter, VolumeSpace, volume_root


class MemoryStatus(ct.Structure):
    _fields_ = [('length', w.DWORD), ('load', w.DWORD)] + [
        (name, ct.c_ulonglong) for name in ('total', 'available', 'page_total', 'page_available',
                                           'virtual_total', 'virtual_available', 'extended')]


class DiskSpace(ct.Structure):
    _fields_ = [(name, ct.c_ulonglong) for name in (
        'actual_total', 'actual_available', 'actual_pool_unavailable', 'caller_total',
        'caller_available', 'caller_pool_unavailable', 'used', 'reserved', 'storage_reserve',
        'available_committed', 'pool_available')] + [('sectors_per_unit', w.DWORD), ('bytes_per_sector', w.DWORD)]


class ProcessMemory(ct.Structure):
    _fields_ = [('cb', w.DWORD), ('faults', w.DWORD)] + [(name, ct.c_size_t) for name in (
        'peak_working_set', 'working_set', 'peak_paged', 'paged', 'peak_nonpaged',
        'nonpaged', 'pagefile', 'peak_pagefile', 'private_commit')]


class RawCounter(ct.Structure):
    _fields_ = [('status', w.DWORD), ('timestamp', w.FILETIME),
                ('first', ct.c_longlong), ('second', ct.c_longlong), ('multi', w.DWORD)]


class CounterUnion(ct.Union):
    _fields_ = [('long_value', w.LONG), ('double_value', ct.c_double), ('large_value', ct.c_longlong),
                ('ansi', ct.c_void_p), ('wide', ct.c_void_p)]


class FormattedCounter(ct.Structure):
    _anonymous_ = ('data',)
    _fields_ = [('status', w.DWORD), ('data', CounterUnion)]


def ticks(value):
    return (value.dwHighDateTime << 32) | value.dwLowDateTime


def bind(dll, name, args, result):
    function = getattr(dll, name)
    function.argtypes, function.restype = args, result
    return function


def check(value):
    if not value:
        code = ct.get_last_error()
        if code == 5:
            raise PermissionError('native_read_denied')
        raise OSError(code, 'native_read_failed')


class WindowsReadApi:
    def __init__(self):
        if os.name != 'nt' or ct.sizeof(ct.c_void_p) != 8:
            raise RuntimeError('Windows_x64_required')
        # LOAD_LIBRARY_SEARCH_SYSTEM32, never the working directory.
        self.kernel = ct.WinDLL('kernel32.dll', use_last_error=True, winmode=0x800)
        self.advapi = ct.WinDLL('advapi32.dll', use_last_error=True, winmode=0x800)
        k = self.kernel
        bind(k, 'GetCurrentProcess', [], w.HANDLE)
        bind(k, 'CloseHandle', [w.HANDLE], w.BOOL)
        bind(k, 'GetSystemTimes', [ct.POINTER(w.FILETIME)] * 3, w.BOOL)
        bind(k, 'GlobalMemoryStatusEx', [ct.POINTER(MemoryStatus)], w.BOOL)
        bind(k, 'GetLogicalDrives', [], w.DWORD)
        bind(k, 'GetDriveTypeW', [w.LPCWSTR], w.UINT)
        bind(k, 'GetActiveProcessorCount', [w.WORD], w.DWORD)
        bind(k, 'GetProcessTimes', [w.HANDLE] + [ct.POINTER(w.FILETIME)] * 4, w.BOOL)
        bind(k, 'K32GetProcessMemoryInfo', [w.HANDLE, ct.POINTER(ProcessMemory), w.DWORD], w.BOOL)
        self.space_function = None
        try:
            self.space_function = bind(k, 'GetDiskSpaceInformationW', [w.LPCWSTR, ct.POINTER(DiskSpace)], ct.c_long)
        except AttributeError:
            pass
        bind(self.advapi, 'OpenProcessToken', [w.HANDLE, w.DWORD, ct.POINTER(w.HANDLE)], w.BOOL)
        bind(self.advapi, 'GetTokenInformation', [w.HANDLE, ct.c_int, ct.c_void_p,
                                               w.DWORD, ct.POINTER(w.DWORD)], w.BOOL)
        self.query = None
        self.pdh = None
        self.handles = {}
        self.counter_failures = {}

    def require_non_elevated(self):
        token, size, elevated = w.HANDLE(), w.DWORD(), w.DWORD()
        check(self.advapi.OpenProcessToken(self.kernel.GetCurrentProcess(), 0x0008, ct.byref(token)))
        try:
            check(self.advapi.GetTokenInformation(token, 20, ct.byref(elevated),
                                                  ct.sizeof(elevated), ct.byref(size)))
            if elevated.value:
                raise PermissionError('elevated_collection_forbidden')
        finally:
            check(self.kernel.CloseHandle(token))

    def fixed_volumes(self):
        mask = self.kernel.GetLogicalDrives()
        check(mask)
        return tuple(root for i in range(26) if mask & (1 << i)
                     for root in (chr(65 + i) + ':\\',) if self.kernel.GetDriveTypeW(root) == 3)

    def cpu_times(self):
        idle, kernel, user = w.FILETIME(), w.FILETIME(), w.FILETIME()
        check(self.kernel.GetSystemTimes(ct.byref(idle), ct.byref(kernel), ct.byref(user)))
        return ticks(idle), ticks(kernel), ticks(user)

    def memory(self):
        value = MemoryStatus()
        value.length = ct.sizeof(value)
        check(self.kernel.GlobalMemoryStatusEx(ct.byref(value)))
        return value.total, value.available

    def volume_space(self, root):
        volume_root(root)
        if self.space_function is None:
            raise NotImplementedError('volume_information_unavailable')
        value = DiskSpace()
        result = self.space_function(root, ct.byref(value))
        if result != 0:
            if result & 0xffffffff == 0x80070005:
                raise PermissionError('volume_read_denied')
            raise OSError('volume_read_failed')
        cluster = value.sectors_per_unit * value.bytes_per_sector
        if not cluster:
            raise OSError('invalid_volume_geometry')
        return VolumeSpace(value.actual_total * cluster, value.actual_available * cluster,
                           value.caller_available * cluster, value.used * cluster)

    def logical_processors(self):
        value = self.kernel.GetActiveProcessorCount(0xffff)
        check(value)
        return value

    def own_resources(self):
        creation, exit_time, kernel, user = (w.FILETIME() for _ in range(4))
        handle = self.kernel.GetCurrentProcess()
        check(self.kernel.GetProcessTimes(handle, ct.byref(creation), ct.byref(exit_time),
                                          ct.byref(kernel), ct.byref(user)))
        memory = ProcessMemory()
        memory.cb = ct.sizeof(memory)
        check(self.kernel.K32GetProcessMemoryInfo(handle, ct.byref(memory), ct.sizeof(memory)))
        return {'cpu_seconds': (ticks(kernel) + ticks(user)) / 10_000_000,
                'working_set_bytes': memory.working_set,
                'private_commit_bytes': memory.private_commit}

    def open_disk_query(self, volumes):
        if self.query is not None or self.pdh is not None:
            raise RuntimeError('query_already_attempted')
        self.pdh = ct.WinDLL('pdh.dll', use_last_error=True, winmode=0x800)
        p = self.pdh
        bind(p, 'PdhOpenQueryW', [w.LPCWSTR, ct.c_size_t, ct.POINTER(w.HANDLE)], w.DWORD)
        bind(p, 'PdhAddEnglishCounterW', [w.HANDLE, w.LPCWSTR, ct.c_size_t, ct.POINTER(w.HANDLE)], w.DWORD)
        bind(p, 'PdhCollectQueryData', [w.HANDLE], w.DWORD)
        bind(p, 'PdhGetRawCounterValue', [w.HANDLE, ct.POINTER(w.DWORD), ct.POINTER(RawCounter)], w.DWORD)
        bind(p, 'PdhGetFormattedCounterValue', [w.HANDLE, w.DWORD, ct.POINTER(w.DWORD),
                                              ct.POINTER(FormattedCounter)], w.DWORD)
        bind(p, 'PdhCloseQuery', [w.HANDLE], w.DWORD)
        query = w.HANDLE()
        status = p.PdhOpenQueryW(None, 0, ct.byref(query))
        if status == 0:
            self.query = query  # Retain immediately so partial setup can be closed.
        for root in volumes:
            volume_root(root)
            for suffix, counter in (('read_rate', 'Disk Read Bytes/sec'),
                                    ('write_rate', 'Disk Write Bytes/sec'), ('activity', '% Idle Time')):
                key = 'storage.' + root[0].lower() + '.' + suffix
                handle = w.HANDLE()
                code = status or p.PdhAddEnglishCounterW(query, '\\LogicalDisk(' + root[:2]
                                                        + ')\\' + counter, 0, ct.byref(handle))
                if code:
                    self.counter_failures[key] = A.PERMISSION_DENIED if code == 5 else A.UNSUPPORTED
                else:
                    self.handles[key] = handle

    def disk_counters(self):
        counters = {key: DiskCounter(0, 0, None, state) for key, state in self.counter_failures.items()}
        if self.query is None:
            return counters
        if self.pdh.PdhCollectQueryData(self.query) != 0:
            counters.update({key: DiskCounter(0, 0, None, A.UNAVAILABLE) for key in self.handles})
            return counters
        for key, handle in self.handles.items():
            raw, value = RawCounter(), FormattedCounter()
            code = self.pdh.PdhGetRawCounterValue(handle, None, ct.byref(raw))
            if code or raw.status not in (0, 1):
                counters[key] = DiskCounter(0, 0, None, A.UNAVAILABLE)
                continue
            formatted = self.pdh.PdhGetFormattedCounterValue(handle, 0x200 | 0x8000, None, ct.byref(value))
            number = value.double_value if not formatted and value.status in (0, 1) else None
            if key.endswith('.activity') and number is not None:
                number = 100 - number  # Idle complement only; never % Disk Time or bytes/sec.
            counters[key] = DiskCounter(raw.first, raw.second, number)
        return counters

    def close_disk_query(self):
        if self.query is not None:
            query, self.query = self.query, None
            if self.pdh.PdhCloseQuery(query) != 0:
                raise OSError('query_close_failed')
        self.handles.clear()
