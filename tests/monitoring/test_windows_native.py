"""Native ABI and read adapter tested with DLL/function substitutes ONLY."""
import ast
import ctypes as ct
from pathlib import Path
from unittest.mock import Mock, patch
import unittest

from monitoring.contracts import Availability as A
from monitoring.windows_native import (DiskSpace, FormattedCounter, MemoryStatus,
                                        ProcessMemory, RawCounter, WindowsReadApi)


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.kernel, self.advapi, self.pdh = Mock(), Mock(), Mock()
        libraries = {'kernel32.dll': self.kernel, 'advapi32.dll': self.advapi, 'pdh.dll': self.pdh}
        self.loader = self.enterContext(patch('ctypes.WinDLL', side_effect=lambda name, **kw: libraries[name]))
        self.api = WindowsReadApi()

    def test_x64_structures_offsets(self):
        self.assertEqual([ct.sizeof(t) for t in (MemoryStatus, DiskSpace, ProcessMemory, RawCounter, FormattedCounter)],
                         [64, 96, 80, 40, 16])
        self.assertEqual(RawCounter.first.offset, 16)
        self.assertEqual(FormattedCounter.data.offset, 8)
        self.assertEqual(DiskSpace.sectors_per_unit.offset, 88)

    def test_dll_load_restricted_to_system32_and_no_calls_on_import_or_construction(self):
        self.assertEqual(self.loader.call_count, 2)
        for call in self.loader.call_args_list:
            self.assertEqual(call.kwargs['winmode'], 0x800)
        self.kernel.GetSystemTimes.assert_not_called()
        self.kernel.GlobalMemoryStatusEx.assert_not_called()
        self.kernel.GetDriveTypeW.assert_not_called()

    def test_non_elevated_token_query_only_and_handle_closed(self):
        self.kernel.GetCurrentProcess.return_value = -1
        self.advapi.OpenProcessToken.return_value = 1
        def token_info(token, info, ptr, size, out):
            ptr._obj.value = 0
            return 1
        self.advapi.GetTokenInformation.side_effect = token_info
        self.kernel.CloseHandle.return_value = 1
        self.api.require_non_elevated()
        self.assertEqual(self.advapi.OpenProcessToken.call_args.args[1], 0x0008)
        self.kernel.CloseHandle.assert_called_once()

    def test_elevated_token_blocks_collection(self):
        self.kernel.GetCurrentProcess.return_value = -1
        self.advapi.OpenProcessToken.return_value = 1
        def elevated(token, info, ptr, size, out):
            ptr._obj.value = 1
            return 1
        self.advapi.GetTokenInformation.side_effect = elevated
        self.kernel.CloseHandle.return_value = 1
        with self.assertRaises(PermissionError):
            self.api.require_non_elevated()
        self.kernel.GetSystemTimes.assert_not_called()

    def test_only_fixed_mounted_drive_letters_no_file_scan(self):
        self.kernel.GetLogicalDrives.return_value = sum(1 << n for n in (2, 3, 4))
        self.kernel.GetDriveTypeW.side_effect = lambda root: {'C:\\': 3, 'D:\\': 4, 'E:\\': 2}[root]
        self.assertEqual(self.api.fixed_volumes(), ('C:\\',))

    def test_cpu_filetime_integer_conversion_and_memory(self):
        def cpu(idle, kernel, user):
            for ptr, value in zip((idle, kernel, user), (2**32 + 5, 2**33 + 10, 20)):
                ptr._obj.dwHighDateTime = value >> 32
                ptr._obj.dwLowDateTime = value & 0xffffffff
            return 1
        self.kernel.GetSystemTimes.side_effect = cpu
        self.assertEqual(self.api.cpu_times(), (2**32 + 5, 2**33 + 10, 20))
        def memory(ptr):
            self.assertEqual(ptr._obj.length, 64)
            ptr._obj.total, ptr._obj.available = 16 * 1024**3, 8 * 1024**3
            return 1
        self.kernel.GlobalMemoryStatusEx.side_effect = memory
        self.assertEqual(self.api.memory(), (16 * 1024**3, 8 * 1024**3))

    def test_space_allocation_units_and_quota_kept_separate(self):
        def space(root, ptr):
            v = ptr._obj
            v.sectors_per_unit, v.bytes_per_sector = 8, 512
            v.actual_total, v.actual_available, v.caller_available, v.used = 100, 70, 10, 20
            return 0
        self.api.space_function.side_effect = space
        v = self.api.volume_space('C:\\')
        self.assertEqual((v.total, v.free, v.available, v.used), (409600, 286720, 40960, 81920))

    def test_missing_disk_space_api_no_unsafe_fallback(self):
        self.api.space_function = None
        with self.assertRaises(NotImplementedError):
            self.api.volume_space('C:\\')
        with self.assertRaises(ValueError):
            self.api.volume_space('C:\\personal')

    def prepare_pdh(self):
        def opened(source, data, handle):
            handle._obj.value = 10
            return 0
        counter_index = [10]
        def added(query, name, data, handle):
            counter_index[0] += 1
            handle._obj.value = counter_index[0]
            return 0
        self.pdh.PdhOpenQueryW.side_effect = opened
        self.pdh.PdhAddEnglishCounterW.side_effect = added
        self.pdh.PdhCollectQueryData.return_value = 0
        self.pdh.PdhCloseQuery.return_value = 0
        self.api.open_disk_query(('C:\\',))

    def test_pdh_fixed_english_counters_and_exact_idle_complement(self):
        self.prepare_pdh()
        paths = [call.args[1] for call in self.pdh.PdhAddEnglishCounterW.call_args_list]
        self.assertEqual(paths, ['\\LogicalDisk(C:)\\Disk Read Bytes/sec',
                                 '\\LogicalDisk(C:)\\Disk Write Bytes/sec', '\\LogicalDisk(C:)\\% Idle Time'])
        def raw(handle, kind, ptr):
            ptr._obj.status, ptr._obj.first, ptr._obj.second = 0, 100, 200
            return 0
        def formatted(handle, fmt, kind, ptr):
            self.assertEqual(fmt, 0x200 | 0x8000)
            ptr._obj.status = 0
            ptr._obj.double_value = 92 if handle.value == 13 else 4096
            return 0
        self.pdh.PdhGetRawCounterValue.side_effect = raw
        self.pdh.PdhGetFormattedCounterValue.side_effect = formatted
        values = self.api.disk_counters()
        self.assertEqual(values['storage.c.activity'].value, 8)
        self.assertEqual(values['storage.c.read_rate'].value, 4096)

    def test_pdh_raw_status_checked_even_when_api_returns_success(self):
        self.prepare_pdh()
        def raw(handle, kind, ptr):
            ptr._obj.status = 0x800007d1
            return 0
        self.pdh.PdhGetRawCounterValue.side_effect = raw
        self.assertTrue(all(v.status == A.UNAVAILABLE for v in self.api.disk_counters().values()))
        self.pdh.PdhGetFormattedCounterValue.assert_not_called()

    def test_pdh_add_or_collect_failures_do_not_enable_or_repair_counters(self):
        self.prepare_pdh()
        self.pdh.PdhCollectQueryData.return_value = 1
        self.assertTrue(all(v.status == A.UNAVAILABLE for v in self.api.disk_counters().values()))
        with self.assertRaises(RuntimeError):
            self.api.open_disk_query(('C:\\',))
        self.api.close_disk_query()
        self.api.close_disk_query()
        self.pdh.PdhCloseQuery.assert_called_once()

    def test_native_exports_are_an_explicit_read_and_handle_allowlist(self):
        tree = ast.parse(Path(__file__).resolve().parents[2].joinpath('monitoring/windows_native.py').read_text(encoding='utf-8'))
        names = {node.args[1].value for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Name) and node.func.id == 'bind'}
        self.assertEqual(names, {'GetCurrentProcess', 'CloseHandle', 'GetSystemTimes', 'GlobalMemoryStatusEx',
                                'GetLogicalDrives', 'GetDriveTypeW', 'GetActiveProcessorCount', 'GetProcessTimes',
                                'K32GetProcessMemoryInfo', 'GetDiskSpaceInformationW', 'OpenProcessToken',
                                'GetTokenInformation', 'PdhOpenQueryW', 'PdhAddEnglishCounterW',
                                'PdhCollectQueryData', 'PdhGetRawCounterValue', 'PdhGetFormattedCounterValue', 'PdhCloseQuery'})
