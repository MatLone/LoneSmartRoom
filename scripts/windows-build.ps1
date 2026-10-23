$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$env:npm_config_cache = Join-Path $root '.cache\npm'
$env:ELECTRON_CACHE = Join-Path $root '.cache\electron'
$env:ELECTRON_BUILDER_CACHE = Join-Path $root '.cache\electron-builder'
$env:CSC_IDENTITY_AUTO_DISCOVERY = 'false'
Push-Location (Join-Path $root 'apps\windows-ui')
try {
    & npm.cmd ci --no-fund --no-audit
    if ($LASTEXITCODE -ne 0) { throw "npm ci failed: $LASTEXITCODE" }
    & (Join-Path $PSScriptRoot 'prepare-windows-tools.ps1')
    & npm.cmd run dist:win
    if ($LASTEXITCODE -ne 0) { throw "Windows packaging failed: $LASTEXITCODE" }
} finally { Pop-Location }
