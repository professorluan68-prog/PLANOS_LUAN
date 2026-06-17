# MELHORIAS DO SISTEMA PLANOS_LUAN — LÍNGUA INGLESA
## Documento de Instruções para Implantação — Codex

**Gerado em:** 2026-06-13  
**Base de análise:** PDFs de Língua Inglesa (EF e EM) em `D:\PDF novos\LINGUA_INGLESA`.  
**Objetivo:** Orientar a correção de desvios pedagógicos em Língua Inglesa, focando na integração gradual de vocabulário e audição/produção oral.

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

O perfil de Língua Inglesa falha ao omitir o **apoio prévio de vocabulário (pre-reading/pre-listening)** e a indicação de como orientar as atividades de compreensão oral (listening), muitas vezes tratando a escuta de áudios apenas como leitura silenciosa de texto.

---

## 2. PROBLEMAS CRÍTICOS — ALTA PRIORIDADE

### 2.1 Falta de Etapa de Vocabulário Prévio (Warm-up / Pre-reading)
**Arquivo afetado:** `core/lib/metodologia.py`

**Descrição do problema:**  
Os planos partem diretamente para a leitura do texto principal em inglês sem uma etapa de ativação de vocabulário essencial, gerando frustração.

**Como corrigir:**  
```python
# DEPOIS:
def gerar_etapa_pre_leitura_ingles(vocabulario, dados_pdf):
    return (
        f"Conduzir o Vocabulário de apoio: apresentar os termos-chave em inglês ({vocabulario}) "
        "e seus significados ou cognatos em português na lousa antes de iniciar a leitura principal."
    )
```

### 2.2 Omissão de Instruções de Listening
**Descrição do problema:**  
Aulas que envolvem faixas de áudio (listening) apenas dizem "ouça o áudio", sem detalhar o processo de escuta dirigida (primeira escuta para compreensão geral, segunda para detalhes).

**Como corrigir:**  
```python
# DEPOIS:
def gerar_etapa_listening_ingles():
    return (
        "Orientar a primeira escuta do áudio para identificar a ideia geral (gist). "
        "Na segunda reprodução, orientar o preenchimento dos exercícios propostos, com foco em termos específicos."
    )
```

---

## 3. PROBLEMAS MÉDIOS — MÉDIA PRIORIDADE

### 3.1 Falta de Produção Oral (Speaking)
**Descrição:** Planos focam apenas na escrita de exercícios gramaticais, omitindo a prática comunicativa.  
**Correção:** Inserir em todas as aulas de gramática prática oral em duplas com as estruturas estudadas.

---

## 4. PROBLEMAS MENORES — BAIXA PRIORIDADE

### 4.1 Tradução Literal Excessiva
**Correção:** Impedir que o professor traduza todo o texto visível; focar na tradução funcional apenas de termos difíceis.

---

## 5. MELHORIAS POR ARQUIVO/MÓDULO

| Arquivo | Alteração | Prioridade |
|---------|-----------|------------|
| `core/lib/classificador.py` | Detectar tags de `listening`, `speaking` e `reading` em inglês | 🔴 ALTA |
| `core/lib/metodologia.py` | Estruturar etapas de vocabulário e compreensão auditiva | 🔴 ALTA |

---

## 6. REGRAS FIXAS QUE NUNCA DEVEM SER VIOLADAS

1. **Vocabulário prévio**: Apresentar termos-chave na lousa antes da leitura ou áudio.
2. **Escuta dirigida**: Listening deve ter pelo menos duas repetições orientadas (geral e detalhada).
3. **Foco comunicativo**: Estimular a interação oral entre estudantes ao final da aula.

---

## 7. EXEMPLOS DE SAÍDA CORRETA VS. INCORRETA

### 7.1 Aula de Listening
* **❌ INCORRETO:** *"Orientar a reprodução do áudio e pedir que respondam às questões 1 e 2."*
* **✅ CORRETO:** *"Na prática: Orientar a primeira audição do áudio para identificar quem são os falantes. Na segunda audição, guiar o preenchimento do exercício de completar lacunas."*

---

## 8. CHECKLIST DE VALIDAÇÃO PÓS-GERAÇÃO

```python
def validar_plano_ingles(plano: dict) -> list[str]:
    erros = []
    for aula in plano.get('aulas', []):
        if "leitura" in aula['metodologia'].lower() and "vocabulário" not in aula['metodologia'].lower():
            erros.append(f"Aula {aula['numero']}: Leitura iniciada sem vocabulário de apoio prévio.")
    return erros
```

---

## 9. APÊNDICE — ORDEM DE IMPLANTAÇÃO RECOMENDADA
1. Mapear as tags de competências de inglês no classificador.
2. Adicionar o motor de etapas com vocabulário de pré-leitura.
