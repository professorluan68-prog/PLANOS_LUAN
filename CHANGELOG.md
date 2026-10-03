# Histórico de Atualizações (CHANGELOG)

Este arquivo registra as alterações do sistema **Planos Luan** para que professores, mantenedores e outros agentes saibam o que foi corrigido ou implementado. Versão atual do gerador: **1.2.14** (`core/revisao_final.py`). As entradas mais recentes ficam no topo.

## [2026-10-03] - Conferência Mensal, mês pela pasta e auditoria documental
### Adicionado
- **ui/conferencia_mensal.py** e **planos_luan_app.py**: nova aba **Conferência Mensal**. O professor escolhe, em listas de seleção, o **professor** e o **mês**; o sistema lista todas as turmas/disciplinas cadastradas dele, marcando ✅ os planos feitos e ⬜ os pendentes, com barra de progresso, filtro "somente pendentes" e botão **Baixar** do DOCX. Um plano só conta como feito se existir registro no histórico **e** o arquivo `.docx` estiver em disco (registro sem arquivo aparece como ⚠️).
- **core/database.py**: `obter_conferencia_mensal()`, `obter_meses_conferencia()` e `_mes_efetivo_plano()`. Vínculos repetidos (vários horários da mesma disciplina/turma) são agrupados em uma única linha.
- **tests/test_conferencia_mensal.py**: testes do cruzamento turmas × planos, da regra de arquivo existente e da regra de mês pela pasta.
- A aba indexa automaticamente os DOCX novos de `Planos feitos` na primeira abertura de cada sessão (botão "Atualizar índice de arquivos" continua disponível).

### Alterado
- **core/database.py**: a **pasta do mês manda**. Em `PLANOS_FEITOS_DIR/PROFESSOR/DISCIPLINA/MÊS/arquivo.docx`, o mês do plano é lido da pasta (`_mes_plano_pela_pasta()`), e não da data de geração; a data só resolve o ano (com virada de ano, ex.: JANEIRO gerado em dezembro). `_metadados_historico()` aplica a regra em novas indexações; registros antigos são lidos pela pasta sem alteração dos dados gravados.
- **core/calendario.py / docx_generator/preencher.py**: feriados passam a ter descrição (`feriados_com_descricao`, `descricao_feriado`) e semanas sem aula por feriado são preservadas no DOCX com linhas em branco e **0 aulas previstas** (`eh_feriado`).

### Documentação
- Auditoria completa do sistema e atualização de `AGENTS.md`, `GEMINI.md`, `CHANGELOG.md`, `README.md`, `CODE_OF_CONDUCT.md`, `DOCUMENTACAO_SISTEMA_PLANOS_LUAN.docx` e `DOCUMENTACAO_ESTRUTURA_CORE_PLANOS_LUAN.docx`. Criado `AUDITORIA_SISTEMA_2026-10-03.md` com o diagnóstico do repositório.

## [2026-10-02] - Modularização da interface, bloco sem PDF e memória da última aula
### Adicionado
- **ui/** (modularização do `planos_luan_app.py`): telas separadas em `cadastro.py`, `historico.py`, `diagnostico.py`, `geracao_lote.py`, `revisao_aulas.py`, `painel_pdfs.py`, `acompanhamento.py`, `reescrita_cdp.py`, `relatorio_conferencia.py`, `shared.py`, `ui_components.py` e `tela_inicial_moderna.py`.
- **Subpastas por mês** em `Planos feitos` (`PROFESSOR/DISCIPLINA/MES/`) e observação específica de novembro (feriados).
- **Campo editável e memória persistente da última aula trabalhada** (tabela `progresso_aulas`), permitindo continuar a sequência de PDFs de onde parou.
- **docx_generator/preencher.py**: bloco "sem PDF" é preenchido automaticamente com *Recomposição da Aprendizagem* formatada.

### Corrigido
- **core/gestao_aulas.py**: detecção da última aula a partir dos DOCX reais; turmas espelho da mesma série são unificadas.

## [2026-09-20 a 2026-09-27] - CDP padronizado, EJA Inglês e aulas duplas
### Adicionado
- **CDP**: padronização completa do módulo (turmas oficiais C, H, J, E; disciplinas no formato `<DISCIPLINA> - CDP - EJA - MULTISSERIADO`; banco consolidado com deduplicação de vínculos). Documentações DOCX atualizadas em 23/09.
- **EJA**: rotas de 1º e 2º Termo de Língua Inglesa EJA (`LINGUA_INGLESA_EJA\EM`) e cadastro atualizado.
- **Calendário**: feriado/evento de 15/10 e 16/10 (Dia do Professor e Conselho de Classe).
- **Aulas duplas**: horários duplos com 2 PDFs; 1 PDF + 1 sem PDF gera duas linhas separadas no DOCX.

### Corrigido
- Preenchimento de **AE priorizado** e restauração de todas as semanas no lote do Word.
- Resolução de turma e bimestre em DOCX de referência para títulos das aulas.
- Compatibilidade de linguagem e extração de títulos nas referências CDP.
- `UnboundLocalError` causado por `import re` local.

## [2026-08-26 a 2026-09-06] - Dia sem PDF, continuidade pedagógica e Ciências
### Adicionado
- **Um dia sem PDF** por disciplina (semanal ou quinzenal), inclusive para Ciências e para aulas duplas (1 com PDF + 1 sem PDF, ou ambas sem PDF).
- Continuidade pedagógica e padronização da grade de horários; seleção de escolas vinculada à constante global `ESCOLAS`.
- Aba **CDP-EF/EM** e disciplinas Ciências/Matemática CDP, com parser de DOCX mais robusto.

### Corrigido
- Remoção do bloqueio de PDFs sem texto para Orientação de Estudos; resolução da referência de Orientação de Estudos de Matemática.
- Validador permite desenvolvimento curto quando há indicação de divisão/continuação.

## [2026-08-08] - Histórico mais completo
### Alterado
- **Histórico**: novos metadados (chaves normalizadas, `mes_plano`, hash e tamanho do arquivo, última aula e total de aulas), índices de consulta e progresso por contexto. PDFs automáticos protegidos. Dados administrativos piloto no cadastro (`professor_dados`).

## [2026-07-24 a 2026-07-30] - Fluxo pedagógico unificado e referências DOCX
### Alterado
- **Fluxo unificado**: DOCX literal sem IA; refinamento por IA até 350 caracteres. Limite padrão de 300 caracteres por etapa (350 em EJA e DOCX de referência); regra de bloqueio quando o DOCX tem etapas > 350 caracteres sem IA.
- Referências metodológicas centralizadas e flexibilizadas; cache por PDF/conteúdo reutilizado entre turmas paralelas; refino de DOCX pela IA protegido.
- DOCX restaurado como fonte dos planos regulares; continuidade de aulas informada pelo histórico.


## [2026-07-21] - Correção do Bug de Pydantic, Fallback de Leitura de Metodologia e Redução do Tamanho via IA
### Corrigido
- **core/models.py**: Ajustado o método `PlanoCompleto.from_any` para aceitar que o campo `metodologia` venha da IA como uma string (texto longo). Quando isso ocorre, o sistema agora divide a string por blocos (`\n\n`) e estrutura corretamente em lista de dicionários (`titulo` e `texto`). Isso elimina os erros de validação Pydantic (`A entrada deve ser uma lista válida`) quando o JSON da IA saía um pouco fora do formato.
- **core/seletor_referencias.py**: Resolvido o bug que impedia o sistema de achar o arquivo `Metodologias_...docx` quando o plano era gerado pelo Streamlit. Como o Streamlit joga o PDF numa pasta temporária (`temp_...`), a busca local por DOCX falhava. Adicionado o método `_resolver_caminho_original` que mapeia o caminho temporário de volta para o diretório `PDF_AULAS_DIR` e encontra a pasta e o DOCX corretos para injeção de metodologias (crucial para Orientação de Estudos).
- **core/referencias_orientacao_estudos.py**: Flexibilizada a Expressão Regular (Regex) que localizava a string `AULA X - Titulo` (`re.match(r'^AULA\s+(\d{1,2})[\s\-–—.:]*(.+)$')`) no arquivo docx. Agora o regex aceita se o professor não utilizar traço entre o número da aula e o título, reduzindo falhas na associação.

### Alterado
- **core/ia.py**: Atualizado o `_montar_prompt` adicionando uma regra UNIVERSAL e EXTREMAMENTE RESTRITIVA para o tamanho da metodologia gerada via Inteligência Artificial para todas as disciplinas. A regra exige textos de 15 a 40 palavras (2 a 3 linhas por etapa), impedindo que a IA explique os detalhes teóricos, foque apenas na ação docente e deixe a metodologia muito curta, telegráfica e objetiva.


## [2026-07-16] - Correção de leitura de planilha de habilidades (AE) e correção de regex da metodologia
### Corrigido
- **core/lote.py**: Removida a lógica redundante e frágil que usava o `pandas.read_excel` com `regex` para localizar a coluna contendo a palavra "HABILIDADE". Em vez disso, refatoramos a função `_enriquecer_com_planilha` para utilizar a lógica já consolidada de `core.ae_priorizado.carregar_base_habilidades_planilha`, que localiza corretamente a habilidade com base na formatação padrão do sistema para extração da Aprendizagem Essencial (AE). O retorno da função agora busca as chaves corretas `aula_numero` e `habilidade_textos` geradas pela função canônica.
- **docx_generator/preencher.py**: Corrigido um bug onde a geração dos planos perdia os títulos das metodologias (ex: "Para começar:", "Foco no conteúdo:"). A função `_texto_ja_comeca_com_etapa` possuía uma regex (`^[^:]{2,40}:\s*`) muito permissiva que casava com qualquer texto que tivesse um dois-pontos logo no início (por exemplo: `Realizar a leitura do texto "Migrar: um direito humano"`). A regex foi ajustada para `^[^:\"\'\.\?!]{2,40}:\s*`, ignorando aspas ou pontuações de fim de frase, para que o sistema apenas identifique como "título prefixado" quando for de fato um título limpo de etapa, prevenindo falsos-positivos com citações textuais na primeira etapa da metodologia.


## 2026-07-19 - Melhorias de UI e Metodologia Automática
- **UI**: Adicionado painel informativo na interface do Streamlit exibindo a pasta oficial de PDFs resolvida e a quantidade necessária de PDFs para gerar o plano.
- **Core**: Implementada busca automática por arquivos de metodologia (.docx ou .md) contendo a palavra METODOLOGIA diretamente na pasta do PDF oficial, eliminando a necessidade de atualizar o código toda vez que um arquivo de referência for adicionado.
