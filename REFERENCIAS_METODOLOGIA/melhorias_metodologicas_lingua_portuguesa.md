# MELHORIAS DO SISTEMA PLANOS_LUAN — LÍNGUA PORTUGUESA
## Documento de Instruções para Implantação — Codex

**Gerado em:** 2026-06-13  
**Base de análise:** PDFs do 1º, 2º e 3º bimestre de Língua Portuguesa (EF e EM) em `D:\PDF novos\LINGUA_PORTUGUESA`.  
**Objetivo:** Orientar a correção de desvios pedagógicos em Língua Portuguesa, garantindo a diferenciação entre tipos de aula e eliminando trechos genéricos na metodologia.

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

O perfil de Língua Portuguesa no sistema possui boa separação entre o Ensino Fundamental (`lingua_portuguesa_ef`) e o Ensino Médio (`lingua_portuguesa_em`). Contudo, o sistema falha ao tratar as aulas de leitura, gramática e produção escrita como idênticas, aplicando o mesmo pool de frases de fallback. Em Língua Portuguesa, o maior problema é a **falta de conexão ativa com o gênero textual do PDF** e o pedido de escritas ou análises de fontes sem planejamento gradual.

---

## 2. PROBLEMAS CRÍTICOS — ALTA PRIORIDADE

### 2.1 Metodologia de Leitura e Escrita sem Gênero Textual Específico
**Arquivo afetado:** `core/lib/metodologia.py` (função `gerar_metodologia`)

**Descrição do problema:**  
Independentemente do PDF abordar crônicas, posts de blog, editoriais ou notícias, a etapa "Hora da leitura" ou "Na prática" utiliza um texto genérico sobre "localizar as informações principais do texto" e "socializar as respostas em duplas". O gênero literário ou jornalístico não é mencionado.

**Como corrigir:**  
Integrar o gênero textual detectado pelo classificador diretamente nos blocos de texto:
```python
# ANTES:
def hora_leitura_generico(texto_pdf):
    return "Orientar os estudantes a realizar a leitura silenciosa do texto, sublinhando os pontos principais."

# DEPOIS:
def hora_leitura_por_genero(genero, texto_pdf):
    if genero == "cronica":
        return "Conduzir a HORA DA LEITURA da crônica, orientando os estudantes a identificar as marcas do narrador, a situação cotidiana retratada e o ponto de virada ou conflito que gera a reflexão final."
    if genero == "noticia":
        return "Conduzir a HORA DA LEITURA da notícia, orientando a identificação do fato central, as circunstâncias (quem, quando, onde) e as decorrências relatadas, mapeando o lide."
    return "Orientar a leitura do texto, com foco na estrutura composicional do gênero estudado."
```

### 2.2 Escrita Mecânica Sem Processo de Planejamento e Revisão
**Arquivo afetado:** `core/lib/metodologia.py`  
**Descrição do problema:**  
Nas aulas de produção escrita (`producao_textual`), a instrução manda os alunos "escreverem o texto diretamente", violando a diretriz de Língua Portuguesa de tratar a escrita como processo (planejar, rascunhar, revisar e reescrever).

**Como corrigir:**  
Mapear a produção em etapas de processo:
```python
# DEPOIS (Correto):
def gerar_etapa_producao(genero, tema):
    return f"Conduzir o TODO MUNDO ESCREVE para que cada estudante elabore o planejamento de sua produção sobre {tema}, definindo o público-alvo, o suporte de circulação e o objetivo do texto. Em seguida, iniciar a escrita do rascunho primário."
```

---

## 3. PROBLEMAS MÉDIOS — MÉDIA PRIORIDADE

### 3.1 Falha na Classificação de Gêneros Híbridos
**Arquivo afetado:** `core/lib/classificador.py`  
**Descrição:** Notícias em formato de infográfico ou posts de opinião estão sendo jogados em fallbacks genéricos de gramática.  
**Correção:** Adicionar termos como "multissemiótico", "infográfico", "tirinha", "charge" e "leitura de imagem" no classificador de Língua Portuguesa.

---

## 4. PROBLEMAS MENORES — BAIXA PRIORIDADE

### 4.1 Falta de Variação de Verbos nas Etapas de LP
**Correção:** Garantir alternância nos inícios de frases usando verbos observáveis de leitura/análise (ex: *Mapear*, *Analisar*, *Depurar*, *Articular*, *Sistematizar*).

---

## 5. MELHORIAS POR ARQUIVO/MÓDULO

| Arquivo | Alteração | Prioridade |
|---------|-----------|------------|
| `core/lib/classificador.py` | Melhorar detecção de gênero e termos multimodais | 🔴 ALTA |
| `core/lib/metodologia.py` | Adicionar geradores específicos para crônica, notícia e editorial | 🔴 ALTA |
| `core/lib/metodologia.py` | Integrar planejamento na etapa de produção de texto | 🔴 ALTA |

---

## 6. REGRAS FIXAS QUE NUNCA DEVEM SER VIOLADAS

1. **A escrita é um processo**: Nunca pedir para o aluno redigir um texto sem antes detalhar a etapa de planejamento (público-alvo, suporte, gênero).
2. **Leitura ativa**: A etapa de leitura deve focar nos elementos específicos do gênero estudado (ex: lide para notícia, eu lírico para poesia).
3. **Acompanhamento com foco em gênero**: Pelo menos 1 item de acompanhamento deve verificar a apropriação do gênero textual da aula.

---

## 7. EXEMPLOS DE SAÍDA CORRETA VS. INCORRETA

### 7.1 Aula de Crônica
* **❌ INCORRETO:** *"Foco no conteúdo: ler o texto e identificar as informações principais e o ponto de vista do autor."*
* **✅ CORRETO:** *"Foco no conteúdo: Ler a crônica identificando o narrador-observador e como ele transforma uma situação do cotidiano (fila de banco) em reflexão lírica."*

---

## 8. CHECKLIST DE VALIDAÇÃO PÓS-GERAÇÃO

```python
def validar_plano_portugues(plano: dict) -> list[str]:
    erros = []
    for aula in plano.get('aulas', []):
        if "escreva" in aula['metodologia'].lower() and "planejamento" not in aula['metodologia'].lower():
            erros.append(f"Aula {aula['numero']}: Produção textual sem etapa de planejamento.")
    return erros
```

---

## 9. APÊNDICE — ORDEM DE IMPLANTAÇÃO RECOMENDADA
1. Implementar detecção de gênero no classificador.
2. Criar os geradores de metodologia por gênero textual em `core/lib/metodologia.py`.
3. Adicionar as regras de processo de escrita.
