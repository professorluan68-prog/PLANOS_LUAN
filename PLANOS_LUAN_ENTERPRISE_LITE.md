# PLANOS_LUAN -- ARQUITETURA ENTERPRISE LITE

## Visao geral

Este documento reescreve a proposta "enterprise" de forma realista para o
momento atual do PLANOS_LUAN.

O objetivo nao e transformar o projeto inteiro de uma vez em uma arquitetura
grande e abstrata. O objetivo e evoluir o sistema sem perder o que ja funciona:

- geracao de planos com qualidade pedagogica;
- leitura de PDFs com heuristicas praticas;
- preservacao do modelo Word da escola;
- compatibilidade com Windows;
- manutencao simples para quem usa e ajusta o sistema no dia a dia.

Em resumo: primeiro consolidar o nucleo que gera bons planos; depois organizar
camadas; so entao subir nivel de infraestrutura.

---

## Principios para este projeto

### 1. Nao reescrever tudo sem necessidade

O sistema ja possui regras pedagogicas valiosas, testes e fluxo de geracao de
`.docx`. A refatoracao deve aproveitar isso.

### 2. Melhorar confiabilidade antes de escalar

Antes de pensar em Redis, fila, plugins ou SaaS, o sistema precisa gerar
resultado consistente para professor, disciplina, turma, PDF e modelo de Word.

### 3. Separar responsabilidades aos poucos

O ganho real vira de separar melhor:

- extracao de PDF;
- regras pedagogicas;
- montagem do plano;
- saida `.docx`;
- persistencia e historico.

### 4. Manter o Word como parte central do produto

No PLANOS_LUAN, o `.docx` nao e detalhe tecnico. Ele e a entrega final. Toda
mudanca arquitetural precisa proteger:

- tabelas;
- estilos;
- negritos;
- cores;
- estrutura do modelo;
- compatibilidade com LibreOffice e Word no Windows.

---

## Diagnostico do estagio atual

Hoje o projeto ja tem bases importantes:

- extracao de PDF com heuristicas e fallback;
- geracao de metodologia por disciplina;
- geracao de acompanhamento e acessibilidade;
- preenchimento de `.docx` com preservacao do modelo;
- banco local com historico;
- testes para partes criticas;
- Streamlit como interface principal.

O principal desafio nao e falta de tecnologia. O principal desafio e excesso de
regras espalhadas entre modulos diferentes, com alguns caminhos especiais por
disciplina e comportamento dificil de prever.

Por isso, a prioridade arquitetural correta e:

1. reduzir duplicacao;
2. padronizar pipeline;
3. validar melhor entradas e saidas;
4. isolar partes sensiveis;
5. so depois pensar em escala operacional.

---

## Arquitetura alvo, sem exagero

Em vez de impor `domain/application/infrastructure/interfaces` logo de cara, a
proposta e aproximar o projeto dessa organizacao em etapas.

### Estrutura recomendada de medio prazo

```text
/core
    /extracao
    /pedagogico
    /pipeline
    /saida_docx
    /persistencia
    /ia
    /validacao

/ui
/tests
/templates
```

### Leitura dessa estrutura

- `core/extracao`: leitura de PDF, OCR fallback, heuristicas de titulo,
  habilidade, etapas e recursos;
- `core/pedagogico`: metodologia, acompanhamento, acessibilidade e regras por
  disciplina;
- `core/pipeline`: orquestracao da geracao do plano;
- `core/saida_docx`: preenchimento de modelos, preservacao visual e validacao
  do arquivo final;
- `core/persistencia`: banco, historico e versoes;
- `core/ia`: clientes, retry, timeout, fallback e normalizacao;
- `core/validacao`: schemas, contratos internos e saneamento de dados.

Isso ja traz beneficio real sem obrigar o projeto a virar uma "Clean
Architecture pura" de uma vez.

---

## Pipeline recomendado

O fluxo principal deve ficar claro e previsivel:

```text
PDFs/entrada
-> extracao
-> normalizacao
-> regras pedagogicas
-> validacao
-> montagem do plano
-> geracao DOCX
-> validacao final do DOCX
-> historico/versao
```

### Regra importante

Cada etapa deve devolver dados claros para a proxima. Evitar que uma funcao
misture:

- leitura de arquivo;
- regra pedagogica;
- decisao de disciplina;
- escrita de Word;
- acesso a banco.

---

## Prioridades reais de arquitetura

## Fase 1 -- agora

Foco: confiabilidade do nucleo.

### Entregas

- padronizar o pipeline de geracao;
- reduzir caminhos especiais desnecessarios por disciplina;
- criar validacao forte para estruturas internas do plano;
- melhorar fallback da IA;
- reforcar testes do fluxo que gera `.docx`.

### Resultado esperado

O sistema continua simples de usar, mas fica mais previsivel e menos sujeito a
quebras quando surgem novos PDFs, novas disciplinas ou ajustes pedagogicos.

---

## Fase 2 -- organizacao interna

Foco: separar responsabilidades sem quebrar a aplicacao.

### Entregas

- mover regras pedagogicas para modulos mais previsiveis;
- centralizar classificacao de disciplina, tipo de aula e recursos;
- isolar o pipeline principal em um servico de orquestracao;
- concentrar a geracao `.docx` em uma camada claramente protegida.

### Resultado esperado

Fica mais facil alterar metodologia, acompanhamento ou acessibilidade sem
acidentalmente mexer em banco, UI ou Word.

---

## Fase 3 -- robustez operacional

Foco: IA e processamento mais seguros.

### Entregas

- wrapper unico para IA com timeout, retry e tratamento de erro;
- schemas com Pydantic para entradas e saidas criticas;
- cache local em memoria ou disco para evitar retrabalho;
- logs mais claros para diagnostico.

### Resultado esperado

Se a IA falhar, o sistema nao desaba. Ele tenta, valida e cai para fallback com
mais seguranca.

---

## Fase 4 -- historico e versoes

Foco: rastreabilidade.

### Entregas

- versionamento de planos no banco local;
- guardar metadados da geracao;
- identificar qual pipeline gerou cada plano;
- permitir comparar revisoes futuras.

### Resultado esperado

O sistema deixa de "sobrescrever o ultimo resultado" como referencia unica e
passa a ter memoria melhor do que foi produzido.

---

## Fase 5 -- escala de verdade

Foco: so quando houver necessidade real.

### Entram aqui, e nao antes

- PostgreSQL;
- Redis;
- fila assincrona;
- workers;
- plugins dinamicos;
- API REST;
- telemetria pesada;
- Prometheus/Grafana/OpenTelemetry.

### Regra de decisao

Esses itens so entram quando o uso justificar:

- muitos usuarios simultaneos;
- alto volume de PDFs;
- processamento demorado;
- necessidade de execucao em servidor;
- necessidade real de integracao externa.

Se ainda estamos no estagio de consolidar qualidade pedagogica e estabilidade
do `.docx`, antecipar isso tende a complicar mais do que ajudar.

---

## Validacao forte: prioridade alta

Este e um dos melhores pontos da proposta enterprise original e deve entrar
cedo.

### Exemplo de contratos internos

```python
from pydantic import BaseModel


class EtapaPlanoSchema(BaseModel):
    titulo: str
    texto: str


class PlanoGeradoSchema(BaseModel):
    tema: str
    aprendizagem: str
    metodologia: list[EtapaPlanoSchema]
    acompanhamento: list[str]
    acessibilidade: list[str]
```

### Onde aplicar

- saida de IA;
- resultado da extracao;
- estrutura final antes do `.docx`;
- historico salvo em banco.

### Beneficio

Em vez de descobrir problema so no Word final, o sistema identifica mais cedo
quando vier:

- campo vazio;
- lista malformada;
- etapa quebrada;
- retorno inesperado de IA;
- texto fora do padrao.

---

## IA resiliente: vale a pena, mas sem excesso

Uma camada unica para IA faz sentido agora.

### O que essa camada deve ter

- timeout;
- retry controlado;
- validacao da resposta;
- normalizacao do texto;
- fallback local;
- log simples de erro.

### O que nao precisa agora

- multiprovedor super complexo;
- observabilidade pesada;
- engenharia de prompt distribuida em varias classes abstratas.

Primeiro precisamos de previsibilidade, nao de sofisticacao ornamental.

---

## Cache: comecar simples

Cache e boa ideia, mas comecando local.

### Recomendacao

- hash do PDF e dos parametros principais;
- cache em memoria ou arquivo local;
- invalida quando mudar regra relevante.

### Nao comecar por Redis

Redis faz sentido mais adiante. Agora, um cache local bem definido ja pode
reduzir retrabalho sem aumentar manutencao.

---

## Banco de dados: evolucao gradual

O banco atual local ainda pode servir bem por um tempo.

### Agora

- melhorar versionamento;
- registrar metadados da geracao;
- reforcar integridade do historico.

### Depois

Migrar para PostgreSQL apenas quando o sistema precisar:

- multiusuario real;
- acesso remoto;
- concorrencia maior;
- operacao em servidor.

---

## Plugins pedagogicos: boa ideia, mas na hora certa

A ideia de plugins e boa para crescimento, principalmente em regras por:

- disciplina;
- rede de ensino;
- modelo de escola;
- contexto como CDP ou EJA.

Mas isso so vale a pena depois que o nucleo estiver bem consolidado.

Antes disso, "plugin" pode virar apenas mais uma camada de complexidade sobre um
core ainda instavel.

---

## Testes que fazem mais sentido para o PLANOS_LUAN

### Prioridade alta

- testes de extracao de PDF;
- testes de metodologia por disciplina;
- testes de acompanhamento e acessibilidade;
- testes de preservacao do `.docx`;
- testes de regressao com casos reais que ja deram problema.

### Prioridade media

- testes de fallback da IA;
- testes de historico e versionamento;
- testes de normalizacao e validacao.

### Prioridade posterior

- testes de fila;
- testes distribuidos;
- testes de infraestrutura externa.

---

## Roadmap pratico

## Sprint 1

- mapear pipeline atual do plano;
- identificar pontos duplicados;
- introduzir schema interno para plano final;
- reforcar testes do `.docx`.

## Sprint 2

- isolar camada de extracao;
- isolar camada pedagogica;
- isolar camada de geracao Word;
- reduzir regras espalhadas.

## Sprint 3

- criar servico unico de IA com retry e fallback;
- adicionar cache local simples;
- registrar logs de erro mais claros.

## Sprint 4

- versionar planos no banco;
- registrar metadados de geracao;
- preparar terreno para API ou operacao futura.

## Sprint 5

- avaliar se faz sentido subir para PostgreSQL, Redis ou fila.

---

## Conclusao

O PLANOS_LUAN pode, sim, caminhar para uma arquitetura mais forte. Mas o
melhor caminho nao e virar "enterprise" por fora antes de estabilizar o que
faz o sistema ser valioso por dentro.

A forma mais inteligente de evoluir este projeto e:

1. proteger o nucleo pedagogico;
2. preservar a geracao do `.docx`;
3. padronizar o pipeline;
4. validar melhor os dados;
5. escalar infraestrutura apenas quando houver necessidade concreta.

Essa versao "Enterprise Lite" mantem ambicao, mas com os pes no chao.
