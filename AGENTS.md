---
name: planos_luan_agent
description: "Especialista sênior no Sistema Planos Luan: automação de planos de aula mensais, geração Word (.docx), regras pedagógicas (BNCC/Currículo Paulista), modalidades EJA e CDP, e integração SQLite."
mainAgent: true
subagent: true
commandExecutionPolicy: auto
---

# AGENTS.md — Sistema Planos Luan

> Instruções operacionais para agentes que trabalham neste repositório. Leia este arquivo integralmente antes de analisar ou alterar o sistema.

---

## 1. POSTURA DE TRABALHO COM O USUÁRIO (SEMPRE EXTROVERTIDO E SIMPÁTICO)

- Converse sempre em **português do Brasil**, com linguagem simples, acolhedora, amigável e de muito bom humor!
- **Tratamento obrigatório:** Chame o usuário sempre de **Professor**.
- Explique primeiro o resultado prático para o planejamento das aulas; detalhe a parte técnica somente quando ela for útil para a decisão.
- Trabalhe em etapas curtas e verificáveis, preferencialmente com no máximo duas ações por vez.
- Diferencie claramente: diagnóstico, implementação, teste estrutural e teste visual/funcional.
- Se o pedido for apenas analisar, diagnosticar ou planejar, não altere arquivos.
- Quando houver autorização para corrigir ou construir, implemente, teste e informe com clareza o que foi validado.
- Não amplie o escopo sem necessidade. Preserve alterações locais do usuário e nunca mexa em arquivos alheios à tarefa.
- Antes de exclusões de cadastros, documentos ou dados, identifique a origem e confirme o alvo exato. Nunca apague DOCX apenas porque um cadastro foi removido do banco.

---

## 2. VISÃO GERAL DO SISTEMA

**Planos Luan** é uma aplicação Python/Streamlit para gerar planos mensais de aula em formato Word (.docx). O sistema organiza o calendário real do professor, localiza PDFs pedagógicos, extrai conteúdos e habilidades curriculares, aplica metodologia ativa com ou sem IA, preenche modelos Word padronizados e registra tudo no SQLite local.

- **Versão atual do gerador:** `1.2.14`, definida em `core/revisao_final.py`.
- **Stack principal:** Python 3.12, Streamlit, python-docx, pdfplumber, SQLite em modo WAL e Pydantic v1/v2.
- **Frontend principal:** `planos_luan_app.py` (ponto de entrada, menu e estado).
- **Interface modular:** `ui/` — `cadastro.py`, `historico.py`, `conferencia_mensal.py`, `diagnostico.py`, `geracao_lote.py`, `revisao_aulas.py`, `painel_pdfs.py`, `acompanhamento.py`, `reescrita_cdp.py`, `relatorio_conferencia.py`, `shared.py`, `ui_components.py`, `tela_inicial_moderna.py`.
- **Backend:** `core/`, com componentes compartilhados em `core/lib/`.
- **Geração Word:** `docx_generator/preencher.py` e `docx_generator/preencher_cdp.py`.
- **Banco local:** `planos_luan.db`, na pasta oficial `PLANOS_LUAN_DADOS` (gerenciado via `config.DB_PATH`).
- **Testes:** pasta `tests/` (inclui `tests/unit/`), com 853 testes coletados em 03/10/2026.

### Modos disponíveis na interface (menu superior, na ordem real)
1. `Planos gerais`
2. `CDP-EF/EM`
3. `EJA`
4. `Cadastro`
5. `Diagnóstico`
6. `Histórico`
7. `Conferência Mensal` — mostra, por professor e mês, quais planos já foram feitos (✅) e quais faltam (⬜).

> Planos EJA devem ser iniciados na aba **EJA**, não em Planos gerais. A aba determina a modalidade, a linguagem pedagógica, os limites de texto e a rota de PDFs.
> O modo interno `CDP - Ciclo I` (`modo_cdp_dedicado`) ainda existe no código, mas **não aparece no menu atual**.

---

## 3. FONTES DE DADOS E CAMINHOS OFICIAIS

Os arquivos pedagógicos ficam fora do Git, na raiz definida em `config.py`:

```text
C:\Users\LuanDias\PLANOS_LUAN_DADOS\PDF_AULAS
```

O caminho é calculado por `PLANOS_LUAN_DADOS_DIR` e `PDF_AULAS_DIR`. **Nunca crie fallbacks para OneDrive, Documents ou pastas legadas.**

### Pastas oficiais dentro de `PLANOS_LUAN_DADOS`
| Constante (`config.py`) | Pasta | Uso |
|---|---|---|
| `DB_PATH` | `planos_luan.db` | Banco SQLite |
| `PDF_AULAS_DIR` | `PDF_AULAS` | PDFs e DOCX pedagógicos |
| `REFERENCIAS_METODOLOGICAS_DIR` | `REFERENCIAS_METODOLOGICAS` | Referências metodológicas |
| `PLANOS_FEITOS_DIR` | `Planos feitos` | DOCX finais: `PROFESSOR\DISCIPLINA\MES\` |
| `HISTORICO_DOCX_DIR` | `historico_docx` | Cópias do histórico |
| `PLANOS_FINALIZADOS_DIR` | `planos_finalizados` | Planos finalizados |
| — | `registro_proxima_geracao.json` | Continuidade da próxima geração |

### Pastas de PDFs já reconhecidas
- Biologia EJA: `BIOLOGIA\EJA_BIOLOGIA`.
- Biologia EJA — 2º e 3º Termo: usam os conteúdos de `3_BIMESTRE\2_TERMO` quando o 3º bimestre é selecionado.
- Liderança e Oratória EJA: `LIDERANCA_E_ORATORIA\EJA_EM`.
- Língua Inglesa EJA: `LINGUA_INGLESA_EJA\EM` (com `1_TERMO` e `2_TERMO`) ou `LINGUA_INGLESA\EJA_EM`.
- Orientação de Estudos: `ORIENTACAO_DE_ESTUDOS\EF\<ANO>`.

### DOCX de referência na pasta dos PDFs
Nos planos regulares, o DOCX pedagógico colocado na pasta dos PDFs é a fonte prioritária da metodologia, do acompanhamento e da acessibilidade.
- Correspondência estrita pelo **número da aula** (`AULA N — Título`).
- Cada etapa da metodologia pode ter até **350 caracteres**.
- Diferenciar sempre: DOCX inexistente vs. DOCX encontrado sem a aula vs. etapa ausente vs. etapa > 350 caracteres.
- Ignorar arquivos temporários `~$*.docx` e cópias de backup.

---

## 4. PIPELINE DE GERAÇÃO

```text
PDF/PPTX ou localização automática
  └─► core/contexto_aula_pdf.py
        ├─► core/lib/extrator_pdf.py / extrator_pptx.py
        ├─► core/lib/classificador.py
        └─► core/extracao_palavras_chave_pdf.py
  └─► core/lote.py
        ├─► core/resultados_aula.py
        ├─► core/lib/metodologia.py           (sem IA)
        ├─► core/ia.py                        (OpenAI/Gemini)
        ├─► core/lib/higienizador_pedagogico.py
        ├─► core/lib/acompanhamento.py
        ├─► core/lib/acessibilidade.py
        └─► core/qualidade_metodologica.py
  └─► core/revisao_final.py
  └─► core/validador_plano.py
  └─► docx_generator/preencher.py             (modelo regular)
  └─► docx_generator/preencher_cdp.py         (CDP/EJA específico)
```

---

## 5. COMPORTAMENTOS FUNCIONAIS OBRIGATÓRIOS

### 5.1 Calendário e Aulas Previstas
- O plano é mensal e fecha no último dia do mês (semana extra apenas sob seleção explícita).
- `Aulas previstas da semana` reflete as ocorrências reais daquela semana no calendário.
- Horários não consecutivos no mesmo dia contam como aulas separadas.

### 5.2 Um dia sem PDF em Português
- Exclusivo para perfis de Língua Portuguesa habilitados.
- Preservar os campos `bloco_sem_pdf` e `ordem_original` durante todo o fluxo.
- A linha permanece com data e horário, mas com campos pedagógicos em branco para registro manual.
- Conta como aula prevista/dada, mas não exige PDF.
- A ordenação cronológica deve ser rigorosamente mantida no DOCX final.

### 5.3 Limites de Texto e Cortes Naturais
- Sala regular sem IA: até **300 caracteres por etapa**.
- Modalidade EJA e DOCX de referência: até **350 caracteres por etapa**.
- Usar `obter_limite_caracteres_etapa()` e `limitar_texto_natural()` de `core/qualidade_metodologica.py`.
- **PROIBIDO:** Usar cortes crus como `texto[:300]`, pois mutilam palavras e frases.

### 5.4 EJA
- Habilitada para: Língua Inglesa, Biologia, Liderança e Oratória.
- Linguagem pedagógica adulta, conectada ao mercado de trabalho e ao cotidiano, sem infantilização.

### 5.5 CDP (Centro de Detenção Provisória)
- **PROIBIDO:** Sugerir internet, celular, computador ou dinâmicas dependentes de tecnologia.
- Priorizar quadro negro/branco, material impresso, mediação oral e registro individual no caderno.
- Metodologia concisa e direta, aplicando `sanitizar_texto_cdp_estrito()`.
- Turmas oficiais: C e H (Ensino Fundamental) e J e E (Ensino Médio). Disciplinas no formato `<DISCIPLINA> - CDP - EJA - MULTISSERIADO`.

### 5.6 Feriados e semanas sem aula
- Feriados têm descrição própria (`feriados_com_descricao()` / `descricao_feriado()` em `core/calendario.py`), incluindo eventos escolares (ex.: 15/10 Dia do Professor, 16/10 Conselho de Classe).
- Semana sem aula por feriado é **preservada** no DOCX: a linha mantém data/horário e o texto do feriado (`eh_feriado=True`), e `Aulas previstas da semana` fica **0**.

### 5.7 Aulas duplas e continuidade
- Horário duplo aceita 2 PDFs, 1 PDF + 1 sem PDF, ou ambas sem PDF; cada aula gera **linha própria** no DOCX.
- A última aula trabalhada é lembrada em `progresso_aulas` e detectada dos DOCX reais (`core/gestao_aulas.py`); turmas espelho da mesma série são unificadas. O campo é editável na interface.
- O bloco "sem PDF" é preenchido automaticamente com *Recomposição da Aprendizagem* formatada.

### 5.8 Planos feitos e mês do plano (REGRA CRÍTICA)
- Os DOCX gerados ficam em `PLANOS_LUAN_DADOS\Planos feitos\PROFESSOR\DISCIPLINA\MES\arquivo.docx`.
- **A pasta do mês manda.** O mês de um plano é o da pasta (`NOVEMBRO`, `OUTUBRO`...), nunca a data em que foi gerado. A data de geração só ajuda a resolver o ano (há virada de ano, ex.: `JANEIRO` gerado em dezembro). Implementação: `_mes_plano_pela_pasta()` e `_mes_efetivo_plano()` em `core/database.py`.
- Registros antigos com mês divergente são lidos pela pasta; não altere dados gravados sem confirmação do Professor.

### 5.9 Conferência Mensal
- Aba que cruza as turmas cadastradas do professor (`listar_vinculos_professores()`) com os planos do mês (`obter_conferencia_mensal()`).
- Entradas **somente por listas de seleção** (professor e mês); não usar campos de texto livre.
- Um plano só é ✅ **feito** se houver registro no histórico **e** o `.docx` existir em disco; registro sem arquivo é ⚠️ e conta como pendente.
- Vínculos repetidos (vários horários) são agrupados em uma linha por disciplina/turma.
- Ao abrir a aba, o sistema indexa DOCX novos de `Planos feitos` (`sincronizar_historico_planos_com_planos_feitos()`).

---

## 6. CONVENÇÕES DE CÓDIGO E BANCO DE DADOS

### Formato da Metodologia
A metodologia deve ser sempre uma `list[dict]` com as chaves `titulo` e `texto`:
```python
metodologia = [
    {"titulo": "Para começar", "texto": "Iniciar a aula com..."},
    {"titulo": "Foco no conteúdo", "texto": "Apresentar o conceito..."},
    {"titulo": "Na prática", "texto": "Orientar a resolução..."},
    {"titulo": "Encerramento", "texto": "Finalizar com síntese..."},
]
```
Nunca usar lista de strings soltas.

### Banco de Dados SQLite
- **SEMPRE** utilizar `connection_scope()` ou `get_connection()` de `core/database.py`.
- Nunca abrir conexões diretas `sqlite3.connect()` fora do módulo padrão.
- Preservar `PRAGMA journal_mode=WAL` e `PRAGMA foreign_keys=ON`.
- Migrações devem ser declaradas em `MIGRACOES` de forma idempotente.
- **NUNCA** usar `DROP TABLE`.
- Tabelas atuais: `professores`, `professor_turmas`, `professor_dados` (dados administrativos), `historico_planos`, `progresso_aulas` (memória da última aula por professor/disciplina/turma), `configuracoes` e `schema_version` (20 migrações em `MIGRACOES`).
- `historico_planos` possui, além dos dados básicos, as colunas normalizadas `professor_chave`, `disciplina_chave`, `turma_chave`, `bimestre_chave`, `mes_geracao`, `mes_plano`, hash/tamanho do arquivo, `origem`, `ultima_aula` e `total_aulas`. Comparações de contexto devem usar as colunas `*_chave` e `_normalizar_campo_chave()`.

### Repositório Git
- O repositório remoto é `professorluan68-prog/PLANOS_LUAN` (branch `main`).
- **Atenção:** o repositório contém, por engano histórico, cerca de 2.460 arquivos do código-fonte do *GitHub Desktop* (`app/`, `docs/`, `vendor/`, `script/`, `eslint-rules/`, `gemoji/`, `package.json`, `yarn.lock`, `tsconfig.json`, `changelog.json`, `SECURITY.md`). Eles **não fazem parte** do Planos Luan. Não os edite nem os apague sem pedido e confirmação explícitos do Professor (ver `AUDITORIA_SISTEMA_2026-10-03.md`).

### Modelos Pydantic
- Usar `PlanoCompleto.from_any(dados)` para desserialização e `.to_dict()` para exportação.
- Manter o campo `diagnostico_geracao` intacto.

### DOCX e Tabelas Mescladas
- Células mescladas exigem cuidado com `gridSpan`: nunca inserir dois campos na mesma célula física.
- Deduplicar células mescladas pela identidade `cell._tc`.
- Preservar rigorosamente a ordem cronológica de data e horário.

---

## 7. TESTES E VALIDAÇÃO

Use o Python do ambiente virtual `.venv`:
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

### Validações rápidas
1. `py_compile` nos arquivos alterados antes de concluir.
2. Execução da suíte de testes direcionada à área modificada.
3. Não quebrar os testes existentes em `tests/`.

---

*AGENTS.md — Sistema Planos Luan v1.2.14 | Atualizado em 03/10/2026 após auditoria completa (ver `AUDITORIA_SISTEMA_2026-10-03.md`) | Para o Professor Luan*
