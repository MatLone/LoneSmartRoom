"""No real process creation. All launch paths use a substituted Popen."""
import ctypes as c
from ctypes import wintypes as w
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'agent/windows'))
import steam_launcher as launcher
from secure_apps import launch_allowed


class SteamLauncherTests(unittest.TestCase):
    def setUp(self):
        (ROOT / '.cache/tests').mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / '.cache/tests')
        self.addCleanup(self.temp.cleanup)
        self.exe = Path(self.temp.name) / 'steam.exe'
        self.exe.write_bytes(b'MZsynthetic executable; never run')
        self.popen = self.enterContext(patch('steam_launcher.subprocess.Popen'))
        self.uri = self.enterContext(patch('os.startfile', create=True))

    def test_direct_dispatch_has_only_absolute_exe_cwd_and_no_shell(self):
        with patch.object(launcher, 'registered_executables', return_value=[self.exe]), \
                patch.object(launcher, 'verify_valve_signature') as signature:
            message = launcher.launch_steam()
        signature.assert_called_once_with(self.exe)
        self.popen.assert_called_once_with([str(self.exe)], executable=str(self.exe),
            cwd=str(self.exe.parent), shell=False, close_fds=True,
            stdin=launcher.subprocess.DEVNULL, stdout=launcher.subprocess.DEVNULL,
            stderr=launcher.subprocess.DEVNULL)
        self.assertIn('janela não verificada', message)
        self.uri.assert_not_called()

    def test_invalid_local_paths_rejected_before_dispatch(self):
        for value in ('steam.exe', 'C:steam.exe', r'\steam.exe', r'\\server\share\steam.exe',
                      r'\\?\C:\Steam\steam.exe', r'C:\Steam\..\evil\steam.exe',
                      r'C:\Steam\.\steam.exe', r'C:\Steam\steam.exe:payload',
                      '"C:\\Steam\\steam.exe" -- bad', '%LOCALAPPDATA%\\Steam\\steam.exe',
                      ' C:\\Steam\\steam.exe', 'C:\\Steam\\steam.exe\x00'):
            with self.subTest(value=value), self.assertRaises(launcher.SteamLaunchError):
                launcher._local_absolute(value)
        self.popen.assert_not_called()

    def test_missing_file_and_wrong_executable_never_launch(self):
        for path in (self.exe.parent/'absent'/'steam.exe', self.exe.parent/'cmd.exe'):
            with self.subTest(path=path), patch.object(launcher, 'registered_executables', return_value=[path]), \
                    self.assertRaises((OSError, launcher.SteamLaunchError)):
                launcher.launch_steam()
        self.exe.write_bytes(b'not a PE')
        with patch.object(launcher, 'registered_executables', return_value=[self.exe]), self.assertRaises(launcher.SteamLaunchError):
            launcher.launch_steam()
        self.popen.assert_not_called()

    def test_conflicting_registrations_rejected(self):
        other = self.exe.parent/'other'; other.mkdir(); (other/'steam.exe').write_bytes(b'MZfake')
        with patch.object(launcher, 'registered_executables', return_value=[self.exe, other/'steam.exe']), \
                patch.object(launcher, 'verify_valve_signature') as signature, self.assertRaisesRegex(launcher.SteamLaunchError, 'conflicting'):
            launcher.launch_steam()
        signature.assert_not_called(); self.popen.assert_not_called()

    def test_duplicate_registration_of_same_path_is_allowed(self):
        with patch.object(launcher, 'registered_executables', return_value=[self.exe, self.exe]), \
                patch.object(launcher, 'verify_valve_signature'):
            launcher.launch_steam()
        self.popen.assert_called_once()

    def test_redirected_component_rejected(self):
        original = Path.lstat
        def redirected(path, *args, **kwargs):
            return SimpleNamespace(st_file_attributes=0x400) if path == self.exe.parent else original(path, *args, **kwargs)
        with patch.object(Path, 'lstat', redirected), patch.object(launcher, 'registered_executables', return_value=[self.exe]), \
                self.assertRaisesRegex(launcher.SteamLaunchError, 'redirected'):
            launcher.launch_steam()
        self.popen.assert_not_called()

    def test_untrusted_signer_file_change_and_access_failure_no_fallback(self):
        for failure in (launcher.SteamLaunchError('steam_signature_untrusted'),
                        launcher.SteamLaunchError('steam_publisher_not_allowed'), PermissionError('synthetic')):
            with self.subTest(failure=type(failure).__name__), patch.object(launcher, 'registered_executables', return_value=[self.exe]), \
                    patch.object(launcher, 'verify_valve_signature', side_effect=failure), self.assertRaises(type(failure)):
                launcher.launch_steam()
        def change(path): path.write_bytes(b'MZdifferent size')
        with patch.object(launcher, 'registered_executables', return_value=[self.exe]), \
                patch.object(launcher, 'verify_valve_signature', side_effect=change), self.assertRaisesRegex(launcher.SteamLaunchError, 'changed'):
            launcher.launch_steam()
        self.popen.assert_not_called(); self.uri.assert_not_called()

    def test_popen_failure_is_one_attempt_without_uri_fallback(self):
        self.popen.side_effect = OSError('synthetic creation failure')
        with patch.object(launcher, 'registered_executables', return_value=[self.exe]), \
                patch.object(launcher, 'verify_valve_signature'), self.assertRaises(OSError):
            launcher.launch_steam()
        self.popen.assert_called_once(); self.uri.assert_not_called()

    def test_adapter_checks_interactive_user_before_resolver_and_does_not_accept_path(self):
        with patch('secure_apps.require_interactive_user', side_effect=PermissionError), \
                patch.object(launcher, 'validated_steam_executable') as resolver, self.assertRaises(PermissionError):
            launch_allowed('steam')
        resolver.assert_not_called()
        for app in ('cmd.exe', 'powershell', 'C:\\Steam\\steam.exe', 'steam --bad', 'shutdown'):
            with self.subTest(app=app), self.assertRaises(ValueError):launch_allowed(app)
        self.popen.assert_not_called(); self.uri.assert_not_called()

    def test_fixed_registry_values_and_wrong_types(self):
        import winreg
        key = MagicMock(); key.__enter__.return_value = key
        def query(handle, name):
            if name == 'SteamExe':return (str(self.exe), winreg.REG_SZ)
            return (str(self.exe.parent), winreg.REG_SZ)
        with patch.object(winreg, 'OpenKey', return_value=key) as opened, patch.object(winreg, 'QueryValueEx', side_effect=query):
            self.assertEqual(set(launcher.registered_executables()), {self.exe})
            self.assertTrue(all(call.args[3] & winreg.KEY_READ for call in opened.call_args_list))
        with patch.object(winreg, 'OpenKey', side_effect=FileNotFoundError), self.assertRaisesRegex(launcher.SteamLaunchError, 'not_registered'):
            launcher.registered_executables()
        with patch.object(winreg, 'OpenKey', return_value=key), patch.object(winreg, 'QueryValueEx', return_value=('C:\\Steam', winreg.REG_EXPAND_SZ)), \
                self.assertRaises(launcher.SteamLaunchError):launcher.registered_executables()

    def native_libraries(self, organization='Valve Corp.', status=0):
        trust, crypt = MagicMock(), MagicMock()
        certs = (launcher._ProviderCert*1)(); certs[0].cert = 123
        signer = launcher._ProviderSigner(); signer.count = 1; signer.certs = certs
        def verify(hwnd, action, data):
            if data._obj.action == 1:data._obj.state = 1
            return status
        trust.WinVerifyTrust.side_effect = verify
        trust.WTHelperProvDataFromStateData.return_value = 1
        trust.WTHelperGetProvSignerFromChain.return_value = c.pointer(signer)
        def name(cert, kind, flags, oid, output, size):
            output.value = organization
            return len(organization)+1
        crypt.CertGetNameStringW.side_effect = name
        return trust, crypt, signer, certs

    def test_native_signature_uses_cache_only_no_ui_and_verified_subject(self):
        trust, crypt, signer, certs = self.native_libraries()
        with patch.object(c, 'WinDLL', side_effect=[trust, crypt]):launcher.verify_valve_signature(self.exe)
        calls = trust.WinVerifyTrust.call_args_list
        self.assertEqual(len(calls), 2)  # verify + state close, never process creation
        self.assertEqual(calls[0].args[0].value, w.HWND(-1).value)
        data = calls[0].args[2]._obj
        self.assertEqual(data.ui, 2); self.assertEqual(data.flags, 0x1000|0x80|0x2000)
        self.assertEqual(data.action, 2)
        self.assertEqual(crypt.CertGetNameStringW.call_args.args[1:3], (3, 0))
        self.popen.assert_not_called()

    def test_native_untrusted_or_other_publisher_is_rejected_and_state_closed(self):
        for organization, status in (('Unrelated signer', 0), ('Valve Corp.', 0x800b0100)):
            trust, crypt, signer, certs = self.native_libraries(organization, status)
            with patch.object(c, 'WinDLL', side_effect=[trust, crypt]), self.assertRaises(launcher.SteamLaunchError):
                launcher.verify_valve_signature(self.exe)
            self.assertEqual(trust.WinVerifyTrust.call_count, 2)
        self.popen.assert_not_called()

    def test_native_missing_state_or_signer_fails_closed(self):
        trust, crypt, signer, certs = self.native_libraries()
        trust.WinVerifyTrust.side_effect = None
        trust.WinVerifyTrust.return_value = 0
        with patch.object(c, 'WinDLL', side_effect=[trust, crypt]), self.assertRaisesRegex(launcher.SteamLaunchError, 'signer_unavailable'):
            launcher.verify_valve_signature(self.exe)
        trust.WTHelperProvDataFromStateData.assert_not_called()
        trust, crypt, signer, certs = self.native_libraries()
        signer.count = 0
        with patch.object(c, 'WinDLL', side_effect=[trust, crypt]), self.assertRaisesRegex(launcher.SteamLaunchError, 'signer_unavailable'):
            launcher.verify_valve_signature(self.exe)
        self.popen.assert_not_called()


if __name__ == '__main__':unittest.main()
