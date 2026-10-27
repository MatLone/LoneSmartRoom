param(
    [string]$JavaHome = 'C:\Program Files\Android\Android Studio\jbr',
    [string]$SdkRoot = "$env:LOCALAPPDATA\Android\Sdk",
    [ValidatePattern('^[a-z0-9-]{1,40}$')][string]$CandidateTag
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
# No adb, install, uninstall, data cleanup, or device operation is performed here.
& (Join-Path $PSScriptRoot 'android-build.ps1') -JavaHome $JavaHome -SdkRoot $SdkRoot `
    -OriginalSigning -Tasks @('--offline', 'assembleDebug', 'lintDebug')
$verificationArguments = @('--sdk-root', $SdkRoot)
if ($CandidateTag) { $verificationArguments += @('--candidate-tag', $CandidateTag) }
& (Join-Path $root '.venv\Scripts\python.exe') -B (Join-Path $PSScriptRoot 'verify-compatible-apk.py') @verificationArguments
if ($LASTEXITCODE -ne 0) { throw 'Compatible APK verification failed; do not install.' }
