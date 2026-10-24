"""Dispatch only CS2 through the validated Steam client; never run cs2.exe directly."""
from pathlib import PureWindowsPath
import re
import subprocess
import steam_launcher as steam


class Cs2LaunchError(RuntimeError):
    """Fixed diagnostic codes only, without metadata or account information."""


def _plain_path(path):
    path = steam._local_absolute(str(path))
    for component in (path, *path.parents):
        if getattr(component.lstat(), 'st_file_attributes', 0) & 0x400:
            raise Cs2LaunchError('redirected_cs2_installation')
    if path.resolve(strict=True) != path:
        raise Cs2LaunchError('invalid_cs2_installation')
    return path


_TOKEN = re.compile(r'\s+|//[^\r\n]*|"(?:\\[\\"]|[^"\\\x00-\x1f])*"|[{}]')


def _keyvalues(path):
    """Bounded quoted KeyValues subset used by current library/manifest files.

    Unsupported syntax, duplicate keys and malformed files fail closed. No eval,
    external includes, account files, third-party parser or metadata execution.
    """
    path = _plain_path(path)
    with path.open('rb') as source:
        raw = source.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise Cs2LaunchError('cs2_metadata_too_large')
    text = raw.decode('utf-8-sig')
    tokens, position = [], 0
    while position < len(text):
        match = _TOKEN.match(text, position)
        if not match:
            raise Cs2LaunchError('invalid_cs2_metadata')
        token = match.group()
        position = match.end()
        if token.isspace() or token.startswith('//'):
            continue
        tokens.append(token)
        if len(tokens) > 20000:
            raise Cs2LaunchError('cs2_metadata_too_large')
    index = 0

    def string(token):
        if not token.startswith('"'):
            raise Cs2LaunchError('invalid_cs2_metadata')
        return re.sub(r'\\([\\"])', r'\1', token[1:-1])

    def object_(depth):
        nonlocal index
        if depth > 8:
            raise Cs2LaunchError('invalid_cs2_metadata')
        result = {}
        while index < len(tokens) and tokens[index] != '}':
            key = string(tokens[index]).casefold()
            index += 1
            if index >= len(tokens) or key in result:
                raise Cs2LaunchError('invalid_cs2_metadata')
            if tokens[index] == '{':
                index += 1
                result[key] = object_(depth + 1)
            else:
                result[key] = string(tokens[index])
                index += 1
        if depth:
            if index >= len(tokens) or tokens[index] != '}':
                raise Cs2LaunchError('invalid_cs2_metadata')
            index += 1
        return result

    result = object_(0)
    if index != len(tokens):
        raise Cs2LaunchError('invalid_cs2_metadata')
    return result


def validated_cs2_installation(steam_executable):
    """Read local Steam metadata; return the expected game path as evidence only."""
    libraries = _keyvalues(steam_executable.parent / 'steamapps/libraryfolders.vdf').get('libraryfolders')
    if not isinstance(libraries, dict):
        raise Cs2LaunchError('invalid_cs2_metadata')
    roots = set()
    for key, entry in libraries.items():
        if not key.isascii() or not key.isdecimal() or not isinstance(entry, dict):
            raise Cs2LaunchError('unsupported_steam_library_format')
        apps = entry.get('apps', {})
        if not isinstance(apps, dict):
            raise Cs2LaunchError('invalid_cs2_metadata')
        if '730' in apps:
            roots.add(_plain_path(steam._local_absolute(entry.get('path'))))
    if len(roots) != 1:
        raise Cs2LaunchError('cs2_missing_or_conflicting_libraries')
    root = roots.pop()
    manifest = _keyvalues(root / 'steamapps/appmanifest_730.acf').get('appstate')
    if not isinstance(manifest, dict) or manifest.get('appid') != '730':
        raise Cs2LaunchError('invalid_cs2_manifest')
    if manifest.get('stateflags') != '4':
        raise Cs2LaunchError('cs2_not_fully_installed')
    directory = manifest.get('installdir')
    if (not isinstance(directory, str) or not directory or directory in ('.', '..')
            or directory != directory.strip() or directory.endswith('.')
            or PureWindowsPath(directory).name != directory
            or any(ord(char) < 32 or char in '<>:"/\\|?*' for char in directory)):
        raise Cs2LaunchError('invalid_cs2_install_directory')
    game = _plain_path(root / 'steamapps/common' / directory / 'game/bin/win64/cs2.exe')
    with game.open('rb') as source:
        if source.read(2) != b'MZ':
            raise Cs2LaunchError('invalid_cs2_executable')
    return game


def launch_cs2():
    """Popen return confirms dispatch only, never process/game readiness."""
    executable = steam.validated_steam_executable()
    validated_cs2_installation(executable)
    if steam._canonical_executable(executable) != executable:
        raise Cs2LaunchError('invalid_steam_executable')
    subprocess.Popen([str(executable), '-applaunch', '730'], executable=str(executable),
                     cwd=str(executable.parent), shell=False, close_fds=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return 'Pedido para abrir CS2 entregue à Steam; processo e jogo não verificados.'
