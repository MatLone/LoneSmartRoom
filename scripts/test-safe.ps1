$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$python = Join-Path $root '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $python)) { throw 'Prepare the agent virtual environment first.' }
Push-Location $root
try {
    & $python -B agent/windows/test_agent.py
    if ($LASTEXITCODE -ne 0) { throw 'Agent tests failed.' }
    & $python -B -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Baseline regression tests failed.' }
    & node --check apps/windows-ui/app.js
    if ($LASTEXITCODE -ne 0) { throw 'Renderer syntax check failed.' }
    & node --check apps/windows-ui/main.cjs
    if ($LASTEXITCODE -ne 0) { throw 'Main process syntax check failed.' }
    & node --check apps/windows-ui/preload.cjs
    if ($LASTEXITCODE -ne 0) { throw 'Preload syntax check failed.' }
    & node --check apps/windows-ui/agent-status.js
    if ($LASTEXITCODE -ne 0) { throw 'Status UI syntax check failed.' }
} finally { Pop-Location }
