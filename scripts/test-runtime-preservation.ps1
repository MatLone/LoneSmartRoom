$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$base=Join-Path $root ('.cache/runtime-preservation-test/'+[Guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($base)
$saved=$env:LOCALAPPDATA
try {
 $env:LOCALAPPDATA=$base
 $source=Join-Path $base 'fixture-app';[void][IO.Directory]::CreateDirectory($source)
 $known=Join-Path $base 'known.txt';$names=@('Lone Smart Room.exe')+(1..10|ForEach-Object {'packaged-'+$_+'.bin'})
 $names|Set-Content -LiteralPath $known -Encoding UTF8
 'owned fixture only'|Set-Content -LiteralPath (Join-Path $source 'Lone Smart Room.exe')
 $log=Join-Path $source 'debug.log';'preserved fixture log'|Set-Content -LiteralPath $log
 $before=(Get-FileHash -LiteralPath $log -Algorithm SHA256).Hash
 $journal=Join-Path $base 'LoneSmartRoom-RuntimePreservation/fixture'
 $helper=Join-Path $root 'apps/windows-ui/build/preserve-runtime.ps1'
 $ps=Join-Path $env:SystemRoot 'System32/WindowsPowerShell/v1.0/powershell.exe'
 & $ps -NoProfile -NonInteractive -File $helper -Mode prepare -Source $source -Journal $journal -Known $known
 if($LASTEXITCODE -ne 0){throw 'prepare_failed'}
 if(![IO.Path]::GetFullPath($log).StartsWith([IO.Path]::GetFullPath($base)+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'fixture_scope'}
 Remove-Item -LiteralPath $log # Emulate old uninstaller on this owned test file only.
 & $ps -NoProfile -NonInteractive -File $helper -Mode restore -Source $source -Journal $journal
 if($LASTEXITCODE -ne 0 -or (Get-FileHash -LiteralPath $log -Algorithm SHA256).Hash -ne $before){throw 'restore_failed'}
 $acl=Get-Acl -LiteralPath $journal
 if(!$acl.AreAccessRulesProtected -or @($acl.Access).Count -ne 1){throw 'acl_not_private'}
 'conflicting newer fixture'|Set-Content -LiteralPath $log
 & $ps -NoProfile -NonInteractive -File $helper -Mode restore -Source $source -Journal $journal
 if($LASTEXITCODE -eq 0){throw 'conflict_not_rejected'}
 if(!(Test-Path -LiteralPath (Join-Path $journal 'data/debug.log'))){throw 'backup_lost'}
 $invalid=Join-Path $base 'invalid-known.txt';@('../outside.log')+$names|Set-Content -LiteralPath $invalid -Encoding UTF8
 $invalidJournal=Join-Path $base 'LoneSmartRoom-RuntimePreservation/invalid'
 & $ps -NoProfile -NonInteractive -File $helper -Mode prepare -Source $source -Journal $invalidJournal -Known $invalid
 if($LASTEXITCODE -eq 0 -or (Test-Path -LiteralPath $invalidJournal)){throw 'unsafe_manifest_accepted'}
 1..257|ForEach-Object {[IO.File]::WriteAllText((Join-Path $source ('runtime-'+$_+'.tmp')),'owned test fixture')}
 $largeJournal=Join-Path $base 'LoneSmartRoom-RuntimePreservation/excessive'
 & $ps -NoProfile -NonInteractive -File $helper -Mode prepare -Source $source -Journal $largeJournal -Known $known
 if($LASTEXITCODE -eq 0 -or (Test-Path -LiteralPath $largeJournal)){throw 'file_budget_ignored'}
 @{ok=$true;checks=8;realInstallerExecuted=$false;productionFilesTouched=$false;fixtureRetained=$true}|ConvertTo-Json
}finally{$env:LOCALAPPDATA=$saved}
