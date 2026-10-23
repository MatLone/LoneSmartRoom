@echo off
cd /d "%~dp0"
where node >nul 2>&1
if errorlevel 1 (
  echo Instale o Node.js LTS: https://nodejs.org/
  pause
  exit /b 1
)
if not exist "node_modules\electron" call npm install
call npm run dist:win
if errorlevel 1 (
  echo Falha ao empacotar. Verifique os detalhes acima.
) else (
  echo Instalador e versao portatil salvos na pasta dist.
)
pause
