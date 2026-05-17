$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root ".venv_PLANOS_LUAN\Scripts\python.exe"
$App = Join-Path $Root "planos_luan_app.py"
$InstallBat = Join-Path $Root "InstalarPLANOS_LUAN.bat"
$OutLog = Join-Path $Root "planos_luan.out.log"
$ErrLog = Join-Path $Root "planos_luan.err.log"

Set-Location $Root

function Test-Python {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return $false
    }

    & $Path --version *> $null
    return ($LASTEXITCODE -eq 0)
}

function Test-Module {
    param(
        [string]$Path,
        [string]$Module
    )

    & $Path -c "import $Module" *> $null
    return ($LASTEXITCODE -eq 0)
}

function Ensure-Environment {
    if (-not (Test-Python $Python)) {
        Write-Host "Preparando ambiente do PLANOS_LUAN..."
        & $InstallBat
    }

    if (-not (Test-Python $Python)) {
        throw "Python do PLANOS_LUAN nao iniciou. Execute InstalarPLANOS_LUAN.bat ou instale Python 3.11/3.12."
    }

    if (-not (Test-Module $Python "streamlit")) {
        Write-Host "Dependencias incompletas. Instalando pacotes..."
        & $InstallBat
    }

    if (-not (Test-Module $Python "streamlit")) {
        throw "Streamlit nao esta instalado no ambiente do PLANOS_LUAN."
    }
}

function Test-PortOpen {
    param([int]$Port)

    $client = [Net.Sockets.TcpClient]::new()
    try {
        $iar = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        if (-not $iar.AsyncWaitHandle.WaitOne(300)) {
            return $false
        }
        $client.EndConnect($iar)
        return $true
    }
    catch {
        return $false
    }
    finally {
        $client.Close()
    }
}

function Get-PlanosLuanPort {
    $preferred = 8501

    if (-not (Test-PortOpen $preferred)) {
        return $preferred
    }

    for ($port = 8502; $port -le 8515; $port++) {
        if (-not (Test-PortOpen $port)) {
            return $port
        }
    }

    throw "Nao encontrei uma porta livre entre 8501 e 8515."
}

Ensure-Environment

$Port = Get-PlanosLuanPort
$Url = "http://127.0.0.1:$Port"

Write-Host "Abrindo PLANOS_LUAN em $Url ..."

$args = @(
    "-m", "streamlit", "run", $App,
    "--server.address", "127.0.0.1",
    "--server.port", "$Port",
    "--server.headless", "true",
    "--browser.gatherUsageStats", "false"
)

Start-Process `
    -FilePath $Python `
    -ArgumentList $args `
    -WorkingDirectory $Root `
    -WindowStyle Hidden `
    -RedirectStandardOutput $OutLog `
    -RedirectStandardError $ErrLog | Out-Null

for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 500
    if (Test-PortOpen $Port) {
        Start-Process $Url
        exit 0
    }
}

throw "O PLANOS_LUAN foi iniciado, mas nao respondeu em $Url. Confira planos_luan.err.log."
