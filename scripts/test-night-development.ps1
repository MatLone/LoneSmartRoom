param([switch]$BuildAndroid)
$ErrorActionPreference='Stop'
$repoRoot=Split-Path $PSScriptRoot -Parent
Push-Location $repoRoot
try {
    if($BuildAndroid){ & "$PSScriptRoot/android-build.ps1" -SdkRoot (Join-Path $env:USERPROFILE 'AppData\Local\Android\Sdk') -Tasks @('assembleDebug','lintDebug','testDebugUnitTest') }
    # Ephemeral loopback test identity/store only. Never run passive/live-agent scripts here.
    & '.venv/Scripts/python.exe' -B 'tests/test_remote_telemetry.py'
    if($LASTEXITCODE -ne 0){throw 'Remote telemetry regression failed'}
    & '.venv/Scripts/python.exe' -B 'scripts/test-diagnostic-evidence.py'
    if($LASTEXITCODE -ne 0){throw 'Python preservation regression failed'}
    & '.venv/Scripts/python.exe' -B -m unittest discover -s tests -p test_android_visual_preservation.py -v
    if($LASTEXITCODE -ne 0){throw 'Android preservation regression failed'}
    foreach($suite in @('scripts/test-diagnostic-evidence.cjs','tests/remote-telemetry.cjs','tests/performance-history.cjs','tests/diagnostic-adapter-integration.cjs','tests/gamer-session.cjs','scripts/measure-night-mocks.cjs')){
        & 'C:\Program Files\nodejs\node.exe' $suite
        if($LASTEXITCODE -ne 0){throw "Isolated Node suite failed: $suite"}
    }
} finally { Pop-Location }
