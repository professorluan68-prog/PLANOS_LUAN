# PLANOS_LUAN — Instruções permanentes

## Comunicação com o proprietário

- Responder sempre em português brasileiro.
- O proprietário do sistema não é desenvolvedor.
- Explicar decisões técnicas em linguagem simples.
- Trabalhar em etapas pequenas, apresentando no máximo duas ações por vez.
- Quando houver dúvida que possa mudar o comportamento do sistema, perguntar antes de implementar.

## Objetivo do sistema

O PLANOS_LUAN é um sistema local em Python 3.12 e Streamlit que extrai conteúdo pedagógico de PDFs, cruza essas informações com professores, turmas, horários e modelos Word, e gera planos de aula em DOCX. Utiliza SQLite, pdfplumber, python-docx, Pydantic e integrações opcionais com OpenAI e Google Gemini.

## Regras obrigatórias

- Antes de alterar código, entender o fluxo completo relacionado à tarefa.
- Ler a documentação existente antes de iniciar auditorias ou refatorações.
- Inspecionar o estado do Git antes de modificar arquivos.
- Preservar alterações existentes do proprietário.
- Não fazer mudanças destrutivas, exclusões em massa ou redefinições do Git.
- Não alterar formatos de dicionários, interfaces públicas ou comportamento existente sem avaliar retrocompatibilidade.
- Fazer uma mudança lógica por vez.
- Não realizar refatorações extensas junto com correções pequenas.
- Apresentar um plano antes de mudanças amplas ou arquiteturais.

## Proteção de dados e arquivos

- Nunca modificar diretamente bancos SQLite de produção sem autorização.
- Utilizar cópias temporárias para testes com bancos, PDFs e documentos Word.
- Não sobrescrever templates DOCX originais nem documentos do histórico.
- Não expor dados pessoais de professores ou alunos.
- Nunca gravar chaves de API, senhas ou tokens no código, Git ou relatórios.
- Não enviar PDFs, documentos ou dados para serviços externos sem autorização explícita.
- Solicitar autorização antes de instalar dependências ou acessar serviços externos.

## Validação

- Utilizar o Python do ambiente virtual `.venv`.
- Executar testes relacionados à mudança quando existirem.
- Fazer verificação de sintaxe e importações após alterações em Python.
- Em alterações de DOCX, validar o arquivo gerado sem sobrescrever o original.
- Não afirmar que uma correção funciona sem informar qual verificação foi executada.
- Se não for possível testar, explicar claramente a limitação.

## Comandos do Windows

Executar o sistema:

& ".\.venv\Scripts\python.exe" -m streamlit run planos_luan_app.py

Executar testes, quando houver:

& ".\.venv\Scripts\python.exe" -m pytest -q

Verificar sintaxe:

& ".\.venv\Scripts\python.exe" -m compileall -q core docx_generator ui planos_luan_app.py

## Entrega das alterações

Ao concluir uma tarefa, informar de maneira simples:

- O que foi alterado.
- Quais arquivos foram modificados.
- Como a mudança foi verificada.
- Quais riscos ou limitações permanecem.
- Qual é o próximo passo recomendado.

## Perfil técnico do proprietário

- O proprietário possui conhecimento avançado de Windows, instalação, configuração, PowerShell e administração local.
- Está aprendendo Python e práticas de desenvolvimento durante a evolução do sistema.
- Não simplificar excessivamente explicações técnicas.
- Explicar conceitos de programação, arquitetura e Git de forma clara, relacionando-os ao PLANOS_LUAN.
- Quando pertinente, apresentar brevemente o conceito de Python envolvido na mudança.

## Protocolo obrigatório antes de mudanças

- Interpretar cada solicitação como uma descrição do resultado desejado, não como obrigação de executar literalmente o caminho técnico sugerido.
- Separar claramente o objetivo do proprietário da solução técnica proposta.
- Antes de mudanças relevantes, explicar:
  - o comportamento atual;
  - o resultado que foi entendido;
  - a solução recomendada;
  - as possíveis consequências diretas e indiretas;
  - os riscos, limitações e alternativas;
  - como a mudança será validada.
- Aguardar aprovação antes de mudanças arquiteturais, alterações de comportamento, banco de dados, dependências, templates, integrações externas ou operações difíceis de reverter.
- Se a solução solicitada for inviável, frágil ou prejudicial, não implementá-la silenciosamente.
- Explicar o problema e propor uma ou mais rotas alternativas.
- Se uma solicitação estiver ambígua ou permitir interpretações que produzam resultados diferentes, interromper a implementação e fazer perguntas objetivas.
- Procurar entender o que o proprietário deseja, até onde a mudança deve chegar e por que ela é necessária.
- Não interromper tarefas por dúvidas irrelevantes; o nível de planejamento deve ser proporcional ao risco.
- Mudanças pequenas, claras e reversíveis podem receber um plano curto.
- Se surgir durante a implementação algo que altere o plano aprovado, parar e realinhar antes de ampliar o escopo.

## Avaliação das “reações” de uma mudança

Ao propor alterações, avaliar quando aplicável os impactos sobre:

- outras funções e módulos;
- formatos de dados e retrocompatibilidade;
- banco SQLite;
- extração de PDFs;
- templates e documentos DOCX gerados;
- interface Streamlit;
- desempenho;
- segurança e privacidade;
- testes e manutenção futura;
- possibilidade de reversão.

## Contexto operacional e comercial

- O PLANOS_LUAN é atualmente uma ferramenta de uso exclusivo do proprietário.
- Os professores atendidos são clientes e destinatários dos planos gerados, não usuários do software.
- Não implementar autenticação, múltiplos usuários, portal externo, arquitetura SaaS ou recursos colaborativos sem solicitação e aprovação explícitas.
- Evitar complexidade prematura, mas não criar decisões que impeçam uma possível evolução futura.
- O sistema sustenta uma atividade profissional remunerada e deve ser tratado como ferramenta comercial crítica.
- Priorizar confiabilidade, produtividade, previsibilidade, recuperação de falhas e qualidade do documento entregue.
- O fluxo atual reduziu o tempo aproximado de produção de cada plano de 25 minutos para até 2 minutos.
- Alterações não devem prejudicar essa produtividade sem uma justificativa apresentada e aprovada.

## Fonte pedagógica oficial

- Os PDFs do Material Digital da Secretaria da Educação do Estado de São Paulo são a fonte pedagógica primária.
- Os PDFs devem ser tratados como documentos de entrada autoritativos.
- O sistema deve manter rastreabilidade entre o conteúdo do PDF, os dados extraídos e o plano gerado.
- Não inventar conteúdos pedagógicos ausentes da fonte sem que essa complementação esteja claramente autorizada.
- Não modificar PDFs oficiais.
- Não adicionar PDFs oficiais completos ao Git sem autorização.
- Não enviar PDFs ou conteúdos extraídos para serviços externos sem autorização explícita.
- Quando a IA for utilizada, ela deve refinar ou estruturar o conteúdo, e não substituir silenciosamente a fonte oficial.

## Natureza da transformação pedagógica

- O sistema não realiza apenas transcrição de PDF para DOCX.
- Ele transforma materiais digitais de aula em planos mensais organizados por professor, turma, horário e calendário.
- O documento final precisa reunir, conforme o modelo aplicável:
  - identificação do professor, escola, componente, turma, mês e bimestre;
  - semanas, datas, horários e quantidade de aulas;
  - número e título do material digital;
  - aprendizagem essencial;
  - desenvolvimento ou metodologia;
  - acompanhamento da aprendizagem;
  - acessibilidade.
- Os modelos DOCX e sua formatação são parte do produto entregue ao cliente e devem ser tratados como contratos de saída.
- Não alterar estrutura, células, estilos ou disposição dos templates sem análise de impacto e validação visual.

## Regras para metodologia

- A metodologia é uma transformação pedagógica baseada no PDF, não um resumo genérico.
- Antes de alterar sua geração, mapear e compreender todas as regras pedagógicas já existentes no sistema.
- Considerar disciplina, etapa de ensino, turma, quantidade de aulas, duração, tema, aprendizagem essencial e técnicas pedagógicas presentes no material.
- Preservar uma sequência didática coerente, como abertura, desenvolvimento, prática e encerramento, quando compatível com a fonte.
- Não criar uma regra universal quando disciplinas ou modalidades exigirem comportamentos diferentes.
- Se faltarem informações ou regras suficientes, sinalizar a limitação para revisão humana em vez de preencher silenciosamente com conteúdo genérico.
- Mudanças na metodologia devem ser validadas comparando PDFs reais com os DOCX gerados.
- Utilizar amostras representativas de diferentes disciplinas e séries nos testes.
- A revisão humana do proprietário continua sendo a decisão pedagógica final.

## Proteção dos dados dos clientes

- Tratar nomes, horários, escolas, turmas, planos e cadastros dos professores como dados profissionais confidenciais.
- Não utilizar o banco de produção em testes.
- Não incluir bancos reais, planos de clientes, históricos gerados ou dados pessoais em commits sem autorização.
- Preferir dados fictícios ou anonimizados em testes automatizados e relatórios técnicos.
