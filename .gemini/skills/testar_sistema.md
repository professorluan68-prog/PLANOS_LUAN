---
name: testar_sistema
description: Executa os testes automatizados do PLANOS_LUAN e reporta resultados detalhados
---

# Testar Sistema PLANOS_LUAN

## Objetivo
Rodar todos os testes automatizados e reportar o estado de saúde do sistema.

## Passos

### 1. Executar testes completos
```bash
cd D:\PLANOS_LUAN
.venv_PLANOS_LUAN\Scripts\python.exe -m pytest tests/ -v --tb=short
```

### 2. Analisar resultados
- **Todos passaram**: Reportar sucesso com resumo
- **Falhas**: Para cada teste que falhou:
  1. Mostrar o nome do teste
  2. Mostrar o traceback resumido
  3. Identificar o módulo afetado
  4. Sugerir correção

### 3. Se houve mudanças recentes em core/
Rodar com mais detalhes:
```bash
.venv_PLANOS_LUAN\Scripts\python.exe -m pytest tests/ -v --tb=long -x
```
O `-x` para no primeiro erro para investigar a fundo.

### 4. Teste rápido de imports
Verificar se todos os módulos importam corretamente:
```python
import sys
sys.path.insert(0, r"D:\PLANOS_LUAN")
modulos = [
    "core.ia", "core.lote", "core.database", "core.cdp",
    "core.lib.classificador", "core.lib.extrator_pdf",
    "core.lib.metodologia", "core.lib.acompanhamento",
    "core.lib.acessibilidade", "core.validador_plano",
    "docx_generator.preencher",
]
for m in modulos:
    try:
        __import__(m)
        print(f"  OK: {m}")
    except Exception as e:
        print(f"  ERRO: {m} -> {e}")
```

## Regras
- SEMPRE use o ambiente virtual `.venv_PLANOS_LUAN`
- NÃO modifique testes sem pedir ao usuário
- Reporte resultados de forma clara e visual (tabela)
