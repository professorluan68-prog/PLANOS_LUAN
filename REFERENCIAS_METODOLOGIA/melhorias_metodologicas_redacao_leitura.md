# MELHORIAS DO SISTEMA PLANOS_LUAN — REDAÇÃO E LEITURA
## Documento de Instruções para Implantação — Codex

**Gerado em:** 2026-06-13  
**Base de análise:** PDFs de Redação e Leitura (EF e EM) em `D:\PDF novos\REDACAO_E_LEITURA`.  
**Objetivo:** Orientar a implantação de melhorias estruturais no perfil de Redação e Leitura, garantindo o fluxo fixo de 6 etapas e foco na função social da escrita.

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

O perfil de Redação e Leitura possui a especificação técnica mais rígida do sistema: **6 etapas fixas obrigatórias**. O problema recorrente é o motor de fallback local e a IA omitirem etapas (como "Análise guiada" ou "Revisão e fechamento"), gerando planos incompletos ou desalinhados do gênero textual proposto.

---

## 2. PROBLEMAS CRÍTICOS — ALTA PRIORIDADE

### 2.1 Omissão ou Fusão das 6 Etapas Fixas Obrigatórias
**Arquivo afetado:** `core/lib/metodologia.py` (ou `core/redacao_leitura_metodologia.py`)

**Descrição do problema:**  
O plano é gerado com a estrutura padrão de 4 ou 5 etapas (como Ciências/Matemática), ignorando a sequência metodológica obrigatória do perfil de redação.

**Como corrigir:**  
Forçar a estrutura exata no motor local e no prompt de IA:
```python
# DEPOIS:
def obter_etapas_redacao_leitura():
    return [
        ("Disparo inicial / contextualização", "abertura_disparo"),
        ("Leitura ou exploração inicial", "hora_leitura_genero"),
        ("Análise guiada", "analise_perguntas"),
        ("Sistematização", "checklist_regras"),
        ("Produção textual", "producao_escrita"),
        ("Revisão e fechamento", "revisao_autoral")
    ]
```

### 2.2 Falta de Intencionalidade Comunicativa na Produção Textual
**Descrição do problema:**  
A etapa "Produção textual" apenas diz "peça para escreverem o texto", sem explicitar: o que escrever, para quem escrever e onde o texto vai circular.

**Como corrigir:**  
```python
# DEPOIS:
def gerar_etapa_escrita_redacao(genero, publico, suporte):
    return (
        f"Conduzir a escrita individual do gênero {genero}, direcionada ao público-alvo ({publico}) "
        f"para publicação/veiculação no suporte ({suporte})."
    )
```

---

## 3. PROBLEMAS MÉDIOS — MÉDIA PRIORIDADE

### 3.1 Falta de Perguntas de Compreensão na Análise Guiada
**Descrição:** A etapa de análise guiada omite as perguntas reflexivas necessárias.  
**Correção:** Inserir no mínimo três perguntas obrigatórias na etapa (Compreensão, Interpretação e Reflexão Crítica).

---

## 4. PROBLEMAS MENORES — BAIXA PRIORIDADE

### 4.1 Confusão com "Resenha" vs "Resumo"
**Correção:** Garantir que a resenha inclua obrigatoriamente a opinião/crítica do estudante, diferenciando-se do resumo informativo.

---

## 5. MELHORIAS POR ARQUIVO/MÓDULO

| Arquivo | Alteração | Prioridade |
|---------|-----------|------------|
| `core/lib/metodologia.py` | Travar a estrutura em 6 etapas para o perfil `leitura_redacao` | 🔴 ALTA |
| `core/redacao_leitura_metodologia.py` | Refinar geradores específicos de parágrafos estruturados | 🔴 ALTA |

---

## 6. REGRAS FIXAS QUE NUNCA DEVEM SER VIOLADAS

1. **6 etapas obrigatórias**: Nunca fundir ou pular etapas do fluxo de Redação e Leitura.
2. **Propósito comunicativo**: Toda produção escrita deve explicitar gênero, público e suporte de veiculação.
3. **Análise guiada reflexiva**: Incluir no mínimo 3 perguntas de níveis progressivos de leitura.

---

## 7. EXEMPLOS DE SAÍDA CORRETA VS. INCORRETA

### 7.1 Etapa de Produção Textual (Crônica)
* **❌ INCORRETO:** *"Orientar que escrevam uma crônica livre em seus cadernos."*
* **✅ CORRETO:** *"Produção textual: Orientar a escrita individual de uma crônica (gênero) sobre um acontecimento escolar cotidiano, destinada aos colegas de classe (público) para fixação no mural da sala (suporte)."*

---

## 8. CHECKLIST DE VALIDAÇÃO PÓS-GERAÇÃO

```python
def validar_plano_redacao(plano: dict) -> list[str]:
    erros = []
    for aula in plano.get('aulas', []):
        etapas = [e['titulo'].lower() for e in aula.get('metodologia', [])]
        if len(etapas) != 6:
            erros.append(f"Aula {aula['numero']}: Estrutura incorreta com {len(etapas)} etapas (esperado: 6).")
    return erros
```

---

## 9. APÊNDICE — ORDEM DE IMPLANTAÇÃO RECOMENDADA
1. Forçar a verificação de 6 etapas obrigatórias no validador do sistema.
2. Integrar geradores de gênero compostos (Gênero + Público + Suporte) na etapa 5.
