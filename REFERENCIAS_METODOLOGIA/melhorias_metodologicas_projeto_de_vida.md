# MELHORIAS DO SISTEMA PLANOS_LUAN — PROJETO DE VIDA
## Documento de Instruções para Implantação — Codex

**Gerado em:** 2026-06-13  
**Base de análise:** PDFs de Projeto de Vida (EF) em `D:\PDF novos\PROJETO_DE_VIDA`.  
**Objetivo:** Orientar a correção de desvios pedagógicos em Projeto de Vida, garantindo abordagens reflexivas e a eliminação completa de técnicas mecânicas de comportamento.

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

O perfil de Projeto de Vida no sistema costuma ser afetado pela contaminação de técnicas comportamentais mecânicas (LEMOV), o que é completamente inadequado para aulas voltadas ao desenvolvimento socioemocional, autoconhecimento e construção de valores éticos e pessoais.

---

## 2. PROBLEMAS CRÍTICOS — ALTA PRIORIDADE

### 2.1 Presença de Técnicas LEMOV e Rotação Mecânica de Atividades
**Arquivo afetado:** `core/lib/metodologia.py`

**Descrição do problema:**  
Aulas que envolvem reflexão íntima sobre sonhos, autoimagem ou sentimentos são geradas usando técnicas como `TODO MUNDO ESCREVE` ou `VIREM E CONVERSEM` de forma invasiva, obrigando a socialização de respostas pessoais.

**Como corrigir:**  
```python
# DEPOIS:
def gerar_etapa_reflexiva_pv(tema, dados_pdf):
    return (
        f"Conduzir a reflexão individual orientada sobre {tema}. Assegurar aos estudantes que o registro "
        "é pessoal e confidencial. O professor deve mediar sem julgar ou avaliar as respostas individuais."
    )
```

### 2.2 Socialização Obrigatória de Assuntos Pessoais
**Descrição do problema:**  
O plano orienta a "socialização na lousa" de respostas sobre medos, defeitos ou sentimentos, expondo os estudantes indevidamente.

**Como corrigir:**  
```python
# DEPOIS:
def gerar_socializacao_voluntaria_pv(tema):
    return "Promover uma roda de conversa onde os estudantes possam socializar voluntariamente suas impressões sobre o tema, acolhendo as falas e garantindo uma escuta ativa e respeitosa de toda a turma."
```

---

## 3. PROBLEMAS MÉDIOS — MÉDIA PRIORIDADE

### 3.1 Tratamento Conteudista
**Descrição:** O plano trata temas de PV como se fossem conceitos teóricos a serem decorados (ex: "sistematizar o conceito de resiliência").  
**Correção:** Mapear os temas sempre como experiências vivenciais (ex: "identificar atitudes resilientes em situações do cotidiano").

---

## 4. PROBLEMAS MENORES — BAIXA PRIORIDADE

### 4.1 Termos Proibidos
**Correção:** Impedir o surgimento de palavras como "certo", "errado", "nota" ou "avaliação quantitativa" nos planos de Projeto de Vida.

---

## 5. MELHORIAS POR ARQUIVO/MÓDULO

| Arquivo | Alteração | Prioridade |
|---------|-----------|------------|
| `core/lib/classificador.py` | Filtrar e classificar por tipo de experiência (Autoconhecimento, Convivência, Tomada de Decisão) | 🔴 ALTA |
| `core/lib/metodologia.py` | Remover qualquer chamada de LEMOV para o perfil de Projeto de Vida | 🔴 ALTA |

---

## 6. REGRAS FIXAS QUE NUNCA DEVEM SER VIOLADAS

1. **Privacidade e Confidencialidade**: Registros sobre sentimentos e autoimagem são de preenchimento livre e pessoal.
2. **Socialização Voluntária**: Ninguém deve ser obrigado a expor suas opiniões pessoais em roda de conversa.
3. **Professor como Facilitador**: A ação docente deve ser focada em "mediar", "acolher", "facilitar", nunca em "expor", "avaliar" ou "corrigir".

---

## 7. EXEMPLOS DE SAÍDA CORRETA VS. INCORRETA

### 7.1 Aula sobre Autoimagem
* **❌ INCORRETO:** *"Aplicar TODO MUNDO ESCREVE para que escrevam suas qualidades e socializar as respostas na lousa."*
* **✅ CORRETO:** *"Foco no conteúdo: Propor uma reflexão individual sobre autopercepção e valores pessoais. Esclarecer que as anotações são pessoais e servirão de base para o projeto do estudante."*

---

## 8. CHECKLIST DE VALIDAÇÃO PÓS-GERAÇÃO

```python
def validar_plano_pv(plano: dict) -> list[str]:
    erros = []
    for aula in plano.get('aulas', []):
        if any(termo in aula['metodologia'].upper() for termo in ["LEMOV", "TODO MUNDO ESCREVE", "VIREM E CONVERSEM"]):
            erros.append(f"Aula {aula['numero']}: Presença inadequada de técnicas LEMOV em Projeto de Vida.")
    return erros
```

---

## 9. APÊNDICE — ORDEM DE IMPLANTAÇÃO RECOMENDADA
1. Criar filtro rígido em `core/lib/metodologia.py` para bloquear LEMOV em Projeto de Vida.
2. Adicionar o gerador de roda de conversa e escrita voluntária/reflexão pessoal.
