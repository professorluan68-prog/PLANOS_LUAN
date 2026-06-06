$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$FecharBat = Join-Path $Root "FecharPLANOS_LUAN.bat"
$AbrirBatPreferido = Join-Path $Root "ABRIR_PLANOS_LUAN_VENV.bat"
$AbrirBatLegado = Join-Path $Root "AbrirPLANOS_LUAN.bat"

Set-Location $Root

if (Test-Path -LiteralPath $FecharBat) {
    Write-Host "Fechando instancias abertas do PLANOS_LUAN..."
    & $FecharBat
    Start-Sleep -Seconds 2
}

if (Test-Path -LiteralPath $AbrirBatPreferido) {
    $AbrirBat = $AbrirBatPreferido
}
elseif (Test-Path -LiteralPath $AbrirBatLegado) {
    $AbrirBat = $AbrirBatLegado
}
else {
    throw "Nao encontrei um arquivo de abertura do PLANOS_LUAN."
}

Write-Host "Abrindo novamente o PLANOS_LUAN..."
& $AbrirBat
