# ANÁLISE METODOLÓGICA - MATEMÁTICA
## Sistema Python — Geração Automática de Planos de Aula SEDUC/SP
### Baseada em análise real dos PDFs de aula (Ensino Médio — 2º Bimestre)

---

## 1. IDENTIDADE METODOLÓGICA DA DISCIPLINA

A Matemática na SEDUC/SP parte **sempre de uma situação-problema ou contexto real** antes de qualquer formalização. Os PDFs analisados revelam um padrão consistente: o conteúdo matemático nunca é apresentado de forma abstrata no início — ele emerge de uma necessidade concreta (planejamento financeiro, juros de cartão, velocidade de internet, crescimento populacional, placas de carro, Mega-Sena, playlists aleatórias).

**Características centrais identificadas nos PDFs:**

- **Contextualização obrigatória**: toda aula começa com uma situação do mundo real (consumo, tecnologia, finanças, esportes, cotidiano)
- **Progressão lógica**: do concreto → representação → formalização → generalização
- **Múltiplas representações**: numérica, algébrica, gráfica, tabular e verbal aparecem na mesma aula
- **Técnicas recorrentes**: VIREM E CONVERSEM (discussão em duplas/grupos), TODO MUNDO ESCREVE (resolução individual), COM SUAS PALAVRAS (síntese), HORA DA LEITURA (texto motivador), DE OLHO NO MODELO (exemplo resolvido)
- **Validação de resultados**: o sistema deve sempre incluir etapa de verificação e discussão de estratégias
- **Conexão interdisciplinar**: os contextos envolvem Educação Financeira, Ciências, Tecnologia e Cidadania

**O sistema Python deve entender que Matemática:**
- NUNCA começa com definição ou fórmula
- SEMPRE parte de problema ou questionamento
- SEMPRE inclui discussão de estratégias (não apenas resposta final)
- SEMPRE formaliza após exploração
- SEMPRE conecta com aplicação real

---

## 2. ESTRUTURA PADRÃO DA METODOLOGIA

### Estrutura Principal (mais frequente nos PDFs)

```
Para começar → Exploração → Foco no conteúdo → Formalização → Pause e responda → Na prática → Encerramento
```

### Quando cada etapa aparece:

| Etapa | Quando usar | Quando omitir | Quando reforçar |
|-------|-------------|---------------|-----------------|
| **Para começar** | SEMPRE — toda aula | Nunca omitir | Aulas de retomada: usar "Relembre" |
| **Exploração** | Aulas de conceito novo, investigação, gráficos | Aulas de verificação (só Na prática) | Aulas com GeoGebra, experimentos, tabelas |
| **Foco no conteúdo** | SEMPRE — toda aula conceitual | Aulas de verificação pura | Aulas com definição formal, propriedades |
| **Formalização** | Após exploração de conceito novo | Aulas de aplicação/verificação | Álgebra, logaritmos, combinatória |
| **Pause e responda** | SEMPRE — após construção do conceito | Nunca omitir | Aulas com múltiplos exemplos |
| **Na prática** | SEMPRE — toda aula | Nunca omitir | Aulas de verificação: é a etapa central |
| **Encerramento** | SEMPRE | Nunca omitir | Aulas de síntese, mapa mental |

### Variações por tipo de aula (identificadas nos PDFs):

**Aula de conceito novo** (ex: Função Exponencial, Logaritmo, Combinatória):
```
Para começar (VIREM E CONVERSEM) → Foco no conteúdo → Formalização → Pause e responda → Na prática (TODO MUNDO ESCREVE) → Encerramento
```

**Aula de modelagem/resolução de problemas** (ex: Modelagem Algébrica):
```
Para começar (VIREM E CONVERSEM) → Exploração (COM SUAS PALAVRAS) → Foco no conteúdo → Pause e responda → Na prática (TODO MUNDO ESCREVE) → Encerramento
```

**Aula de verificação** (ex: Aula de Verificação — Equações, Combinatória):
```
Relembre (retomada) → Na prática (TODO MUNDO ESCREVE — múltiplas atividades) → Encerramento
```

**Aula de investigação com tecnologia** (ex: Gráfico no GeoGebra):
```
Para começar → Exploração (com software/ferramenta) → Foco no conteúdo → Pause e responda → Encerramento
```

**Aula de retomada** (ex: Retomando Equações do 1º grau):
```
Relembre (VIREM E CONVERSEM) → Foco no conteúdo (DE OLHO NO MODELO) → Pause e responda → Na prática → Encerramento
```

---

## 3. TIPOS DE AULA DE MATEMÁTICA

### 3.1 Álgebra
**Objetivo pedagógico:** Desenvolver a capacidade de modelar situações com linguagem simbólica, resolver equações e interpretar resultados no contexto original.

**Sinais típicos no PDF:**
- Palavras: equação, variável, incógnita, expressão, polinômio, modelar, sentença matemática
- Presença de letras representando grandezas (x, y, n)
- Situações-problema com relação entre grandezas
- Exemplos resolvidos passo a passo

**Linguagem metodológica ideal:**
- "Modelar a situação utilizando equação do 1º grau..."
- "Identificar as grandezas envolvidas e representá-las algebricamente..."
- "Resolver a equação aplicando propriedades de igualdade..."
- "Interpretar o resultado no contexto do problema..."

**Cuidados:**
- Nunca apresentar a equação antes do problema
- Sempre incluir etapa de interpretação do resultado (não apenas o valor de x)
- Sempre mostrar as etapas: compreender → planejar → executar → verificar

---

### 3.2 Funções
**Objetivo pedagógico:** Compreender relações de dependência entre grandezas, representar em múltiplas formas e interpretar comportamentos.

**Sinais típicos no PDF:**
- Palavras: função, lei de formação, crescimento, decrescimento, gráfico, dependência, variável
- Tabelas de valores, gráficos cartesianos
- Contextos de crescimento/decrescimento (populacional, financeiro, viral)
- Uso de GeoGebra ou calculadora

**Linguagem metodológica ideal:**
- "Investigar a relação de dependência entre [grandeza A] e [grandeza B]..."
- "Representar graficamente a função, identificando comportamento crescente/decrescente..."
- "Analisar o comportamento da função a partir da lei de formação..."
- "Conectar a representação gráfica com a situação-problema..."

**Cuidados:**
- Sempre partir da relação entre grandezas antes da definição formal
- Incluir representação tabular antes da gráfica
- Nunca apresentar gráfico sem interpretação contextual

---

### 3.3 Geometria
**Objetivo pedagógico:** Desenvolver percepção espacial, raciocínio dedutivo e capacidade de calcular medidas com compreensão das propriedades.

**Sinais típicos no PDF:**
- Palavras: ângulo, triângulo, área, perímetro, volume, figura, polígono, circunferência, construção
- Figuras geométricas, malha quadriculada
- Construções com régua e compasso ou software
- Problemas de medição e cálculo

**Linguagem metodológica ideal:**
- "Explorar as propriedades de [figura] através de [observação/construção]..."
- "Calcular [área/perímetro/volume], justificando o procedimento utilizado..."
- "Identificar relações entre os elementos da figura..."

**Cuidados:**
- Sempre incluir apoio visual (figura, malha, construção)
- Nunca apresentar fórmula sem derivação ou justificativa
- Sempre conectar com aplicações práticas (arquitetura, design, engenharia)

---

### 3.4 Grandezas e Medidas / Proporcionalidade
**Objetivo pedagógico:** Compreender relações entre grandezas direta e inversamente proporcionais e aplicar em contextos reais.

**Sinais típicos no PDF:**
- Palavras: razão, proporção, grandeza, velocidade, taxa, km/h, Mbps, litros, tempo
- Tabelas de valores proporcionais
- Problemas com unidades de medida diferentes
- Contextos de velocidade, consumo, densidade

**Linguagem metodológica ideal:**
- "Identificar as grandezas envolvidas e analisar como se relacionam..."
- "Verificar se as grandezas são direta ou inversamente proporcionais..."
- "Calcular a razão entre grandezas de espécies diferentes..."

**Cuidados:**
- Sempre identificar as unidades antes de calcular
- Sempre verificar se a relação é direta ou inversa antes de resolver
- Nunca calcular sem interpretar o significado da razão

---

### 3.5 Estatística e Probabilidade
**Objetivo pedagógico:** Desenvolver letramento estatístico — ler, interpretar e produzir dados; calcular e interpretar probabilidades.

**Sinais típicos no PDF:**
- Palavras: dados, tabela, gráfico, média, mediana, moda, probabilidade, espaço amostral, evento, frequência
- Tabelas de dados reais (censo, população, resultados de experimentos)
- Experimentos aleatórios (moeda, dado, sorteio)
- Contextos: Mega-Sena, playlist aleatória, censo demográfico

**Linguagem metodológica ideal:**
- "Realizar experimento aleatório e registrar resultados..."
- "Calcular a probabilidade de [evento], expressando em fração, decimal e porcentagem..."
- "Interpretar os dados da tabela/gráfico, identificando tendências..."

**Cuidados:**
- Sempre partir de experimento concreto antes da definição formal
- Sempre incluir interpretação dos resultados (não apenas cálculo)
- Nunca apresentar probabilidade sem espaço amostral definido

---

### 3.6 Análise Combinatória
**Objetivo pedagógico:** Desenvolver raciocínio de contagem sistemática, distinguindo permutação, arranjo e combinação.

**Sinais típicos no PDF:**
- Palavras: combinação, permutação, arranjo, fatorial, contagem, possibilidades, agrupamento, ordem
- Situações de escolha e organização (placas, senhas, times, eventos)
- Árvore de possibilidades
- Problemas com "importa a ordem?" como questão central

**Linguagem metodológica ideal:**
- "Identificar se a ordem dos elementos importa para classificar o tipo de agrupamento..."
- "Calcular o número de possibilidades utilizando [permutação/arranjo/combinação]..."
- "Construir árvore de possibilidades para visualizar os casos..."

**Cuidados:**
- Sempre discutir "a ordem importa?" antes de escolher a técnica
- Nunca apresentar fórmula sem o raciocínio de contagem
- Sempre conectar com situações reais (senhas, placas, campeonatos)

---

### 3.7 Resolução de Problemas
**Objetivo pedagógico:** Desenvolver estratégias de resolução, comparação de caminhos e validação de resultados.

**Sinais típicos no PDF:**
- Palavras: situação-problema, desafio, estratégia, etapas, compreender, planejar, executar, verificar
- Problemas com múltiplas etapas de resolução
- Comparação de estratégias diferentes
- Problemas de vestibular/ENEM adaptados

**Linguagem metodológica ideal:**
- "Compreender o problema, identificando dados e o que se pede..."
- "Construir um plano de ação, escolhendo a estratégia mais adequada..."
- "Executar a resolução, registrando cada etapa..."
- "Verificar o resultado, interpretando no contexto do problema..."

**Cuidados:**
- Sempre incluir as 4 etapas de Polya (compreender, planejar, executar, verificar)
- Nunca avaliar apenas pela resposta final
- Sempre valorizar estratégias diferentes que chegam ao mesmo resultado

---

### 3.8 Modelagem Matemática
**Objetivo pedagógico:** Traduzir situações reais em linguagem matemática, resolver e interpretar os resultados no contexto original.

**Sinais típicos no PDF:**
- Palavras: modelar, representar, sentença matemática, lei de formação, equação, função
- Situações com dados reais (preços, distâncias, populações)
- Processo de tradução: verbal → algébrico → resolução → interpretação
- Contextos: carros elétricos vs híbridos, viralização, crescimento populacional

**Linguagem metodológica ideal:**
- "Identificar as grandezas e relações presentes na situação..."
- "Traduzir a situação para uma expressão/equação/função matemática..."
- "Resolver o modelo e interpretar o resultado no contexto original..."

---

## 4. REGRAS DE TRANSFORMAÇÃO DO PDF EM METODOLOGIA

| Elemento encontrado no PDF | O que o sistema deve entender | Como escrever na metodologia |
|---|---|---|
| **"VIREM E CONVERSEM"** | Atividade de discussão em duplas/grupos — etapa Para começar | "Propor discussão em duplas sobre [situação], levantando [hipóteses/estratégias/conhecimentos prévios]..." |
| **"TODO MUNDO ESCREVE"** | Atividade de resolução individual — etapa Na prática | "Orientar resolução individual de [atividade], solicitando registro de [procedimentos/estratégias/justificativas]..." |
| **"COM SUAS PALAVRAS"** | Síntese ou exploração com linguagem própria — Exploração ou Encerramento | "Solicitar que os estudantes expressem [conceito/estratégia] com suas próprias palavras, promovendo [síntese/reflexão]..." |
| **"HORA DA LEITURA"** | Texto motivador — etapa Para começar | "Realizar leitura compartilhada de [texto/notícia], identificando [conexão com conteúdo matemático]..." |
| **"DE OLHO NO MODELO"** | Exemplo resolvido — etapa Foco no conteúdo | "Apresentar exemplo resolvido de [tipo de problema], destacando [etapas/procedimentos/justificativas]..." |
| **"Relembre"** | Retomada de conteúdo anterior — substitui Para começar em aulas de revisão | "Retomar [conceito/procedimento] através de [atividade/discussão], verificando [compreensões prévias]..." |
| **Situação-problema inicial** | Contexto motivador — etapa Para começar | "Apresentar situação-problema sobre [contexto real], propondo [questionamento] para mobilizar conhecimentos prévios..." |
| **Gráfico cartesiano** | Representação visual de função/dados — Foco no conteúdo ou Exploração | "Analisar o gráfico de [função/dados], identificando [comportamento/tendência/valores específicos]..." |
| **Tabela de valores** | Dados organizados para análise — Exploração ou Foco no conteúdo | "Explorar a tabela de [dados], identificando [padrões/relações/variações] entre as grandezas..." |
| **Exemplo resolvido passo a passo** | Modelagem do procedimento — Foco no conteúdo | "Desenvolver coletivamente a resolução de [exemplo], destacando cada etapa e justificando os procedimentos..." |
| **Atividade com alternativas (A, B, C, D, E)** | Questão objetiva estilo ENEM/vestibular — Na prática | "Orientar resolução de questão objetiva sobre [tema], solicitando justificativa da alternativa escolhida..." |
| **"Veja no livro!"** | Referência ao material didático — Na prática | "Orientar consulta ao livro didático para [atividade], articulando com [conceito trabalhado]..." |
| **Uso de GeoGebra/calculadora** | Exploração com tecnologia — Exploração | "Orientar exploração de [conceito] utilizando [GeoGebra/calculadora], investigando [comportamento/propriedades]..." |
| **Árvore de possibilidades** | Representação de contagem — Foco no conteúdo | "Construir árvore de possibilidades para [situação], identificando sistematicamente todos os casos possíveis..." |
| **Mapa mental** | Síntese visual de conceitos — Encerramento ou Relembre | "Orientar construção de mapa mental sobre [tema], estabelecendo conexões entre [conceitos/propriedades/aplicações]..." |
| **Sequência numérica/padrão** | Investigação de regularidade — Exploração | "Investigar o padrão da sequência [dados], formulando hipótese sobre o termo geral..." |
| **Equação com incógnita** | Resolução algébrica — Foco no conteúdo | "Resolver a equação [tipo], aplicando [propriedades/técnicas], verificando a solução no contexto..." |
| **Porcentagem/fração/decimal** | Representações equivalentes — Foco no conteúdo | "Calcular [porcentagem/fração], convertendo entre representações e interpretando no contexto..." |
| **Dados reais (censo, pesquisa)** | Contextualização com dados verídicos — Para começar ou Exploração | "Analisar dados reais de [fonte], identificando [tendências/padrões] e conectando com [conceito matemático]..." |
| **Problema com etapas numeradas** | Resolução estruturada — Na prática | "Orientar resolução estruturada, seguindo as etapas: compreender o problema → planejar → executar → verificar..." |
| **Comparação de dois casos/situações** | Análise comparativa — Exploração ou Foco no conteúdo | "Comparar [situação A] e [situação B], identificando [semelhanças/diferenças/relações] e generalizando..." |
| **Texto de notícia/artigo** | Contextualização real — Para começar (HORA DA LEITURA) | "Realizar leitura de [texto/notícia], identificando o problema matemático implícito e levantando hipóteses..." |

---

## 5. TEMPLATES PRONTOS PARA O SISTEMA

### Para começar

**Modelo 1 — VIREM E CONVERSEM (mais frequente):**
"Apresentar situação-problema sobre [contexto real — ex: planejamento financeiro, velocidade de internet, crescimento populacional], propondo discussão em duplas a partir de questionamentos como: [pergunta 1] e [pergunta 2]. Socializar as respostas com a turma, levantando hipóteses e mobilizando conhecimentos prévios sobre [conceito matemático]."

**Modelo 2 — HORA DA LEITURA:**
"Realizar leitura compartilhada de [texto/notícia sobre tema real], identificando o problema matemático presente na situação. Propor discussão sobre [conexão com conteúdo], levantando o que os estudantes já sabem sobre [conceito]."

**Modelo 3 — COM SUAS PALAVRAS (exploração inicial):**
"Apresentar [situação/questionamento inicial], solicitando que os estudantes expressem com suas próprias palavras [o que entendem / o que precisam descobrir / como resolveriam]. Socializar as respostas, identificando estratégias e conhecimentos prévios."

**Modelo 4 — Relembre (aulas de retomada/verificação):**
"Retomar os conceitos de [conteúdo anterior] através de [discussão/atividade], verificando a compreensão dos estudantes e identificando possíveis dúvidas antes de avançar para [novo conteúdo/aplicação]."

---

### Exploração

**Modelo 1 — Investigação com dados:**
"Explorar [tabela/gráfico/sequência de dados], orientando os estudantes a identificar padrões, relações e variações entre as grandezas. Propor questionamentos como: [o que acontece quando...?] e [qual a relação entre...?], estimulando a formulação de hipóteses antes da formalização."

**Modelo 2 — Investigação com tecnologia:**
"Orientar exploração de [função/conceito] utilizando [GeoGebra/calculadora científica], propondo que os estudantes investiguem [comportamento/propriedades] a partir de [parâmetros/valores específicos]. Registrar as observações e discutir os padrões identificados."

**Modelo 3 — Construção coletiva:**
"Desenvolver coletivamente a análise de [situação/exemplo], orientando os estudantes a identificar [grandezas/relações/padrões] e a construir progressivamente a compreensão de [conceito], partindo do concreto para o abstrato."

---

### Foco no conteúdo

**Modelo 1 — Conceito novo com DE OLHO NO MODELO:**
"Apresentar o conceito de [conteúdo matemático], conectando com a situação-problema inicial. Desenvolver exemplo resolvido passo a passo, destacando: [etapa 1], [etapa 2] e [etapa 3]. Enfatizar [propriedade/regra central] e sua justificativa, evitando a memorização mecânica."

**Modelo 2 — Formalização após exploração:**
"Sistematizar os padrões identificados na exploração, formalizando o conceito de [conteúdo]. Apresentar a definição/propriedade/fórmula como consequência natural da investigação realizada, conectando a linguagem matemática formal com a linguagem verbal utilizada pelos estudantes."

**Modelo 3 — Análise de representações múltiplas:**
"Analisar [conceito/situação] em suas diferentes representações: [numérica/tabular/gráfica/algébrica/verbal], destacando como cada representação revela aspectos diferentes do mesmo objeto matemático. Orientar a transição entre representações."

---

### Formalização

**Modelo 1 — Definição formal:**
"Apresentar formalmente a definição de [conceito], destacando [condições/restrições/propriedades]. Justificar cada elemento da definição a partir dos exemplos explorados, garantindo que a formalização seja compreendida e não apenas memorizada."

**Modelo 2 — Propriedades e consequências:**
"Sistematizar as propriedades de [conceito], demonstrando cada uma a partir de [exemplos/casos específicos]. Orientar os estudantes a verificar as propriedades com valores concretos antes de generalizá-las."

---

### Pause e responda

**Modelo 1 — Socialização de estratégias:**
"Socializar as respostas e estratégias utilizadas pelos estudantes, promovendo discussão sobre [diferentes caminhos de resolução]. Retomar [conceito/propriedade central], corrigindo equívocos e reforçando a compreensão. Validar coletivamente os resultados obtidos."

**Modelo 2 — Verificação de compreensão:**
"Propor questão de verificação sobre [conceito trabalhado], solicitando que os estudantes respondam individualmente e depois comparem com o colega. Socializar as respostas, identificando dúvidas e consolidando a compreensão antes de avançar para a prática."

---

### Na prática

**Modelo 1 — TODO MUNDO ESCREVE (resolução individual):**
"Orientar resolução individual das atividades [número/tipo], solicitando registro completo dos procedimentos e justificativas. Circular pela sala, acompanhando o desenvolvimento e identificando dificuldades. Ao final, socializar as resoluções, valorizando diferentes estratégias que chegam ao mesmo resultado."

**Modelo 2 — Questões objetivas com justificativa:**
"Orientar resolução de questões objetivas sobre [tema], solicitando que os estudantes não apenas marquem a alternativa, mas registrem o raciocínio utilizado. Socializar as resoluções, discutindo por que as alternativas incorretas estão erradas."

**Modelo 3 — Resolução estruturada em etapas:**
"Orientar resolução de [problema/situação] seguindo as etapas: (1) compreender o problema — identificar dados e o que se pede; (2) construir um plano — escolher a estratégia; (3) executar — resolver registrando cada passo; (4) verificar — checar o resultado no contexto. Socializar e comparar estratégias."

---

### Encerramento

**Modelo 1 — Síntese coletiva:**
"Retomar coletivamente os principais conceitos e procedimentos trabalhados na aula, solicitando que os estudantes sintetizem [aprendizado central] com suas próprias palavras. Registrar no quadro as ideias-chave e conectar com [próxima aula/aplicação futura]."

**Modelo 2 — Mapa mental / síntese visual:**
"Orientar construção de mapa mental ou síntese visual sobre [tema da aula], estabelecendo conexões entre [conceitos/propriedades/aplicações]. Socializar as produções, complementando com elementos não mencionados."

**Modelo 3 — Conexão com contexto real:**
"Retomar a situação-problema inicial, respondendo coletivamente à questão proposta no início da aula com os conceitos formalizados. Destacar como a Matemática permitiu [resolver/compreender/modelar] a situação real, conectando com [aplicações cotidianas/outras disciplinas]."

---

## 6. PALAVRAS-CHAVE PARA CLASSIFICAÇÃO AUTOMÁTICA

### Álgebra
```python
["equação", "equações", "variável", "incógnita", "expressão", "polinômio",
 "1º grau", "2º grau", "exponencial", "logaritmo", "logarítmica",
 "modelar", "sentença matemática", "resolver", "solução", "raiz",
 "sistema", "inequação", "módulo"]
```

### Funções
```python
["função", "funções", "lei de formação", "domínio", "imagem", "contradomínio",
 "crescente", "decrescente", "gráfico", "dependência", "variável dependente",
 "variável independente", "f(x)", "taxa de variação", "zero da função",
 "linear", "afim", "quadrática", "exponencial", "logarítmica"]
```

### Geometria
```python
["ângulo", "triângulo", "quadrilátero", "polígono", "circunferência", "círculo",
 "área", "perímetro", "volume", "superfície", "diagonal", "altura", "base",
 "semelhança", "congruência", "teorema", "Pitágoras", "trigonometria",
 "seno", "cosseno", "tangente", "construção geométrica", "malha"]
```

### Grandezas e Medidas / Proporcionalidade
```python
["razão", "proporção", "grandeza", "diretamente proporcional",
 "inversamente proporcional", "taxa", "velocidade", "densidade",
 "escala", "unidade", "conversão", "km/h", "m/s", "Mbps", "Kbps",
 "regra de três", "porcentagem", "juros", "desconto"]
```

### Estatística e Probabilidade
```python
["probabilidade", "evento", "espaço amostral", "experimento aleatório",
 "frequência", "frequência relativa", "média", "mediana", "moda",
 "desvio", "variância", "tabela de frequência", "gráfico de barras",
 "histograma", "diagrama", "dados", "amostra", "população",
 "censo", "pesquisa", "equiprovável", "árvore de possibilidades"]
```

### Análise Combinatória
```python
["combinação", "permutação", "arranjo", "fatorial", "contagem",
 "princípio multiplicativo", "princípio aditivo", "agrupamento",
 "possibilidades", "ordem importa", "sem repetição", "com repetição",
 "anagrama", "senha", "placa", "time", "comissão", "delegação"]
```

### Números e Operações
```python
["número", "natural", "inteiro", "racional", "irracional", "real",
 "fração", "decimal", "porcentagem", "potência", "raiz", "logaritmo",
 "operação", "adição", "subtração", "multiplicação", "divisão",
 "mmc", "mdc", "divisibilidade", "primo", "fatoração"]
```

### Resolução de Problemas
```python
["situação-problema", "problema", "desafio", "estratégia", "etapas",
 "compreender", "planejar", "executar", "verificar", "solução",
 "raciocínio", "modelagem", "contexto", "aplicação", "ENEM",
 "vestibular", "adaptada", "resolva", "determine", "calcule"]
```

### Modelagem Matemática
```python
["modelar", "modelo matemático", "representar", "traduzir",
 "lei de formação", "equação que representa", "função que modela",
 "situação real", "contexto", "grandezas", "relação entre",
 "crescimento", "decrescimento", "variação"]
```

---

## 7. TÉCNICAS PEDAGÓGICAS DA DISCIPLINA

### Técnicas identificadas nos PDFs e como devem aparecer na metodologia:

| Técnica | Como aparece no PDF | Como escrever na metodologia |
|---------|---------------------|------------------------------|
| **VIREM E CONVERSEM** | Discussão em duplas/grupos sobre situação inicial | "Propor discussão em duplas sobre [situação], levantando [hipóteses/estratégias]..." |
| **TODO MUNDO ESCREVE** | Resolução individual de atividades | "Orientar resolução individual de [atividade], solicitando registro completo dos procedimentos..." |
| **COM SUAS PALAVRAS** | Síntese ou exploração com linguagem própria | "Solicitar síntese de [conceito] com as próprias palavras, promovendo [reflexão/consolidação]..." |
| **HORA DA LEITURA** | Texto motivador no início da aula | "Realizar leitura de [texto/notícia], identificando o problema matemático e levantando hipóteses..." |
| **DE OLHO NO MODELO** | Exemplo resolvido passo a passo | "Apresentar exemplo resolvido de [tipo], destacando cada etapa e justificando os procedimentos..." |
| **Relembre** | Retomada de conteúdo anterior | "Retomar [conceito] através de [atividade], verificando compreensões e identificando dúvidas..." |
| **Exploração com GeoGebra** | Investigação com software de geometria dinâmica | "Orientar exploração de [conceito] no GeoGebra, investigando [comportamento/propriedades]..." |
| **Exploração com calculadora** | Investigação de padrões com calculadora científica | "Orientar exploração de [padrão/propriedade] com calculadora, completando tabela e identificando relações..." |
| **Árvore de possibilidades** | Representação sistemática de casos | "Construir árvore de possibilidades para [situação], listando sistematicamente todos os casos..." |
| **Mapa mental** | Síntese visual de conceitos e conexões | "Orientar construção de mapa mental sobre [tema], conectando [conceitos/propriedades/aplicações]..." |
| **Resolução em etapas (Polya)** | Problema com etapas: compreender → planejar → executar → verificar | "Orientar resolução estruturada em 4 etapas: compreender, planejar, executar e verificar..." |
| **Comparação de estratégias** | Múltiplas formas de resolver o mesmo problema | "Socializar diferentes estratégias de resolução, comparando caminhos e validando resultados..." |

### Técnicas e abordagens que devem ser EVITADAS:

```python
TECNICAS_PROIBIDAS_MATEMATICA = [
    "memorização de fórmulas sem compreensão",
    "repetição mecânica de algoritmos sem discussão",
    "cálculo sem justificativa ou interpretação",
    "correção apenas pela resposta final (sem valorizar o processo)",
    "apresentar definição/fórmula antes do problema motivador",
    "exercícios sem contexto ou aplicação real",
    "correção expositiva sem participação dos estudantes",
    "avaliação punitiva de erros sem aproveitamento pedagógico"
]
```

---

## 8. EXEMPLOS DE SAÍDA FINAL

### Exemplo 1 — Álgebra (Modelagem com Equação do 1º Grau)

**Para começar:**
Apresentar situação-problema sobre planejamento financeiro: "Marta quer comprar um celular que custa R$ 3.800,00. Ela já tem R$ 290,00 e pretende guardar a mesma quantia todo mês. Em quantos meses ela atingirá seu objetivo?" Propor discussão em duplas (VIREM E CONVERSEM) sobre: quais grandezas estão envolvidas? Como representar matematicamente a situação? Socializar as hipóteses com a turma.

**Exploração:**
Orientar os estudantes a identificar as grandezas do problema (tempo e valor acumulado) e a representar a relação entre elas de forma verbal e depois simbólica. Propor: "Se ela guardar x reais por mês, como fica a expressão para o total acumulado após n meses?" Registrar as representações no quadro, comparando as diferentes formas encontradas pelos estudantes.

**Foco no conteúdo:**
Apresentar o conceito de equação do 1º grau como ferramenta para modelar a situação. Desenvolver coletivamente (DE OLHO NO MODELO) a resolução: identificar a incógnita → montar a equação → aplicar propriedades de igualdade → encontrar a solução. Destacar que a equação ax + b = c representa a relação entre as grandezas do problema.

**Formalização:**
Sistematizar a definição de equação do 1º grau na forma ax + b = 0, apresentando as propriedades de igualdade utilizadas na resolução. Justificar cada propriedade com exemplos concretos, conectando com a resolução da situação-problema inicial.

**Pause e responda:**
Socializar as resoluções, comparando estratégias utilizadas pelos estudantes. Verificar se o resultado faz sentido no contexto: "O número de meses encontrado é razoável? Como podemos verificar?" Retomar as propriedades de igualdade, corrigindo equívocos identificados.

**Na prática:**
Orientar resolução individual (TODO MUNDO ESCREVE) de situações-problema envolvendo equações do 1º grau em contextos variados (consumo, distância, produção). Solicitar registro completo: identificação das grandezas → montagem da equação → resolução → interpretação do resultado. Socializar as resoluções, valorizando diferentes estratégias.

**Encerramento:**
Retomar a situação-problema inicial, respondendo coletivamente com o conceito formalizado. Sintetizar: "Quando temos uma relação linear entre grandezas e precisamos encontrar um valor desconhecido, a equação do 1º grau é a ferramenta adequada." Conectar com aplicações em Educação Financeira e situações cotidianas.

---

### Exemplo 2 — Geometria (Gráfico de Função Exponencial)

**Para começar:**
Apresentar situação sobre crescimento exponencial: "Em uma corrente do bem, cada pessoa ajuda outras 3. Iniciando com 1 pessoa, em quanto tempo o gesto poderia atingir o mundo todo?" Propor discussão em duplas (VIREM E CONVERSEM) sobre: como o número de pessoas cresce a cada dia? Há algum padrão? Socializar as hipóteses, registrando as estimativas no quadro.

**Exploração:**
Orientar exploração no GeoGebra: digitar as funções y = 2^x e y = (1/2)^x, depois y = 3^x e y = (1/3)^x. Propor investigação: "O que acontece com o gráfico quando a base é maior que 1? E quando está entre 0 e 1?" Registrar as observações em tabela, identificando padrões no comportamento crescente e decrescente.

**Foco no conteúdo:**
Sistematizar as observações da exploração, apresentando as características do gráfico da função exponencial f(x) = a^x: quando a > 1 (crescente), quando 0 < a < 1 (decrescente), domínio, imagem, ponto fixo (0,1). Conectar com a situação da corrente do bem: "Qual função modela o crescimento? Qual é a base? O que representa?"

**Formalização:**
Apresentar formalmente a definição de função exponencial, destacando as restrições da base (a > 0 e a ≠ 1). Justificar cada restrição com exemplos concretos. Sistematizar as propriedades do gráfico identificadas na exploração, conectando representação gráfica com lei de formação.

**Pause e responda:**
Propor questão de verificação: "Dado o gráfico de uma função exponencial, como identificar se a base é maior ou menor que 1?" Socializar as respostas, consolidando a compreensão das características do gráfico. Retomar a situação da corrente do bem, respondendo à questão inicial com o conceito formalizado.

**Na prática:**
Orientar resolução individual (TODO MUNDO ESCREVE) de atividades envolvendo identificação e análise de gráficos de funções exponenciais. Incluir questões que exijam: identificar a base a partir do gráfico, determinar valores, comparar comportamentos. Socializar as resoluções, discutindo as estratégias utilizadas.

**Encerramento:**
Retomar coletivamente as características do gráfico da função exponencial, conectando com situações reais de crescimento e decrescimento (população, juros, radioatividade, viralização). Sintetizar: "A função exponencial modela situações em que há crescimento ou decrescimento muito acentuado, com taxa constante de multiplicação."

---

### Exemplo 3 — Estatística e Probabilidade (Cálculo de Probabilidade)

**Para começar:**
Realizar atividade experimental: em duplas, lançar uma moeda 14 vezes e registrar os resultados em tabela. Propor discussão: "O que saiu mais vezes — cara ou coroa? Esse resultado era esperado? Se lançássemos mais vezes, o que aconteceria?" Socializar os resultados de todas as duplas, construindo uma tabela coletiva e identificando a tendência de equilíbrio.

**Exploração:**
Apresentar dados históricos de experimentos com moedas (Kerrich: 10.000 lançamentos, 50,67% caras; Pearson: 24.000 lançamentos, 50,05% caras). Propor análise: "Por que, mesmo com resultados diferentes, todos ficaram próximos de 50%? O que isso indica sobre a probabilidade teórica?" Conectar frequência relativa experimental com probabilidade teórica.

**Foco no conteúdo:**
Apresentar o conceito de probabilidade de um evento: P(E) = número de casos favoráveis / número de casos possíveis. Desenvolver o conceito de espaço amostral, evento e evento equiprovável. Calcular a probabilidade de cara no lançamento de moeda, conectando com os resultados experimentais obtidos. Apresentar as formas de expressão: fração, decimal e porcentagem.

**Formalização:**
Sistematizar a definição formal de probabilidade, destacando as propriedades: 0 ≤ P(E) ≤ 1, P(evento certo) = 1, P(evento impossível) = 0. Apresentar a classificação de eventos: impossível, pouco provável, muito provável, certo. Conectar com os experimentos realizados.

**Pause e responda:**
Propor questão: "Em um dado honesto, qual a probabilidade de sair número par? E número maior que 4?" Socializar as resoluções, verificando se os estudantes identificam corretamente o espaço amostral e os casos favoráveis. Retomar a definição, corrigindo equívocos.

**Na prática:**
Orientar resolução individual (TODO MUNDO ESCREVE) de problemas de probabilidade em contextos variados (dados, cartas, urnas, sorteios). Solicitar: identificação do espaço amostral → identificação dos casos favoráveis → cálculo → expressão em fração, decimal e porcentagem → interpretação. Socializar as resoluções.

**Encerramento:**
Retomar a atividade experimental inicial, conectando os resultados obtidos com a probabilidade teórica calculada. Sintetizar: "A probabilidade teórica indica o que esperamos que aconteça no longo prazo — quanto mais experimentos, mais os resultados se aproximam da probabilidade teórica." Conectar com aplicações: seguros, medicina, meteorologia, jogos.

---

### Exemplo 4 — Resolução de Problemas (Análise Combinatória)

**Para começar:**
Apresentar situação sobre placas de veículos: "Até 2018, as placas seguiam o padrão AAA-0000. A partir de 2018, o padrão Mercosul é AAA0A00. Por que essa mudança foi necessária? Como ela aumenta as combinações possíveis?" Propor discussão em duplas (VIREM E CONVERSEM): quais são as diferenças? Como calcular o total de combinações de cada padrão? Socializar as hipóteses.

**Exploração:**
Orientar exploração sistemática: "Para uma placa com apenas 2 letras (A-Z) e 1 número (0-9), quantas combinações são possíveis?" Construir árvore de possibilidades para casos simples, identificando o padrão multiplicativo. Propor: "O que acontece quando aumentamos o número de posições? Existe uma regra geral?" Registrar as descobertas.

**Foco no conteúdo:**
Apresentar o Princípio Multiplicativo da Contagem: se uma escolha pode ser feita de m maneiras e outra de n maneiras, o total de combinações é m × n. Aplicar ao problema das placas: calcular o total de combinações do padrão antigo e do novo. Destacar a diferença e justificar por que o novo padrão garante mais opções.

**Formalização:**
Sistematizar o Princípio Multiplicativo, apresentando a notação e generalizando para k etapas independentes. Conectar com os conceitos de permutação, arranjo e combinação, destacando a questão central: "A ordem importa?" Apresentar as fórmulas como consequência do raciocínio de contagem, não como regras a memorizar.

**Pause e responda:**
Propor questão: "Em um evento com 5 palestrantes, de quantas formas diferentes podemos organizar a ordem das apresentações? E se precisarmos escolher apenas 3 dos 5 para apresentar, sem importar a ordem?" Socializar as resoluções, discutindo a diferença entre permutação, arranjo e combinação.

**Na prática:**
Orientar resolução individual (TODO MUNDO ESCREVE) de problemas de contagem em contextos variados (senhas, times, comissões, campeonatos). Para cada problema, solicitar: identificar se a ordem importa → escolher a técnica adequada → calcular → verificar se o resultado faz sentido. Socializar, comparando estratégias.

**Encerramento:**
Retomar a situação das placas, respondendo com os conceitos formalizados. Sintetizar as três técnicas: "Permutação — todos os elementos, ordem importa; Arranjo — parte dos elementos, ordem importa; Combinação — parte dos elementos, ordem não importa." Conectar com aplicações: criptografia, segurança digital, logística, esportes.

---

## 9. REGRAS PARA IMPLEMENTAÇÃO EM PYTHON

```python
# ============================================================
# REGRAS IMPLEMENTÁVEIS — MATEMÁTICA
# Sistema Python de Geração de Planos de Aula SEDUC/SP
# ============================================================

# --- IDENTIFICAÇÃO DO PERFIL ---
# se disciplina contém "Matemática" ou "matematica" → usar perfil "matematica"
# se disciplina contém "Matemática" + "Fundamental" → usar perfil "matematica_ef"
# se disciplina contém "Matemática" + "Médio" → usar perfil "matematica_em"

# --- CLASSIFICAÇÃO DO TIPO DE AULA ---
# se texto contém ["equação", "variável", "incógnita", "expressão", "polinômio"] → tipo "algebra"
# se texto contém ["função", "lei de formação", "f(x)", "domínio", "imagem", "gráfico"] → tipo "funcoes"
# se texto contém ["área", "perímetro", "ângulo", "triângulo", "polígono", "volume"] → tipo "geometria"
# se texto contém ["razão", "proporção", "grandeza", "taxa", "velocidade", "escala"] → tipo "grandezas_medidas"
# se texto contém ["probabilidade", "evento", "espaço amostral", "frequência", "média", "mediana"] → tipo "estatistica_probabilidade"
# se texto contém ["combinação", "permutação", "arranjo", "fatorial", "contagem"] → tipo "combinatoria"
# se texto contém ["situação-problema", "desafio", "estratégia", "etapas", "modelar"] → tipo "resolucao_problemas"
# se texto contém ["modelar", "modelo matemático", "lei de formação", "representa"] → tipo "modelagem"

# --- DETECÇÃO DO TIPO DE AULA PELO TÍTULO ---
# se título contém "verificação" ou "verificação" → tipo_aula = "verificacao" → estrutura: Relembre → Na prática → Encerramento
# se título contém "retomando" ou "explorando" → tipo_aula = "retomada" → estrutura: Relembre → Foco → Na prática → Encerramento
# se título contém "modelagem" ou "modelando" → tipo_aula = "modelagem" → estrutura completa com Exploração
# se título contém "resolução de problemas" → tipo_aula = "resolucao" → estrutura completa com Exploração

# --- DETECÇÃO DE TÉCNICAS NO PDF ---
# se texto contém "VIREM E CONVERSEM" → incluir técnica na etapa "Para começar"
# se texto contém "TODO MUNDO ESCREVE" → incluir técnica na etapa "Na prática"
# se texto contém "COM SUAS PALAVRAS" → incluir técnica na etapa "Exploração" ou "Encerramento"
# se texto contém "HORA DA LEITURA" → incluir técnica na etapa "Para começar"
# se texto contém "DE OLHO NO MODELO" → incluir técnica na etapa "Foco no conteúdo"
# se texto contém "Relembre" → substituir "Para começar" por "Relembre" na estrutura
# se texto contém "GeoGebra" ou "geogebra" → incluir exploração com tecnologia
# se texto contém "calculadora" → incluir exploração com calculadora
# se texto contém "mapa mental" → incluir no Encerramento

# --- ESTRUTURA DE ETAPAS POR TIPO ---
ESTRUTURAS_MATEMATICA = {
    "conceito_novo": ["Para começar", "Exploração", "Foco no conteúdo", "Formalização", "Pause e responda", "Na prática", "Encerramento"],
    "modelagem": ["Para começar", "Exploração", "Foco no conteúdo", "Pause e responda", "Na prática", "Encerramento"],
    "verificacao": ["Relembre", "Na prática", "Encerramento"],
    "retomada": ["Relembre", "Foco no conteúdo", "Pause e responda", "Na prática", "Encerramento"],
    "investigacao_tecnologia": ["Para começar", "Exploração", "Foco no conteúdo", "Pause e responda", "Encerramento"],
    "resolucao_problemas": ["Para começar", "Exploração", "Foco no conteúdo", "Pause e responda", "Na prática", "Encerramento"],
    "default": ["Para começar", "Foco no conteúdo", "Pause e responda", "Na prática", "Encerramento"]
}

# --- VERBOS PRIORITÁRIOS ---
# para perfil "matematica", priorizar verbos:
VERBOS_MATEMATICA = [
    "apresentar", "explorar", "investigar", "desenvolver", "sistematizar",
    "orientar", "socializar", "validar", "formalizar", "analisar",
    "comparar", "identificar", "calcular", "modelar", "interpretar",
    "justificar", "verificar", "generalizar", "conectar", "retomar"
]

# --- VERBOS PROIBIDOS ---
VERBOS_PROIBIDOS_MATEMATICA = [
    "memorizar", "decorar", "copiar", "repetir mecanicamente",
    "treinar", "praticar sem compreensão"
]

# --- REGRAS OBRIGATÓRIAS ---
# para perfil "matematica", SEMPRE:
REGRAS_OBRIGATORIAS_MATEMATICA = [
    "iniciar com situação-problema ou contexto real (nunca com definição/fórmula)",
    "incluir discussão de estratégias (não apenas resposta final)",
    "incluir validação/verificação do resultado",
    "incluir interpretação do resultado no contexto do problema",
    "incluir pelo menos uma técnica identificada no PDF (VIREM E CONVERSEM, TODO MUNDO ESCREVE, etc.)",
    "conectar o conteúdo com aplicação real ao final"
]

# --- REGRAS PROIBIDAS ---
REGRAS_PROIBIDAS_MATEMATICA = [
    "NUNCA apresentar fórmula/definição antes do problema motivador",
    "NUNCA avaliar apenas pela resposta final sem valorizar o processo",
    "NUNCA incluir exercícios sem contexto ou aplicação",
    "NUNCA omitir etapa de interpretação do resultado",
    "NUNCA usar linguagem de memorização (ex: 'memorize que...', 'a fórmula é...')"
]

# --- REGRAS POR TIPO ---
# para tipo "geometria": SEMPRE incluir apoio visual e análise de propriedades
# para tipo "estatistica_probabilidade": SEMPRE incluir leitura e interpretação de dados; incluir experimento quando possível
# para tipo "algebra": SEMPRE incluir relação entre linguagem verbal → expressão algébrica → resolução → interpretação
# para tipo "funcoes": SEMPRE incluir múltiplas representações (tabela, gráfico, expressão, verbal)
# para tipo "combinatoria": SEMPRE discutir "a ordem importa?" antes de escolher a técnica
# para tipo "modelagem": SEMPRE incluir etapas: identificar grandezas → traduzir → resolver → interpretar
# para tipo "resolucao_problemas": SEMPRE incluir as 4 etapas de Polya

# --- DETECÇÃO DE AULA DE VERIFICAÇÃO ---
# se título contém "verificação" E estrutura do PDF tem apenas "Na prática" com múltiplas atividades
# → usar estrutura: Relembre → Na prática (atividade 1, 2, 3...) → Encerramento
# → NÃO incluir Foco no conteúdo ou Formalização

# --- TEMPO POR ETAPA (referência dos PDFs) ---
TEMPO_ETAPAS_MATEMATICA = {
    "Para começar / VIREM E CONVERSEM": "5-10 minutos",
    "Para começar / HORA DA LEITURA": "10 minutos",
    "Exploração / GeoGebra": "20 minutos",
    "Foco no conteúdo": "10-15 minutos",
    "Na prática / TODO MUNDO ESCREVE": "5-10 minutos por atividade",
    "Relembre / COM SUAS PALAVRAS": "10 minutos"
}
```

---

## 10. MAPA RESUMIDO FINAL

| Disciplina | Perfil Python | Tipos de aula | Etapas principais | Palavras-chave centrais | Cuidados críticos | Exemplo curto de metodologia |
|---|---|---|---|---|---|---|
| **Matemática** | `matematica` | álgebra, funções, geometria, grandezas_medidas, estatistica_probabilidade, combinatoria, resolucao_problemas, modelagem, verificacao | Para começar → Exploração → Foco no conteúdo → Formalização → Pause e responda → Na prática → Encerramento | equação, função, gráfico, probabilidade, combinação, situação-problema, modelar, grandeza, razão | NUNCA começar com fórmula/definição; SEMPRE partir de situação-problema; SEMPRE incluir interpretação do resultado; NUNCA avaliar só pela resposta final; SEMPRE incluir discussão de estratégias | **Para começar:** Apresentar situação sobre [contexto real], propondo discussão em duplas sobre [questionamento]. **Foco:** Desenvolver [conceito] a partir da situação, formalizando após exploração. **Na prática:** Orientar resolução individual com registro de procedimentos e justificativas. **Encerramento:** Retomar a situação inicial, respondendo com o conceito formalizado. |

---

## APÊNDICE — PADRÃO REAL DOS PDFs ANALISADOS

### Séries identificadas nos PDFs:
- **Série Aula01-Aula10** (Ensino Médio): Equações do 1º grau, Modelagem algébrica, Grandezas de espécies diferentes, Proporcionalidade, Relação entre grandezas
- **Série Aula001-Aula012** (Ensino Médio): Equações exponenciais, Função exponencial, Gráfico de função exponencial, Logaritmos, Equações logarítmicas
- **Série Aula0001-Aula0011** (Ensino Médio): Princípio multiplicativo, Permutações, Arranjos, Combinações, Probabilidade, Espaço amostral

### Técnicas mais frequentes (por ordem de ocorrência):
1. VIREM E CONVERSEM — presente em quase todas as aulas de Para começar
2. TODO MUNDO ESCREVE — presente em quase todas as aulas de Na prática
3. COM SUAS PALAVRAS — presente em aulas de exploração e síntese
4. HORA DA LEITURA — presente em aulas com texto motivador
5. DE OLHO NO MODELO — presente em aulas com exemplo resolvido
6. Relembre — presente em aulas de retomada e verificação

### Contextos reais mais utilizados (referência para o sistema):
- Finanças pessoais (planejamento, juros, cartão de crédito, orçamento)
- Tecnologia (internet, velocidade, GeoGebra, aplicativos)
- Esportes (Brasileirão, campeonatos, artilheiros)
- Meio ambiente (consumo de água, sustentabilidade)
- Cultura e entretenimento (Virada Cultural, filmes, playlists)
- Cidadania (placas Mercosul, ENEM, gov.br, Mega-Sena como contexto matemático)
- Ciências (crescimento populacional, viralização, pH)

---

*Análise gerada com base em 30 PDFs reais de aulas de Matemática — Ensino Médio — SEDUC/SP — 2º Bimestre*
*Perfil Python: `matematica` | Versão: 2.0 — Baseada em dados reais*