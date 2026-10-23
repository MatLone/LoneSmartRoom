@echo off
chcp 65001 >nul
cd /d "%~dp0"
python agent.py --serve
if errorlevel 1 (
  echo Falha ao iniciar. Confira IP Ethernet e porta. IP esperado: 172.31.250.8
  pause
)
