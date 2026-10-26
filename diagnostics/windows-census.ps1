# Fixed read-only inventory. Private command lines stay in memory, never in reports.
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$processes=@(Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe' OR Name='Lone Smart Room.exe' OR Name='electron.exe' OR Name='bridge.exe'" -OperationTimeoutSec 3 | Select-Object ProcessId,ParentProcessId,ExecutablePath,CommandLine,SessionId,@{n='created';e={$_.CreationDate.ToUniversalTime().ToString('o')}})
if($processes.Count -gt 256){throw 'process_limit'}
$listeners=@(Get-CimInstance -Namespace root/StandardCimv2 -ClassName MSFT_NetTCPConnection -Filter 'LocalPort=8776 AND State=2' -OperationTimeoutSec 3 | Select-Object OwningProcess,LocalPort,LocalAddress)
$run=$null
$key=[Microsoft.Win32.Registry]::CurrentUser.OpenSubKey('Software\Microsoft\Windows\CurrentVersion\Run',$false)
if($null -ne $key){try{$run=$key.GetValue('LoneSmartRoomSecureAgent',$null,[Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)}finally{$key.Close()}}
@{v=1;processes=$processes;listeners=$listeners;run=$run}|ConvertTo-Json -Depth 5 -Compress
