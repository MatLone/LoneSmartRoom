param([ValidateSet('all','cores-fail','descriptor-fail','both-fail')][string]$Case='all')
# EXPLICIT MOCKS: this wrapper never calls Windows CIM or operational readers.
$ErrorActionPreference='Stop';$global:LsrFixtureCase=$Case
function global:Get-CimInstance {
 param([string]$ClassName,[int]$OperationTimeoutSec)
 if($ClassName -eq 'Win32_Processor'){
  if($global:LsrFixtureCase -in @('descriptor-fail','both-fail')){throw 'PRIVATE_PATH_SHOULD_NOT_LEAK'}
  return [pscustomobject]@{Name='FIXTURE CPU';NumberOfLogicalProcessors=2;NumberOfCores=1;CurrentClockSpeed=2500;MaxClockSpeed=4000}
 }
 if($ClassName -eq 'Win32_PerfFormattedData_PerfOS_Processor'){
  if($global:LsrFixtureCase -in @('cores-fail','both-fail')){throw 'PRIVATE_PATH_SHOULD_NOT_LEAK'}
  return @([pscustomobject]@{Name='0';PercentProcessorTime=0},[pscustomobject]@{Name='1';PercentProcessorTime=12})
 }
 throw 'Unexpected mock class'
}
& (Join-Path $PSScriptRoot '../../apps/windows-ui/windows-inventory.ps1') -Kind hardware
