# Planos Luan

Sistema em **Python/Streamlit** que gera **planos de aula mensais em Word (.docx)** para o Professor Luan e sua equipe. Ele organiza o calendário real de cada professor, localiza os PDFs pedagógicos, extrai conteúdos e habilidades (BNCC / Currículo Paulista), aplica metodologia ativa com ou sem IA, preenche os modelos Word padronizados e registra tudo em um banco SQLite local.

- **Versão do gerador:** `1.2.14` (`core/revisao_final.py`)
- **Última atualização desta documentação:** 03/10/2026
- **Testes:** 853 coletados (828 aprovados e 25 ignorados na última execução completa, em 03/10/2026)

## Abas da interface

| Aba | Para que serve |
|---|---|
| **Planos gerais** | Geração de planos de salas regulares (Ensino Fundamental e Médio) |
| **CDP-EF/EM** | Planos do Centro de Detenção Provisória (turmas C, H, J e E) |
| **EJA** | Educação de Jovens e Adultos (Língua Inglesa, Biologia, Liderança e Oratória) |
| **Cadastro** | Professores, turmas, horários e dados administrativos |
| **Diagnóstico** | Inspeção técnica dos modelos e da qualidade metodológica |
| **Histórico** | Consulta e download dos planos já gerados |
| **Conferência Mensal** | Escolha o professor e o mês: ✅ planos feitos × ⬜ pendentes |

> A **pasta do mês** em `Planos feitos\PROFESSOR\DISCIPLINA\MES\` define o mês de cada plano, e não a data em que ele foi gerado.

## Como executar

```powershell
# Ativar o ambiente virtual
.\.venv\Scripts\Activate.ps1

# Instalar dependências (primeira vez)
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Abrir o sistema
.\.venv\Scripts\streamlit.exe run planos_luan_app.py
```

Atalhos para o dia a dia (Windows): `AbrirPLANOS_LUAN.ps1`, `ABRIR_PLANOS_LUAN.vbs`, `ReiniciarPLANOS_LUAN.bat`, `FecharPLANOS_LUAN.bat` e `InstalarPLANOS_LUAN.bat`.

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -q
```

## Estrutura do repositório

```text
planos_luan_app.py      Ponto de entrada (Streamlit), menu e estado
config.py               Caminhos oficiais e configurações
core/                   Regras, pipeline de geração, IA, banco e calendário
core/lib/               Inteligência pedagógica (metodologia, acompanhamento, acessibilidade...)
ui/                     Telas modulares (cadastro, histórico, conferência mensal...)
docx_generator/         Preenchimento dos modelos Word (regular e CDP/EJA)
templates/              Modelos Word (MODELOEGLE, MODELOPADRE, MODELOCDP)
tests/                  Testes automatizados (pytest), inclusive tests/unit/
```

## Pastas de dados (fora do Git)

Os dados ficam em `C:\Users\LuanDias\PLANOS_LUAN_DADOS`, definidos em `config.py`:

| Pasta / arquivo | Conteúdo |
|---|---|
| `planos_luan.db` | Banco SQLite (modo WAL) |
| `PDF_AULAS` | PDFs e DOCX pedagógicos por disciplina e ano |
| `Planos feitos` | DOCX finais: `PROFESSOR\DISCIPLINA\MES\arquivo.docx` |
| `historico_docx` | Cópias de arquivos do histórico |
| `REFERENCIAS_METODOLOGICAS` | Referências metodológicas |

> Nunca crie fallbacks para OneDrive, Documentos ou pastas antigas.

## Regras pedagógicas principais

- Metodologia em 4 etapas (`list[dict]` com `titulo` e `texto`): *Para começar*, *Foco no conteúdo*, *Na prática* e *Encerramento*.
- Limite por etapa: **300 caracteres** (sala regular sem IA) e **350** (EJA e DOCX de referência), sempre com corte natural (`limitar_texto_natural()`).
- **CDP:** sem internet, celular ou computador; foco em quadro, material impresso e caderno.
- **EJA:** linguagem adulta, ligada ao mundo do trabalho.
- O DOCX pedagógico na pasta dos PDFs é a fonte prioritária da metodologia, do acompanhamento e da acessibilidade.

## Documentação do projeto

| Arquivo | Conteúdo |
|---|---|
| [AGENTS.md](AGENTS.md) | Regras operacionais completas para agentes e mantenedores |
| [GEMINI.md](GEMINI.md) | Contexto resumido para o agente Gemini |
| [CHANGELOG.md](CHANGELOG.md) | Histórico de atualizações |
| [AUDITORIA_SISTEMA_2026-10-03.md](AUDITORIA_SISTEMA_2026-10-03.md) | Auditoria do sistema e pendências conhecidas |
| `DOCUMENTACAO_SISTEMA_PLANOS_LUAN.docx` | Manual de arquitetura, funcionalidades e regras de negócio |
| `DOCUMENTACAO_ESTRUTURA_CORE_PLANOS_LUAN.docx` | Referência técnica da estrutura `core/` |
| [PLANOS_LUAN_ENTERPRISE_LITE.md](PLANOS_LUAN_ENTERPRISE_LITE.md) | Proposta de evolução arquitetural gradual |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Código de conduta |

## Licença

Consulte o arquivo [LICENSE](LICENSE).
