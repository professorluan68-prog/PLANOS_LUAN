# GEMINI.md — Contexto Operacional do Sistema Planos Luan

> Atualizado em Outubro de 2026. Versão do gerador: **1.2.14** (`core/revisao_final.py`).

## 1. Visão Geral

O **PLANOS LUAN** é um sistema completo e automatizado para elaboração, estruturação e preenchimento de planos de aula mensais e Planos Educacionais Individualizados (PEI) em formato Word (.docx), integrando materiais digitais oficiais da SEDUC-SP / Centro de Mídias (PDFs de slides), modelos de gabaritos escolares e cadastros docentes.

A interface gráfica opera em **Streamlit** (tema Dark Mode) com geração inteligente via **Google Gemini API** (`google-genai`), **OpenAI** ou **modo determinístico sem IA**.

### Menu Oficial da Aplicação (Ordem Real das Abas)
1. `Planos gerais` — Geração individual de planos regulares com pré-visualização de aulas e PDFs.
2. `CDP-EF/EM` — Geração específica para Centro de Detenção Provisória (regime fechado, sem tecnologia).
3. `EJA` — Geração para Educação de Jovens e Adultos (linguagem madura e contextualizada).
4. `PEI Inclusão` — Motor autônomo para estudantes elegíveis da Educação Especial.
5. `Geração em Lote` — Automação em massa por varredura de pastas de professores.
6. `Cadastro` — Gerenciamento de docentes, disciplinas, turmas e matrizes horárias.
7. `Diagnóstico` — Verificação de modelos Word (.docx), caminhos e integridade de ambiente.
8. `Histórico` — Consulta, download e rastreabilidade dos planos gerados.
9. `Conferência Mensal` — Matriz visual de conformidade por professor e mês (✅ Feito / ⬜ Pendente).

---

## 2. Stack Tecnológica e Ferramentas

* **Python 3.12** com ambiente virtual isolado em `.venv`.
* **Streamlit** (+ `streamlit-option-menu`) — Interface web moderna com gerenciamento em `st.session_state`.
* **python-docx** — Preenchimento de gabaritos Word, tabelas dinâmicas e sanitização de caracteres OpenXML.
* **PyMuPDF (`fitz`) / pdfplumber / pytesseract** — Extração veloz de texto e OCR para slides de aula.
* **SQLite em modo WAL** — Banco relacional (`PLANOS_LUAN_DADOS/planos_luan.db`) de alta concorrência.
* **Google Gemini API (`google-genai`)** — Geração com `system_instruction` nativa e `response_schema=PlanoAulaIA`.
* **pytest** — Suíte de testes automatizados com mais de 850 testes unitários e de integração.

---

## 3. Comandos Essenciais de Operação e Desenvolvimento

Execute todos os comandos no terminal **PowerShell** a partir da raiz do projeto (`C:\Users\LuanDias\PLANOS_LUAN`):

### 3.1 Inicialização e Gerenciamento do Servidor
```powershell
# Ativar ambiente virtual oficial
.\.venv\Scripts\Activate.ps1

# Iniciar o sistema Streamlit (Porta padrão 8501, modo estável)
.\.venv\Scripts\streamlit.exe run planos_luan_app.py --server.port 8501

# Atalhos rápidos oficiais do sistema:
.\AbrirPLANOS_LUAN.ps1       # Inicia ambiente e abre navegador
.\ReiniciarPLANOS_LUAN.ps1   # Mata instâncias presas e reinicia o Streamlit
.\FecharPLANOS_LUAN.ps1      # Encerra graciosamente o processo
```

### 3.2 Execução sem Interface Gráfica (Motor CLI em Lote)
```powershell
# Gerar planos de um mês completo via terminal
.\.venv\Scripts\python.exe planos_luan_cli.py --mes "OUTUBRO" --bimestre "4º Bimestre" --modo "Sem IA"

# Gerar planos com IA Gemini para um professor específico
.\.venv\Scripts\python.exe planos_luan_cli.py --professor "HELOÍSA" --mes "OUTUBRO" --modo "Gemini"
```

### 3.3 Testes e Validação de Código
```powershell
# Validar sintaxe após alterações (obrigatório antes de commitar)
.\.venv\Scripts\python.exe -m py_compile planos_luan_app.py core/ia.py core/gerador_pei.py

# Executar testes da suíte completa de forma rápida
.\.venv\Scripts\python.exe -m pytest tests/ -q

# Testar áreas críticas isoladas:
.\.venv\Scripts\python.exe -m pytest tests/test_database.py -v           # Banco e migrações
.\.venv\Scripts\python.exe -m pytest tests/test_qualidade_metodologica.py -v # Regras de 350 chars
.\.venv\Scripts\python.exe -m pytest tests/test_docx_generator.py -v     # Geração de Word
```

### 3.4 Diagnóstico e Manutenção do Banco SQLite
```powershell
# Verificar integridade física do banco de dados
.\.venv\Scripts\python.exe -c "from core.database import get_connection; conn=get_connection(); print(conn.execute('PRAGMA integrity_check;').fetchall()); conn.close()"

# Forçar sincronização imediata do histórico com os arquivos DOCX em disco
.\.venv\Scripts\python.exe -c "from core.database import sincronizar_historico_planos_com_planos_feitos; sincronizar_historico_planos_com_planos_feitos()"

# Criar backup manual de segurança do banco
Copy-Item C:\Users\LuanDias\PLANOS_LUAN_DADOS\planos_luan.db "C:\Users\LuanDias\PLANOS_LUAN_DADOS\backups_planos_luan\planos_luan_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"
```

### 3.5 Limpeza Preventiva de Arquivos Temporários
```powershell
# Remover arquivos temporários do Word que travam a leitura de pastas
Get-ChildItem -Path C:\Users\LuanDias\PLANOS_LUAN_DADOS -Filter "~$*.docx" -Recurse | Remove-Item -Force

# Remover travas residuais de processamento em lote
Remove-Item -Path "lock_processamento.txt" -ErrorAction SilentlyContinue
```

---

## 4. Diretórios Oficiais e Fontes de Dados

Os dados operacionais e arquivos finais ficam armazenados em `PLANOS_LUAN_DADOS` (fora do versionamento Git):

| Diretório Oficial | Finalidade |
| :--- | :--- |
| `C:\Users\LuanDias\PLANOS_LUAN` | Repositório oficial do código-fonte |
| `C:\Users\LuanDias\PLANOS_LUAN_DADOS` | Raiz de todos os dados locais e operacionais |
| `...\PLANOS_LUAN_DADOS\planos_luan.db` | Banco relacional SQLite principal |
| `...\PLANOS_LUAN_DADOS\PDF_AULAS` | Acervo de PDFs de slides organizados por disciplina e ano |
| `...\PLANOS_LUAN_DADOS\Planos feitos` | Documentos DOCX finalizados: `PROFESSOR\DISCIPLINA\MES\*.docx` |
| `...\PLANOS_LUAN_DADOS\PASTA MESTRE - PLANOS PEI` | Gabaritos em branco e `Textos_Adaptados.md` de inclusão |
| `...\PLANOS_LUAN_DADOS\historico_docx` | Cópias versionadas de segurança |
| `...\PLANOS_LUAN_DADOS\REFERENCIAS_METODOLOGICAS` | Arquivos DOCX de metodologias por componente |
| `templates/` (na raiz do projeto) | Modelos Word padronizados (`MODELOEGLE.docx`, `MODELOPADRE.docx`, `MODELOCDP.docx`) |

> **Atenção Inegociável:** Nunca configure fallbacks para caminhos de OneDrive ou pastas antigas de downloads. A orquestração dinâmica de caminhos é centralizada exclusivamente em `config.py`.

---

## 5. Regras de Ouro para o Agente Gemini

1. **Tratamento Obrigatório:** Dirija-se ao usuário sempre como **Professor**, com postura prestativa, bem-humorada, comunicativa e resolutiva.
2. **Ambiente Python Estrito:** Use sempre `.\.venv\Scripts\python.exe`. Nunca instale pacotes no escopo global do sistema.
3. **Limite Crítico de Caracteres (350 caracteres):** Cada etapa metodológica (`Para começar`, `Foco no conteúdo`, `Na prática`, `Encerramento`) deve conter no **MÁXIMO 350 caracteres**. Use sempre cortes em finais de frases naturais com `limitar_texto_natural()`; nunca faça cortes crus `[:350]`.
4. **Formato da Metodologia:** Estrutura obrigatória de `list[dict]` com as chaves `titulo` e `texto`.
5. **Técnicas Ativas LEMOV em Caixa Alta:** Destaque termos pedagógicos oficiais em maiúsculas (`VIREM E CONVERSEM`, `TODO MUNDO ESCREVE`, `COM SUAS PALAVRAS`, `HORA DA LEITURA`, `DE OLHO NO MODELO`).
6. **Módulo PEI (Inclusão):**
   - Extraia códigos da BNCC tanto do Ensino Fundamental (`EF`) quanto do Ensino Médio (`EM`) usando `re.findall(r'\(?(?:EF|EM|EI)\d{2}[A-Z0-9]{2,6}\)?', texto)`.
   - Aplique sempre sanitização estrita de XML antes de escrever nas células do Word para evitar documentos corrompidos.
7. **Regra de Ouro do Mês:** **A pasta do mês manda.** O mês de um plano é determinado pelo nome da pasta física em `Planos feitos` (`OUTUBRO`, `NOVEMBRO`), e nunca pela data em que o script foi executado.
8. **Disciplina em Maiúsculas no Banco:** Ao consultar ou salvar no SQLite, o campo `disciplina` deve estar rigorosamente em **UPPERCASE** (`LÍNGUA PORTUGUESA`, `HISTÓRIA`, `CIÊNCIAS`).
9. **Proteção de Processamento:** Ao executar ou criar rotinas de lote, crie o arquivo `lock_processamento.txt` para impedir que a thread `_monitorar_sessoes_ativas()` encerre o servidor prematuramente.
10. **Preservação de Dados e Git:** Não exclua registros do banco de dados ou arquivos `.docx` sem confirmação explícita. Não edite a pasta histórica do GitHub Desktop (`app/`, `vendor/`) presente no repositório.
