param(
    [string]$JavaHome = 'C:\Program Files\Android\Android Studio\jbr',
    [string]$SdkRoot = "$env:LOCALAPPDATA\Android\Sdk"
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
# No adb, install, uninstall, data cleanup, or device operation is performed here.
& (Join-Path $PSScriptRoot 'android-build.ps1') -JavaHome $JavaHome -SdkRoot $SdkRoot `
    -OriginalSigning -Tasks @('--offline', 'assembleDebug', 'lintDebug')
& (Join-Path $root '.venv\Scripts\python.exe') -B (Join-Path $PSScriptRoot 'verify-compatible-apk.py') `
    --sdk-root $SdkRoot
if ($LASTEXITCODE -ne 0) { throw 'Compatible APK verification failed; do not install.' }
