# PLANOS_LUAN — Contexto do Sistema

## O que é este projeto
Sistema de montagem automatizada de planos de aula em Word (.docx) a partir de
materiais digitais em PDF, modelos de plano existentes e cadastros de professores.
Utiliza Streamlit como interface web e suporta IA (OpenAI/Gemini) para extração
inteligente do conteúdo dos PDFs.

## Stack Tecnológica
- **Python 3.x** com ambiente virtual em `.venv_PLANOS_LUAN`
- **Streamlit 1.28.1** — interface web (`planos_luan_app.py`)
- **pdfplumber 0.10.3** — leitura de PDFs
- **python-docx 0.8.11** — geração de Word
- **SQLite** — banco de dados (`planos_luan.db`)
- **OpenAI / Google Gemini** — extração via IA
- **pytest** — testes

## Como Executar
```bash
# Ativar ambiente virtual
.venv_PLANOS_LUAN\Scripts\activate

# Rodar o sistema
streamlit run planos_luan_app.py

# Rodar testes
pytest tests/ -v
```

## Arquitetura Principal

### Fluxo de Dados
```
PDFs → extrator_pdf.py → lote.py → ia.py (opcional) → preencher.py → .docx final
```

### Módulos Críticos (NÃO modificar sem testes)
- `core/lote.py` — Motor principal (6000+ linhas). Modificar com EXTREMO cuidado.
- `core/ia.py` — Ponte com IA. `PlanoAulaIA` é Pydantic BaseModel com `EtapaMetodologia`.
- `core/database.py` — Schema SQLite (professores, professor_turmas, historico_planos, configuracoes). Migrações manuais.
- `docx_generator/preencher.py` — Preenche templates Word (.docx).
- `docx_generator/preencher_cdp.py` — Preenche templates CDP/EJA.

### Módulos de Regras Pedagógicas (core/lib/)
- `metodologia.py` (42KB) — Regras de metodologia por disciplina
- `acompanhamento.py` (35KB) — Geração de acompanhamento da aprendizagem
- `acessibilidade.py` (32KB) — Adaptações e inclusão
- `classificador.py` (13KB) — 18 perfis disciplinares, tipos de aula, detecção de recursos
- `extrator_pdf.py` (17KB) — Extração semântica (13 campos estruturados)
- `progressao.py` (4KB) — Variação entre aulas para evitar repetição
- `tecnicas.py` (10KB) — Banco de técnicas pedagógicas (LEMOV, etc.)

### Outros Módulos Core
- `core/cdp.py` (44KB) — Motor dos planos CDP com planilhas Excel/Word
- `core/qualidade_metodologica.py` (22KB) — Revisão de qualidade com score mínimo
- `core/validador_plano.py` (7KB) — Validação de aulas geradas
- `core/disciplinas.py` — 23 disciplinas, 3 modos (pdf, cdp, cdp_fundamental)
- `core/professores_planos.py` — Leitor das pastas dos professores
- `core/referencias_metodologia.py` — Referências metodológicas por disciplina
- `core/prompts_por_disciplina.py` — Orientações de prompt por disciplina para IA
- `core/calendario.py` — Gerenciamento de datas e feriados

### Configuração Central
- `config.py` — Caminhos, limites, modelos de IA padrão

## Regras para o Agente

### SEMPRE faça:
- Rodar `pytest tests/ -v` após qualquer mudança em `core/`
- Usar o ambiente virtual: `.venv_PLANOS_LUAN\Scripts\python.exe`
- Manter docstrings e comentários existentes em português
- Testar encoding de arquivos (muitos CSV são latin-1/cp1252, não UTF-8)
- Usar `processar_plano_ia()` como API pública para geração via IA
- Usar `normalizar_texto()` de `core.lib.classificador` como função canônica de normalização

### NUNCA faça:
- Modificar `planos_luan.db` diretamente (use `core/database.py`)
- Remover funções de `core/lote.py` sem verificar dependências
- Alterar a estrutura de `PlanoAulaIA` sem atualizar todos os consumidores
- Usar `_montar_prompt()` diretamente (é privada, use `processar_plano_ia()`)
- Chamar `lote.py._normalizar()` em código novo (use `classificador.normalizar_texto()`)
- Assumir encoding UTF-8 para CSVs — sempre detectar ou usar fallback

### Atenção especial:
- `lote.py` tem versões duplicadas de `_normalizar()` e `_perfil_disciplina()` — prefira `classificador.py`
- Todos os PDFs em `D:\PDF novos` se chamam `AULA N.pdf` — diferenciar pela pasta (Disciplina/Turma)
- Templates Word: EGLE (padrão), PADRE, CDP — seleção automática em `core/modelos_docx.py`
- O CSV `mapa_arquivos.csv` tem 6 colunas: origem, destino, professor_inferido, disciplina, turma, aula_detectada

## Pastas Importantes
| Pasta | Conteúdo |
|---|---|
| `D:\PLANOS DE JUNHO` | Pasta principal de trabalho dos professores |
| `D:\PDF novos` | PDFs classificados por disciplina/turma (3978 arquivos, 20 disciplinas) |
| `D:\PDF novos\mapa_arquivos.csv` | Mapeamento completo de PDFs (origem → destino, disciplina, professor) |
| `D:\PDF novos\NAO_CLASSIFICADOS` | 388 PDFs ainda não classificados |
| `D:\BACKUPS_PLANOS_LUAN` | Backups automáticos |
| `D:\arquivonovo` | Módulo `improved_system.py` — orquestrador em lote via CSV |
| `templates/` | Modelos Word (MODELOEGLE, MODELOPADRE, MODELOCDP) |
| `Planos feitos/` | Planilhas CDP e habilidades |
| `REFERENCIAS_METODOLOGIA/` | Textos de referência metodológica por disciplina |
| `tests/` | Testes automatizados do sistema |

## Disciplinas do Sistema (23)
Arte, Biologia, Ciências, Educação Financeira, Educação Física, Filosofia,
Física, Geografia, História, Liderança e Oratória, Língua Inglesa,
Língua Portuguesa, Matemática, Orientação de Estudos, CDP-ENSINO FUNDAMENTAL,
CDP-ENSINO MÉDIO, CDP-Multisseriada, Projeto de Vida, Química,
Redação e Leitura, Sociologia, Tecnologia e Inovação, Outra

## Banco de Dados (SQLite)
- `professores` — id, nome (UNIQUE)
- `professor_turmas` — professor_id (FK), disciplina, turma, dia_semana, horario, aulas_semana, arquivo_modelo, template_id, componente_curricular
- `historico_planos` — professor_nome, disciplina, turma, data_geracao, arquivo_nome, arquivo_docx (BLOB)
- `configuracoes` — chave (PK), valor
