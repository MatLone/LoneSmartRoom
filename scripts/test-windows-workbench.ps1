param([ValidateSet('1','1.25','1.5')][string]$Scale='1')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$run=[Guid]::NewGuid().ToString('N')
$oldOptions=$env:NODE_OPTIONS;$oldRun=$env:LONE_WORKBENCH_RUN_ID
try {
 $env:LONE_WORKBENCH_RUN_ID=$run
 $bootstrap=(Join-Path $root 'tests/electron-workbench-bootstrap.cjs').Replace('\','/')
 $env:NODE_OPTIONS='--require="'+$bootstrap+'"'
 $exe=Join-Path $root 'apps/windows-ui/node_modules/electron/dist/electron.exe'
 $entry=Join-Path $root 'apps/windows-ui'
 # GUI processes require an explicit wait; a stale LASTEXITCODE is not a result.
 $process=Start-Process -FilePath $exe -ArgumentList @(('"'+$entry+'"'),'--lone-development-review','--lone-workbench-development',('--force-device-scale-factor='+$Scale)) -WorkingDirectory $root -WindowStyle Hidden -PassThru -Wait
 $receipt=Join-Path $root ('.cache/windows-workbench-review/'+$run+'/result.json')
 if($process.ExitCode -ne 0 -or !(Test-Path -LiteralPath $receipt)){throw 'Electron development review did not complete'}
 $result=Get-Content -LiteralPath $receipt -Raw | ConvertFrom-Json
 if(!$result.ok){throw 'Electron review reported failure'}
 $result | ConvertTo-Json -Depth 8
} finally {$env:NODE_OPTIONS=$oldOptions;$env:LONE_WORKBENCH_RUN_ID=$oldRun}
