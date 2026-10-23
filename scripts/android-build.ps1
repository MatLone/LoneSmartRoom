param(
    [string]$JavaHome = 'C:\Program Files\Android\Android Studio\jbr',
    [string]$SdkRoot = "$env:LOCALAPPDATA\Android\Sdk",
    [string[]]$Tasks = @('assembleDebug'),
    [switch]$OriginalSigning
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
if (!(Test-Path -LiteralPath "$JavaHome\bin\java.exe")) { throw 'Provide -JavaHome pointing to a JDK.' }
if (!(Test-Path -LiteralPath "$SdkRoot\platforms\android-35\android.jar")) { throw 'Android SDK platform 35 is required.' }
$env:JAVA_HOME = $JavaHome
$env:ANDROID_HOME = $SdkRoot
$env:ANDROID_SDK_ROOT = $SdkRoot
$env:GRADLE_USER_HOME = Join-Path $root '.cache\gradle'
$env:ANDROID_USER_HOME = Join-Path $root '.cache\android'
# Do not set both mechanisms: AGP rejects inconsistent legacy preference paths.
$env:ANDROID_PREFS_ROOT = $null
$previousSigningKeystore = $env:LONE_ANDROID_SIGNING_KEYSTORE
if ($OriginalSigning) {
    $originalKeystore = Join-Path ([Environment]::GetFolderPath('UserProfile')) '.android\debug.keystore'
    if (!(Test-Path -LiteralPath $originalKeystore -PathType Leaf)) { throw 'Original signing keystore is unavailable.' }
    $env:LONE_ANDROID_SIGNING_KEYSTORE = $originalKeystore
} else {
    $env:LONE_ANDROID_SIGNING_KEYSTORE = $null
}
New-Item -ItemType Directory -Path $env:ANDROID_USER_HOME -Force | Out-Null
Push-Location (Join-Path $root 'apps\android')
try {
    & '.\gradlew.bat' --no-daemon --console=plain @Tasks
    if ($LASTEXITCODE -ne 0) { throw "Android build failed: $LASTEXITCODE" }
} finally {
    Pop-Location
    $env:LONE_ANDROID_SIGNING_KEYSTORE = $previousSigningKeystore
}
