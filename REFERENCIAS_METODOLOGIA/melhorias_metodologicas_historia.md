# MELHORIAS DO SISTEMA PLANOS_LUAN — HISTÓRIA
## Documento de Instruções para Implantação — Codex

**Gerado em:** 2026-06-13  
**Base de análise:** PDFs de História (EF) em `D:\PDF novos\HISTORIA`.  
**Objetivo:** Orientar a correção de desvios pedagógicos em História, focando em análise de fontes históricas e estabelecimento de conexões entre passado e presente.

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

O perfil de História no sistema tende a gerar planos meramente expositivos, onde o professor apenas fala e os alunos ouvem. Em História, a **leitura crítica de fontes documentais** (imagens, charges de época, trechos de leis, diários ou relatos) é fundamental e deve ser mediada por meio de perguntas norteadoras explícitas no plano.

---

## 2. PROBLEMAS CRÍTICOS — ALTA PRIORIDADE

### 2.1 Leitura Passiva de Textos Sem Análise de Fontes Históricas
**Arquivo afetado:** `core/lib/metodologia.py`

**Descrição do problema:**  
Os planos abordam fatos (como a Revolução Industrial ou a Colonização) apenas descrevendo o que aconteceu, sem orientar a leitura de fontes de época presentes no material.

**Como corrigir:**  
```python
# DEPOIS:
def gerar_etapa_analise_fonte(fonte_tipo, contexto_pdf):
    return (
        f"Orientar a análise da fonte histórica ({fonte_tipo}) presente no material. "
        "Mediar o processo por meio de três perguntas: "
        "1. Quem produziu esta fonte e em qual contexto? "
        "2. Qual a mensagem ou ponto de vista implícito? "
        "3. Como este documento nos ajuda a compreender o período histórico estudado?"
    )
```

### 2.2 Ausência de Conexões com o Presente (Presentismo/Anacronismo)
**Descrição do problema:**  
O plano trata o passado de forma desconectada da atualidade ou incorre em anacronismos ao avaliar o passado com a ética de hoje sem debate.

**Como corrigir:**  
```python
# DEPOIS:
def gerar_etapa_fechamento_historia(tema):
    return f"Conduzir o debate final conectando o tema ({tema}) às discussões atuais, identificando permanências, rupturas ou legados desse período histórico na nossa sociedade atual."
```

---

## 3. PROBLEMAS MÉDIOS — MÉDIA PRIORIDADE

### 3.1 Falta de Sequência Cronológica
**Descrição:** Omissão de contextualização temporal inicial (datas, séculos).  
**Correção:** Toda aula de História deve ter no "Para começar" a fixação de uma linha do tempo na lousa com o marco do período.

---

## 4. PROBLEMAS MENORES — BAIXA PRIORIDADE

### 4.1 Substituir Termos Administrativos nos Títulos
**Correção:** Substituir títulos que contenham números de leis ou códigos puramente por sua descrição pedagógica histórica correspondente.

---

## 5. MELHORIAS POR ARQUIVO/MÓDULO

| Arquivo | Alteração | Prioridade |
|---------|-----------|------------|
| `core/lib/classificador.py` | Identificar termos de fontes históricas (carta, lei, imagem, monumento) | 🔴 ALTA |
| `core/lib/metodologia.py` | Estruturar etapas de leitura de fontes na lousa | 🔴 ALTA |

---

## 6. REGRAS FIXAS QUE NUNCA DEVEM SER VIOLADAS

1. **Localização temporal**: Sempre desenhar/citar a linha do tempo ou o século no início da aula.
2. **Contexto de produção**: Toda fonte histórica deve ter autor, público e intencionalidade explicitados.
3. **Legados e permanências**: Conectar o passado ao presente no fechamento da aula.

---

## 7. EXEMPLOS DE SAÍDA CORRETA VS. INCORRETA

### 7.1 Aula de Revolução Industrial
* **❌ INCORRETO:** *"Explicar que a máquina a vapor mudou a indústria e pedir que respondam às questões do material."*
* **✅ CORRETO:** *"Foco no conteúdo: Analisar o relato de um trabalhador de fábrica de 1830. Orientar a turma a destacar as denúncias de jornadas de trabalho, comparando com as leis trabalhistas e condições laborais atuais."*

---

## 8. CHECKLIST DE VALIDAÇÃO PÓS-GERAÇÃO

```python
def validar_plano_historia(plano: dict) -> list[str]:
    erros = []
    for aula in plano.get('aulas', []):
        if "fonte" not in aula['metodologia'].lower() and "documento" not in aula['metodologia'].lower():
            erros.append(f"Aula {aula['numero']}: Falta atividade mediada de análise de fontes históricas.")
    return erros
```

---

## 9. APÊNDICE — ORDEM DE IMPLANTAÇÃO RECOMENDADA
1. Implementar rotina de linha do tempo no início de cada aula de História.
2. Mapear as perguntas de análise crítica de fontes históricas no motor de metodologia.
