param(
    [Parameter(Mandatory)][ValidateSet('pair','devices','revoke','serve','install-startup','remove-startup')][string]$Action,
    [ValidatePattern('^[0-9a-f]{32}$')][string]$DeviceId
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$python = Join-Path $root '.venv\Scripts\python.exe'
$agent = Join-Path $root 'agent\windows\secure_agent.py'
if ($Action -eq 'revoke') {
    if (!$DeviceId) { throw 'Provide -DeviceId from the devices list.' }
    & $python -B $agent revoke $DeviceId
} else {
    & $python -B $agent $Action
}
if ($LASTEXITCODE -ne 0) { throw 'Agent management failed.' }
