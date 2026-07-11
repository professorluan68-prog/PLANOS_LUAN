@echo off
setlocal

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

cd /d "%ROOT%"

set "PYTHON_CMD="
set "VENV_DIR=.venv"

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

if exist "%VENV_DIR%\Scripts\python.exe" (
    "%VENV_DIR%\Scripts\python.exe" --version >nul 2>nul
    if errorlevel 1 (
        echo Ambiente virtual quebrado. Reparando %VENV_DIR%...
        %PYTHON_CMD% -m venv %VENV_DIR%
    )
)

if not exist "%VENV_DIR%\Scripts\python.exe" (
    if exist ".venv_PLANOS_LUAN\Scripts\python.exe" (
        set "VENV_DIR=.venv_PLANOS_LUAN"
    ) else (
        %PYTHON_CMD% -m venv %VENV_DIR%
    )
)

"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
"%VENV_DIR%\Scripts\python.exe" -m pip install -r requirements.txt

echo.
echo PLANOS_LUAN preparado com sucesso em %VENV_DIR%.
pause
