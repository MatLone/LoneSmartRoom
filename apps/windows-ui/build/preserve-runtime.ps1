param([ValidateSet('prepare','restore')][string]$Mode,[string]$Source,[string]$Journal,[string]$Known)
# Fixed installer helper, filesystem only. Keeps the recovery copy after success.
$ErrorActionPreference='Stop'
$stage='scope'
try {
 if(![Environment]::Is64BitProcess){throw 'native_x64_host_required'}
 $sourceRoot=[IO.Path]::GetFullPath($Source).TrimEnd('\')
 $journalRoot=[IO.Path]::GetFullPath($Journal).TrimEnd('\')
 if($sourceRoot -eq [IO.Path]::GetPathRoot($sourceRoot).TrimEnd('\') -or !$journalRoot.StartsWith(([IO.Path]::GetFullPath($env:LOCALAPPDATA)+'\LoneSmartRoom-RuntimePreservation\'),[StringComparison]::OrdinalIgnoreCase)){throw 'scope'}
 function NoLink([string]$p){if(Test-Path -LiteralPath $p){if((Get-Item -LiteralPath $p -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'reparse'}}}
 foreach($p in @($sourceRoot,$journalRoot)){for($cursor=$p;$cursor;$cursor=[IO.Path]::GetDirectoryName($cursor)){NoLink $cursor}}
 $manifest=Join-Path $journalRoot 'manifest.json'
 function Hash([string]$p){
  # NSIS does not inherit a PowerShell session's module imports. Use the
  # framework's streaming SHA-256 rather than depending on Get-FileHash autoload.
  $stream=[IO.File]::OpenRead($p);$algorithm=[Security.Cryptography.SHA256]::Create()
  try{return [BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-','').ToLowerInvariant()}
  finally{$algorithm.Dispose();$stream.Dispose()}
 }
 if($Mode -eq 'prepare'){
  $stage='known_manifest'
  if(Test-Path -LiteralPath $journalRoot){throw 'preserve_existing_journal'}
  $knownFiles=New-Object 'Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
  foreach($name in [IO.File]::ReadAllLines($Known)){
   if(!$name -or $name.Contains('..') -or [IO.Path]::IsPathRooted($name)){throw 'manifest_path'}
   [void]$knownFiles.Add($name.Replace('/','\'))
  }
  if($knownFiles.Count -gt 512 -or $knownFiles.Count -lt 10){throw 'manifest_limit'}
  $stage='inventory';$files=New-Object 'Collections.Generic.List[object]'
  function Walk([string]$folder){foreach($item in Get-ChildItem -LiteralPath $folder -Force){NoLink $item.FullName;if($item.PSIsContainer){Walk $item.FullName}else{
   $relative=$item.FullName.Substring($sourceRoot.Length+1)
   if(!$knownFiles.Contains($relative)){$files.Add(@{relative=$relative;bytes=$item.Length;sha256=(Hash $item.FullName)})}
   if($files.Count -gt 256){throw 'file_limit'}
  }}}
  if(Test-Path -LiteralPath $sourceRoot){if(!(Test-Path -LiteralPath (Join-Path $sourceRoot 'Lone Smart Room.exe'))){throw 'not_application'};Walk $sourceRoot}
  if(($files|ForEach-Object {$_.bytes}|Measure-Object -Sum).Sum -gt 67108864){throw 'size_limit'}
  $stage='private_acl';$sid=[Security.Principal.WindowsIdentity]::GetCurrent().User
  $acl=New-Object Security.AccessControl.DirectorySecurity
  $acl.SetAccessRuleProtection($true,$false)
  $rule=New-Object Security.AccessControl.FileSystemAccessRule($sid,'FullControl','ContainerInherit,ObjectInherit','None','Allow')
  $acl.AddAccessRule($rule)
  [void][IO.Directory]::CreateDirectory($journalRoot)
  [IO.Directory]::SetAccessControl($journalRoot,$acl)
  $stage='stable_copy';foreach($f in $files){$from=Join-Path $sourceRoot $f.relative;$to=Join-Path $journalRoot ('data\'+$f.relative);[void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($to));[IO.File]::Copy($from,$to,$false);if((Hash $to) -ne $f.sha256 -or (Hash $from) -ne $f.sha256){throw 'unstable_copy'}}
  @{v=1;source=$sourceRoot;files=@($files.ToArray());complete=$true;helper_architecture_bits=([IntPtr]::Size*8)}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $manifest -Encoding UTF8
 } else {
  $stage='restore_verify'
  $v=Get-Content -LiteralPath $manifest -Raw|ConvertFrom-Json
  if($v.v -ne 1 -or !$v.complete -or $v.source -ne $sourceRoot -or $v.files.Count -gt 256){throw 'journal_rejected'}
  foreach($f in $v.files){if(!$f.relative -or $f.relative.Contains('..') -or [IO.Path]::IsPathRooted($f.relative)){throw 'restore_path'}
   $from=Join-Path $journalRoot ('data\'+$f.relative);$to=Join-Path $sourceRoot $f.relative
   for($cursor=$to;$cursor;$cursor=[IO.Path]::GetDirectoryName($cursor)){NoLink $cursor}
   if((Hash $from) -ne $f.sha256){throw 'backup_hash'}
   if(Test-Path -LiteralPath $to){if((Hash $to) -ne $f.sha256){throw 'conflict_preserved'}}else{[void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($to));[IO.File]::Copy($from,$to,$false)}
   if((Hash $to) -ne $f.sha256){throw 'restore_hash'}
  }
 }
 exit 0
}catch{$rule=($_.FullyQualifiedErrorId -split ',')[0];if($rule -notin @('scope','reparse','preserve_existing_journal','manifest_path','manifest_limit','file_limit','size_limit','not_application','restore_path','backup_hash','conflict_preserved','restore_hash','CommandNotFoundException','CouldNotAutoloadMatchingModule','UnauthorizedAccessException','InvokeMethodOnNull')){$rule='other'};[Console]::Error.WriteLine(('runtime_preservation_failed:{0}:line={1}:code={2}:rule={3}' -f $stage,$_.InvocationInfo.ScriptLineNumber,$_.Exception.HResult,$rule));exit 2}
