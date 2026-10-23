@echo off
cd /d "%~dp0"
where node >nul 2>&1
if errorlevel 1 (
  echo Node.js nao encontrado. Instale o Node.js LTS em https://nodejs.org/
  pause
  exit /b 1
)
if not exist "node_modules\electron" (
  echo Instalando dependencias do aplicativo...
  call npm install
  if errorlevel 1 (
    echo Erro ao instalar dependencias. Confira sua conexao de internet.
    pause
    exit /b 1
  )
)
call npm start
