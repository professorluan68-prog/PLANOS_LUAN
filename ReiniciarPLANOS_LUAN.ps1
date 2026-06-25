$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$FecharBat = Join-Path $Root "FecharPLANOS_LUAN.bat"
$AbrirPs1 = Join-Path $Root "AbrirPLANOS_LUAN.ps1"

Set-Location $Root

if (Test-Path -LiteralPath $FecharBat) {
    Write-Host "Fechando instancias abertas do PLANOS_LUAN..."
    & $FecharBat
    Start-Sleep -Seconds 2
}

if (-not (Test-Path -LiteralPath $AbrirPs1)) {
    throw "Nao encontrei o script de abertura AbrirPLANOS_LUAN.ps1."
}

Write-Host "Abrindo novamente o PLANOS_LUAN..."
& powershell -NoProfile -ExecutionPolicy Bypass -File $AbrirPs1

