# AGENTS.md — Sistema Planos Luan
> Arquivo de instrução para o agente Codex. Leia este documento integralmente antes de qualquer tarefa.

---

## 🎯 VISÃO GERAL DO PROJETO

**Planos Luan** é uma aplicação Python/Streamlit para geração automatizada de planos de aula para professores e coordenadores escolares. O sistema extrai conteúdo de PDFs pedagógicos, classifica o tipo de aula, gera metodologia estruturada (com ou sem IA), preenche documentos Word (.docx) e persiste tudo em SQLite.

- **Versão atual do gerador:** 1.2.10
- **Stack principal:** Python 3.12, Streamlit, python-docx, pdfplumber, SQLite (WAL), Pydantic v1/v2
- **Frontend:** `planos_luan_app.py` (Streamlit)
- **Backend:** módulos em `core/` e `docx_generator/`

---

## 🗂️ ARQUITETURA E MÓDULOS PRINCIPAIS

### Pipeline de Geração (ordem de execução)
```
PDF/PPTX
  └─► contexto_aula_pdf.py       → prepara contexto completo da aula
        └─► extrator_pdf.py      → extrai texto, habilidade BNCC, conceito, recursos
        └─► classificador.py     → detecta perfil disciplinar e tipo de aula
  └─► lote.py                    → orquestrador principal (3146 linhas — monolítico)
        └─► metodologia.py       → MotorMetodologico — gera metodologia SEM IA
        └─► core/ia.py           → geração COM IA (OpenAI/Gemini)
        └─► higienizador_pedagogico.py → limpa termos incoerentes na metodologia
        └─► acompanhamento.py    → gera 3 itens de acompanhamento da aprendizagem
        └─► acessibilidade.py    → gera 3 itens de acessibilidade
        └─► qualidade_metodologica.py → sanitiza, naturaliza e consolida etapas
  └─► revisao_final.py           → auditoria pedagógica + confidence_score
  └─► validador_plano.py         → validações semânticas e de aderência ao PDF
  └─► docx_generator/preencher.py     → preenche template Word (modo PDF)
  └─► docx_generator/preencher_cdp.py → preenche template Word (modo CDP/EJA)
```

### Módulos de Suporte
| Módulo | Responsabilidade |
|---|---|
| `core/models.py` | Modelos Pydantic: `PlanoCompleto`, `PlanoAulaIA`, `EtapaMetodologia` |
| `core/database.py` | SQLite WAL, migrações versionadas, histórico de planos |
| `core/disciplinas.py` | Catálogo de disciplinas, modos CDP/PDF, classificação de turmas |
| `core/tecnicas.py` | Catálogo de técnicas Lemov por momento e perfil disciplinar |
| `core/progressao.py` | Variação determinística entre aulas sequenciais (blake2b) |
| `core/qualidade_metodologica.py` | Sanitização, correção de encoding, naturalização de texto |
| `core/revisao_final.py` | `revisar_aula_gerada()` — scoring e regeneração seletiva |

---

## 📐 CONVENÇÕES DE CÓDIGO OBRIGATÓRIAS

### 1. Estrutura da Metodologia
A metodologia é **sempre** uma `list[dict]` com as chaves `"titulo"` e `"texto"`:
```python
# CORRETO
metodologia = [
    {"titulo": "Para começar", "texto": "Iniciar a aula com..."},
    {"titulo": "Foco no conteúdo", "texto": "Apresentar o conceito..."},
    {"titulo": "Na prática", "texto": "Orientar a resolução..."},
    {"titulo": "Encerramento", "texto": "Finalizar com síntese..."},
]

# ERRADO — nunca usar strings soltas
metodologia = ["Iniciar a aula com...", "Apresentar o conceito..."]
```

### 2. Normalização de Texto
Sempre usar as funções do módulo `core/lib/classificador.py` para normalização:
```python
from core.lib.classificador import normalizar_texto
# Nunca implementar normalização própria inline
```

### 3. Correção de Encoding
Sempre usar `corrigir_mojibake()` antes de processar texto vindo de PDF:
```python
from core.qualidade_metodologica import corrigir_mojibake
texto_limpo = corrigir_mojibake(texto_bruto)
```

### 4. Banco de Dados
- **Sempre** usar `connection_scope()` ou `get_connection()` de `core/database.py`
- **Nunca** criar conexões SQLite diretamente
- **Sempre** manter `PRAGMA journal_mode=WAL` e `PRAGMA foreign_keys=ON`

### 5. Modelos Pydantic
- Usar `PlanoCompleto.from_any(dados)` para converter qualquer entrada em `PlanoCompleto`
- Usar `.to_dict()` para serializar antes de salvar ou passar para outras funções
- **Nunca** acessar campos do plano diretamente em dicts sem passar por `PlanoCompleto.from_any()`

### 6. Variação Determinística
Para qualquer seleção que precise variar entre aulas sem ser aleatória, usar `_indice_hash()` de `core/lib/progressao.py`:
```python
from core.lib.progressao import _indice_hash
idx = _indice_hash([disciplina, tema, str(indice_aula)], len(opcoes))
```

---

## 🚫 REGRAS ABSOLUTAS — NUNCA FAÇA ISSO

### ❌ NÃO altere o campo `_tentativas_regeneracao` sem cuidado
Em `revisao_final.py`, o campo `_tentativas_regeneracao` controla a proteção contra loop infinito na regeneração recursiva. Ele deve ser:
1. Lido com `.get("_tentativas_regeneracao", 0)` no início
2. Incrementado antes da chamada recursiva
3. Removido com `.pop()` apenas no retorno final (não intermediário)

### ❌ NÃO adicione penalizações duplas no `confidence_score`
Em `revisao_final.py`, cada critério de qualidade deve penalizar o score **uma única vez**. O padrão correto é:
```python
# CORRETO: uma única penalização proporcional
if aderencia < 80:
    penalidade = max(10, int(80 - aderencia))
    deducoes += penalidade

# ERRADO: penalização dupla (dedução + teto fixo)
deducoes += penalidade
aula["confidence_score"] = min(aula["confidence_score"], 75)  # NÃO FAZER
```

### ❌ NÃO use `return "literatura"` como fallback genérico no higienizador
Em `higienizador_pedagogico.py`, o fallback para Língua Portuguesa deve ser `"geral_nao_jornalistica"`, não `"literatura"`. Usar `"literatura"` como fallback causa substituição incorreta de termos jornalísticos válidos.

### ❌ NÃO consolide etapas de perfis especializados
A função `consolidar_quatro_etapas()` em `qualidade_metodologica.py` **não deve ser chamada** para os perfis:
- `"educacao_financeira"` — tem etapas específicas (Análise de caso, Cálculos financeiros, etc.)
- `"projeto_de_vida"` — tem etapas específicas (Ponto de partida, Compartilhamento, etc.)
- `"ingles"` — tem etapas específicas (Vocabulário, Listening, etc.)

### ❌ NÃO crie conexões SQLite fora de `core/database.py`
Toda interação com o banco deve passar pelas funções de `core/database.py`.

### ❌ NÃO use `re.sub()` com padrões não compilados em loops
Em `higienizador_pedagogico.py`, os padrões de `REGRAS_SUBSTITUICAO` devem ser pré-compilados no nível do módulo, não compilados a cada chamada.

### ❌ NÃO remova o campo `diagnostico_geracao` do `PlanoCompleto`
Este campo é usado pela UI para exibir o pipeline de transformação da metodologia (tabs: Rascunho Local → Resposta IA → Higienização → Final). Ele deve ser populado pelo `MotorMetodologico`.

---

## ⚠️ BUGS CONHECIDOS — NÃO REINTRODUZA

Os seguintes bugs foram identificados em auditoria e estão sendo corrigidos. Ao modificar os arquivos relacionados, verifique se as correções já foram aplicadas:

| Bug | Arquivo | Status |
|---|---|---|
| Penalização dupla de aderência ao PDF | `revisao_final.py` | 🔧 Pendente correção |
| Fallback `"literatura"` agressivo no higienizador | `higienizador_pedagogico.py` | 🔧 Pendente correção |
| Dead code: `elif perfil == "arte"` duplicado | `metodologia.py` (~linha 1670) | 🔧 Pendente remoção |
| Dead code: `pratica_oral` duplicado em LP EM | `metodologia.py` | 🔧 Pendente remoção |
| Mojibake em strings hardcoded (tipo `futureme`) | `acompanhamento.py` | 🔧 Pendente correção |
| `consolidar_quatro_etapas()` sem parâmetro `perfil` | `qualidade_metodologica.py` | 🔧 Pendente correção |
| Palavras-chave ignoradas silenciosamente | `revisao_final.py` | 🔧 Pendente correção |
| Falha silenciosa na extração de palavras-chave | `contexto_aula_pdf.py` | 🔧 Pendente correção |

---

## 🔑 CONCEITOS PEDAGÓGICOS ESSENCIAIS

Para trabalhar corretamente neste sistema, entenda estes conceitos:

### Perfis Disciplinares
O sistema classifica cada disciplina em um **perfil** que determina a estrutura da metodologia:
```
matematica | lingua_portuguesa_ef | lingua_portuguesa_em | leitura_redacao
ciencias_ef | biologia | quimica | fisica | historia | geografia
ingles | arte | projeto_de_vida | lideranca_oratoria
educacao_financeira | tecnologia_inovacao | sociologia | orientacao_estudos
```

### Tipos de Aula
Dentro de cada perfil, o sistema detecta o **tipo de aula** para selecionar frases específicas:
- LP EF: `leitura`, `producao_textual`, `argumentacao_debate`, `gramatica_contextualizada`, etc.
- Matemática: `algebra`, `geometria`, `funcoes`, `estatistica_probabilidade`, etc.
- Ciências EF: `analise_dados`, `modelagem_cientifica`, `pratica_experimental`, etc.

### Técnicas Lemov
O sistema usa técnicas pedagógicas específicas que aparecem em MAIÚSCULAS no texto:
- `VIREM E CONVERSEM` — discussão em duplas
- `TODO MUNDO ESCREVE` — registro individual
- `COM SUAS PALAVRAS` — síntese verbal
- `HORA DA LEITURA` — leitura orientada
- `DE OLHO NO MODELO` — exemplo comentado
- `PAUSE E RESPONDA` — verificação formativa
- `UM PASSO DE CADA VEZ` — explicação em etapas

### Modos CDP/EJA
Turmas CDP (Centro de Detenção Provisória) e EJA têm restrições especiais:
- **Proibido:** internet, celular, computador, trabalho em grupo, técnicas Lemov digitais
- **Obrigatório:** quadro, material impresso, oralidade mediada, registro no caderno
- A função `sanitizar_texto_cdp_estrito()` aplica essas restrições automaticamente

### Confidence Score
O `confidence_score` (0–100) indica a qualidade do plano gerado:
- **≥ 70:** Plano aceitável para entrega
- **< 70:** Aciona regeneração seletiva (apenas perfil `"historia"` atualmente)
- **Penalizações:** cada problema detectado deduz pontos do score base de 100

---

## 📁 ARQUIVOS SENSÍVEIS — CUIDADO REDOBRADO

| Arquivo | Por que é sensível |
|---|---|
| `core/revisao_final.py` | Controla o scoring final e regeneração recursiva |
| `core/higienizador_pedagogico.py` | Substituições incorretas contaminam toda a metodologia |
| `core/qualidade_metodologica.py` | 1225 linhas — mudanças têm efeito cascata em todo o sistema |
| `core/metodologia.py` | 2034 linhas — motor principal de geração sem IA |
| `core/lote.py` | 3146 linhas — orquestrador principal, muito acoplado |
| `core/models.py` | Modelos Pydantic usados em todo o sistema |
| `core/database.py` | Schema SQLite com migrações versionadas |
| `docx_generator/preencher.py` | Geração do Word final — bugs aqui afetam o produto entregue |

---

## 🧪 COMO TESTAR SUAS ALTERAÇÕES

### Testes Unitários Prioritários
Antes de qualquer PR, verifique manualmente estas funções críticas:

```python
# 1. Higienizador não deve substituir termos jornalísticos válidos
from core.higienizador_pedagogico import detectar_perfil_pedagogico_real
assert detectar_perfil_pedagogico_real("Elementos da notícia", "Língua Portuguesa") == "jornalistico_valido"
assert detectar_perfil_pedagogico_real("Modernismo brasileiro", "Língua Portuguesa") == "literatura"

# 2. Consolidação não deve destruir etapas de Educação Financeira
from core.qualidade_metodologica import consolidar_quatro_etapas
met_ef = [
    {"titulo": "Para começar", "texto": "..."},
    {"titulo": "Análise de caso", "texto": "..."},
    {"titulo": "Cálculos financeiros", "texto": "..."},
    {"titulo": "Encerramento", "texto": "..."},
]
resultado = consolidar_quatro_etapas(met_ef, perfil="educacao_financeira")
assert len(resultado) == 4  # Não deve perder etapas

# 3. Confidence score não deve ser penalizado duas vezes
from core.revisao_final import revisar_aula_gerada
# Score com aderência 75% não deve ser menor que 100 - (80-75) = 95
```

### Verificação de Mojibake
Após qualquer edição em arquivos de `core/`:
```bash
grep -rn "â€" core/ --include="*.py"
grep -rn "Ã" core/ --include="*.py" | grep -v "import\|#"
```

### Verificação de Dead Code
```bash
# Verificar se ainda existe o bloco duplicado de arte
grep -n "elif perfil == \"arte\"" core/metodologia.py
# Deve retornar apenas UMA ocorrência
```

---

## 🏗️ PLANO DE REFATORAÇÃO EM ANDAMENTO

O sistema está sendo refatorado em 3 sprints. Ao receber tarefas, verifique em qual sprint ela se encaixa:

### Sprint 1 — Correções Imediatas (baixo esforço, alto impacto)
- [ ] Corrigir fallback `"literatura"` → `"geral_nao_jornalistica"` no higienizador
- [ ] Remover dead code `elif perfil == "arte"` duplicado em `metodologia.py`
- [ ] Remover dead code `pratica_oral` duplicado em LP EM em `metodologia.py`
- [ ] Corrigir mojibake em strings hardcoded em `acompanhamento.py`
- [ ] Corrigir penalização dupla de aderência em `revisao_final.py`
- [ ] Adicionar parâmetro `perfil` em `consolidar_quatro_etapas()`

### Sprint 2 — Correções Estruturais (1–2 semanas)
- [ ] Normalizar campo `metodologia` no Pydantic via `field_validator`
- [ ] Pré-compilar regras regex do higienizador no nível do módulo
- [ ] Adicionar flag `extracao_palavras_chave_ok` no retorno de `contexto_aula_pdf.py`
- [ ] Implementar logging estruturado no `MotorMetodologico`
- [ ] Adicionar testes unitários para funções críticas

### Sprint 3 — Refatoração Estrutural (2–4 semanas)
- [ ] Decompor `lote.py` em módulos menores
- [ ] Decompor `qualidade_metodologica.py` em 4 arquivos especializados
- [ ] Refatorar `DependenciasContextoAulaPDF` (26 Callables → sub-dataclasses)
- [ ] Implementar cache de extração de PDF com `lru_cache` por hash SHA-256
- [ ] Expandir regeneração seletiva para outros perfis além de `"historia"`

---

## 💡 DICAS PARA O AGENTE

### Ao modificar a metodologia gerada
1. Sempre verifique o perfil disciplinar antes de alterar frases
2. Nunca remova etapas sem verificar se o perfil as exige
3. Mantenha a progressão: abertura → desenvolvimento → prática → encerramento
4. Técnicas Lemov devem aparecer em MAIÚSCULAS quando explicitadas

### Ao modificar o higienizador
1. Teste com temas jornalísticos (notícia, reportagem) em LP antes de alterar fallbacks
2. Cada perfil em `REGRAS_SUBSTITUICAO` tem ~20 padrões — compile-os no módulo
3. O fallback de LP deve ser `"geral_nao_jornalistica"`, nunca `"literatura"`

### Ao modificar o scoring (`revisao_final.py`)
1. Cada critério penaliza **uma única vez**
2. O `SCORE_MINIMO_ACEITAVEL = 70` não deve ser alterado sem discussão
3. A regeneração recursiva tem limite de 1 tentativa — não aumente sem adicionar proteção

### Ao modificar o banco de dados
1. Novas colunas devem ser adicionadas via `MIGRACOES` list em `database.py`
2. Nunca use `DROP TABLE` — sempre use `ALTER TABLE ADD COLUMN`
3. Mantenha os índices em `_criar_indices_banco()`

### Ao adicionar novos perfis disciplinares
1. Adicionar em `_DISCIPLINAS` em `disciplinas.py`
2. Adicionar em `TECNICAS_POR_PERFIL` em `tecnicas.py`
3. Adicionar em `_ACOMPANHAMENTO_POR_PERFIL_TIPO` em `acompanhamento.py`
4. Adicionar em `_FALLBACK_POR_PERFIL` em `acessibilidade.py`
5. Adicionar em `VERBOS_POR_PERFIL` em `qualidade_metodologica.py`
6. Adicionar em `_etapas_por_perfil()` em `metodologia.py`
7. Adicionar em `detectar_perfil_pedagogico_real()` em `higienizador_pedagogico.py`

---

## 📊 ESTRUTURA DO BANCO DE DADOS

```sql
-- Tabelas principais
professores (id, nome UNIQUE)
professor_turmas (id, professor_id FK, disciplina, turma, dia_semana,
                  horario, aulas_semana, arquivo_modelo, template_id,
                  componente_curricular)
historico_planos (id, professor_nome, disciplina, turma, bimestre,
                  data_geracao, arquivo_nome, arquivo_path)
configuracoes (chave PK, valor)
schema_version (versao PK)  -- controle de migrações
```

---

*AGENTS.md — Planos Luan v1.2.10 | Atualizado em 2026-07-08*