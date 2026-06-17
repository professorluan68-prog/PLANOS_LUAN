# MELHORIAS DO SISTEMA PLANOS_LUAN — EDUCAÇÃO FINANCEIRA
## Documento de Instruções para Implantação — Codex

**Gerado em:** 2026-06-13  
**Base de análise:** PDFs de Educação Financeira (EF e EM) em `D:\PDF novos\EDUCACAO_FINANCEIRA`.  
**Objetivo:** Orientar a correção de desvios pedagógicos em Educação Financeira, focando em simulações de cenários, orçamento pessoal e tomada de decisão de consumo.

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

O perfil de Educação Financeira no sistema costuma ser tratado como se fosse uma aula pura de matemática (calculando juros de forma abstrata) ou uma aula puramente moralista (dizendo o que é "certo" ou "errado" comprar). O plano deve focar na **análise crítica de escolhas de consumo** e na modelagem de orçamentos práticos de forma contextualizada à realidade local dos estudantes.

---

## 2. PROBLEMAS CRÍTICOS — ALTA PRIORIDADE

### 2.1 Resolução de Exercícios puramente Abstratos sem Aplicação Prática
**Arquivo afetado:** `core/lib/metodologia.py`

**Descrição do problema:**  
Cálculos de juros compostos ou investimentos são feitos sem contextualizar em metas reais de poupança, taxas reais do mercado ou simulações de consumo consciente.

**Como corrigir:**  
```python
# DEPOIS:
def gerar_etapa_simulacao_financeira(cenario, dados_pdf):
    return (
        f"Apresentar o cenário real: {cenario}. Orientar os estudantes a elaborar uma simulação prática "
        "calculando os juros/taxas aplicados a essa escolha, e em seguida debater as consequências "
        "dessa decisão no orçamento mensal simulado."
    )
```

### 2.2 Julgamento Moral sobre Decisões de Consumo
**Descrição do problema:**  
O plano usa termos julgadores como "ensinar a comprar apenas o necessário" ou "condenar o endividamento", em vez de debater causas socioeconômicas do consumo e estratégias de prevenção.

**Como corrigir:**  
```python
# DEPOIS:
def gerar_etapa_debate_consumo(tema):
    return f"Conduzir o debate sobre {tema}, orientando a identificação dos fatores psicológicos e de marketing que influenciam as decisões de compra, auxiliando os estudantes a construir estratégias de planejamento pessoal antes de compras impulsivas."
```

---

## 3. PROBLEMAS MÉDIOS — MÉDIA PRIORIDADE

### 3.1 Falta de Análise de Planilhas
**Descrição:** Aulas que abordam orçamento e planilhas no PDF apenas dizem para "olhar a tabela", sem ensinar a preencher.  
**Correção:** Mediar o preenchimento prático de uma tabela simples de receitas e despesas na lousa com dados fictícios.

---

## 4. PROBLEMAS MENORES — BAIXA PRIORIDADE

### 4.1 Erros de Nomenclatura nos Termos Bancários
**Correção:** Padronizar termos de economia no classificador (ex: juros simples, juros compostos, CDI, poupança, inflação).

---

## 5. MELHORIAS POR ARQUIVO/MÓDULO

| Arquivo | Alteração | Prioridade |
|---------|-----------|------------|
| `core/lib/classificador.py` | Adicionar termos específicos de orçamento e planejamento de consumo | 🔴 ALTA |
| `core/lib/metodologia.py` | Implementar gerador de simulação de orçamento na lousa | 🔴 ALTA |

---

## 6. REGRAS FIXAS QUE NUNCA DEVEM SER VIOLADAS

1. **Simulação antes do cálculo**: Contextualizar o motivo do cálculo financeiro em uma escolha real antes de aplicar fórmulas.
2. **Neutralidade pedagógica**: Não julgar as escolhas de consumo dos estudantes, mas instrumentalizá-los para analisar suas consequências.
3. **Budget de realidade**: Adaptar os cenários de simulação à faixa etária e contexto social dos alunos.

---

## 7. EXEMPLOS DE SAÍDA CORRETA VS. INCORRETA

### 7.1 Aula de Cartão de Crédito
* **❌ INCORRETO:** *"Explicar que o cartão de crédito cobra juros altos e que os alunos não devem usá-lo."*
* **✅ CORRETO:** *"Foco no conteúdo: Apresentar o cenário de pagamento mínimo da fatura de cartão de crédito. Orientar os grupos a calcular os juros de rotativo simulados na lousa e debater alternativas para renegociar a dívida."*

---

## 8. CHECKLIST DE VALIDAÇÃO PÓS-GERAÇÃO

```python
def validar_plano_financeiro(plano: dict) -> list[str]:
    erros = []
    for aula in plano.get('aulas', []):
        if "cálculo" in aula['metodologia'].lower() and "cenário" not in aula['metodologia'].lower() and "simulação" not in aula['metodologia'].lower():
            erros.append(f"Aula {aula['numero']}: Falta contextualização prática do cálculo financeiro.")
    return erros
```

---

## 9. APÊNDICE — ORDEM DE IMPLANTAÇÃO RECOMENDADA
1. Mapear termos de simulação e cenários reais de consumo no classificador.
2. Construir etapas de preenchimento de orçamento pessoal na lousa.
