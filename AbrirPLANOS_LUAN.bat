@echo off
setlocal

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\AbrirPLANOS_LUAN.ps1"
if errorlevel 1 (
    echo.
    echo Nao foi possivel abrir o PLANOS_LUAN.
    echo Veja planos_luan.err.log ou execute InstalarPLANOS_LUAN.bat.
    echo.
    pause
    exit /b 1
)

exit /b 0
