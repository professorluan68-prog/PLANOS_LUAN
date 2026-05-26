@echo off
setlocal

set "EDGE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not exist "%EDGE%" set "EDGE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"

if not exist "%EDGE%" (
  echo Nao encontrei o Microsoft Edge neste computador.
  pause
  exit /b 1
)

set "PERFIL=%USERPROFILE%\Edge_CentroMidias_Downloads"

echo Abrindo o portal em um Edge normal, preparado para o baixador...
echo.
echo Depois de fazer login e chegar na pagina das aulas, execute:
echo BAIXAR_PDFS_CENTRO_MIDIAS.bat
echo.

start "" "%EDGE%" --remote-debugging-port=9222 --user-data-dir="%PERFIL%" "https://repositorio.educacao.sp.gov.br/midia"

pause

