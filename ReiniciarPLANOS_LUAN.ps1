$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$FecharBat = Join-Path $Root "FecharPLANOS_LUAN.bat"
$AbrirBat = Join-Path $Root "AbrirPLANOS_LUAN.bat"

Set-Location $Root

if (Test-Path -LiteralPath $FecharBat) {
    Write-Host "Fechando instancias abertas do PLANOS_LUAN..."
    & $FecharBat
    Start-Sleep -Seconds 2
}

if (-not (Test-Path -LiteralPath $AbrirBat)) {
    throw "Nao encontrei o arquivo AbrirPLANOS_LUAN.bat."
}

Write-Host "Abrindo novamente o PLANOS_LUAN..."
& $AbrirBat
