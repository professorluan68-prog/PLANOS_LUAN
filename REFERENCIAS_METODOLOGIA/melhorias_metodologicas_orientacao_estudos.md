# MELHORIAS DO SISTEMA PLANOS_LUAN — ORIENTAÇÃO DE ESTUDOS
## Documento de Instruções para Implantação — Codex

**Gerado em:** 2026-06-13  
**Base de análise:** PDFs de Orientação de Estudos (EF e EM) em `D:\PDF novos\ORIENTACAO_DE_ESTUDOS`.  
**Objetivo:** Orientar a correção de desvios pedagógicos em Orientação de Estudos, focando no ensino de técnicas de estudo e organização do raciocínio.

---

## ÍNDICE

1. [Diagnóstico Geral](#1-diagnóstico-geral)
2. [Problemas Críticos — Alta Prioridade](#2-problemas-críticos--alta-prioridade)
3. [Problemas Médios — Média Prioridade](#3-problemas-médios--média-prioridade)
4. [Problemas Menores — Baixa Prioridade](#4-problemas-menores--baixa-prioridade)
5. [Melhorias por Arquivo/Módulo](#5-melhorias-por-arquivomódulo)
6. [Regras Fixas que Nunca Devem Ser Violadas](#6-regras-fixas-que-nunca-devem-ser-violadas)
7. [Exemplos de Saída Correta vs. Incorreta](#7-exemplos-de-saída-correta-vs-incorreta)
8. [Checklist de Validação Pós-Geração](#8-checklist-de-validação-pós-geração)
9. [Apêndice — Ordem de Implantação Recomendada](#9-apêndice--ordem-de-implantação-recomendada)

---

## 1. DIAGNÓSTICO GERAL

O perfil de Orientação de Estudos costuma ser deturpado pelo sistema, que o trata apenas como se fosse uma aula complementar de Língua Portuguesa ou Matemática. O objetivo de Orientação de Estudos é **ensinar os estudantes a estudar**, focando em metacognição (como gerenciar o tempo, fazer esquemas, ler enunciados críticos, organizar o caderno e justificar escolhas de estudo).

---

## 2. PROBLEMAS CRÍTICOS — ALTA PRIORIDADE

### 2.1 Resolução de Exercícios Sem Enfoque nas Estratégias de Aprendizagem
**Arquivo afetado:** `core/lib/metodologia.py` (ou `core/orientacao_estudos_metodologia.py`)

**Descrição do problema:**  
O plano foca apenas em "corrigir as respostas dos exercícios" do PDF, sem ensinar técnicas para encontrar essas respostas (ex: grifar palavras-chave no enunciado, fazer anotações em tópicos).

**Como corrigir:**  
```python
# DEPOIS:
def gerar_etapa_leitura_comandos_oe():
    return (
        "Orientar a leitura guiada do enunciado. Instruir os estudantes a circular os verbos de comando "
        "(ex: identifique, justifique, compare) e a sublinhar as condições estabelecidas no problema antes de iniciar a resolução."
    )
```

### 2.2 Ausência de Metacognição (Reflexão sobre as Estratégias de Estudo)
**Descrição do problema:**  
O fechamento das aulas em Orientação de Estudos é genérico ("socializar as respostas na lousa"), sem discutir quais métodos de estudo foram mais eficazes para os alunos (ex: mapa mental, resumo, tópicos).

**Como corrigir:**  
```python
# DEPOIS:
def gerar_etapa_fechamento_metacognitivo():
    return (
        "Encerrar a aula com uma reflexão metacognitiva. Questionar os estudantes sobre quais estratégias de estudo "
        "facilitaram a resolução da tarefa (ex: grifar, esquematizar, revisar as etapas) e como podem aplicar "
        "essas técnicas nas próximas disciplinas."
    )
```

---

## 3. PROBLEMAS MÉDIOS — MÉDIA PRIORIDADE

### 3.1 Omissão da Organização do Caderno
**Descrição:** Os planos ignoram o uso físico e sistemático do caderno escolar.  
**Correção:** Inserir a orientação explícita para os alunos registrarem o cabeçalho, as palavras-chave do tema e estruturarem as anotações em tópicos numerados ou esquemas no caderno.

---

## 4. PROBLEMAS MENORES — BAIXA PRIORIDADE

### 4.1 Missão e Trilhas sem Enfoque
**Correção:** Preservar a nomenclatura lúdica do material (Missão, Jornada, Trilha) no plano, orientando o professor a usar esses termos em sala.

---

## 5. MELHORIAS POR ARQUIVO/MÓDULO

| Arquivo | Alteração | Prioridade |
|---------|-----------|------------|
| `core/lib/classificador.py` | Detectar tags de técnicas de estudo (mapa mental, resumo, grifos) | 🔴 ALTA |
| `core/lib/metodologia.py` | Forçar etapas metacognitivas e organização ativa de caderno | 🔴 ALTA |

---

## 6. REGRAS FIXAS QUE NUNCA DEVEM SER VIOLADAS

1. **Enfoque processual**: Focar em *como resolver* a tarefa, não apenas na resposta certa/errada.
2. **Registro estruturado**: Toda aula deve ter uma etapa dedicada a ensinar a organizar os registros no caderno.
3. **Fechamento metacognitivo**: Sempre debater a eficácia das estratégias de estudo usadas.

---

## 7. EXEMPLOS DE SAÍDA CORRETA VS. INCORRETA

### 7.1 Aula de Preparação de Provas
* **❌ INCORRETO:** *"Pedir que resolvam o simulado e corrigir as questões erradas na lousa."*
* **✅ CORRETO:** *"Foco no conteúdo: Orientar a leitura dirigida do simulado. Demonstrar na lousa como identificar o comando da questão, eliminar alternativas notoriamente incorretas e justificar a resposta escolhida por escrito no caderno."*

---

## 8. CHECKLIST DE VALIDAÇÃO PÓS-GERAÇÃO

```python
def validar_plano_oe(plano: dict) -> list[str]:
    erros = []
    for aula in plano.get('aulas', []):
        if "estratégia" not in aula['metodologia'].lower() and "caderno" not in aula['metodologia'].lower():
            erros.append(f"Aula {aula['numero']}: Plano focado apenas em conteúdo sem focar em técnicas de estudo.")
    return erros
```

---

## 9. APÊNDICE — ORDEM DE IMPLANTAÇÃO RECOMENDADA
1. Implementar rotina de grifo e análise de enunciado no início de Orientação de Estudos.
2. Integrar a revisão metacognitiva obrigatória na etapa de Encerramento.
