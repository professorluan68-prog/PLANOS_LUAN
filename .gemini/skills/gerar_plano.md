---
name: gerar_plano
description: Gera um plano de aula a partir de PDFs de uma disciplina e turma específicas usando o motor do PLANOS_LUAN
---

# Gerar Plano de Aula

## Objetivo
Gerar um plano de aula completo em Word (.docx) a partir dos PDFs de material digital.

## Passos

### 1. Coletar informações
Pergunte ao usuário (se não informou):
- **Disciplina** (ex.: Matemática, Língua Portuguesa, História)
- **Turma** (ex.: 7º ano A, 1º ANO B)
- **Mês** e **Bimestre**
- **Professor** (opcional — buscar no banco se não informado)

### 2. Localizar PDFs
Procure os PDFs em `D:\PDF novos\{disciplina}\{turma}\`. Liste os arquivos encontrados:
```python
from pathlib import Path
pasta = Path(r"D:\PDF novos") / disciplina / turma
pdfs = sorted(pasta.glob("*.pdf"))
print(f"Encontrados: {len(pdfs)} PDFs")
for p in pdfs:
    print(f"  - {p.name} ({p.stat().st_size // 1024}KB)")
```

### 3. Processar PDFs
Use o ambiente virtual e o motor principal:
```python
import sys
sys.path.insert(0, r"D:\PLANOS_LUAN")
from core.lote import processar_varios_pdfs

aulas = processar_varios_pdfs(
    caminhos_pdf=[str(p) for p in pdfs],
    disciplina=disciplina,
    turma=turma,
    provedor="gemini",  # ou "openai"
    modelo="",  # usa padrão do config
)
```

### 4. Revisar resultados
Mostre ao usuário cada aula extraída:
- Tema
- Aprendizagem essencial / BNCC
- Metodologia (etapas)
- Acompanhamento
- Acessibilidade

### 5. Gerar Word
Se aprovado, gere o .docx:
```python
from docx_generator.preencher import preencher_plano
# usar template adequado e dados das aulas
```

## Regras
- SEMPRE use `.venv_PLANOS_LUAN\Scripts\python.exe`
- Valide que os PDFs existem antes de processar
- Mostre preview das aulas ANTES de gerar o Word
- Se faltar PDF, avise o usuário
