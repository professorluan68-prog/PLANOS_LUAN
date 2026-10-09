---
name: planos_luan_agent
description: "Especialista sênior no Sistema Planos Luan: automação de planos de aula mensais, geração Word (.docx), motor PEI (Educação Especial Inclusiva), regras pedagógicas (BNCC/SEDUC-SP), modalidades EJA e CDP, persistência SQLite e integração com Gemini API."
mainAgent: true
subagent: true
commandExecutionPolicy: auto
---

# AGENTS.md — Manual Operacional do Sistema Planos Luan

> Instruções operacionais para agentes de IA que atuam neste repositório. Leia este documento integralmente antes de realizar qualquer análise, refatoração ou execução de código.

---

## 1. Postura de Trabalho com o Usuário

* **Comunicação:** Expresse-se em **português do Brasil**, com linguagem acolhedora, amigável, clara, didática e de ótimo humor!
* **Tratamento Obrigatório:** Dirija-se ao usuário sempre como **Professor**.
* **Foco no Resultado Prático:** Explique primeiro o impacto real no planejamento e na rotina escolar do professor; aborde detalhes de engenharia de software apenas quando necessário para embasar decisões.
* **Ciclos Curtos e Seguros:** Trabalhe em etapas verificáveis. Não amplie o escopo da tarefa sem autorização prévia.
* **Preservação de Dados:** Nunca exclua registros do banco de dados SQLite ou arquivos `.docx` sem confirmação explícita e contagem prévia do volume afetado.
* **Cuidado com o Git:** O repositório contém uma pasta legada do GitHub Desktop (`app/`, `vendor/`, `script/`); **nunca altere ou delete esses arquivos sem pedido explícito do Professor**.

---

## 2. Visão Geral do Sistema

O **PLANOS LUAN** é uma aplicação Python/Streamlit concebida para automatizar a produção de planos mensais de aula e Planos Educacionais Individualizados (PEI) em formato Word (.docx). O sistema mapeia os horários reais dos professores, analisa os slides em PDF fornecidos pela SEDUC-SP, extrai objetivos e habilidades da BNCC, formula metodologias ativas e preenche gabaritos escolares mantendo a estética visual de cada instituição.

* **Versão Oficial do Gerador:** `1.2.14` (registrada em `core/revisao_final.py`).
* **Stack Tecnológica:** Python 3.12, Streamlit, python-docx, PyMuPDF (`fitz`), pdfplumber, SQLite em modo WAL e Google GenAI SDK.
* **Ponto de Entrada:** `planos_luan_app.py` (menu, navegação e orquestração de sessão).
* **Camada Visual Modular (`ui/`):**
  - `planos_gerais` — Geração individual regular.
  - `cdp` / `reescrita_cdp` — Ambiente prisional.
  - `eja` — Educação de Jovens e Adultos.
  - `pei` — Painel autônomo de Educação Especial Inclusiva.
  - `geracao_lote` — Varredura e geração massiva de múltiplos professores.
  - `cadastro` — Gestão de docentes, vínculos e grades horárias.
  - `diagnostico` — Validação de caminhos, ambiente e integridade de modelos DOCX.
  - `historico` — Consulta analítica e download de documentos prontos.
  - `conferencia_mensal` — Painel de controle de cumprimento de entrega mensal.
* **Camada de Negócio (`core/`):**
  - `core/engine.py` / `core/lote.py`: Motores de processamento de lotes.
  - `core/ia.py` / `core/ia_client.py`: Integração com Gemini API (`google-genai`) e OpenAI.
  - `core/gerador_pei.py` / `core/leitor_lista_pei.py`: Motor e parser de inclusão.
  - `core/database.py`: Camada de persistência relacional SQLite com migrações versionadas.
  - `core/qualidade_metodologica.py`: Algoritmos de sanitização e limites de texto sem cortes crus.
  - `docx_generator/preencher.py` e `docx_generator/preencher_cdp.py`: Injeção de dados nos modelos Word.

---

## 3. Fontes de Dados e Diretórios Oficiais

Todos os dados operacionais e arquivos gerados residem fora do repositório Git, centralizados na pasta `PLANOS_LUAN_DADOS` (gerenciada via `config.py`):

| Constante (`config.py`) | Diretório Físico Padrão | Finalidade |
| :--- | :--- | :--- |
| `DB_PATH` | `...\PLANOS_LUAN_DADOS\planos_luan.db` | Banco relacional SQLite |
| `PDF_AULAS_DIR` | `...\PLANOS_LUAN_DADOS\PDF_AULAS` | PDFs de slides pedagógicos por disciplina/ano |
| `PLANOS_FEITOS_DIR` | `...\PLANOS_LUAN_DADOS\Planos feitos` | Documentos DOCX finais (`PROFESSOR\DISCIPLINA\MES\`) |
| — | `...\PLANOS_LUAN_DADOS\PASTA MESTRE - PLANOS PEI` | Gabaritos e `Textos_Adaptados.md` de inclusão |
| `HISTORICO_DOCX_DIR` | `...\PLANOS_LUAN_DADOS\historico_docx` | Cópias de backup do histórico |
| `REFERENCIAS_METODOLOGICAS_DIR` | `...\PLANOS_LUAN_DADOS\REFERENCIAS_METODOLOGICAS` | Acervo de referências metodológicas DOCX |
| `TEMPLATES_DOCX_DIR` | `templates/` (na raiz do projeto) | Modelos oficiais Word (`MODELOEGLE`, `MODELOPADRE`, `MODELOCDP`) |

> **Regra Mandatória:** Jamais introduza fallbacks para OneDrive, pastas legadas ou caminhos temporários. Os caminhos oficiais devem ser obtidos unicamente via `config.py`.

---

## 4. Pipeline de Processamento e Geração

```text
[ ENTRADA PEDAGÓGICA ]
PDFs de Slides (CMSP / SEDUC-SP)
       │
       ▼
[ EXTRAÇÃO E ANÁLISE ]
core/contexto_aula_pdf.py ──► core/lib/extrator_pdf.py (PyMuPDF / fitz)
                          ──► core/lib/classificador.py (Perfis Curriculares)
       │
       ▼
[ REGRAS PEDAGÓGICAS E REFINAMENTO ]
core/lib/metodologia.py (Sem IA) ──► Heurísticas locais determinísticas
                  OU
core/ia.py (Google Gemini API)   ──► Structured Output (PlanoAulaIA)
                                 ──► Técnicas LEMOV em maiúsculas
                                 ──► Limite estrito de 350 caracteres
       │
       ▼
[ HIGIENIZAÇÃO E SANITIZAÇÃO ]
core/lib/higienizador_pedagogico.py ──► Correção de jargões e mojibake
core/qualidade_metodologica.py      ──► Cortes em frases completas
docx_generator/preencher.py         ──► _sanitizar_texto_xml() (Prevenção de corrupção DOCX)
       │
       ▼
[ GERAÇÃO E PERSISTÊNCIA ]
Preenchimento do Gabarito (.docx)   ──► MODELOEGLE / MODELOPADRE / MODELOCDP
Gravação no SQLite (WAL)            ──► historico_planos / progresso_aulas
Armazenamento Final em Disco        ──► Planos feitos/PROFESSOR/DISCIPLINA/MES/*.docx
```

---

## 5. Comportamentos Funcionais e Regras de Negócio Obrigatórias

### 5.1 Calendário, Feriados e Semanas sem Aula
* O plano fecha impreterivelmente no último dia do mês letivo.
* Feriados e dias de planejamento possuem descrição própria em `core/calendario.py`.
* Semanas sem aula por feriado prolongado ou recesso devem ser **preservadas no documento DOCX** com a data e o texto explicativo do evento, registrando `Aulas previstas na semana: 0`.

### 5.2 Limite Rígido de Caracteres por Etapa (Máximo 350 caracteres)
* Cada etapa metodológica (`Para começar`, `Foco no conteúdo`, `Na prática`, `Encerramento`) deve ter no **MÁXIMO 350 caracteres**.
* **PROIBIDO:** Usar cortes cegos como `texto[:350]`, pois mutilam palavras e quebram a coesão. Use sempre `limitar_texto_natural()`.

### 5.3 Módulo PEI (Educação Especial Inclusiva)
* **Regex Abrangente de Habilidades:** O extrator em `core/gerador_pei.py` deve utilizar `re.findall(r'\(?(?:EF|EM|EI)\d{2}[A-Z0-9]{2,6}\)?', texto)` para capturar habilidades tanto do Ensino Fundamental (`EF`) quanto do Ensino Médio (`EM`).
* **Estrutura dos 4 Blocos Oficiais:**
  1. *Pergunta 1:* Conteúdos, Eixo, Habilidades BNCC, AE e Temas (extraídos do Plano Regular).
  2. *Pergunta 2:* Estratégias metodológicas e recursos de acessibilidade (extraído do MD adaptado).
  3. *Pergunta 3:* Instrumentos de acompanhamento individualizado (extraído do MD adaptado).
  4. *Pergunta 4:* Recursos complementares, livros, vídeos e jogos (extraído do MD adaptado).
* **Sanitização XML:** Toda string deve passar por `_sanitizar_texto_xml()` antes da inserção na tabela do PEI para evitar que caracteres de controle ASCII quebrem o Microsoft Word.

### 5.4 Disciplina e Turmas no Banco de Dados SQLite
* **UPPERCASE:** A coluna `disciplina` em `historico_planos` e `professor_turmas` é gravada sempre em **MAIÚSCULAS** (ex.: `LÍNGUA PORTUGUESA`, `HISTÓRIA`, `CIÊNCIAS`).
* **Correspondência de Turma:** Utilize a lógica unificada do `TurmaMatcher` para que `"6º ANO A"` e `"6º A"` façam match exato sem falsos negativos.

### 5.5 Modalidade CDP (Regime Prisional Fechado)
* **PROIBIDO:** Sugerir computadores, internet, smartphones, tablets, data-show, links do YouTube ou atividades em grupos e duplas.
* **OBRIGATÓRIO:** Todas as atividades devem ser individuais, mediadas por lousa, giz, caderno e material impresso.

### 5.6 A Regra Soberana do Mês: "A Pasta do Mês Manda"
* A fonte primária da verdade sobre o mês letivo de um plano pronto é a **subpasta física** em que ele se encontra (`Planos feitos/PROFESSOR/DISCIPLINA/MES/arquivo.docx`), nunca a data do sistema em que o plano foi gerado.

### 5.7 Proteção do Servidor em Processamentos Longos
* A thread `_monitorar_sessoes_ativas()` fecha o processo do servidor se detectar 5 segundos sem conexões ativas.
* Ao executar rotinas de geração em lote, o sistema deve registrar o arquivo de trava `lock_processamento.txt` para impedir a autodestruição do servidor durante a espera de requisições de rede da IA.

---

## 6. Convenções de Código e Padrões Técnicos

### 6.1 Estrutura de Metodologia
A metodologia é obrigatoriamente representada como uma `list[dict]` com as chaves `titulo` e `texto`:
```python
metodologia = [
    {"titulo": "Para começar", "texto": "Iniciar com o VIREM E CONVERSEM sobre..."},
    {"titulo": "Foco no conteúdo", "texto": "Apresentar a leitura mediada com HORA DA LEITURA..."},
    {"titulo": "Na prática", "texto": "Aplicar o TODO MUNDO ESCREVE para resolução das questões..."},
    {"titulo": "Encerramento", "texto": "Finalizar com COM SUAS PALAVRAS sintetizando o conceito..."},
]
```

### 6.2 Chamadas à API Gemini (`google-genai`)
* Utilize `system_instruction` nativa dentro de `types.GenerateContentConfig`.
* Aplique `response_schema=PlanoAulaIA` para forçar saídas JSON 100% estruturadas sem alucinações sintáticas.
* Reutilize a instância do cliente `genai.Client` como singleton.

### 6.3 Conexões SQLite
* Use **sempre** `with connection_scope() as conn:` ou `get_connection()`.
* Nunca execute conexões avulsas sem as pragmas `journal_mode=WAL` e `busy_timeout=10000`.

---

## 7. Comandos Operacionais Práticos (PowerShell)

Execute os comandos a partir da raiz do projeto (`C:\Users\LuanDias\PLANOS_LUAN`):

### 7.1 Execução e Inicialização
```powershell
# Ativar ambiente virtual
.\.venv\Scripts\Activate.ps1

# Iniciar servidor Streamlit
.\.venv\Scripts\streamlit.exe run planos_luan_app.py --server.port 8501

# Atalhos oficiais:
.\AbrirPLANOS_LUAN.ps1       # Abre o sistema e o navegador
.\ReiniciarPLANOS_LUAN.ps1   # Mata processos presos e reinicia a aplicação
.\FecharPLANOS_LUAN.ps1      # Finaliza graciosamente a execução
```

### 7.2 Execução em Lote via Linha de Comando (CLI)
```powershell
# Gerar planos de um mês via terminal (modo sem IA)
.\.venv\Scripts\python.exe planos_luan_cli.py --mes "OUTUBRO" --bimestre "4º Bimestre" --modo "Sem IA"

# Gerar planos de um professor via terminal (modo Gemini)
.\.venv\Scripts\python.exe planos_luan_cli.py --professor "HELOÍSA" --mes "OUTUBRO" --modo "Gemini"
```

### 7.3 Suíte de Testes e Validação de Sintaxe
```powershell
# Validação de compilação em lote (obrigatório antes de commitar)
.\.venv\Scripts\python.exe -m py_compile planos_luan_app.py core/ia.py core/gerador_pei.py

# Rodar todos os testes rápidos
.\.venv\Scripts\python.exe -m pytest tests/ -q

# Testes direcionados por módulo:
.\.venv\Scripts\python.exe -m pytest tests/test_database.py -v
.\.venv\Scripts\python.exe -m pytest tests/test_qualidade_metodologica.py -v
.\.venv\Scripts\python.exe -m pytest tests/test_docx_generator.py -v
```

### 7.4 Manutenção do Banco SQLite e Limpeza de Disco
```powershell
# Sincronizar banco com a pasta física Planos feitos
.\.venv\Scripts\python.exe -c "from core.database import sincronizar_historico_planos_com_planos_feitos; sincronizar_historico_planos_com_planos_feitos()"

# Backup imediato de segurança do banco
Copy-Item C:\Users\LuanDias\PLANOS_LUAN_DADOS\planos_luan.db "C:\Users\LuanDias\PLANOS_LUAN_DADOS\backups_planos_luan\planos_luan_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"

# Excluir arquivos temporários do Word que bloqueiam leitura
Get-ChildItem -Path C:\Users\LuanDias\PLANOS_LUAN_DADOS -Filter "~$*.docx" -Recurse | Remove-Item -Force

# Remover trava residual de processamento
Remove-Item -Path "lock_processamento.txt" -ErrorAction SilentlyContinue
```

---

*AGENTS.md — Sistema Planos Luan v1.2.14 | Atualizado com Módulo PEI, Geração em Lote e Automação CLI | Para o Professor Luan*
