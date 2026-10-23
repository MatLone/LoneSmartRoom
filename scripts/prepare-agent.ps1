$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
Push-Location $root
try {
    if (!(Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
        & python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
    }
    & '.\.venv\Scripts\python.exe' -m pip install --require-hashes -r agent/windows/requirements.lock --cache-dir .cache/pip
    if ($LASTEXITCODE -ne 0) { throw 'Verified dependency installation failed.' }
} finally { Pop-Location }
