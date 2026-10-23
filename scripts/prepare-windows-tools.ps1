# Extract only Windows tools from the vendor bundle; macOS symlinks need privileges.
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$archive = Join-Path $root '.cache\electron-builder\winCodeSign-2.6.0.7z'
$target = Join-Path $root '.cache\electron-builder\winCodeSign\winCodeSign-2.6.0'
$expected = 'CDAEC7154DDA7CC31F88D886E2489379A0625A737D610B5AE7F62A12F16743A4'
New-Item -ItemType Directory -Path (Split-Path $archive) -Force | Out-Null
if (!(Test-Path -LiteralPath $archive)) {
    Invoke-WebRequest -Uri 'https://github.com/electron-userland/electron-builder-binaries/releases/download/winCodeSign-2.6.0/winCodeSign-2.6.0.7z' -OutFile $archive
}
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $expected) {
    throw 'Windows packaging vendor-tool checksum mismatch.'
}
if (!(Test-Path -LiteralPath (Join-Path $target 'rcedit-x64.exe'))) {
    $sevenZip = Join-Path $root 'apps\windows-ui\node_modules\7zip-bin\win\x64\7za.exe'
    & $sevenZip x $archive ('-o' + $target) '-xr!darwin' '-xr!linux' -y -bd
    if ($LASTEXITCODE -ne 0) { throw 'Windows vendor-tool extraction failed.' }
}
