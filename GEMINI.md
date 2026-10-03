# GEMINI.md — Contexto do Sistema Planos Luan

> Atualizado em 03/10/2026 após auditoria completa. Versão do gerador: **1.2.14** (`core/revisao_final.py`).

## 1. Visão Geral
Sistema de montagem automatizada de planos de aula mensais em Word (.docx) a partir de materiais digitais (PDF/PPTX), modelos de plano pré-configurados e cadastros de professores.
Interface web moderna desenvolvida em **Streamlit** com suporte a extração inteligente via **Google Gemini** ou **OpenAI** (ou **sem IA**, por regras determinísticas).

Abas do menu (ordem real): `Planos gerais`, `CDP-EF/EM`, `EJA`, `Cadastro`, `Diagnóstico`, `Histórico` e `Conferência Mensal`.

---

## 2. Stack Tecnológica
- **Python 3.12** com ambiente virtual em `.venv`
- **Streamlit** (+ `streamlit-option-menu`) — interface web (`planos_luan_app.py` e `ui/`)
- **python-docx** — geração e preenchimento de documentos Word (.docx)
- **pdfplumber** / **pytesseract** / **python-pptx** — extração de conteúdos e habilidades
- **SQLite (WAL)** — banco relacional (`PLANOS_LUAN_DADOS/planos_luan.db`)
- **Google Gemini API** e **OpenAI** (`core/ia.py`, `core/ia_client.py`) — extração e aprimoramento pedagógico com IA, com retry
- **pytest** — suíte automatizada (`tests/` e `tests/unit/`, 853 testes coletados em 03/10/2026)

---

## 3. Comandos de Execução e Testes

```powershell
# Ativar ambiente virtual
.\.venv\Scripts\Activate.ps1

# Iniciar o sistema Streamlit
.\.venv\Scripts\streamlit.exe run planos_luan_app.py

# Executar testes rápidos
.\.venv\Scripts\python.exe -m pytest tests/ -q

# Validar sintaxe após alterações
.\.venv\Scripts\python.exe -m py_compile planos_luan_app.py
```

Atalhos de uso diário: `AbrirPLANOS_LUAN.ps1`, `ABRIR_PLANOS_LUAN.vbs`, `ReiniciarPLANOS_LUAN.bat/.ps1`, `FecharPLANOS_LUAN.bat/.ps1`, `InstalarPLANOS_LUAN.bat`.

---

## 4. Diretórios Oficiais do Sistema

| Diretório | Finalidade |
|---|---|
| `C:\Users\LuanDias\PLANOS_LUAN` | Repositório de código da aplicação |
| `C:\Users\LuanDias\PLANOS_LUAN_DADOS` | Dados locais, banco SQLite e históricos |
| `...\PLANOS_LUAN_DADOS\PDF_AULAS` | PDFs pedagógicos organizados por disciplina e ano |
| `...\PLANOS_LUAN_DADOS\Planos feitos` | DOCX finais, em `PROFESSOR\DISCIPLINA\MES\arquivo.docx` |
| `...\PLANOS_LUAN_DADOS\historico_docx` | Cópias de arquivos do histórico |
| `...\PLANOS_LUAN_DADOS\REFERENCIAS_METODOLOGICAS` | Referências metodológicas |
| `...\PLANOS_LUAN_DADOS\planos_luan.db` | Banco SQLite principal |
| `templates/` | Modelos Word (.docx) padronizados (MODELOEGLE, MODELOPADRE, MODELOCDP) |

> **Atenção:** Nunca configure fallbacks para caminhos de OneDrive ou pastas antigas. Os caminhos oficiais são gerenciados dinamicamente via `config.py`.

---

## 5. Arquitetura e Módulos Críticos

- `planos_luan_app.py` — Ponto de entrada da interface Streamlit, menu e gerenciamento de estado.
- `ui/` — Telas modulares: `cadastro`, `historico`, `conferencia_mensal`, `diagnostico`, `geracao_lote`, `revisao_aulas`, `painel_pdfs`, `acompanhamento`, `reescrita_cdp`, `relatorio_conferencia`, `shared`, `ui_components`, `tela_inicial_moderna`.
- `core/lote.py` — Orquestrador do processamento em lote.
- `core/ia.py` — Integração com Google Gemini e OpenAI via Pydantic (`PlanoAulaIA`).
- `core/database.py` — Conexões, migrações (20) e consultas SQLite. Usar sempre `connection_scope()`/`get_connection()`. Contém a conferência mensal e a regra do mês pela pasta.
- `core/calendario.py` — Dias úteis, feriados com descrição e eventos escolares.
- `core/gestao_aulas.py` — Detecção da última aula trabalhada a partir dos DOCX reais.
- `core/lib/classificador.py` — Classificação por perfis disciplinares e normalização canônica (`normalizar_texto`).
- `core/qualidade_metodologica.py` — Limites de caracteres e sanitização sem cortes crus.
- `docx_generator/preencher.py` — Preenchimento dos modelos Word regulares.
- `docx_generator/preencher_cdp.py` — Preenchimento dos modelos Word específicos para CDP e EJA.

### Tabelas do banco
`professores`, `professor_turmas`, `professor_dados`, `historico_planos` (colunas `*_chave`, `mes_plano`, hash, `ultima_aula`, `total_aulas`), `progresso_aulas`, `configuracoes`, `schema_version`.

---

## 6. Regras de Ouro para o Agente Gemini

1. **Tratamento:** Chame o usuário sempre de **Professor**, com postura extrovertida, prestativa e bem-humorada.
2. **Ambiente:** Use sempre o Python de `.\.venv\Scripts\python.exe`.
3. **Preservação de Dados:** Nunca exclua registros do banco ou documentos sem confirmação e contagem prévia.
4. **Metodologia:** Mantenha sempre a estrutura `list[dict]` com as chaves `titulo` e `texto`.
5. **Limites de Texto:** Máximo de 300 caracteres por etapa em sala regular e 350 caracteres em EJA e referências DOCX, usando `limitar_texto_natural()`.
6. **Git:** Respeite arquivos modificados localmente pelo usuário antes de qualquer alteração.
7. **Mês do plano:** a **pasta do mês** em `Planos feitos` define o mês do plano, nunca a data de geração.
8. **Conferência Mensal:** entradas só por listas de seleção; um plano só é "feito" se o `.docx` existir em disco.
9. **Repositório:** o Git contém arquivos do *GitHub Desktop* (`app/`, `docs/`, `vendor/`, `script/`...) que não pertencem ao sistema; não mexer sem confirmação (ver `AUDITORIA_SISTEMA_2026-10-03.md`).
