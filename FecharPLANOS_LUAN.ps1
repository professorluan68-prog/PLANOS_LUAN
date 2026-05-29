$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$App = Join-Path $Root "planos_luan_app.py"

Set-Location $Root

$processos = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq "python.exe" -and $_.CommandLine -like "*planos_luan_app.py*"
}

if (-not $processos) {
    Write-Host "Nenhuma instancia do PLANOS_LUAN foi encontrada aberta."
    exit 0
}

$ids = @($processos | Select-Object -ExpandProperty ProcessId -Unique)

foreach ($processoId in $ids) {
    try {
        Stop-Process -Id $processoId -Force -ErrorAction Stop
        Write-Host "PLANOS_LUAN encerrado. PID: $processoId"
    }
    catch {
        Write-Host "Nao foi possivel encerrar o PID $processoId."
    }
}
