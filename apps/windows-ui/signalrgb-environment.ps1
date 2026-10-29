$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
# Read-only census. No private SignalRGB databases or settings, no SDK write.
$root = Join-Path $env:LOCALAPPDATA 'VortxEngine'
$launcher = Join-Path $root 'SignalRgbLauncher.exe'
$processes = @(Get-CimInstance Win32_Process -Filter "Name='SignalRgb.exe' OR Name='OpenRGB.exe'")
$signal = @($processes | Where-Object Name -eq 'SignalRgb.exe')
$open = @($processes | Where-Object Name -eq 'OpenRGB.exe')
$listeners = @(Get-NetTCPConnection -State Listen -LocalPort 16038 -ErrorAction SilentlyContinue)
$verified = $false
$version = $null
$effects = @()
$launcherValid = $false
$launcherBuild = $null
if (Test-Path -LiteralPath $launcher -PathType Leaf) {
 $sig = Get-AuthenticodeSignature -LiteralPath $launcher
 $launcherValid = ($sig.Status -eq 'Valid' -and $sig.SignerCertificate.Subject -match '^CN=SignalRGB \(Whirlwind Virtual Realities Inc\.\),')
}
if ($signal.Count -eq 1 -and $signal[0].ExecutablePath) {
 $exe = [IO.Path]::GetFullPath($signal[0].ExecutablePath)
 $expected = '^' + [regex]::Escape($root) + '\\app-[0-9.]+\\Signal-x64\\SignalRgb\.exe$'
 if ($exe -match $expected) {
  $version = (Get-Item -LiteralPath $exe).VersionInfo.FileVersion
  $appDirectory = Split-Path (Split-Path $exe)
  $launcherBuild = (Split-Path $appDirectory -Leaf).Substring(4)
  $launcher = Join-Path $appDirectory 'SignalRgbLauncher.exe'
  $sig = Get-AuthenticodeSignature -LiteralPath $launcher
  $launcherValid = ($sig.Status -eq 'Valid' -and $sig.SignerCertificate.Subject -match '^CN=SignalRGB \(Whirlwind Virtual Realities Inc\.\),')
  $exeSig = Get-AuthenticodeSignature -LiteralPath $exe
  $verified = ($exeSig.Status -eq 'Valid' -and $exeSig.SignerCertificate.Subject -match '^CN=SignalRGB \(Whirlwind Virtual Realities Inc\.\),' -and $listeners.Count -eq 1 -and $listeners[0].OwningProcess -eq $signal[0].ProcessId)
  $folders = @((Join-Path (Split-Path $exe) 'Effects\Dynamic'), (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'WhirlwindFX\Effects'))
  foreach ($folder in $folders) {
   if (!(Test-Path -LiteralPath $folder -PathType Container)) { continue }
   if ((Get-Item -LiteralPath $folder).Attributes -band [IO.FileAttributes]::ReparsePoint) { continue }
   foreach ($file in @(Get-ChildItem -LiteralPath $folder -Filter '*.html' -File | Select-Object -First 256)) {
    if ($file.Length -gt 262144 -or ($file.Attributes -band [IO.FileAttributes]::ReparsePoint)) { continue }
    $html = [IO.File]::ReadAllText($file.FullName)
    $match = [regex]::Match($html, '<title>\s*([^<>\r\n]{1,160})\s*</title>', 'IgnoreCase')
    if ($match.Success) {
     $name = [Net.WebUtility]::HtmlDecode($match.Groups[1].Value.Trim())
     if ($name -notmatch '[\x00-\x1f\x7f<>\\/]') { $effects += @{id=$file.Name;name=$name;source='documented_local_html'} }
    }
   }
  }
 }
}
@{v=1;verified=$verified;signalRunning=($signal.Count -gt 0);openRunning=($open.Count -gt 0);version=$version;launcherValid=$launcherValid;launcherBuild=$launcherBuild;apiBroadBinding=(@($listeners | Where-Object LocalAddress -in @('::','0.0.0.0')).Count -gt 0);effects=@($effects | Sort-Object name -Unique)} | ConvertTo-Json -Depth 4 -Compress
