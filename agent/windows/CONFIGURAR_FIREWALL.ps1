# Execute como Administrador; restrito à sua LAN privada, nunca WAN.
$ErrorActionPreference = 'Stop'
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
  Write-Host 'Abra o PowerShell como Administrador antes de executar este arquivo.'
  exit 1
}
$ruleName = 'Lone Smart Room Agent - LAN somente'
Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue | Remove-NetFirewallRule -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8765 -LocalAddress '172.31.250.8' -RemoteAddress '172.31.250.0/24' -Profile Private | Out-Null
Write-Host 'Liberada somente a porta TCP 8765 na rede 172.31.250.0/24 e no perfil Privado.'
Write-Host 'Nunca configure encaminhamento desta porta no roteador.'
