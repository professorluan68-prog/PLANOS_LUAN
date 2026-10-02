# GEMINI.md — Contexto do Sistema Planos Luan

## 1. Visão Geral
Sistema de montagem automatizada de planos de aula mensais em Word (.docx) a partir de materiais digitais (PDF/PPTX), modelos de plano pré-configurados e cadastros de professores.
Interface web moderna desenvolvida em **Streamlit** com suporte a extração inteligente via **Google Gemini** ou **OpenAI**.

---

## 2. Stack Tecnológica
- **Python 3.12** com ambiente virtual em `.venv`
- **Streamlit** — interface web (`planos_luan_app.py`)
- **python-docx** — geração e preenchimento de documentos Word (.docx)
- **pdfplumber** / **python-pptx** — extração de conteúdos e habilidades
- **SQLite (WAL)** — banco de dados relacional (`PLANOS_LUAN_DADOS/planos_luan.db`)
- **Google Gemini API** (`core/ia.py`) — extração e aprimoramento pedagógico com IA
- **pytest** — suíte de testes automatizados (`tests/`)

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

---

## 4. Diretórios Oficiais do Sistema

| Diretório | Finalidade |
|---|---|
| `C:\Users\LuanDias\PLANOS_LUAN` | Repositório de código da aplicação |
| `C:\Users\LuanDias\PLANOS_LUAN_DADOS` | Dados locais, banco SQLite e históricos |
| `C:\Users\LuanDias\PLANOS_LUAN_DADOS\PDF_AULAS` | PDFs pedagógicos organizados por disciplina e ano |
| `C:\Users\LuanDias\PLANOS_LUAN_DADOS\planos_luan.db` | Banco SQLite principal |
| `templates/` | Modelos Word (.docx) padronizados (MODELOEGLE, MODELOPADRE, MODELOCDP) |

> **Atenção:** Nunca configure fallbacks para caminhos de OneDrive ou pastas antigas. Os caminhos oficiais são gerenciados dinamicamente via `config.py`.

---

## 5. Arquitetura e Módulos Críticos

- `planos_luan_app.py` — Ponto de entrada da interface Streamlit e gerenciamento de estado.
- `core/lote.py` — Orquestrador do processamento em lote.
- `core/ia.py` — Integração com Google Gemini e OpenAI via Pydantic (`PlanoAulaIA`).
- `core/database.py` — Conexões e migrações SQLite. Usar sempre `connection_scope()`.
- `core/lib/classificador.py` — Classificação por perfis disciplinares e normalização canônica (`normalizar_texto`).
- `core/qualidade_metodologica.py` — Limites de caracteres e sanitização sem cortes crus.
- `docx_generator/preencher.py` — Preenchimento dos modelos Word regulares.
- `docx_generator/preencher_cdp.py` — Preenchimento dos modelos Word específicos para CDP e EJA.

---

## 6. Regras de Ouro para o Agente Gemini

1. **Tratamento:** Chame o usuário sempre de **Professor**, com postura extrovertida, prestativa e bem-humorada.
2. **Ambiente:** Use sempre o Python de `.\.venv\Scripts\python.exe`.
3. **Preservação de Dados:** Nunca exclua registros do banco ou documentos sem confirmação e contagem prévia.
4. **Metodologia:** Mantenha sempre a estrutura `list[dict]` com as chaves `titulo` e `texto`.
5. **Limites de Texto:** Máximo de 300 caracteres por etapa em sala regular e 350 caracteres em EJA e referências DOCX, usando `limitar_texto_natural()`.
6. **Git:** Respeite arquivos modificados localmente pelo usuário antes de qualquer alteração.
