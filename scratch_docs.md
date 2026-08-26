# DOC 1
Documentacao Atual do Sistema PLANOS_LUAN
Documento atualizado automaticamente em 26/06/2026 às 20:23, em linguagem simples, descrevendo o comportamento real do sistema hoje.
Leitura proposta
1. O que faz o sistema hoje
O PLANOS_LUAN continua sendo um sistema de montagem de planos de aula em Word, mas hoje ele atua como uma linha de producao pedagogica mais completa. Ele combina banco de dados local, leitura de modelos DOCX, agenda escolar, entrada de PDFs em modos diferentes, extracao local, IA opcional, revisao humana e geracao final do documento.
O sistema atende fluxos comuns por PDF, cenarios CDP, adaptacoes EJA em contextos especificos e AE priorizado quando existe base preparada para a combinacao de disciplina, turma e bimestre.
2. Como o sistema trabalha por dentro hoje
Contexto: o usuario escolhe professor, disciplina, turma, mes, bimestre, escola, componente curricular e, quando necessario, modalidades especiais.
Modelo e agenda: o sistema tenta localizar modelo do professor, cadastro salvo ou template central; depois monta datas reais, feriados, dias sem aula e extensao do mes.
Entrada de PDFs: hoje existem tres modos principais de envio — Automatico, Todos de uma vez e Um por aula.
Memoria do sistema: no modo automatico, o app pode pre-selecionar PDFs a partir da ultima aula salva no historico.
Processamento: o motor local extrai tema, aprendizagem e metodologia; se a IA estiver ativa, a camada externa refina um rascunho base do proprio sistema.
Revisao: antes do DOCX final, o usuario revisa tema, aprendizagem, metodologia, acompanhamento e acessibilidade numa tela centralizada.
Geracao final: o DOCX e montado, pode ser salvo no historico ou nao, e o sistema atualiza a memoria da ultima aula apenas quando isso for autorizado.
Estruturas principais do sistema
3. Mudancas mais importantes desde a versao de 05/06/2026
A tela principal consolidou o fluxo em contexto, extracao, revisao e download, com mais destaque para revisao pedagógica antes do DOCX.
O envio de PDFs passou a trabalhar claramente com os modos Automatico, Todos de uma vez e Um por aula.
A memoria da ultima aula deixou de ser obrigatoria: hoje o usuario pode gerar o DOCX sem salvar no historico.
A camada de IA virou refinamento sobre rascunho local, em vez de trabalhar isoladamente. Agora, as listas de acompanhamento e acessibilidade também são enviadas à IA para refinamento contextual.
Foi criada uma auditoria final por aula, com confidence_score, avisos_validacao, hash do PDF e cache JSON reaproveitavel.
A higienizacao pedagogica ficou mais forte, reduzindo contaminacao entre disciplinas e trocas indevidas de recurso.
A base de testes cresceu e hoje cobre fluxo principal sem lote, cache JSON, revisao final, timeout de IA e blocos pedagogicos mais recentes. Também implementamos testes de cache robustos e suporte à integração de novas disciplinas.
Padronizacao fisica de PDFs e atualizacao automatica de caminhos no arquivo central mapa_arquivos.csv para Matematica, Ciencias, Biologia e Historia.
Adicionados classificadores e metodologias autorais complexas (como linha do tempo, analise critica de fontes e debate de narrativas) para Historia, Ciencias e Biologia.
Integração e configuração do LibreOffice no PATH para conversões headless de .docx para .pdf.
4. Partes que merecem leitura especial hoje
planos_luan_app.py segue sendo o grande orquestrador do uso diario. Ele concentra a experiencia de tela, a memoria de historico, as escolhas de modo de upload e a revisao centralizada.
core/lote.py continua sendo o coracao do fluxo PDF, mas agora conversa mais fortemente com classificadores e higienizadores de core/lib, alem de revisar e gravar cache sidecar por PDF.
core/ia.py, prompts_por_disciplina.py e referencias_metodologia.py formam a trilha de IA opcional. O desenho atual privilegia robustez: se a IA falhar, o motor local continua sustentando o plano.
core/revisao_final.py e tests/ viraram pecas mais relevantes do que eram nos documentos antigos, porque agora o sistema nao apenas gera: ele pontua, valida, reaproveita e tenta evitar que um PDF ja processado precise ser refeito sem necessidade.
5. Operacao e artefatos do dia a dia
O banco principal usado pelo app continua na raiz: planos_luan.db.
Cada PDF processado pode ganhar um sidecar .json com hash, tema, metodologia, confidence_score e avisos.
Hoje existem 14 bases JSON de AE priorizado em assets/ae_priorizado, ainda concentradas no 2o bimestre.
O projeto possui 75 arquivos de teste automatizado em tests/.
As versoes .txt extraidas da documentacao continuam existindo para leitura rapida fora do Word.
O LibreOffice está instalado e configurado globalmente no PATH, servindo para conversão local e rápida de DOCX em PDF.
6. Como a documentacao fica atualizada agora
A documentacao passou a ser regenerada por um script proprio do projeto: scripts/atualizar_documentacao_sistema.py. Esse script atualiza os dois DOCX e tambem as versoes TXT extraidas, reduzindo o risco de a descricao envelhecer depois de novas melhorias.
7. Pontos fortes atuais
Fluxo mais guiado e menos manual do que nas versoes mais antigas.
Capacidade de trabalhar com PDF comum, CDP, EJA e AE priorizado sem trocar de sistema.
IA opcional com fallback local e pos-processamento forte.
Revisao humana antes do documento final.
Historico persistente, memoria de ultima aula e opcao de nao avancar essa memoria quando o plano ainda nao estiver ok.
Cobertura de testes mais madura e mais alinhada ao comportamento real do sistema.
8. Prioridades naturais de evolucao
Continuar modularizando planos_luan_app.py, que ainda concentra muitas responsabilidades de interface e orquestracao.
Expandir a base estruturada de AE priorizado para mais contextos quando os dados estiverem prontos.
Reduzir sobreposicao entre camadas novas e legadas do CDP.
Fortalecer diagnosticos automaticos de modelos Word, bases externas e configuracoes locais.
Manter a documentacao e a automacao diaria como artefatos oficiais de manutencao do projeto.
9. Conclusao
Hoje o PLANOS_LUAN deve ser entendido como uma linha de producao pedagogica com varias camadas de seguranca: cadastro, agenda, leitura de modelos, extracao, IA opcional, higienizacao, revisao humana, auditoria final e geracao Word. Ele ja nao funciona apenas como leitor de PDF com Word na saida; ele organiza memoria, contexto e qualidade antes da entrega.
Integração completa da disciplina de Arte e de Arte e Mídias Digitais (2º Ano EM) no motor de geração, mapeados de forma especializada sob o perfil pedagógico autoral de artes.
Correção crítica no motor de cache JSON (lote.py): agora os planos refinados por IA são preservados no cache e não sofrem mais sobreposição incondicional com a referência crua DOCX.
Adicionado controle de consistência no cache: invalidação automática do cache JSON caso a escolha do usuário de usar IA (flag usar_ia) seja alternada.
Novos utilitários de interface no Streamlit: menu horizontal de navegação, dicas de digitação usando rapidfuzz (similaridade em nomes de professores/disciplinas) e botão para salvar as metodologias corrigidas na tela diretamente nos arquivos DOCX originais.
Atualização Recente - Ajuste de Limite de Caracteres e Invalidação de Cache (Versão 1.2.10)
Ajuste na instrução da IA em core/ia.py: O limite de caracteres para cada etapa metodológica gerada pela Inteligência Artificial foi reduzido de 1200 para 600 caracteres. O objetivo é evitar planos de aula excessivamente prolixos e redundantes. Essa restrição também foi reforçada na função local de pós-processamento de strings '_compactar_metodologia' (hard limit).
Incremento da Versão do Gerador: A constante VERSAO_GERADOR_ATUAL no arquivo core/revisao_final.py foi incrementada para '1.2.10'. Isso garante que o cache antigo de json mantido pelo sistema (em core/reuso_cache_plano.py) seja ignorado, forçando a IA a reprocessar as requisições respeitando as novas diretrizes limitadoras de 600 caracteres.
Registro de Atualizações - 07/07/2026
Atualizações recentes do sistema (Julho 2026):
- Correção no agrupamento de aulas duplas (divisão de metodologia) para não conflitar com a seleção automática de PDFs.
- Ajuste na pasta auxiliar DOCX_AUXILIARES_EXTRACAO: transferida para a raiz do projeto (BASE_DIR) para evitar conflitos de permissão do Windows Defender/OneDrive no diretório Documents.
- Remoção do fallback silencioso da Inteligência Artificial (OpenAI/Gemini): o sistema agora aborta o processamento com um erro explícito (RuntimeError) caso a IA falhe, em vez de recorrer silenciosamente ao motor heurístico local. Isso garante previsibilidade na geração de lotes.
- Nova nomenclatura de arquivos IA: planos gerados com sucesso utilizando motor de IA agora recebem obrigatoriamente o sufixo '_In' (ex: Plano_1o_ANO_A_Biologia_In.docx) indicando Inteligência Artificial, substituindo o antigo '_IA'.
Registro de Atualizações - 12/07/2026
Correção no layout das tabelas do template EJA (MODELOCDP), garantindo a preservação da primeira coluna (Data e Horário) ao lidar com células mescladas na extração do acompanhamento.
Melhoria na formatação dos rótulos de horários contendo tuplas no gerador de lote (ui/geracao_lote.py), evitando que estruturas de código apareçam na impressão do Word.
Nova disciplina 'Biologia-EJA' incorporada nativamente aos identificadores do core (core/disciplinas.py e aliases do core/helpers.py).
Ampliação do dicionário de conjugação e normalização de verbos metodológicos da Inteligência Artificial em core/metodologia_texto.py (ex: Projete, Peça, Divida, Sugira, etc.).
Limpeza de interface aprimorada no Histórico (ui/historico.py): planos deletados das pastas físicas ocultam-se totalmente, ao invés de constarem como 'Indisponível'.
Registro de Atualizações - 13/07/2026 (Auditoria Fases 1 a 3)
Resumo das últimas atualizações focadas na estabilidade do banco de dados, resiliência do Word e reestruturação arquitetural (Padrão Strangler Fig):
- Refatoração do Word (Logical Grid): A gravação nas células (.docx) foi protegida contra o bug do `gridSpan` e `vMerge` (células mescladas). Isso previne a sobreposição de textos silenciosa no arquivo final gerado.
- UUID4 no Histórico: Ao salvar no banco de dados e no disco físico, o timestamp obsoleto foi substituído por geração baseada em UUID, mitigando riscos de sobrescrita de arquivos se gerados no mesmo milissegundo.
- Fallback Transparente de Inteligência Artificial: Se a requisição de IA (Gemini/OpenAI) retornar um Timeout ou Erro de Servidor, a rotina não fará o lote inteiro falhar. O sistema registrará o erro no log e utilizará, com transparência, o motor local de geração heurística, evitando interrupções na fila.
- Desacoplamento Estrutural (Fase 3): A gigantesca rotina do arquivo `lote.py` começou a ser dividida em módulos dedicados (`core/application`, `core/domain`, `core/extraction`, `core/generation`).
- Padrão Strangler Fig: Um orquestrador (`GerarPlanoService`) com injeção de contexto (`ContextBuilder`) e motor de geração (`PlanGenerator`) foi injetado em paralelo no sistema legado. Eles processam e logam a geração de planos usando as novas lógicas otimizadas sem interferir no pipeline original enquanto são validados em produção.


# DOC 2
Estrutura Atual da Pasta core do PLANOS_LUAN
Documento atualizado automaticamente em 26/06/2026 às 20:23, em linguagem simples, com foco na estrutura real observada no codigo.
Objetivo: registrar como a pasta core esta organizada hoje, quais modulos ficaram mais importantes depois das evolucoes recentes e onde entram as camadas de IA, auditoria, higienizacao e CDP.
Visao geral
A pasta core continua sendo o centro da regra de negocio do PLANOS_LUAN, mas hoje ela esta mais distribuida e mais protegida por camadas de revisao do que estava no inicio do projeto. O fluxo PDF ainda nasce em core/lote.py, mas agora passa por classificacao modular em core/lib, higienizacao pedagogica, auditoria final e cache sidecar por PDF.
A camada de IA tambem mudou de papel: em vez de agir sozinha, ela pode trabalhar em modo hibrido, recebendo um rascunho local do proprio sistema como base para refinamento. Em paralelo, a pasta core ganhou modulos novos como constantes.py, normalizacao.py e revisao_final.py, enquanto core/lib ficou mais forte com higienizador_pedagogico.py e regras especializadas por disciplina.
Snapshot atual
Arquivos Python diretos em core: 35
Modulos mapeados em core/lib: 17
Arquivos de teste em tests/: 75
Bases de AE priorizado em assets/ae_priorizado: 14
Subpacotes principais vivos hoje: core/lib, core/cdp e core/eja.
Mapa rapido dos itens da pasta core
Novidades relevantes em relacao a 05/06/2026
revisao_final.py virou a ultima auditoria da aula, adicionando confidence_score, avisos_validacao e versao do gerador.
lote.py passou a salvar e reler cache sidecar .json por PDF, validado por hash do arquivo e versao do gerador.
ia.py hoje trabalha com rascunho_base, isto e, o sistema primeiro monta uma base local e depois pede refinamento a OpenAI ou Gemini.
core/lib ganhou mais peso com higienizador_pedagogico.py e com reforcos por perfil em acompanhamento e acessibilidade.
helpers.py e planos_luan_app.py passaram a sustentar melhor a ordem real de envio dos PDFs e a memoria da ultima aula gerada.
classificador.py e metodologia.py receberam classificadores e geradores especializados para Ciencias, Biologia e Historia.
Instalação e mapeamento do LibreOffice (soffice) para automação e conversão local estável de .docx para .pdf.
Mapa rapido do subpacote core/lib
Leitura final da arquitetura atual
Se a pergunta for onde nascem as aulas comuns, a resposta continua sendo core/lote.py, apoiado por extracao e classificacao em core/lib. Se a pergunta for onde o texto fica mais confiavel, hoje os pontos mais importantes sao qualidade_metodologica.py, higienizador_pedagogico.py, validador_plano.py e revisao_final.py. Se a pergunta for onde a IA entra, ela ja nao substitui o motor local: ela entra para refinar um rascunho base e pode cair de volta no motor heuristico se houver erro, timeout ou indisponibilidade externa.
No CDP, a leitura correta continua sendo em duas camadas: core/cdp como nucleo atual e cdp_legacy.py como compatibilidade ainda ativa. No restante do sistema, a principal mudanca de maturidade foi a presenca de uma trilha completa de saneamento: extracao, classificacao, geracao, higienizacao, validacao, auditoria final e cache reaproveitavel por PDF.
Observacao importante
Esta documentacao descreve o estado atual observado em 26/06/2026. Ela passou a ser regenerada por script interno para reduzir envelhecimento entre uma rodada de melhorias e outra.
Atualização Recente - Ajuste de Limite de Caracteres e Invalidação de Cache (Versão 1.2.10)
Ajuste na instrução da IA em core/ia.py: O limite de caracteres para cada etapa metodológica gerada pela Inteligência Artificial foi reduzido de 1200 para 600 caracteres. O objetivo é evitar planos de aula excessivamente prolixos e redundantes. Essa restrição também foi reforçada na função local de pós-processamento de strings '_compactar_metodologia' (hard limit).
Incremento da Versão do Gerador: A constante VERSAO_GERADOR_ATUAL no arquivo core/revisao_final.py foi incrementada para '1.2.10'. Isso garante que o cache antigo de json mantido pelo sistema (em core/reuso_cache_plano.py) seja ignorado, forçando a IA a reprocessar as requisições respeitando as novas diretrizes limitadoras de 600 caracteres.
Registro de Atualizações - 07/07/2026
Atualizações recentes do sistema (Julho 2026):
- Correção no agrupamento de aulas duplas (divisão de metodologia) para não conflitar com a seleção automática de PDFs.
- Ajuste na pasta auxiliar DOCX_AUXILIARES_EXTRACAO: transferida para a raiz do projeto (BASE_DIR) para evitar conflitos de permissão do Windows Defender/OneDrive no diretório Documents.
- Remoção do fallback silencioso da Inteligência Artificial (OpenAI/Gemini): o sistema agora aborta o processamento com um erro explícito (RuntimeError) caso a IA falhe, em vez de recorrer silenciosamente ao motor heurístico local. Isso garante previsibilidade na geração de lotes.
- Nova nomenclatura de arquivos IA: planos gerados com sucesso utilizando motor de IA agora recebem obrigatoriamente o sufixo '_In' (ex: Plano_1o_ANO_A_Biologia_In.docx) indicando Inteligência Artificial, substituindo o antigo '_IA'.
Registro de Atualizações - 12/07/2026
Correção no layout das tabelas do template EJA (MODELOCDP), garantindo a preservação da primeira coluna (Data e Horário) ao lidar com células mescladas na extração do acompanhamento.
Melhoria na formatação dos rótulos de horários contendo tuplas no gerador de lote (ui/geracao_lote.py), evitando que estruturas de código apareçam na impressão do Word.
Nova disciplina 'Biologia-EJA' incorporada nativamente aos identificadores do core (core/disciplinas.py e aliases do core/helpers.py).
Ampliação do dicionário de conjugação e normalização de verbos metodológicos da Inteligência Artificial em core/metodologia_texto.py (ex: Projete, Peça, Divida, Sugira, etc.).
Limpeza de interface aprimorada no Histórico (ui/historico.py): planos deletados das pastas físicas ocultam-se totalmente, ao invés de constarem como 'Indisponível'.
Registro de Atualizações - 13/07/2026 (Auditoria Fases 1 a 3)
Resumo das últimas atualizações focadas na estabilidade do banco de dados, resiliência do Word e reestruturação arquitetural (Padrão Strangler Fig):
- Refatoração do Word (Logical Grid): A gravação nas células (.docx) foi protegida contra o bug do `gridSpan` e `vMerge` (células mescladas). Isso previne a sobreposição de textos silenciosa no arquivo final gerado.
- UUID4 no Histórico: Ao salvar no banco de dados e no disco físico, o timestamp obsoleto foi substituído por geração baseada em UUID, mitigando riscos de sobrescrita de arquivos se gerados no mesmo milissegundo.
- Fallback Transparente de Inteligência Artificial: Se a requisição de IA (Gemini/OpenAI) retornar um Timeout ou Erro de Servidor, a rotina não fará o lote inteiro falhar. O sistema registrará o erro no log e utilizará, com transparência, o motor local de geração heurística, evitando interrupções na fila.
- Desacoplamento Estrutural (Fase 3): A gigantesca rotina do arquivo `lote.py` começou a ser dividida em módulos dedicados (`core/application`, `core/domain`, `core/extraction`, `core/generation`).
- Padrão Strangler Fig: Um orquestrador (`GerarPlanoService`) com injeção de contexto (`ContextBuilder`) e motor de geração (`PlanGenerator`) foi injetado em paralelo no sistema legado. Eles processam e logam a geração de planos usando as novas lógicas otimizadas sem interferir no pipeline original enquanto são validados em produção.
