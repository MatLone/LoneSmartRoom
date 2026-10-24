param(
    [Parameter(Mandatory=$true)][string]$BackupRoot,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedManifestSha256
)
# Read-only verification. No restore, decryption, ACL writes or process launches.
$ErrorActionPreference='Stop'
$backupPath=[IO.Path]::GetFullPath($BackupRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
$boundary=$backupPath+[IO.Path]::DirectorySeparatorChar
$manifestPath=Join-Path $backupPath 'manifest.json'
if((Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedManifestSha256.ToLowerInvariant()){throw 'Manifest SHA-256 differs from the trusted receipt'}
$manifest=Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if($manifest.format -ne 'LSR-WINDOWS-DATA-BACKUP-1' -or -not $manifest.completeAndStable -or $manifest.issues.Count -ne 0){throw 'Backup manifest is unsupported, incomplete or unstable'}
$userSid=[Security.Principal.WindowsIdentity]::GetCurrent().User
if($userSid.Value -ne $manifest.ownerSid){throw 'Use the original authorized Windows account'}
function Resolve-BackupChild([string]$relative){
    $target=[IO.Path]::GetFullPath((Join-Path $backupPath $relative))
    if(-not $target.StartsWith($boundary,[StringComparison]::OrdinalIgnoreCase)){throw 'Manifest child escapes the backup root'}
    return $target
}
$fileCount=0;$byteCount=0L;$directoryCount=0
foreach($record in $manifest.files){
    $target=Resolve-BackupChild ([string]$record.destinationRelative)
    if((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $record.sha256){throw 'Payload SHA-256 mismatch'}
    if((Get-Item -LiteralPath $target -Force).Length -ne $record.bytes){throw 'Payload size mismatch'}
    $fileCount++;$byteCount+=$record.bytes
}
if($fileCount -ne $manifest.expectedFiles -or $byteCount -ne $manifest.bytes){throw 'Payload totals mismatch'}
foreach($lsrProfile in $manifest.profiles){
    if(-not [IO.Directory]::Exists((Resolve-BackupChild ('data/repository/'+$lsrProfile.relative)))){throw 'Missing profile/session directory'}
    $directoryCount++
}
foreach($directory in $manifest.directories){
    if(-not [IO.Directory]::Exists((Resolve-BackupChild ([string]$directory.destinationRelative)))){throw 'Missing nested or empty directory'}
    $directoryCount++
}
foreach($entry in @((Get-Item -LiteralPath $backupPath -Force))+@(Get-ChildItem -LiteralPath $backupPath -Recurse -Force)){
    if($entry.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Unexpected reparse point'}
    $acl=Get-Acl -LiteralPath $entry.FullName
    $rules=@($acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier]))
    if($rules.Count -eq 0 -or $acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -ne $userSid.Value){throw 'Backup ownership/access rules differ'}
    foreach($rule in $rules){if($rule.IdentityReference.Value -ne $userSid.Value -or $rule.AccessControlType -ne [Security.AccessControl.AccessControlType]::Allow){throw 'Unexpected access identity/type'}}
}
if(-not (Get-Acl -LiteralPath $backupPath).AreAccessRulesProtected){throw 'Root inherits permissions from outside the backup'}
[pscustomobject]@{ok=$true;files=$fileCount;bytes=$byteCount;directories=$directoryCount;sha256Match=$true;userOnlyAcl=$true;restorationPerformed=$false;credentialsDecrypted=$false}
