[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$HostAddress = '172.31.250.8',
    [string]$Network = '172.31.250.0/24',
    [ValidateRange(1024,65535)][int]$Port = 8776
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
Push-Location $root
try {
    & '.\.venv\Scripts\python.exe' -c 'import sys; sys.path.insert(0,"agent/windows"); from secure_protocol import validate_lan; validate_lan(sys.argv[1],sys.argv[2])' $HostAddress $Network
    if ($LASTEXITCODE -ne 0) { throw 'Invalid authorized LAN.' }
    $interface = Get-NetIPAddress -AddressFamily IPv4 -IPAddress $HostAddress -ErrorAction Stop
    $profile = Get-NetConnectionProfile -InterfaceIndex $interface.InterfaceIndex -ErrorAction Stop
    if ($profile.NetworkCategory -ne 'Private') { throw 'Refusing a firewall exception on a non-Private network.' }
    $name = 'Lone Smart Room Secure Status HTTPS'
    if (Get-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue) {
        throw 'Rule already exists. Review it explicitly; it will not be overwritten.'
    }
    if ($PSCmdlet.ShouldProcess("$HostAddress TCP/$Port from $Network, Private profile only", 'Create LAN-only firewall exception')) {
        New-NetFirewallRule -DisplayName $name -Direction Inbound -Action Allow -Protocol TCP `
            -LocalPort $Port -LocalAddress $HostAddress -RemoteAddress $Network -Profile Private `
            -EdgeTraversalPolicy Block | Out-Null
    }
} finally { Pop-Location }
