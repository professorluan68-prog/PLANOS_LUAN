# MELHORIAS DO SISTEMA PLANOS_LUAN — BIOLOGIA
## Documento de Instruções para Implantação — Codex

**Gerado em:** 2026-06-13  
**Base de análise:** PDFs de Biologia (EM) em `D:\PDF novos\BIOLOGIA`.  
**Objetivo:** Orientar a correção de desvios pedagógicos em Biologia, focando em modelagem molecular/fisiológica e conexões ecológicas.

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

O perfil de Biologia no Ensino Médio exige rigor científico elevado. O sistema falha principalmente ao simplificar conceitos bioquímicos ou genéticos em metodologias genéricas de leitura silenciosa, ou ao descrever modelagens fisiológicas (ex: replicação do DNA, síntese proteica, fotossíntese) sem detalhar as etapas dinâmicas do processo.

---

## 2. PROBLEMAS CRÍTICOS — ALTA PRIORIDADE

### 2.1 Omissão da Dinamicidade Fisiológica em Processos Biológicos
**Arquivo afetado:** `core/lib/metodologia.py`

**Descrição do problema:**  
Aulas que abordam processos complexos (ex: divisão celular, síntese de proteínas) descrevem apenas o conceito de forma estática, sem orientar o uso de esquemas passo a passo ou simulações.

**Como corrigir:**  
```python
# DEPOIS:
def gerar_etapa_fisiologia(processo, dados_pdf):
    return (
        f"Conduzir o Foco no conteúdo explicando o processo dinâmico de {processo} por meio de "
        "esquemas sequenciais na lousa. Explicar cada etapa ativa (ex: pareamento de bases, "
        "separação de cromossomos) e o papel de cada enzima/organela envolvida."
    )
```

### 2.2 Abordagem Genérica de Impactos de Doenças ou Genética
**Descrição do problema:**  
Aulas de genética ou patologia são reduzidas a listas de decoreba de sintomas ou regras de cruzamento (quadrado de Punnett) sem correlacionar com hereditariedade real ou prevenção de saúde.

**Como corrigir:**  
```python
# DEPOIS:
def gerar_etapa_genetica(tema):
    return (
        f"Orientar a resolução guiada do cruzamento genético na lousa ({tema}), "
        "desenhando o quadrado de Punnett passo a passo e explicando o cálculo de probabilidades "
        "tanto em frações quanto em porcentagem, interpretando a manifestação fenotípica."
    )
```

---

## 3. PROBLEMAS MÉDIOS — MÉDIA PRIORIDADE

### 3.1 Falha na Leitura de Evidências Evolutivas
**Descrição:** Omissão da leitura crítica de árvores filogenéticas ou cladogramas.  
**Correção:** Mediar a leitura de cladogramas na lousa (nós, ancestrais comuns, novidades evolutivas).

---

## 4. PROBLEMAS MENORES — BAIXA PRIORIDADE

### 4.1 Erros Ortográficos em Termos Científicos
**Correção:** Adicionar corretores de mojibake especializados em taxonomia e bioquímica (ex: mitocôndria, ribossomo, desoxirribose).

---

## 5. MELHORIAS POR ARQUIVO/MÓDULO

| Arquivo | Alteração | Prioridade |
|---------|-----------|------------|
| `core/lib/classificador.py` | Detectar tags específicas de `genética`, `bioquímica` e `fisiologia` | 🔴 ALTA |
| `core/lib/metodologia.py` | Implementar modelagem do quadrado de Punnett e esquemas dinâmicos | 🔴 ALTA |

---

## 6. REGRAS FIXAS QUE NUNCA DEVEM SER VIOLADAS

1. **Rigor conceitual**: Não simplificar termos bioquímicos ou genéticos a ponto de torná-los imprecisos.
2. **Representação dinâmica**: Processos fisiológicos devem ser explicados em etapas sequenciais (início, meio e fim).
3. **Leitura de cladogramas**: Toda árvore evolutiva deve ter seus nós e ramos analisados de forma guiada.

---

## 7. EXEMPLOS DE SAÍDA CORRETA VS. INCORRETA

### 7.1 Aula de Divisão Celular (Mitose)
* **❌ INCORRETO:** *"Explicar que a mitose gera células iguais e pedir que respondam ao exercício do material."*
* **✅ CORRETO:** *"Foco no conteúdo: Desenhar as quatro etapas da mitose (Prófase, Metáfase, Anáfase, Telófase) na lousa, explicando as modificações do núcleo celular, o alinhamento cromossômico e a separação das cromátides irmãs em cada etapa."*

---

## 8. CHECKLIST DE VALIDAÇÃO PÓS-GERAÇÃO

```python
def validar_plano_biologia(plano: dict) -> list[str]:
    erros = []
    for aula in plano.get('aulas', []):
        if "mitose" in aula['titulo'].lower() and "etapas" not in aula['metodologia'].lower():
            erros.append(f"Aula {aula['numero']}: Divisão celular descrita sem as fases ativas do processo.")
    return erros
```

---

## 9. APÊNDICE — ORDEM DE IMPLANTAÇÃO RECOMENDADA
1. Adicionar filtros de terminologia taxionômica/fisiológica ao classificador.
2. Criar os blocos de modelagem conceitual de genética e fisiologia em `core/lib/metodologia.py`.
