# MELHORIAS DO SISTEMA PLANOS_LUAN — ARTE
## Documento de Instruções para Implantação — Codex

**Gerado em:** 2026-06-13  
**Base de análise:** PDFs de Arte (EF e EM) em `D:\PDF novos\ARTE`.  
**Objetivo:** Orientar a correção de desvios pedagógicos em Arte, focando em análise estética de obras e mediação de práticas expressivas.

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

O perfil de Arte no sistema costuma sofrer com a falta de direcionamento prático nas propostas de atelier ou com análises teóricas vazias sobre movimentos artísticos, apenas listando nomes de pintores sem mediar a observação das qualidades formais da obra (linhas, cores, texturas, iluminação, composição).

---

## 2. PROBLEMAS CRÍTICOS — ALTA PRIORIDADE

### 2.1 Análise Teórica Sem Observação Estética da Obra
**Arquivo afetado:** `core/lib/metodologia.py`

**Descrição do problema:**  
O plano cita uma pintura famosa (ex: Tarsila do Amaral ou Van Gogh), mas a atividade pede que os estudantes respondam a perguntas conceituais na teoria, sem direcionar a leitura visual da obra.

**Como corrigir:**  
```python
# DEPOIS:
def gerar_etapa_leitura_visual(obra, dados_pdf):
    return (
        f"Orientar a observação atenta da obra '{obra}'. Conduzir a leitura visual guiando a turma "
        "a identificar: os elementos formais primários (cores predominantes, formas geométricas ou orgânicas, "
        "linhas de força), a composição espacial e o sentimento/mensagem que a imagem transmite."
    )
```

### 2.2 Atividades de Atelier Sem Orientação de Materiais Práticos
**Descrição do problema:**  
Nas atividades de produção prática (pintura, desenho, escultura, colagem), o plano orienta genericamente a "fazer uma obra de arte", sem definir as técnicas e os materiais escolares reais para o professor organizar.

**Como corrigir:**  
```python
# DEPOIS:
def gerar_etapa_atelier(tecnica, materiais_do_pdf):
    return (
        f"Conduzir a prática artística de {tecnica}. Orientar os estudantes a organizar os materiais "
        f"escolares ({materiais_do_pdf}) em suas mesas, demonstrando previamente na lousa/mesa do professor "
        "a técnica de aplicação (ex: mistura de cores secundárias, colagem por camadas) antes do início individual."
    )
```

---

## 3. PROBLEMAS MÉDIOS — MÉDIA PRIORIDADE

### 3.1 Omissão do Contexto Histórico da Arte
**Descrição:** Planos abordam o estilo (ex: Impressionismo) sem relacionar à época (invenção da fotografia, tubos de tinta, saída dos ateliês).  
**Correção:** Inserir contextualização histórica sociocultural nas etapas iniciais.

---

## 4. PROBLEMAS MENORES — BAIXA PRIORIDADE

### 4.1 Julgamentos Subjetivos de Beleza
**Correção:** Garantir que o motor de metodologia não use termos de juízo de valor subjetivo como "bonito", "feio" ou "arte verdadeira".

---

## 5. MELHORIAS POR ARQUIVO/MÓDULO

| Arquivo | Alteração | Prioridade |
|---------|-----------|------------|
| `core/lib/classificador.py` | Identificar técnicas de atelier (desenho, pintura, gravura, teatro) | 🔴 ALTA |
| `core/lib/metodologia.py` | Implementar geradores de leitura de imagem e orientação de atelier | 🔴 ALTA |

---

## 6. REGRAS FIXAS QUE NUNCA DEVEM SER VIOLADAS

1. **Leitura visual guiada**: Toda obra de arte projetada/impressa deve ter suas qualidades formais analisadas com os alunos.
2. **Atelier estruturado**: Práticas de atelier exigem demonstração técnica inicial do professor.
3. **Contexto sociocultural**: Movimentos artísticos devem ser explicados em relação à sua época e intenções.

---

## 7. EXEMPLOS DE SAÍDA CORRETA VS. INCORRETA

### 7.1 Aula sobre o Cubismo
* **❌ INCORRETO:** *"Explicar que o cubismo usa formas geométricas e pedir para fazerem um desenho geométrico livre."*
* **✅ CORRETO:** *"Foco no conteúdo: Projetar/exibir a obra cubista. Orientar os alunos a analisar como as formas tridimensionais são decompostas e representadas em planos bidimensionais simultâneos. Demonstrar a construção de um esboço na lousa antes da prática dos alunos."*

---

## 8. CHECKLIST DE VALIDAÇÃO PÓS-GERAÇÃO

```python
def validar_plano_arte(plano: dict) -> list[str]:
    erros = []
    for aula in plano.get('aulas', []):
        if "obra" in aula['metodologia'].lower() and "observação" not in aula['metodologia'].lower() and "visual" not in aula['metodologia'].lower():
            erros.append(f"Aula {aula['numero']}: Obras de arte mencionadas sem indicação de análise visual guiada.")
    return erros
```

---

## 9. APÊNDICE — ORDEM DE IMPLANTAÇÃO RECOMENDADA
1. Mapear as terminologias estéticas e técnicas de atelier no classificador.
2. Integrar a rotina de leitura visual de imagem no motor de metodologia.
