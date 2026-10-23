"""Fail closed on untrusted Windows network profiles; no profile/firewall mutation."""
import ipaddress
import subprocess
import sys


def private_profile(host):
    host = str(ipaddress.IPv4Address(host))
    if sys.platform != 'win32':
        return False
    command = (f"$i=Get-NetIPAddress -AddressFamily IPv4 -IPAddress '{host}' -ErrorAction Stop; "
               "$p=Get-NetConnectionProfile -InterfaceIndex $i.InterfaceIndex -ErrorAction Stop; "
               "if($p.NetworkCategory -eq 'Private'){[Console]::Write('private')}")
    try:
        result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command],
            capture_output=True, text=True, timeout=8, creationflags=subprocess.CREATE_NO_WINDOW)
        return result.returncode == 0 and result.stdout == 'private'
    except (OSError, subprocess.TimeoutExpired):
        return False
