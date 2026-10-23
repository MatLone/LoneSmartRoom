$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$exe = Join-Path $root 'apps\windows-ui\node_modules\electron\dist\electron.exe'
if (!(Test-Path -LiteralPath $exe)) { throw 'Run windows-build.ps1 (npm ci + Electron runtime install) first.' }
New-Item -ItemType Directory -Path (Join-Path $root '.cache\validation') -Force | Out-Null
$env:ELECTRON_RUN_AS_NODE = $null
$process = Start-Process -FilePath $exe -ArgumentList 'tests/electron-smoke.cjs' -WorkingDirectory $root `
    -WindowStyle Hidden -Wait -PassThru `
    -RedirectStandardOutput (Join-Path $root '.cache\validation\electron-smoke.out.log') `
    -RedirectStandardError (Join-Path $root '.cache\validation\electron-smoke.err.log')
if ($process.ExitCode -ne 0) { throw "Electron smoke failed: $($process.ExitCode)" }
Get-Content -LiteralPath (Join-Path $root '.cache\electron-smoke\result.json')
