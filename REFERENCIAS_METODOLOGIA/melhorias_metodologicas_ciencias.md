# MELHERIAS DO SISTEMA PLANOS_LUAN — CIÊNCIAS
## Documento de Instruções para Implantação — Codex

**Gerado em:** 2026-06-13  
**Base de análise:** PDFs de Ciências (EF) em `D:\PDF novos\CIENCIAS`.  
**Objetivo:** Orientar a correção de desvios pedagógicos em Ciências, focando em modelagem científica, leitura orientada de dados e diferenciação de investigações de laboratório.

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

O perfil de Ciências no sistema costuma sofrer de generalização, onde qualquer aula prática é rotulada como "experimento" (inventando bicos de Bunsen, tubos de ensaio ou materiais não previstos no PDF) ou aulas de modelagem (como maquetes da órbita da Terra) omitem a discussão crucial de que o modelo didático simplifica a realidade.

---

## 2. PROBLEMAS CRÍTICOS — ALTA PRIORIDADE

### 2.1 Uso Indevido do Termo "Experimento" e Alucinação de Materiais
**Arquivo afetado:** `core/lib/metodologia.py`

**Descrição do problema:**  
Aulas teóricas ou de simples leitura de texto são transformadas pelo motor de IA em "aulas experimentais", adicionando materiais que a escola pode não possuir.

**Como corrigir:**  
```python
# DEPOIS:
def gerar_etapa_pratica_ciencias(tipo_aula, dados_pdf):
    if tipo_aula != "aula_pratica_laboratorio":
        return "Conduzir a leitura analítica do infográfico/texto explicativo do material, orientando os estudantes a registrar no caderno as relações de causa e efeito apontadas pelo material."
    return "Conduzir o experimento utilizando EXCLUSIVAMENTE os materiais listados no PDF: [inserir materiais do PDF]."
```

### 2.2 Modelos Didáticos Sem Discussão de Seus Limites
**Descrição do problema:**  
Em aulas de modelagem tridimensional (maquetes, células de isopor, órbitas), os planos omitem que os modelos servem para facilitar a compreensão, mas têm limites de escala, tempo e representação.

**Como corrigir:**  
```python
# DEPOIS:
def gerar_etapa_modelagem_ciencias():
    return "Orientar a construção do modelo tridimensional. Explicar claramente aos estudantes a função do modelo de representar estruturas inacessíveis, mas pontuar seus limites em relação à realidade (ex: distorção de escala, proporções de tamanho e ausência de movimentos dinâmicos)."
```

---

## 3. PROBLEMAS MÉDIOS — MÉDIA PRIORIDADE

### 3.1 Omissão de Leitura de Gráficos e Tabelas
**Descrição:** Planos de ecologia com gráficos apenas dizem "analise o gráfico", sem detalhar o que deve ser lido.  
**Correção:** Adicionar leitura orientada de título, eixos, variáveis, fonte e tendências dos dados.

---

## 4. PROBLEMAS MENORES — BAIXA PRIORIDADE

### 4.1 Contaminação de Termos de LP em Ciências
**Descrição:** Palavras como "estudo gramatical" ou "gêneros" surgindo em planos de ecologia.  
**Correção:** Validar exclusão mútua de vocabulários por meio do módulo centralizado de normalização.

---

## 5. MELHORIAS POR ARQUIVO/MÓDULO

| Arquivo | Alteração | Prioridade |
|---------|-----------|------------|
| `core/lib/classificador.py` | Distinguir `modelagem_cientifica` de `aula_pratica` | 🔴 ALTA |
| `core/lib/metodologia.py` | Forçar termos de simplificação da realidade em modelos | 🔴 ALTA |

---

## 6. REGRAS FIXAS QUE NUNCA DEVEM SER VIOLADAS

1. **Não alucinar materiais**: Nunca incluir vidrarias ou reagentes que não estejam listados na extração textual do PDF.
2. **Leitura orientada**: Todo gráfico deve ser lido passo a passo (Título -> Eixos -> Dados).
3. **Limitação de modelos**: Toda aula de maquete/modelo deve discutir seus limites físicos.

---

## 7. EXEMPLOS DE SAÍDA CORRETA VS. INCORRETA

### 7.1 Maquete de Sistema Solar
* **❌ INCORRETO:** *"Orientar a montagem das bolinhas de isopor e corrigir se as órbitas estiverem erradas."*
* **✅ CORRETO:** *"Foco no conteúdo: Auxiliar a pintura das esferas, explicitando que o modelo representa a ordem planetária, mas não consegue manter a escala correta de distância entre os planetas e o Sol."*

---

## 8. CHECKLIST DE VALIDAÇÃO PÓS-GERAÇÃO

```python
def validar_plano_ciencias(plano: dict) -> list[str]:
    erros = []
    for aula in plano.get('aulas', []):
        if "modelo" in aula['titulo'].lower() and "limite" not in aula['metodologia'].lower() and "realidade" not in aula['metodologia'].lower():
            erros.append(f"Aula {aula['numero']}: Falta discussão sobre limites do modelo científico.")
    return erros
```

---

## 9. APÊNDICE — ORDEM DE IMPLANTAÇÃO RECOMENDADA
1. Adicionar tags de detecção para modelagem e análise de dados em `core/lib/classificador.py`.
2. Criar os geradores de texto para modelagem e análise gráfica em `core/lib/metodologia.py`.
