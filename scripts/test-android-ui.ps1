$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$electron = Join-Path $root 'apps/windows-ui/node_modules/electron/dist/electron.exe'
if (!(Test-Path -LiteralPath $electron -PathType Leaf)) { throw 'Existing Electron runtime is required; this script does not install dependencies.' }
$logs = Join-Path $root '.cache/validation'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
Push-Location $root
try {
    # Test-only preload records calls. No real bridges, devices, network or apps.
    $process = Start-Process -FilePath $electron -ArgumentList 'tests/android-mobile-smoke.cjs' `
        -WindowStyle Hidden -Wait -PassThru `
        -RedirectStandardOutput (Join-Path $logs 'android-mobile-out.log') `
        -RedirectStandardError (Join-Path $logs 'android-mobile-err.log')
    Get-Content -LiteralPath (Join-Path $logs 'android-mobile-out.log')
    Get-Content -LiteralPath (Join-Path $logs 'android-mobile-err.log')
    if ($process.ExitCode -ne 0) { throw "Android renderer tests failed: $($process.ExitCode)" }
} finally { Pop-Location }
