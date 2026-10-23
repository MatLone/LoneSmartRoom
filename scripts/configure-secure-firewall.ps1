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
    & '.\.venv\Scripts\python.exe' -c "import sys; sys.path.insert(0,'agent/windows'); from secure_protocol import validate_lan; validate_lan(sys.argv[1],sys.argv[2])" $HostAddress $Network
    if ($LASTEXITCODE -ne 0) { throw 'Invalid authorized LAN.' }
    $interface = @(Get-NetIPAddress -AddressFamily IPv4 -IPAddress $HostAddress -ErrorAction Stop)
    if ($interface.Count -ne 1) { throw 'Ambiguous local interface.' }
    $profile = @(Get-NetConnectionProfile -InterfaceIndex $interface[0].InterfaceIndex -ErrorAction Stop)
    if ($profile.Count -ne 1 -or $profile[0].NetworkCategory -ne 'Private') { throw 'Refusing a firewall exception on a non-Private network.' }
    if (!(Get-NetFirewallProfile -Name Private).Enabled) { throw 'Private firewall must be enabled.' }
    # Windows venv launchers can redirect to the base Python image. Scope the rule
    # to the verified listener's actual executable, not an assumed launcher path.
    $listener = @(Get-NetTCPConnection -LocalAddress $HostAddress -LocalPort $Port -State Listen -ErrorAction Stop)
    if ($listener.Count -ne 1) { throw 'Start the secure listener first, with the firewall still closed.' }
    $agentPid = [int]$listener[0].OwningProcess
    $agentProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$agentPid"
    $agentScript = Join-Path $root 'agent\windows\secure_agent.py'
    if (!$agentProcess.ExecutablePath -or $agentProcess.CommandLine -notmatch [regex]::Escape($agentScript)) {
        throw 'The listening process is not this project secure agent.'
    }
    $name = 'Lone Smart Room Secure Status HTTPS'
    if (Get-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue) {
        throw 'Rule already exists. Review it explicitly; it will not be overwritten.'
    }
    if ($PSCmdlet.ShouldProcess("$HostAddress TCP/$Port from $Network, Private profile only", 'Create LAN-only firewall exception')) {
        New-NetFirewallRule -DisplayName $name -Direction Inbound -Action Allow -Protocol TCP `
            -LocalPort $Port -LocalAddress $HostAddress -RemoteAddress $Network -Profile Private `
            -InterfaceAlias $interface[0].InterfaceAlias -Program $agentProcess.ExecutablePath `
            -EdgeTraversalPolicy Block | Out-Null
    }
} finally { Pop-Location }
