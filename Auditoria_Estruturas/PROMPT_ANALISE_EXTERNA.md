# Prompt para Auditoria Externa do PLANOS_LUAN

Voce vai atuar como um arquiteto de software senior, com experiencia em Python, Streamlit, pipelines de documentos, PDF parsing, geracao de Word e saneamento de sistemas que cresceram sem modularizacao suficiente.

Quero uma analise franca e pratica do projeto `PLANOS_LUAN`, sem maquiagem e sem recomendacao generica.

## Objetivo

Precisamos entender por que o sistema ficou dificil de manter, onde estao os maiores riscos estruturais e qual seria um plano realista de recuperacao sem reescrever tudo do zero.

## Contexto resumido

O sistema gera planos de aula em `.docx` a partir de PDFs pedagógicos, referencias metodologicas, modelos Word e cadastro de professores. Ele usa Python, Streamlit, `python-docx`, extracao de texto de PDF, heuristicas e IA para montar metodologia, acompanhamento e acessibilidade.

Na pratica, o projeto cresceu muito, acumulou camadas, rotinas legadas, arquivos grandes e mistura codigo com operacao real dentro da mesma pasta.

## Arquivos-base para a sua leitura inicial

Leia primeiro os arquivos desta pasta:

- `Auditoria_Sistema_Planos_Luan.docx`
- `banco_de_dados_schema.txt`
- `estrutura_pastas_projeto.txt`
- `modelos_dados_ia.txt`

Se precisar aprofundar, use o restante do projeto em `D:\\PLANOS_LUAN`.

## Problemas percebidos hoje

- o sistema esta cheio de brechas, falhas e regras espalhadas;
- existem arquivos grandes demais e com muitas responsabilidades;
- esta dificil saber o que e regra de negocio, o que e ajuste temporario e o que e legado;
- a pasta raiz mistura codigo, banco, historico, documentos gerados, referencias e sobras operacionais;
- a revisao pos-geracao dos planos foi desabilitada temporariamente porque estava gerando ruido demais para a operacao;
- precisamos de mais confiabilidade no fluxo PDF -> metodologia -> DOCX final.

## Restricoes importantes

- nao queremos reescrever tudo do zero sem necessidade;
- a correcao precisa ser incremental, segura e compatível com Windows;
- o sistema usa caminhos locais em `C:\\` e `D:\\`;
- a geracao de Word precisa preservar o modelo visual oficial;
- a metodologia precisa continuar especifica ao PDF e com linguagem de professor experiente;
- o sistema nao pode depender de ideias vagas. Precisamos de um plano executavel.

## O que eu quero como resposta

Quero uma resposta organizada nestes blocos:

1. Diagnostico estrutural do sistema
2. Principais riscos tecnicos e operacionais, em ordem de gravidade
3. Onde o acoplamento esta mais perigoso hoje
4. O que deve ser congelado, o que deve ser simplificado e o que deve ser refatorado primeiro
5. Proposta de reorganizacao por fases, sem reescrever tudo
6. Sugestao de nova divisao de modulos e pastas
7. Estrategia para separar:
   - extracao de PDF
   - referencias metodologicas
   - enriquecimento por IA
   - validacao
   - geracao de DOCX
   - interface Streamlit
8. Estrategia de testes para Windows
9. Ganhos rapidos que ja poderiam reduzir risco em poucos dias
10. Riscos de uma refatoracao mal feita e como evitar isso

## Tipo de analise esperada

- seja direto;
- aponte causas-raiz e nao apenas sintomas;
- mostre trade-offs;
- evite conselho generico como "melhorar arquitetura";
- proponha um plano de estabilizacao realista para um sistema que ja esta em producao local e sendo usado para gerar documentos reais.

## Observacao final

Se identificar que o problema principal nao e apenas codigo ruim, mas falta de fronteiras entre codigo, dados, historico e laboratorio, deixe isso muito claro e proponha como resolver sem travar a operacao do dia a dia.
