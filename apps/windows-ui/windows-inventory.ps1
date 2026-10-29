param([ValidateSet('hardware','memory','network','processes','applications','startup','services','drivers','events','disks','peripherals','games','gameprocesses','localstatus','deviceproviders','ping','dns')][string]$Kind,[string]$Target='')
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false)
$ProgressPreference='SilentlyContinue'
function Short($value){if($null -eq $value){return $null};$s=[string]$value;if($s.Length -gt 180){return $s.Substring(0,180)};return $s}
function FailureCode($record,[string]$stage){$rule=($record.FullyQualifiedErrorId -split ',')[0];if($rule -notin @('CimException','OperationTimeout','AccessDenied','UnauthorizedAccessException','CommandNotFoundException','CouldNotAutoloadMatchingModule','PathNotFound','NoMatchingEventsFound','InvalidOperation')){$rule='other'};return @{stage=$stage;code=$record.Exception.HResult;rule=$rule}}
try {
 $items=@();$extra=@{};$resultState='available'
 switch($Kind){
  'gameprocesses' {$processes=@(Get-Process -Name cs2 -ErrorAction SilentlyContinue | Select-Object -First 8);$unverified=0;foreach($process in $processes){try{$image=$process.Path;if($image -notmatch '\\steamapps\\common\\[^\\]+\\game\\bin\\win64\\cs2\.exe$'){$unverified++;continue};$items+=@{game='cs2';pid=$process.Id}}catch{$unverified++}};if($unverified){$resultState='unavailable';$extra=@{unverified_processes=$unverified}}}
  'localstatus' {$listeners=@(Get-NetTCPConnection -State Listen -LocalPort 8776 -ErrorAction SilentlyContinue);$items=@(@{listener_count=$listeners.Count;identity_verified=$false;authentication='not_verified';source='Windows TCP table; presence is not authentication'})}
  'deviceproviders' {$known=@('OpenRGB','SignalRgb');$items=@(foreach($name in $known){$running=@(Get-Process -Name $name -ErrorAction SilentlyContinue);@{name=$name;process_present=($running.Count -gt 0);protocol_verified=$false;configured=$false}})}
  'games' {
   $steam=(Get-ItemProperty -LiteralPath 'HKCU:\Software\Valve\Steam' -ErrorAction SilentlyContinue).SteamPath
   $libraries=@();if($steam -match '^[A-Za-z]:[\\/]'){$libraries+=([IO.Path]::GetFullPath($steam))}
   if($libraries.Count){$vdf=Join-Path $libraries[0] 'steamapps/libraryfolders.vdf';if((Test-Path -LiteralPath $vdf -PathType Leaf) -and (Get-Item -LiteralPath $vdf).Length -lt 131072){$text=[IO.File]::ReadAllText($vdf);foreach($m in [regex]::Matches($text,'"path"\s+"([^"\r\n]+)"')){$p=$m.Groups[1].Value.Replace('\\','\');if($p -match '^[A-Za-z]:[\\/]'){$libraries+=[IO.Path]::GetFullPath($p)}}}}
   foreach($library in ($libraries | Select-Object -Unique -First 16)){
    $folder=Join-Path $library 'steamapps';if(!(Test-Path -LiteralPath $folder -PathType Container)){continue}
    if((Get-Item -LiteralPath $folder).Attributes -band [IO.FileAttributes]::ReparsePoint){continue}
    foreach($file in (Get-ChildItem -LiteralPath $folder -Filter 'appmanifest_*.acf' -File | Select-Object -First 128)){
     if($file.Length -gt 65536 -or $file.Attributes -band [IO.FileAttributes]::ReparsePoint){continue}
     $text=[IO.File]::ReadAllText($file.FullName);$id=[regex]::Match($text,'"appid"\s+"(\d{1,10})"').Groups[1].Value;$name=[regex]::Match($text,'"name"\s+"([^"\r\n]+)"').Groups[1].Value
     if($id -and $name){$items+=@{name=(Short $name);steam_app_id=$id;source='steam_manifest';installation_state='manifest_present_not_game_integrity_verified';last_played=$null;launch_enabled=$false}}
    }
   }
   $items=@($items | Select-Object -First 128)
  }
  'hardware' {
   $failures=@();$cores=@();$descriptorState='available';$coreState='available'
   try{$items=@(Get-CimInstance Win32_Processor -OperationTimeoutSec 3 | ForEach-Object {@{name=(Short $_.Name);logical_cores=$_.NumberOfLogicalProcessors;physical_cores=$_.NumberOfCores;reported_clock_mhz=$_.CurrentClockSpeed;max_clock_mhz=$_.MaxClockSpeed;cpu_temperature_celsius=$null;cpu_power_watts=$null}});if(!$items.Count){$descriptorState='unavailable'}}catch{$descriptorState='unavailable';$failures+=FailureCode $_ 'cpu_descriptor'}
   # A transient WMI performance-counter failure must not erase a valid CPU
   # descriptor/clock. Each source retains its own availability, never fake zero.
   try{$cores=@(Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor -OperationTimeoutSec 3 | Where-Object Name -ne '_Total' | Select-Object -First 128 | ForEach-Object {@{id=(Short $_.Name);utilization_percent=$_.PercentProcessorTime}});if(!$cores.Count){$coreState='unavailable'}}catch{$coreState='unavailable';$failures+=FailureCode $_ 'per_core_counters'}
   $extra=@{cores=$cores;cpu_descriptor_state=$descriptorState;per_core_state=$coreState;partial=($descriptorState -ne 'available' -or $coreState -ne 'available');failures=$failures;clock_semantic='Windows reported clock; not a calibrated frequency measurement'}
   if(!$items.Count -and !$cores.Count){$resultState='unavailable'}
  }
  'memory' {$items=@(Get-CimInstance Win32_PhysicalMemory -OperationTimeoutSec 3 | Select-Object -First 32 | ForEach-Object {@{name=(Short $_.DeviceLocator);capacity_bytes=$_.Capacity;configured_clock_mhz=$_.ConfiguredClockSpeed;reported_speed_mhz=$_.Speed;manufacturer=(Short $_.Manufacturer)}})}
  'network' {$items=@([Net.NetworkInformation.NetworkInterface]::GetAllNetworkInterfaces() | Where-Object OperationalStatus -eq 'Up' | Select-Object -First 32 | ForEach-Object {$s=$_.GetIPStatistics();@{id=(Short $_.Id);name=(Short $_.Name);description=(Short $_.Description);link_bits_per_second=$_.Speed;received_bytes=$s.BytesReceived;sent_bytes=$s.BytesSent;type=[string]$_.NetworkInterfaceType}})}
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
 @{v=1;state=$resultState;source=('windows.readonly.'+$Kind);observed_at=[DateTime]::UtcNow.ToString('o');items=@($items);extra=$extra;simulation=$false} | ConvertTo-Json -Depth 7 -Compress
} catch {
 @{v=1;state='unavailable';source=('windows.readonly.'+$Kind);observed_at=[DateTime]::UtcNow.ToString('o');items=@();error='readonly_provider_unavailable';extra=@{failure=(FailureCode $_ 'inventory')};simulation=$false} | ConvertTo-Json -Depth 4 -Compress
}
