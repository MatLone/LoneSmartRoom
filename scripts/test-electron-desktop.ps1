param([ValidateSet('1','1.25','1.5')][string]$Scale = '1')
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$electron = Join-Path $root 'apps/windows-ui/node_modules/electron/dist/electron.exe'
$output = Join-Path $root '.cache/validation/windows-desktop-integration'
New-Item -ItemType Directory -Force -Path $output | Out-Null
$previousOptions = $env:NODE_OPTIONS
$previousScale = $env:LONE_TEST_SCALE
try {
    $bootstrap = (Join-Path $root 'tests/electron-native-bootstrap.cjs').Replace('\','/')
    $env:NODE_OPTIONS = '--require="' + $bootstrap + '"'
    $env:LONE_TEST_SCALE = $Scale
    $process = Start-Process -FilePath $electron -ArgumentList @('apps/windows-ui','--lone-development-review',('--force-device-scale-factor='+$Scale)) `
        -WorkingDirectory $root -WindowStyle Normal -Wait -PassThru `
        -RedirectStandardOutput (Join-Path $output ('native-'+$Scale+'-out.txt')) `
        -RedirectStandardError (Join-Path $output ('native-'+$Scale+'-err.txt'))
    Get-Content -LiteralPath (Join-Path $output ('native-'+$Scale+'-out.txt'))
    Get-Content -LiteralPath (Join-Path $output ('native-'+$Scale+'-err.txt'))
    if ($process.ExitCode -ne 0) { throw ('Native Electron UI test failed: '+$process.ExitCode) }
} finally {
    $env:NODE_OPTIONS = $previousOptions
    $env:LONE_TEST_SCALE = $previousScale
}
