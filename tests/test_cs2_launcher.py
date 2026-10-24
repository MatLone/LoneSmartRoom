"""Synthetic Steam libraries and replaced Popen only; no real games or clients."""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'agent/windows'))
import cs2_launcher as launcher
from secure_apps import launch_allowed


def kv(values):
    return '\n'.join(json.dumps(key, ensure_ascii=False) + ' ' + (
        '{\n' + kv(value) + '\n}' if isinstance(value, dict) else json.dumps(value, ensure_ascii=False))
        for key, value in values.items())


class Cs2LauncherTests(unittest.TestCase):
    def setUp(self):
        (ROOT / '.cache/tests').mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / '.cache/tests')
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.exe = root / 'Steam/steam.exe'
        self.exe.parent.mkdir(); self.exe.write_bytes(b'MZsynthetic steam; never run')
        self.library = root / 'Library'
        self.libraries = self.exe.parent / 'steamapps/libraryfolders.vdf'
        self.manifest = self.library / 'steamapps/appmanifest_730.acf'
        self.game = self.library / 'steamapps/common/Counter-Strike Global Offensive/game/bin/win64/cs2.exe'
        self.game.parent.mkdir(parents=True); self.game.write_bytes(b'MZsynthetic game; never run')
        self.libraries.parent.mkdir()
        self.write_libraries({'0': {'path': str(self.library), 'apps': {'730': '123'}}})
        self.write_manifest()
        self.resolver = self.enterContext(patch.object(launcher.steam, 'validated_steam_executable', return_value=self.exe))
        self.popen = self.enterContext(patch.object(launcher.subprocess, 'Popen'))
        self.uri = self.enterContext(patch('os.startfile', create=True))

    def write_libraries(self, values):
        self.libraries.write_text(kv({'libraryfolders': values}), encoding='utf-8')

    def write_manifest(self, **extra):
        values = {'appid': '730', 'stateflags': '4', 'installdir': 'Counter-Strike Global Offensive', **extra}
        self.manifest.write_text(kv({'AppState': values}), encoding='utf-8')

    def test_dispatch_uses_only_validated_steam_fixed_applaunch_730_and_steam_cwd(self):
        self.assertEqual(launcher.validated_cs2_installation(self.exe), self.game)
        result = launcher.launch_cs2()
        self.popen.assert_called_once_with([str(self.exe), '-applaunch', '730'], executable=str(self.exe),
            cwd=str(self.exe.parent), shell=False, close_fds=True, stdin=launcher.subprocess.DEVNULL,
            stdout=launcher.subprocess.DEVNULL, stderr=launcher.subprocess.DEVNULL)
        self.assertIn('não verificados', result)
        self.assertNotIn(str(self.game), str(self.popen.call_args))
        self.uri.assert_not_called()

    def test_missing_untrusted_or_changed_steam_is_failure_without_fallback(self):
        for failure in (FileNotFoundError(), PermissionError(), launcher.steam.SteamLaunchError('steam_signature_untrusted')):
            with self.subTest(error=type(failure).__name__), patch.object(launcher.steam, 'validated_steam_executable', side_effect=failure), self.assertRaises(type(failure)):
                launcher.launch_cs2()
        self.exe.unlink()
        with self.assertRaises(FileNotFoundError): launcher.launch_cs2()
        self.popen.assert_not_called(); self.uri.assert_not_called()

    def test_missing_metadata_or_game_and_non_executable_never_dispatch(self):
        for path in (self.libraries, self.manifest, self.game):
            original = path.read_bytes(); path.unlink()
            with self.subTest(path=path.name), self.assertRaises(OSError): launcher.launch_cs2()
            path.write_bytes(original)
        self.game.write_bytes(b'not an executable')
        with self.assertRaisesRegex(launcher.Cs2LaunchError, 'executable'): launcher.launch_cs2()
        self.popen.assert_not_called(); self.uri.assert_not_called()

    def test_uninstalled_or_conflicting_libraries_never_dispatch(self):
        for values in ({'0': {'path': str(self.library), 'apps': {}}},
                       {'0': {'path': str(self.library), 'apps': {'730': '1'}}, '1': {'path': str(self.exe.parent), 'apps': {'730': '1'}}},
                       {'0': str(self.library)}, {'0': {'path': str(self.library), 'apps': 'bad'}}):
            with self.subTest(values=values):
                self.write_libraries(values)
                with self.assertRaises(launcher.Cs2LaunchError): launcher.launch_cs2()
        self.popen.assert_not_called()

    def test_registry_and_library_path_injection_never_dispatch(self):
        for value in ('library', r'\\server\share', r'C:\Library\..\bad', r'C:\Library:stream',
                      r'"C:\Library" -insecure', '%TEMP%\\Library'):
            self.write_libraries({'0': {'path': value, 'apps': {'730': '1'}}})
            with self.subTest(value=value), self.assertRaises(launcher.steam.SteamLaunchError): launcher.launch_cs2()
        self.popen.assert_not_called(); self.uri.assert_not_called()

    def test_manifest_identity_state_and_directory_injection_rejected(self):
        changes = [{'appid': '999'}, {'stateflags': '6'}, {'stateflags': '0'}]
        changes += [{'installdir': value} for value in ('', '..', '../bad', r'..\bad', r'C:\bad', 'a:ads',
                     'dir --bad/other', 'dir.', ' dir', 'dir ', 'a|b', 'a\x00b')]
        for change in changes:
            self.write_manifest(**change)
            with self.subTest(change=change), self.assertRaises(launcher.Cs2LaunchError): launcher.launch_cs2()
        self.popen.assert_not_called(); self.uri.assert_not_called()

    def test_malformed_duplicate_large_and_deep_keyvalues_fail_closed(self):
        for text in ('#include "evil"', '"a" "1" "A" "2"', '"a" {', '"a" { "b" "c" } }',
                     '"a" "bad\\q"', '"a" { '*10 + '"x" "y"' + '}'*10, 'x'*(1024*1024+1)):
            self.libraries.write_text(text)
            with self.subTest(prefix=text[:30]), self.assertRaises(launcher.Cs2LaunchError): launcher.launch_cs2()
        self.popen.assert_not_called()

    def test_comments_bom_and_escaped_library_paths_supported(self):
        self.libraries.write_text('// local metadata\n'+self.libraries.read_text(encoding='utf-8'), encoding='utf-8-sig')
        self.assertEqual(launcher.validated_cs2_installation(self.exe), self.game)
        self.popen.assert_not_called()

    def test_library_manifest_or_game_redirection_rejected(self):
        original = Path.lstat
        for redirected in (self.library, self.manifest, self.game, self.game.parent):
            def info(path, *args, **kwargs):
                return SimpleNamespace(st_file_attributes=0x400) if path == redirected else original(path, *args, **kwargs)
            with self.subTest(component=redirected.name), patch.object(Path, 'lstat', info), self.assertRaisesRegex(launcher.Cs2LaunchError, 'redirected'):
                launcher.launch_cs2()
        self.popen.assert_not_called()

    def test_popen_failure_is_one_attempt_no_uri_or_direct_game_fallback(self):
        self.popen.side_effect = OSError('synthetic creation failure')
        with self.assertRaises(OSError): launcher.launch_cs2()
        self.popen.assert_called_once(); self.uri.assert_not_called()

    def test_interactive_guard_precedes_cs2_resolution_and_no_client_parameters(self):
        with patch('secure_apps.require_interactive_user', side_effect=PermissionError), self.assertRaises(PermissionError):
            launch_allowed('cs2')
        self.resolver.assert_not_called()
        with self.assertRaises(TypeError): launcher.launch_cs2('-insecure')
        for value in ('cs2 -insecure', 'cs2.exe', 'steam://rungameid/730', 'cmd.exe'):
            with self.assertRaises(ValueError): launch_allowed(value)
        self.popen.assert_not_called()


if __name__ == '__main__': unittest.main()
