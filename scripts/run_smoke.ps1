param(
    [string]$PythonExe = ".\.venv\Scripts\python.exe"
)

if (-not (Test-Path $PythonExe)) {
    throw "Python da virtualenv nao encontrado em: $PythonExe"
}

& $PythonExe -c "from core.cache_manager import CacheManager; from core.ia_client import IAClient; print('Smoke: instantiate components'); CacheManager('.cache_test', 'v1'); print('Cache OK'); IAClient('http://example.invalid', 'key', max_retries=0); print('IAClient OK')"

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Smoke OK"
