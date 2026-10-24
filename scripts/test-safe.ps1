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
    & node --check apps/windows-ui/app-launch.js
    if ($LASTEXITCODE -ne 0) { throw 'App launch UI syntax check failed.' }
    & node tests/version-launch-ui.cjs
    if ($LASTEXITCODE -ne 0) { throw 'Version/app launch UI tests failed.' }
    foreach ($name in @('mobile-shell.js','mobile-bindings.js','wol-ui.js')) {
        & node --check "apps/android/app/src/main/assets/$name"
        if ($LASTEXITCODE -ne 0) { throw "Android UI syntax check failed: $name" }
    }
    & node tests/android-wol-ui.cjs
    if ($LASTEXITCODE -ne 0) { throw 'Android WoL persistence tests failed.' }
} finally { Pop-Location }
