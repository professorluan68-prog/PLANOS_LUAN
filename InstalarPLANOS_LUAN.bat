@echo off
setlocal

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

cd /d "%ROOT%"

set "PYTHON_CMD="

py -3.11 --version >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=py -3.11"
)

if not defined PYTHON_CMD (
    py -3.12 --version >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD=py -3.12"
    )
)

if not defined PYTHON_CMD (
    python --version >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD=python"
    )
)

if not defined PYTHON_CMD (
    echo Python nao encontrado. Instale o Python 3.11 ou 3.12 e marque "Add python.exe to PATH".
    pause
    exit /b 1
)

if exist ".venv_PLANOS_LUAN\Scripts\python.exe" (
    ".venv_PLANOS_LUAN\Scripts\python.exe" --version >nul 2>nul
    if errorlevel 1 (
        echo Ambiente virtual quebrado. Reparando .venv_PLANOS_LUAN...
        %PYTHON_CMD% -m venv .venv_PLANOS_LUAN
    )
)

if not exist ".venv_PLANOS_LUAN\Scripts\python.exe" (
    %PYTHON_CMD% -m venv .venv_PLANOS_LUAN
)

".venv_PLANOS_LUAN\Scripts\python.exe" -m pip install --upgrade pip
".venv_PLANOS_LUAN\Scripts\python.exe" -m pip install -r requirements.txt

echo.
echo PLANOS_LUAN preparado com sucesso.
pause
