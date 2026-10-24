param(
 [Parameter(Mandatory=$true)][string]$BackupRoot,
 [Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedManifestSha256
)
# Independent, read-only verifier. Does not restore, decrypt or launch software.
$ErrorActionPreference='Stop'
$backup=[IO.Path]::GetFullPath($BackupRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
$prefix=$backup+[IO.Path]::DirectorySeparatorChar
$manifestPath=Join-Path $backup 'manifest.json'
if((Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedManifestSha256.ToLowerInvariant()){throw 'Manifest SHA-256 mismatch'}
$manifest=Get-Content -LiteralPath $manifestPath -Raw|ConvertFrom-Json
if($manifest.format -ne 'LSR-WINDOWS-PROFILE-BACKUP-1' -or -not $manifest.completeAndStable -or $manifest.issues.Count -ne 0){throw 'Incomplete/unsupported backup'}
$sid=[Security.Principal.WindowsIdentity]::GetCurrent().User
if($sid.Value -ne $manifest.ownerSid){throw 'Use the original Windows account'}
function Child([string]$relative){
 $p=[IO.Path]::GetFullPath((Join-Path $backup $relative))
 if(-not $p.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)){throw 'Manifest escapes backup root'}
 return $p
}
$files=0;$bytes=0L
foreach($item in $manifest.files){
 $p=Child $item.destinationRelative
 if((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.sha256){throw 'Payload SHA-256 mismatch'}
 if((Get-Item -LiteralPath $p -Force).Length -ne $item.bytes){throw 'Payload size mismatch'}
 $files++;$bytes+=$item.bytes
}
if($files -ne $manifest.expectedFiles -or $bytes -ne $manifest.bytes){throw 'Payload totals differ'}
foreach($dir in $manifest.directories){if(-not [IO.Directory]::Exists((Child $dir))){throw 'Missing directory'}}
$actual=@(Get-ChildItem -LiteralPath (Join-Path $backup 'data/profile') -File -Recurse -Force)
if($actual.Count -ne $files){throw 'Unexpected payload file count'}
foreach($item in @((Get-Item -LiteralPath $backup -Force))+@(Get-ChildItem -LiteralPath $backup -Recurse -Force)){
 if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Backup reparse point rejected'}
 $acl=Get-Acl -LiteralPath $item.FullName
 if($acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -ne $sid.Value){throw 'Owner differs'}
 $rules=@($acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier]))
 if(-not $rules.Count){throw 'No private access rule'}
 foreach($rule in $rules){if($rule.IdentityReference.Value -ne $sid.Value -or $rule.AccessControlType -ne [Security.AccessControl.AccessControlType]::Allow){throw 'Unexpected backup identity'}}
}
if(-not (Get-Acl -LiteralPath $backup).AreAccessRulesProtected){throw 'Root inherits external access'}
[pscustomobject]@{ok=$true;files=$files;bytes=$bytes;directories=$manifest.directories.Count;hashesAndSizesMatch=$true;userOnlyAcl=$true;restorationPerformed=$false;credentialsDecrypted=$false}
