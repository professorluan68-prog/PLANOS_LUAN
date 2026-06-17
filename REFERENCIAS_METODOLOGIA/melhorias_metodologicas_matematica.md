# MELHORIAS DO SISTEMA PLANOS_LUAN — MATEMÁTICA
## Documento de Instruções para Implantação — Codex

**Gerado em:** 2026-06-13  
**Base de análise:** PDFs de Matemática (EF e EM) em `D:\PDF novos\MATEMATICA`.  
**Objetivo:** Orientar a correção de desvios pedagógicos em Matemática, focando na diferenciação entre resolução de problemas, geometria e Khan Academy.

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

O perfil de Matemática no sistema possui bom suporte a técnicas LEMOV, mas peca pela repetição mecânica de blocos estruturados. O sistema ignora a intencionalidade de resoluções de problemas (tratando o erro de forma punitiva ou apressada) e não contextualiza as atividades na Khan Academy (tratando como mera atividade de laboratório).

---

## 2. PROBLEMAS CRÍTICOS — ALTA PRIORIDADE

### 2.1 Aulas de Geometria Sem Desenho ou Esboço de Figuras
**Arquivo afetado:** `core/lib/metodologia.py`

**Descrição do problema:**  
Aulas que envolvem cálculo de área, perímetro ou volumes pulam diretamente para a aplicação de fórmulas sem orientar o professor a desenhar a figura na lousa, dificultando a visualização espacial discente.

**Como corrigir:**  
```python
# DEPOIS:
def gerar_etapa_geometria(tema, dados_pdf):
    return "Desenhar a figura geométrica correspondente na lousa antes de iniciar os cálculos, identificando claramente as dimensões dadas (base, altura, raio, arestas) e a unidade de medida utilizada."
```

### 2.2 Falta de Contextualização e Acompanhamento na Khan Academy
**Descrição do problema:**  
Aulas no modelo `khan` pulam o fechamento reflexivo, apenas mandando os alunos abrirem a plataforma.  
**Como corrigir:**  
```python
# DEPOIS:
def gerar_etapa_khan():
    return [
        ("Abertura", "Contextualizar o tópico de matemática na lousa por 5 a 7 minutos com um exemplo prático."),
        ("Prática na Khan Academy", "Orientar os estudantes a acessar a plataforma, circulando ativamente pela sala para auxiliar dificuldades individuais e mapear erros comuns."),
        ("Fechamento", "Encerrar a aula projetando os relatórios de desempenho e realizando a devolutiva dos principais pontos de atenção identificados.")
    ]
```

---

## 3. PROBLEMAS MÉDIOS — MÉDIA PRIORIDADE

### 3.1 Tratamento de Erro Não Construtivo
**Descrição:** O plano assume que a correção é apenas verificar se está certo.  
**Correção:** Inserir no `Pause e responda` de matemática instruções para o professor explorar caminhos alternativos de resolução propostos pelos alunos.

---

## 4. PROBLEMAS MENORES — BAIXA PRIORIDADE

### 4.1 Sequência Cronológica das Equações
**Correção:** Garantir a etapa de verificação/prova real obrigatória em aulas de equações de 1º e 2º grau.

---

## 5. MELHORIAS POR ARQUIVO/MÓDULO

| Arquivo | Alteração | Prioridade |
|---------|-----------|------------|
| `core/lib/metodologia.py` | Implementar etapas específicas para Khan Academy e Geometria | 🔴 ALTA |
| `core/lib/classificador.py` | Detectar tags de geometria e probabilidade de forma mais assertiva | 🔴 ALTA |

---

## 6. REGRAS FIXAS QUE NUNCA DEVEM SER VIOLADAS

1. **Desenho prévio obrigatório**: Em geometria, desenhar sempre a figura geométrica na lousa antes de calcular.
2. **Prova real**: Em equações algebricas, incluir a verificação do resultado substituindo a incógnita.
3. **Khan contextualizada**: Aulas de Khan devem ter abertura de 5 minutos na lousa e fechamento com relatórios.

---

## 7. EXEMPLOS DE SAÍDA CORRETA VS. INCORRETA

### 7.1 Cálculo de Volume do Cilindro
* **❌ INCORRETO:** *"Aplicar a fórmula V = pi * r^2 * h e encontrar o resultado."*
* **✅ CORRETO:** *"Foco no conteúdo: Desenhar o cilindro na lousa, identificando o raio da base e a altura. Demonstrar como a área da base circular se propaga ao longo da altura para formular a equação do volume."*

---

## 8. CHECKLIST DE VALIDAÇÃO PÓS-GERAÇÃO

```python
def validar_plano_matematica(plano: dict) -> list[str]:
    erros = []
    for aula in plano.get('aulas', []):
        if "geometria" in aula['titulo'].lower() and "desenhar" not in aula['metodologia'].lower():
            erros.append(f"Aula {aula['numero']}: Falta indicação de desenhar figura na lousa em Geometria.")
    return erros
```

---

## 9. APÊNDICE — ORDEM DE IMPLANTAÇÃO RECOMENDADA
1. Implementar o motor de 3 etapas fixas de abertura-prática-fechamento para Khan Academy.
2. Adicionar esboço de lousa obrigatório em Geometria.
3. Integrar verificação de equações.
