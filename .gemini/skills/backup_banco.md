---
name: backup_banco
description: Faz backup do banco de dados SQLite e dos cadastros de professores do PLANOS_LUAN
---

# Backup do Banco de Dados

## Objetivo
Criar um backup seguro do banco SQLite e dos cadastros antes de operações arriscadas.

## Passos

### 1. Criar backup do banco
```python
import sys, shutil
from pathlib import Path
from datetime import datetime

sys.path.insert(0, r"D:\PLANOS_LUAN")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = Path(r"D:\BACKUPS_PLANOS_LUAN")
backup_dir.mkdir(exist_ok=True)

# Backup do banco SQLite
db_src = Path(r"D:\PLANOS_LUAN\planos_luan.db")
db_dst = backup_dir / f"planos_luan_backup_{timestamp}.db"
shutil.copy2(db_src, db_dst)
print(f"Banco: {db_dst} ({db_dst.stat().st_size // 1024}KB)")

# Backup do JSON de professores (se existir)
json_src = Path(r"D:\PLANOS_LUAN\professores_PLANOS_LUAN_backup.json")
if json_src.exists():
    json_dst = backup_dir / f"professores_backup_{timestamp}.json"
    shutil.copy2(json_src, json_dst)
    print(f"JSON: {json_dst}")
```

### 2. Verificar integridade
```python
import sqlite3
conn = sqlite3.connect(str(db_dst))
cursor = conn.cursor()
cursor.execute("PRAGMA integrity_check")
resultado = cursor.fetchone()[0]
print(f"Integridade: {resultado}")

# Contar registros
for tabela in ["professores", "professor_turmas", "historico_planos"]:
    cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
    count = cursor.fetchone()[0]
    print(f"  {tabela}: {count} registros")
conn.close()
```

### 3. Reportar
Informar ao usuário:
- Caminho do backup
- Tamanho do arquivo
- Resultado da verificação de integridade
- Contagem de registros por tabela
- Quantos backups anteriores existem na pasta

## Regras
- SEMPRE faça backup ANTES de modificar o banco
- Não apague backups sem permissão do usuário
- Verifique integridade do backup após criar
