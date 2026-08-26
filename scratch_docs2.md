# DOC 3
Auditoria Técnica Apurada do PLANOS_LUAN
Versão refinada a partir da conferência do código, do banco e do relatório anterior

Data da apuração: 02/07/2026
Escopo desta versão
Esta versão apurada foi montada a partir de quatro bases reais:
leitura do PDF Auditoria Planos Luan.pdf;
conferência do banco planos_luan.db;
leitura pontual de config.py, core/database.py, core/revisao_final.py e planos_luan_app.py;
conferência visual do próprio PDF para separar problema de conteúdo de problema de apresentação.
O objetivo aqui não é reescrever o relatório anterior do zero. É preservar o que ele acertou, corrigir o que ficou impreciso e transformar o diagnóstico em um plano mais seguro para o sistema real.
1. Parecer executivo
O relatório anterior acertou o ponto principal: o maior problema do PLANOS_LUAN não é "código ruim" isoladamente. O problema estrutural é a ausência de fronteiras claras entre:
código-fonte;
dados operacionais;
histórico de geração;
laboratório manual;
contratos de dados do próprio fluxo.
Também está correto dizer que os arquivos centrais cresceram demais e concentram responsabilidades demais, especialmente core/lote.py e planos_luan_app.py.
Onde a versão anterior exagerou ou simplificou além do ponto foi em três lugares:
historico_planos.arquivo_path não guarda hoje um caminho absoluto completo do Windows. O fluxo atual salva o arquivo em HISTORICO_DOCX_DIR e grava no banco apenas unique_filename.
A revisão pós-geração foi desabilitada na interface, mas a camada de auditoria não sumiu do código. confidence_score e avisos_validacao continuam sendo calculados e gravados no sidecar.
Algumas propostas de modularização estão bem direcionadas, mas ainda são hipóteses arquiteturais. Elas precisam ser guiadas por teste e extração gradual, não por corte cego.
Conclusão executiva: o diagnóstico estrutural é bom e merece ser aproveitado. Mas a execução deve partir da versão apurada abaixo, não da leitura literal do PDF anterior.
2. O que o relatório anterior acertou

3. O que precisava de ajuste

4. Fotografia estrutural apurada
No estado atual da pasta de trabalho, o sistema convive com:
194 arquivos .py;
527 arquivos .docx;
55 arquivos .pdf;
quase 1000 arquivos .png;
18 professores cadastrados;
147 vínculos em professor_turmas;
452 registros em historico_planos.
Isso confirma que a árvore do projeto não está guardando apenas software. Ela também está sendo usada como área operacional, histórico e laboratório.
5. Evidências concretas conferidas

6. Diagnóstico apurado por prioridade
Crítico

Alto

Moderado

7. O que eu faria primeiro, na prática
Etapa 0 - Higiene operacional e segurança mínima
Prazo sugerido: 1 a 2 dias
Criar uma pasta de dados fora do código, como D:\PLANOS_LUAN_DATA.
Planejar a mudança de planos_luan.db, historico_docx, historico e EXCLUIR para fora da árvore principal.
Ajustar config.py para apontar para essas novas bases.
Criar backup manual antes e depois da mudança.
Testar uma geração completa logo em seguida.
Resultado esperado: a pasta do projeto volta a parecer um projeto de software, e não um depósito misto de código e operação.
Etapa 1 - Contrato único do plano
Prazo sugerido: 3 a 5 dias
Criar core/models.py.
Definir PlanoCompleto cobrindo os campos usados no fluxo e no sidecar.
Encapsular PlanoAulaIA dentro desse contrato maior, sem descartar o modelo atual.
Fazer gravar_sidecar_json() serializar o contrato tipado.
Resultado esperado: qualquer função importante do pipeline passa a trabalhar com um objeto conhecido, e não com dicionários que crescem no meio do caminho.
Etapa 2 - Reaproveitar a validação sem recolocar ruído na interface
Prazo sugerido: 1 a 2 dias
Manter HABILITAR_REVISAO_POS_GERACAO = False por enquanto.
Criar um script offline, como scripts/validar_sidecars.py.
Rodar os sidecars já gerados para entender padrões reais de aviso.
Só depois decidir se a revisão volta para a interface, e em que formato.
Resultado esperado: a validação volta a ser útil sem travar a operação diária.
Etapa 3 - Quebrar core/lote.py com contrato já definido
Prazo sugerido: 1 a 2 semanas
Extrair primeiro o executor de um único plano.
Separar depois o seletor de referências.
Deixar lote.py original como fachada temporária durante a transição.
Resultado esperado: o sistema começa a ganhar pontos testáveis sem uma ruptura brusca.
Etapa 4 - Só então mexer na fronteira UI x regra
Prazo sugerido: 1 a 2 semanas
Tirar de planos_luan_app.py tudo o que não depende de st.*.
Levar essa lógica para um módulo de operação no core.
Deixar a UI como camada de entrada, exibição e estado.
Resultado esperado: a interface deixa de ser o lugar onde o comportamento real mora.
8. O que eu não faria agora
Não reativaria a revisão pós-geração na interface sem calibrar os avisos offline.
Não refatoraria core/lote.py e planos_luan_app.py ao mesmo tempo.
Não mexeria em docx_generator/preencher.py antes de ter teste de regressão do documento gerado.
Não faria migração de schema do SQLite como primeira frente.
Não trataria a proposta de nova arquitetura como "corte estrutural único". O caminho aqui precisa ser incremental.
9. Decisão recomendada para os próximos 7 dias

10. Conclusão apurada
O relatório anterior é bom como disparador de conversa, porque acerta o centro do problema: o PLANOS_LUAN cresceu sem fronteiras suficientemente claras.
Mas a leitura mais fiel do sistema hoje é esta:
O risco mais urgente é operacional: dados reais morando dentro da pasta do projeto.
O risco mais corrosivo é lógico: um contrato de dados incompleto para o plano final.
O risco mais caro de manutenção é técnico: poucos arquivos tomando decisões demais.
O sistema não precisa ser jogado fora. Ele precisa ser reencaixado por etapas, com sequência, teste e menos improviso estrutural. A ordem importa mais do que a velocidade.
Se a equipe seguir essa sequência, há caminho real para estabilizar o projeto sem interromper o uso do sistema no dia a dia.

# DOC 4
Relatorio de Auditoria do Sistema PLANOS_LUAN
Fotografia estrutural atualizada em 02/07/2026
1. Objetivo deste material
Este documento resume o estado atual do sistema PLANOS_LUAN para apoiar uma analise externa mais profunda. O foco aqui nao e reescrever o projeto inteiro, mas identificar por que ele ficou dificil de manter e quais seriam os caminhos mais seguros para estabilizacao gradual.
2. O que o sistema faz hoje
O PLANOS_LUAN gera planos de aula em Word a partir de PDFs pedagogicos, referencias metodologicas, modelos de documento e cadastro de professores. O fluxo principal passa por extracao de PDF, heuristicas de leitura, enriquecimento por IA, validacoes internas e preenchimento final do modelo .docx.
3. Retrato estrutural atual
A pasta raiz mistura codigo-fonte, banco de dados, historico de geracao, documentos Word, referencias pedagogicas e sobras operacionais.
Os maiores arquivos centrais concentram muitas responsabilidades, especialmente core/lote.py e planos_luan_app.py.
O banco SQLite esta mais leve do que em leituras antigas, porque historico_planos agora salva arquivo_path em vez de BLOB do DOCX.
A revisao pos-geracao dos planos esta desabilitada na interface neste momento, mas a logica tecnica de auditoria ainda existe no codigo.
O sistema depende bastante de convencoes de pastas e caminhos locais em C:\ e D:\.
4. Pontos criticos identificados
Monolitos de codigo: arquivos grandes demais dificultam previsao de impacto a cada ajuste.
Acoplamento alto: interface, regras pedagogicas, validacao e operacao de arquivos estao muito proximas.
Mistura entre sistema e operacao: a raiz do projeto tambem virou deposito de historico, laboratorio e evidencias.
Contratos parciais: o modelo tipado da IA e pequeno, mas o objeto real do fluxo ganha muitos metadados fora do contrato principal.
Dependencia de caminho e estado local: mover arquivos ou pastas manualmente pode alterar o comportamento do sistema.
5. O que melhorou em relacao a diagnosticos antigos
O historico do banco nao guarda mais o binario inteiro do DOCX.
A pasta de auditoria agora foi atualizada com schema real, estrutura atual e modelos de dados mais confiaveis.
A revisao visual pos-geracao pode ficar fora da operacao por enquanto, reduzindo ruido para testes do fluxo principal.
6. Prioridades recomendadas para a proxima auditoria
Separar claramente codigo, dados operacionais, referencias e area de descarte.
Quebrar os arquivos gigantes por responsabilidade, sem reescrever tudo de uma vez.
Definir um contrato unico e rastreavel entre extracao, IA, validacao e geracao do DOCX.
Revisar o papel de JSON sidecar, DOCX de referencia e caches no comportamento final do sistema.
Criar uma estrategia de testes mais objetiva para Windows, incluindo casos reais de PDF e geracao de Word.
7. Arquivos de apoio incluidos nesta pasta
banco_de_dados_schema.txt: schema real do SQLite e observacoes objetivas.
estrutura_pastas_projeto.txt: leitura da organizacao atual do projeto e dos pontos de acoplamento.
modelos_dados_ia.txt: contrato atual da IA, sidecar JSON e estado da revisao.
PROMPT_ANALISE_EXTERNA.md: prompt pronto para enviar a outra ferramenta de analise.
8. Conclusao
O sistema ainda entrega resultado, mas cresceu por acumulacao. O problema principal nao parece ser uma unica falha isolada; e a soma de arquivos grandes, fronteiras pouco claras e mistura entre desenvolvimento, operacao real e laboratorio manual. A boa noticia e que isso pode ser atacado por fases, com reorganizacao gradual e sem parar completamente o uso do sistema.