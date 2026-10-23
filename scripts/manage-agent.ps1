param(
    [Parameter(Mandatory)][ValidateSet('pair','devices','revoke','serve','install-startup','remove-startup','grant-apps','revoke-apps','app-permissions')][string]$Action,
    [ValidatePattern('^[0-9a-f]{32}$')][string]$DeviceId,
    [ValidateSet('steam','cs2')][string[]]$Apps
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$python = Join-Path $root '.venv\Scripts\python.exe'
$agent = Join-Path $root 'agent\windows\secure_agent.py'
if ($Action -eq 'serve') {
    $existing = @(Get-CimInstance Win32_Process -Filter "Name='pythonw.exe'" | Where-Object {
        $_.CommandLine -match [regex]::Escape($agent)
    })
    if ($existing.Count) { Write-Output 'O agente já possui um processo em segundo plano.'; return }
    $backgroundPython = Join-Path $root '.venv\Scripts\pythonw.exe'
    if (!(Test-Path -LiteralPath $backgroundPython)) { throw 'The Windows Python virtual environment is required.' }
    Start-Process -FilePath $backgroundPython -ArgumentList @(('"' + $agent + '"'), 'serve') `
        -WorkingDirectory $root -WindowStyle Hidden | Out-Null
    Write-Output 'Inicialização em segundo plano solicitada; confirme a disponibilidade por HTTPS.'
    return
}
if ($Action -in @('grant-apps','revoke-apps','app-permissions')) {
    if (!$DeviceId) { throw 'Provide the explicitly selected device ID.' }
    if ($Action -eq 'app-permissions') { & $python -B $agent $Action $DeviceId }
    else {
        if (!$Apps) { throw 'Explicitly select Steam and/or CS2.' }
        & $python -B $agent $Action $DeviceId --apps @Apps
    }
} elseif ($Action -eq 'revoke') {
    if (!$DeviceId) { throw 'Provide -DeviceId from the devices list.' }
    & $python -B $agent revoke $DeviceId
} else {
    & $python -B $agent $Action
}
if ($LASTEXITCODE -ne 0) { throw 'Agent management failed.' }
