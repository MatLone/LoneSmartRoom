@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Lone Smart Room 1.5 - Instalacao do agente Windows
where python >nul 2>&1
if errorlevel 1 (
  echo ERRO: Python 3 nao foi encontrado. Instale Python 3.11+ e marque Add to PATH.
  pause
  exit /b 1
)
python agent.py --install
if errorlevel 1 (
  echo Nao foi possivel configurar o agente.
  pause
  exit /b 1
)
echo.
echo IMPORTANTE: guarde a chave exibida acima apenas no seu celular.
echo Depois execute CONFIGURAR_FIREWALL.ps1 como Administrador e INICIAR_AGENTE.bat.
pause
