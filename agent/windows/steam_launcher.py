"""Local Steam installation only. No URI, shell, network arguments or retry."""
import ctypes as c
from ctypes import wintypes as w
import os
from pathlib import Path, PureWindowsPath
import subprocess
import uuid


class SteamLaunchError(RuntimeError):
    """Technical code only: never include registry contents or credentials."""


def _local_absolute(value):
    if not isinstance(value, str) or not value or value != value.strip():
        raise SteamLaunchError('invalid_install_path')
    path = PureWindowsPath(value)
    if (len(path.drive) != 2 or path.drive[1] != ':' or not path.is_absolute()
            or any(part in ('.', '..') for part in value.replace('/', '\\').split('\\'))
            or any(char in value for char in '"\x00\r\n%') or ':' in value[2:]):
        raise SteamLaunchError('invalid_install_path')
    return Path(value)


def registered_executables():
    """Read fixed Windows values; absent entries are allowed, conflicts are not."""
    import winreg
    candidates = []
    for hive, key, names in (
        (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Valve\Steam', ('InstallPath',)),
        (winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam', ('SteamPath', 'SteamExe')),
    ):
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            try:
                handle = winreg.OpenKey(hive, key, 0, winreg.KEY_READ | view)
            except FileNotFoundError:
                continue
            with handle:
                for name in names:
                    try:
                        value, kind = winreg.QueryValueEx(handle, name)
                    except FileNotFoundError:
                        continue
                    if kind != winreg.REG_SZ:
                        raise SteamLaunchError('invalid_install_path')
                    path = _local_absolute(value)
                    candidates.append(path if name == 'SteamExe' else path / 'steam.exe')
    if not candidates:
        raise SteamLaunchError('steam_not_registered')
    return candidates


def _canonical_executable(path):
    path = _local_absolute(str(path))
    if path.name.casefold() != 'steam.exe':
        raise SteamLaunchError('invalid_executable')
    # Reject redirected installation components instead of allowing a junction
    # or symlink to move the approved root between validation and dispatch.
    for component in (path, *path.parents):
        info = component.lstat()
        if getattr(info, 'st_file_attributes', 0) & 0x400:
            raise SteamLaunchError('redirected_installation')
    resolved = path.resolve(strict=True)
    if resolved != path or not resolved.is_file():
        raise SteamLaunchError('invalid_executable')
    with resolved.open('rb') as stream:
        if stream.read(2) != b'MZ':
            raise SteamLaunchError('invalid_executable')
    return resolved


class _FileInfo(c.Structure):
    _fields_ = [('size', w.DWORD), ('path', w.LPCWSTR), ('file', w.HANDLE), ('subject', c.c_void_p)]


class _TrustData(c.Structure):
    _fields_ = [('size', w.DWORD), ('policy', c.c_void_p), ('sip', c.c_void_p),
                ('ui', w.DWORD), ('revocation', w.DWORD), ('choice', w.DWORD),
                ('file', c.POINTER(_FileInfo)), ('action', w.DWORD), ('state', w.HANDLE),
                ('url', w.LPCWSTR), ('flags', w.DWORD), ('context', w.DWORD), ('settings', c.c_void_p)]


class _ProviderCert(c.Structure):
    # SDK prefix through pCert; remaining fields are never accessed.
    _fields_ = [('size', w.DWORD), ('cert', c.c_void_p)]


class _ProviderSigner(c.Structure):
    # SDK prefix through pasCertChain; remaining fields are never accessed.
    _fields_ = [('size', w.DWORD), ('as_of', w.FILETIME), ('count', w.DWORD),
                ('certs', c.POINTER(_ProviderCert))]


def verify_valve_signature(path):
    """Authenticode and verified signer's organization; local revocation cache only.

    A missing chain/revocation cache fails closed. No network retrieval, UI,
    downloaded helper, certificate installation or trust-store mutation.
    """
    if os.name != 'nt':
        raise SteamLaunchError('windows_required')
    trust = c.WinDLL('wintrust', winmode=0x800)
    crypt = c.WinDLL('crypt32', winmode=0x800)
    verify = trust.WinVerifyTrust
    verify.argtypes = [w.HWND, c.c_void_p, c.POINTER(_TrustData)]
    verify.restype = c.c_long
    provider = trust.WTHelperProvDataFromStateData
    provider.argtypes = [w.HANDLE]; provider.restype = c.c_void_p
    signer = trust.WTHelperGetProvSignerFromChain
    signer.argtypes = [c.c_void_p, w.DWORD, w.BOOL, w.DWORD]
    signer.restype = c.POINTER(_ProviderSigner)
    name = crypt.CertGetNameStringW
    name.argtypes = [c.c_void_p, w.DWORD, w.DWORD, c.c_void_p, w.LPWSTR, w.DWORD]
    name.restype = w.DWORD
    action = c.create_string_buffer(uuid.UUID('00aac56b-cd44-11d0-8cc2-00c04fc295ee').bytes_le)
    file = _FileInfo(c.sizeof(_FileInfo), str(path), None, None)
    data = _TrustData()
    data.size = c.sizeof(data); data.ui = 2; data.choice = 1
    data.file = c.pointer(file); data.action = 1
    data.flags = 0x1000 | 0x80 | 0x2000  # cache only; chain except root; reject MD2/MD4
    try:
        if verify(w.HWND(-1), action, c.byref(data)) != 0:
            raise SteamLaunchError('steam_signature_untrusted')
        info = provider(data.state) if data.state else None
        chain = signer(info, 0, False, 0) if info else None
        if not chain or not chain.contents.count or not chain.contents.certs:
            raise SteamLaunchError('steam_signer_unavailable')
        cert = chain.contents.certs[0].cert
        if not cert:
            raise SteamLaunchError('steam_signer_unavailable')
        organization = c.create_unicode_buffer(256)
        oid = c.c_char_p(b'2.5.4.10')  # subject organization, not issuer/display name
        length = name(cert, 3, 0, c.cast(oid, c.c_void_p), organization, len(organization))
        if not 1 < length < len(organization) or organization.value != 'Valve Corp.':
            raise SteamLaunchError('steam_publisher_not_allowed')
    finally:
        data.action = 2  # close provider state even when verification fails
        verify(w.HWND(-1), action, c.byref(data))


def validated_steam_executable():
    candidates = {_canonical_executable(path) for path in registered_executables()}
    if len(candidates) != 1:
        raise SteamLaunchError('conflicting_steam_installations')
    executable = candidates.pop()
    before = executable.stat()
    verify_valve_signature(executable)
    after = executable.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise SteamLaunchError('steam_changed_during_validation')
    return executable


def launch_steam():
    """Popen return is dispatch only; UI/readiness must be verified separately."""
    if os.name != 'nt':
        raise SteamLaunchError('windows_required')
    executable = validated_steam_executable()
    # Recheck redirection immediately before dispatch; no absolute protection against
    # a malicious local user who controls the installation and races CreateProcess.
    if _canonical_executable(executable) != executable:
        raise SteamLaunchError('invalid_executable')
    subprocess.Popen([str(executable)], executable=str(executable), cwd=str(executable.parent),
                     shell=False, close_fds=True, stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return 'Pedido para abrir Steam entregue ao Windows; janela não verificada.'
