$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$run=[Guid]::NewGuid().ToString('N')
$saved=$env:NODE_OPTIONS;$savedRun=$env:LONE_WORKBENCH_RUN_ID
try {
 $env:LONE_WORKBENCH_RUN_ID=$run
 $bootstrap=(Join-Path $root 'tests/electron-deadline-bootstrap.cjs').Replace('\','/')
 $env:NODE_OPTIONS='--require="'+$bootstrap+'"'
 $p=Start-Process -FilePath (Join-Path $root 'apps/windows-ui/node_modules/electron/dist/electron.exe') -ArgumentList @(('"'+(Join-Path $root 'apps/windows-ui')+'"'),'--lone-development-review','--lone-workbench-development') -WorkingDirectory $root -WindowStyle Hidden -PassThru -Wait
 $receipt=Join-Path $root ('.cache/windows-workbench-review/'+$run+'/deadline-result.json')
 if($p.ExitCode -ne 0 -or !(Test-Path -LiteralPath $receipt)){throw 'Deadline test did not complete; no forced stop attempted'}
 $report=Get-Content -LiteralPath $receipt -Raw|ConvertFrom-Json
 if(!$report.ok){throw 'Deadline did not pass'}
 @{ok=$report.ok;runId=$run;elapsedSeconds=$report.elapsed_seconds;exitRequestedMs=$report.requested_elapsed_ms;physicalCollectors=$false}|ConvertTo-Json
}finally{$env:NODE_OPTIONS=$saved;$env:LONE_WORKBENCH_RUN_ID=$savedRun}
