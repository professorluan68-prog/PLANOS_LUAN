param(
    [string]$DbPath = "planos_luan.db",
    [string]$PythonExe = ".\.venv\Scripts\python.exe"
)

if (-not (Test-Path $DbPath)) {
    throw "Banco nao encontrado: $DbPath"
}

if (-not (Test-Path $PythonExe)) {
    throw "Python da virtualenv nao encontrado em: $PythonExe"
}

& $PythonExe -c "import sqlite3, sys; db = sys.argv[1]; conn = sqlite3.connect(db); print('journal_mode:', conn.execute('PRAGMA journal_mode;').fetchone()); print('synchronous:', conn.execute('PRAGMA synchronous;').fetchone()); conn.close()" $DbPath

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
