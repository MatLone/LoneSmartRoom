param([ValidateSet('hardware','memory','network','processes','applications','startup','services','drivers','events','disks','peripherals','ping','dns')][string]$Kind,[string]$Target='')
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false)
$ProgressPreference='SilentlyContinue'
function Short($value){if($null -eq $value){return $null};$s=[string]$value;if($s.Length -gt 180){return $s.Substring(0,180)};return $s}
try {
 $items=@();$extra=@{}
 switch($Kind){
  'hardware' {
   $items=@(Get-CimInstance Win32_Processor -OperationTimeoutSec 3 | ForEach-Object {@{name=(Short $_.Name);logical_cores=$_.NumberOfLogicalProcessors;physical_cores=$_.NumberOfCores;reported_clock_mhz=$_.CurrentClockSpeed;max_clock_mhz=$_.MaxClockSpeed;cpu_temperature_celsius=$null;cpu_power_watts=$null}})
   $cores=@(Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor -OperationTimeoutSec 3 | Where-Object Name -ne '_Total' | Select-Object -First 128 | ForEach-Object {@{id=(Short $_.Name);utilization_percent=$_.PercentProcessorTime}})
   $extra=@{cores=$cores;clock_semantic='Windows reported clock; not a calibrated frequency measurement'}
  }
  'memory' {$items=@(Get-CimInstance Win32_PhysicalMemory -OperationTimeoutSec 3 | Select-Object -First 32 | ForEach-Object {@{name=(Short $_.DeviceLocator);capacity_bytes=$_.Capacity;configured_clock_mhz=$_.ConfiguredClockSpeed;reported_speed_mhz=$_.Speed;manufacturer=(Short $_.Manufacturer)}})}
  'network' {$items=@([Net.NetworkInformation.NetworkInterface]::GetAllNetworkInterfaces() | Where-Object OperationalStatus -eq 'Up' | Select-Object -First 32 | ForEach-Object {$s=$_.GetIPStatistics();@{name=(Short $_.Name);description=(Short $_.Description);link_bits_per_second=$_.Speed;received_bytes=$s.BytesReceived;sent_bytes=$s.BytesSent;type=[string]$_.NetworkInterfaceType}})}
  'processes' {$items=@(Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 100 | ForEach-Object {@{name=(Short $_.ProcessName);pid=$_.Id;resident_bytes=$_.WorkingSet64;cpu_total_seconds=$_.CPU;responding=$_.Responding}})}
  'applications' {
   $keys=@('HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*')
   $items=@(Get-ItemProperty -Path $keys -ErrorAction SilentlyContinue | Where-Object DisplayName | Sort-Object DisplayName -Unique | Select-Object -First 300 | ForEach-Object {@{name=(Short $_.DisplayName);version=(Short $_.DisplayVersion);publisher=(Short $_.Publisher);update_state='not_verified'}})
  }
  'startup' {$items=@(Get-CimInstance Win32_StartupCommand -OperationTimeoutSec 3 | Select-Object -First 100 | ForEach-Object {@{name=(Short $_.Name);registered=$true;enabled=$null;source='Win32_StartupCommand; command and user intentionally omitted'}})}
  'services' {$items=@(Get-CimInstance Win32_Service -OperationTimeoutSec 3 | Select-Object -First 300 | ForEach-Object {@{name=(Short $_.Name);display_name=(Short $_.DisplayName);state=$_.State;start_mode=$_.StartMode;exit_code=$_.ExitCode}})}
  'drivers' {$items=@(Get-CimInstance Win32_PnPSignedDriver -OperationTimeoutSec 3 | Where-Object DeviceName | Select-Object -First 200 | ForEach-Object {@{name=(Short $_.DeviceName);version=(Short $_.DriverVersion);provider=(Short $_.DriverProviderName);signed=$_.IsSigned}})}
  'events' {$items=@(Get-WinEvent -FilterHashtable @{LogName='Application';Id=1000,1001;StartTime=(Get-Date).AddDays(-7)} -MaxEvents 30 -ErrorAction SilentlyContinue | ForEach-Object {@{id=$_.Id;provider=(Short $_.ProviderName);at=$_.TimeCreated.ToUniversalTime().ToString('o');level=$_.LevelDisplayName;detail='Mensagem completa omitida para preservar caminhos e dados privados'}})}
  'disks' {$items=@(Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' -OperationTimeoutSec 3 | Select-Object -First 32 | ForEach-Object {@{name=$_.DeviceID;capacity_bytes=$_.Size;free_bytes=$_.FreeSpace;file_system=$_.FileSystem;health='not_verified'}})}
  'peripherals' {$items=@(Get-CimInstance Win32_PnPEntity -OperationTimeoutSec 3 | Where-Object {$_.PNPClass -in @('Mouse','Keyboard','AudioEndpoint','MEDIA','Monitor')} | Select-Object -First 100 | ForEach-Object {@{name=(Short $_.Name);class=$_.PNPClass;status=$_.Status;dpi=$null;battery_percent=$null;firmware=$null}})}
  'ping' {
   if($Target.Length -gt 253 -or $Target -notmatch '^([a-zA-Z0-9][a-zA-Z0-9.\-]*|[0-9a-fA-F:]+)$' -or $Target.StartsWith('-')){throw 'invalid target'}
   $p=New-Object Net.NetworkInformation.Ping
   try {for($i=0;$i -lt 4;$i++){try{$r=$p.Send($Target,1000);$items+=@{status=[string]$r.Status;rtt_ms=if($r.Status -eq 'Success'){$r.RoundtripTime}else{$null}}}catch{$items+=@{status='Unavailable';rtt_ms=$null}}}}finally{$p.Dispose()}
  }
  'dns' {
   if($Target.Length -gt 253 -or $Target -notmatch '^[a-zA-Z0-9][a-zA-Z0-9.\-]*$'){throw 'invalid target'}
   $items=@([Net.Dns]::GetHostAddresses($Target) | Select-Object -First 16 | ForEach-Object {@{address=$_.IPAddressToString;family=[string]$_.AddressFamily}})
  }
 }
 @{v=1;state='available';source=('windows.readonly.'+$Kind);observed_at=[DateTime]::UtcNow.ToString('o');items=@($items);extra=$extra;simulation=$false} | ConvertTo-Json -Depth 7 -Compress
} catch {
 @{v=1;state='unavailable';source=('windows.readonly.'+$Kind);observed_at=[DateTime]::UtcNow.ToString('o');items=@();error='readonly_provider_unavailable';simulation=$false} | ConvertTo-Json -Compress
}
