---
name: analisar_pdf
description: Analisa o conteúdo de um PDF usando o ExtratorPDF do sistema e mostra os dados semânticos extraídos
---

# Analisar PDF

## Objetivo
Extrair e mostrar todos os dados semânticos de um PDF de material digital usando o extrator inteligente do sistema.

## Passos

### 1. Receber o caminho do PDF
Peça ao usuário o caminho do PDF ou identifique pela disciplina/turma/aula:
- Se o usuário disser "AULA 5 de Matemática do 7º ano A", monte o caminho:
  `D:\PDF novos\Matemática\7º ANO A\AULA 5.pdf`

### 2. Extrair texto e dados semânticos
```python
import sys
sys.path.insert(0, r"D:\PLANOS_LUAN")
import pdfplumber
from core.lib.extrator_pdf import ExtratorPDF
from core.lib.classificador import perfil_disciplina, detectar_tipo_aula, detectar_recursos

# Extrair texto
with pdfplumber.open(CAMINHO_PDF) as pdf:
    texto = "\n".join(p.extract_text() or "" for p in pdf.pages)
    num_paginas = len(pdf.pages)

print(f"Páginas: {num_paginas}")
print(f"Caracteres: {len(texto)}")

# Extração semântica (13 campos)
extrator = ExtratorPDF()
dados = extrator.extrair(texto, "")

# Classificação
perfil = perfil_disciplina(DISCIPLINA)
tipo = detectar_tipo_aula(texto, dados.get("conceito_extraido", ""), DISCIPLINA)
recursos = detectar_recursos(texto, dados.get("conceito_extraido", ""))
```

### 3. Mostrar resultados formatados
Apresente ao usuário em formato de tabela:

| Campo | Valor |
|---|---|
| Conceito central | `dados["conceito_extraido"]` |
| Habilidade BNCC | `dados["habilidade"]` |
| Atividade principal | `dados["atividade_extraida"]` |
| Palavras-chave | `dados["palavras_chave"]` |
| Recursos detectados | `dados["recursos_detectados"]` |
| Etapas detectadas | `dados["etapas_detectadas"]` |
| Contexto da aula | `dados["contexto_aula"]` |
| Perfil disciplinar | `perfil` |
| Tipo de aula | `tipo` |
| Recursos classificados | `recursos` |

### 4. Mostrar trecho do texto
Exiba os primeiros 500 caracteres do texto extraído para conferência visual.

## Regras
- SEMPRE use `.venv_PLANOS_LUAN\Scripts\python.exe`
- Se o PDF não existir, liste os disponíveis na pasta da disciplina/turma
- Não trunque dados da habilidade BNCC — mostre completa
