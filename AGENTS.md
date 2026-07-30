# AGENTS.md — Sistema Planos Luan

> Instruções operacionais para agentes que trabalham neste repositório. Leia este arquivo integralmente antes de analisar ou alterar o sistema.

---

## 1. POSTURA DE TRABALHO COM O USUÁRIO

- Converse em português do Brasil, com linguagem simples, amigável e de bom humor.
- Explique primeiro o resultado prático; detalhe a parte técnica somente quando ela ajudar na decisão.
- Trabalhe em etapas curtas e verificáveis, preferencialmente com no máximo duas ações por vez.
- Diferencie claramente: diagnóstico, implementação, teste estrutural e teste visual/funcional.
- Se o pedido for apenas analisar, diagnosticar ou planejar, não altere arquivos.
- Quando houver autorização para corrigir ou construir, implemente, teste e informe exatamente o que foi validado.
- Não amplie o escopo sem necessidade. Preserve alterações locais do usuário e não mexa em arquivos alheios à tarefa.
- Antes de exclusões de cadastros, documentos ou dados, identifique a origem e confirme o alvo exato. Não apague DOCX apenas porque um cadastro foi removido do banco.

---

## 2. VISÃO GERAL ATUAL

**Planos Luan** é uma aplicação Python/Streamlit para gerar planos mensais de aula. O sistema organiza o calendário real do professor, localiza PDFs pedagógicos, extrai conteúdo e habilidades, aplica metodologia com ou sem IA, preenche modelos Word e registra os planos no SQLite.

- **Versão atual do gerador:** `1.2.13`, definida em `core/revisao_final.py`.
- **Stack principal:** Python 3.12, Streamlit, python-docx, pdfplumber, SQLite em WAL e Pydantic compatível com v1/v2.
- **Frontend principal:** `planos_luan_app.py`.
- **Backend:** `core/`, com componentes compartilhados principalmente em `core/lib/`.
- **Geração Word:** `docx_generator/`.
- **Interface modular:** `ui/`.
- **Testes:** `tests/`.
- **Banco local:** `planos_luan.db`, na raiz do repositório.

### Modos disponíveis na interface

1. `Planos gerais`
2. `CDP - Ciclo I`
3. `EJA`
4. `Cadastro`
5. `Diagnóstico`
6. `Histórico`

Planos EJA devem ser iniciados na aba **EJA**, não em **Planos gerais**. A aba determina a modalidade, a linguagem pedagógica, os limites de texto e a rota de PDFs.

---

## 3. FONTES DE DADOS E CAMINHOS OFICIAIS

Os arquivos pedagógicos operacionais ficam fora do Git, na raiz definida em `config.py`:

```text
C:\Users\Luan Dias\PLANOS_LUAN_DADOS\PDF_AULAS
```

O caminho é calculado por `PLANOS_LUAN_DADOS_DIR` e `PDF_AULAS_DIR`. Não criar fallback para OneDrive, Documents, pastas antigas ou cópias encontradas por acaso. Isso pode fazer o sistema usar um material desatualizado sem avisar.

### Pastas importantes já reconhecidas

- Biologia EJA: `BIOLOGIA\EJA_BIOLOGIA`.
- Biologia EJA — 2º e 3º Termo: ambos usam os conteúdos de `3_BIMESTRE\2_TERMO` quando esse bimestre é selecionado.
- Liderança e Oratória EJA: `LIDERANCA_E_ORATORIA\EJA_EM`.
- Língua Inglesa EJA: `LINGUA_INGLESA\EJA_EM`.
- Orientação de Estudos: `ORIENTACAO_DE_ESTUDOS\EF\<ANO>`.

As regras de aliases e resolução de pastas ficam em `core/helpers.py`. Ao acrescentar uma nova rota, testar nome da disciplina, modalidade, bimestre e turma separadamente.

### DOCX de referência dentro da pasta dos PDFs

Nos planos regulares, o DOCX pedagógico colocado na mesma árvore dos PDFs é a fonte obrigatória da metodologia, do acompanhamento da aprendizagem e da acessibilidade. Sem a referência correspondente, o sistema não deve inventar essas colunas internamente. As exceções são EJA, CDP, Orientação de Estudos (etapas extraídas do PDF da missão) e aulas que já tragam metodologia estruturada no próprio material.

O formato reconhecido deve manter, por aula:

```text
AULA 1 — Título da aula
HABILIDADE: Texto da habilidade

METODOLOGIA
Para começar: ...
Foco no conteúdo: ...

ACOMPANHAMENTO DA APRENDIZAGEM
Item 1
Item 2
Item 3

ACESSIBILIDADE
Item 1
Item 2
Item 3
```

- A correspondência é feita pelo número da aula, não apenas pela semelhança do título.
- Uma aula incompleta no DOCX não deve substituir o conteúdo do PDF silenciosamente.
- Antes de acionar a IA, diferenciar sempre: DOCX inexistente; DOCX encontrado sem aula utilizável; etapa obrigatória ausente; ou etapa acima de 350 caracteres. Nunca informar que o arquivo “não foi encontrado” quando o problema está no conteúdo da aula.
- A mensagem ao usuário deve indicar o nome do DOCX, o número da aula e a correção necessária. Acompanhamento e acessibilidade com menos de três itens continuam opcionais, pois o sistema os completa automaticamente.
- Arquivos temporários `~$*.docx` e cópias com nome de backup devem ser ignorados.
- Em Orientação de Estudos, a habilidade do DOCX padronizado tem prioridade sobre a habilidade do PDF.
- O leitor usa no máximo três itens de acompanhamento e três de acessibilidade por aula.

---

## 4. PIPELINE ATUAL DE GERAÇÃO

```text
PDF/PPTX ou localização automática
  └─► core/contexto_aula_pdf.py
        ├─► core/lib/extrator_pdf.py
        ├─► core/lib/extrator_pptx.py
        ├─► core/lib/classificador.py
        └─► core/extracao_palavras_chave_pdf.py
  └─► core/lote.py
        ├─► core/resultados_aula.py
        ├─► core/lib/metodologia.py           (sem IA)
        ├─► core/ia.py                        (OpenAI/Gemini)
        ├─► core/lib/higienizador_pedagogico.py
        ├─► core/lib/acompanhamento.py
        ├─► core/lib/acessibilidade.py
        └─► core/qualidade_metodologica.py
  └─► core/revisao_final.py
  └─► core/validador_plano.py
  └─► docx_generator/preencher.py             (modelo regular)
  └─► docx_generator/preencher_cdp.py         (CDP/EJA específico)
```

Não confundir módulos antigos citados em documentação histórica com os arquivos ativos em `core/lib/`. Antes de alterar uma função, localize a definição realmente importada e verifique se há wrappers ou definições duplicadas no Streamlit.

---

## 5. COMPORTAMENTOS FUNCIONAIS CONFIRMADOS

### 5.1 Calendário mensal e aulas previstas

- O plano é mensal e normalmente termina no último dia do mês.
- A semana extra só entra quando o usuário escolhe a extensão correspondente.
- `Aulas previstas da semana` deve refletir as ocorrências reais daquela semana no calendário, não o total semanal genérico do cadastro.
- Horários não consecutivos no mesmo dia contam como aulas separadas.
- Em uma semana parcial no fim do mês, entram e são contadas apenas as aulas cujas datas pertencem ao plano.

### 5.2 Um dia sem PDF em Português

Somente os perfis de Português habilitados podem usar a opção **Permitir 1 dia da semana sem PDF**.

- O usuário escolhe um dia da semana.
- Todas as ocorrências desse dia ficam sem PDF no plano.
- A linha permanece no bloco com data e horário, mas os campos pedagógicos ficam vazios para preenchimento manual.
- Essa linha conta como aula prevista/dada.
- Ela não conta como PDF obrigatório.
- A ordem cronológica deve ser preservada mesmo quando a linha vazia fica entre duas aulas com PDF.
- Não permitir que `Usar o mesmo PDF na próxima` atravesse uma linha marcada como `bloco_sem_pdf`.

Preservar os campos `bloco_sem_pdf` e `ordem_original` durante todo o fluxo. A ordenação final por data e horário também é reforçada em `docx_generator/preencher.py`.

### 5.3 Limites de metodologia

- Geração local/regular sem IA: até **300 caracteres por etapa**.
- Modalidade EJA: até **350 caracteres por etapa**.
- Em DOCX de referência, cada etapa pode ter até **350 caracteres**. A ordem e a repetição das etapas são livres; a metodologia precisa conter `Para começar` ou `Relembre`, `Foco no conteúdo`, `Na prática` e `Encerramento`.
- Acompanhamento da aprendizagem e acessibilidade são opcionais no DOCX de referência. Quando não houver três itens em cada bloco, o sistema os gera automaticamente.
- Usar `obter_limite_caracteres_etapa()` e `limitar_texto_natural()` de `core/qualidade_metodologica.py`.
- Nunca voltar a usar cortes crus como `texto[:300]`, pois eles interrompem palavras e frases.

### 5.4 EJA

A aba EJA está habilitada atualmente para:

- Língua Inglesa
- Biologia
- Liderança e Oratória

O texto EJA deve ser adulto, direto e coerente com a vida prática e o mundo do trabalho, sem infantilização. Biologia EJA usa PDFs com estrutura própria; não presumir que todo PDF terá as etapas regulares `Foco no conteúdo` e `Encerramento`. O DOCX de referência pode fornecer a metodologia no formato reconhecido pelo sistema.

### 5.5 Botão “Limpar dados da tela”

O botão deve remover seleções, uploads, revisão, resultados e mensagens da sessão e retornar a interface para `Planos gerais`. Se um novo campo persistente for acrescentado à tela, avaliar se ele também deve entrar em `CAMPOS_TELA` ou em um dos prefixos de limpeza de `planos_luan_app.py`.

---

## 6. CADASTRO: REGRAS E CUIDADOS

### Fonte de cada linha

No diagnóstico/cadastro, um vínculo pode aparecer como:

- `Banco`
- `Pasta DOCX`
- `Banco + DOCX`

Excluir uma linha do banco não apaga seu DOCX. Se uma entrada antiga continuar aparecendo com origem `Pasta DOCX`, identificar o arquivo correspondente. Só remover ou mover o documento com autorização explícita do usuário.

### Padronização e duplicidades

- O componente curricular deve ser escolhido pelo catálogo sempre que possível, evitando texto livre, diferenças de maiúsculas/minúsculas, acentos, espaços e sublinhados.
- A chave equivalente de vínculo considera professor, disciplina, turma e componente curricular normalizados.
- Salvar um vínculo equivalente deve atualizar o registro existente em vez de criar uma duplicata visual.
- Não executar limpeza ampla por semelhança de nome. Primeiro mostre quais registros são equivalentes e qual origem cada um possui.
- O banco em uso é a fonte de verdade para horários atuais. Não recadastre automaticamente vínculos antigos encontrados apenas em documentos.

### Banco de dados

- Sempre usar `connection_scope()` ou `get_connection()` de `core/database.py`.
- Nunca abrir SQLite diretamente em módulos de aplicação, scripts improvisados ou testes de produção.
- Preservar `PRAGMA journal_mode=WAL`, `PRAGMA foreign_keys=ON` e o timeout configurado.
- Alterações de schema devem entrar em `MIGRACOES` e ser idempotentes.
- Nunca usar `DROP TABLE` para evolução normal do banco.
- Antes de excluir dados, consultar e contar os registros-alvo; depois, consultar novamente e informar o resultado.

Estrutura principal:

```sql
professores (
    id, nome UNIQUE
)

professor_turmas (
    id, professor_id FK, disciplina, turma, dia_semana,
    horario, aulas_semana, arquivo_modelo, template_id,
    componente_curricular
)

historico_planos (
    id, professor_nome, disciplina, turma, bimestre,
    data_geracao, arquivo_nome, arquivo_path
)

configuracoes (chave PK, valor)
schema_version (versao PK)
```

---

## 7. CONVENÇÕES DE CÓDIGO OBRIGATÓRIAS

### Metodologia

A metodologia deve ser `list[dict]` com as chaves `titulo` e `texto`:

```python
metodologia = [
    {"titulo": "Para começar", "texto": "Iniciar a aula com..."},
    {"titulo": "Foco no conteúdo", "texto": "Apresentar o conceito..."},
    {"titulo": "Na prática", "texto": "Orientar a resolução..."},
    {"titulo": "Encerramento", "texto": "Finalizar com síntese..."},
]
```

Nunca usar lista de strings soltas como formato interno da metodologia.

### Normalização

```python
from core.lib.classificador import normalizar_texto
```

Não criar normalização própria inline. Para nomes de pasta e aliases, reutilizar as funções de `core/helpers.py`.

### Encoding

```python
from core.qualidade_metodologica import corrigir_mojibake
texto_limpo = corrigir_mojibake(texto_bruto)
```

Aplicar a correção antes de processar texto extraído. Alguns padrões de mojibake aparecem intencionalmente nas tabelas de correção; uma busca textual isolada não prova que existe erro visível.

### Modelos Pydantic

- Usar `PlanoCompleto.from_any(dados)` para converter entradas heterogêneas.
- Usar `.to_dict()` para serializar.
- Não criar uma segunda forma concorrente de representar o plano.
- Não remover `diagnostico_geracao`, pois a interface usa esse campo nas abas de diagnóstico da metodologia.

### Variação determinística

```python
from core.lib.progressao import _indice_hash
idx = _indice_hash([disciplina, tema, str(indice_aula)], len(opcoes))
```

Não usar aleatoriedade quando a mesma aula precisa gerar o mesmo resultado.

### DOCX e tabelas mescladas

- Células mescladas exigem cuidado com `gridSpan`; nunca faça dois campos ocuparem a mesma célula física.
- Ao percorrer células mescladas, deduplicar pela identidade `cell._tc` quando necessário.
- Preservar a ordem cronológica das aulas e o vínculo entre data, horário e conteúdo.
- Alterações estruturais em `docx_generator/preencher.py` exigem geração de um documento real e inspeção visual.

---

## 8. REGRAS PEDAGÓGICAS ESSENCIAIS

### Perfis disciplinares

```text
matematica | lingua_portuguesa_ef | lingua_portuguesa_em | leitura_redacao
ciencias_ef | biologia | quimica | fisica | historia | geografia
ingles | arte | projeto_de_vida | lideranca_oratoria
educacao_financeira | tecnologia_inovacao | sociologia | orientacao_estudos
```

O perfil determina etapas, verbos, técnicas, acompanhamento, acessibilidade, regras de DOCX e tipo de aula. Ao acrescentar um perfil, revisar pelo menos:

1. `core/disciplinas.py`
2. `core/lib/classificador.py`
3. `core/lib/metodologia.py`
4. `core/lib/tecnicas.py`
5. `core/lib/acompanhamento.py`
6. `core/lib/acessibilidade.py`
7. `core/qualidade_metodologica.py`
8. `core/lib/higienizador_pedagogico.py`
9. `core/seletor_referencias.py`
10. testes específicos do perfil

### Técnicas pedagógicas

Quando explicitadas, manter em maiúsculas:

- `VIREM E CONVERSEM`
- `TODO MUNDO ESCREVE`
- `COM SUAS PALAVRAS`
- `HORA DA LEITURA`
- `DE OLHO NO MODELO`
- `PAUSE E RESPONDA`
- `UM PASSO DE CADA VEZ`

### Perfis com etapas próprias

`consolidar_quatro_etapas()` recebe `perfil` e não deve destruir estruturas especializadas de:

- `educacao_financeira`
- `projeto_de_vida`
- `ingles`

### CDP

No contexto CDP:

- Proibido sugerir internet, celular, computador ou dinâmica dependente de tecnologia.
- Não propor trabalho em grupos quando isso contrariar a realidade do ambiente.
- Priorizar quadro, material impresso, oralidade mediada e registro individual no caderno.
- Manter metodologia curta, simples e direta.
- A habilidade deve vir do material fornecido ou do DOCX de referência, nunca ser inventada.
- Aplicar `sanitizar_texto_cdp_estrito()` no fluxo apropriado.

### Higienizador de Língua Portuguesa

- Tema realmente literário pode retornar `literatura`.
- O fallback genérico deve ser `geral_nao_jornalistica`, nunca `literatura`.
- Termos jornalísticos válidos não devem ser substituídos em aulas de notícia ou reportagem.
- As regras de substituição devem permanecer pré-compiladas no nível do módulo.

### Confidence score

- Base: 100 pontos.
- Aceitável: `confidence_score >= 70`.
- Cada critério deve penalizar uma única vez.
- Não combinar dedução e teto fixo para o mesmo problema.
- A regeneração seletiva continua restrita ao perfil `historia`.
- `_tentativas_regeneracao` protege contra recursão infinita: ler no início, incrementar antes da chamada recursiva e remover apenas no retorno final.
- Falha na extração de palavras-chave deve gerar aviso e penalização explícita por meio de `extracao_palavras_chave_ok`; não ignorar silenciosamente.

---

## 9. ARQUIVOS SENSÍVEIS

| Arquivo | Cuidado principal |
|---|---|
| `planos_luan_app.py` | Estado do Streamlit, calendário, upload, EJA e integração geral |
| `core/lote.py` | Orquestração ampla e compatibilidade entre fluxos |
| `core/resultados_aula.py` | Prioridade PDF/DOCX, habilidade, IA e proveniência |
| `core/revisao_final.py` | Score e regeneração recursiva |
| `core/lib/higienizador_pedagogico.py` | Substituições com impacto em toda a metodologia |
| `core/qualidade_metodologica.py` | Limites, sanitização e consolidação de etapas |
| `core/lib/metodologia.py` | Motor principal sem IA e estruturas por perfil |
| `core/models.py` | Contratos Pydantic usados no sistema inteiro |
| `core/database.py` | Banco, migrações e normalização de vínculos |
| `core/helpers.py` | Resolução de pastas, aliases e rotas EJA |
| `docx_generator/preencher.py` | Word final regular, tabelas e ordem cronológica |
| `docx_generator/preencher_cdp.py` | Word final CDP/EJA específico |

Antes de editar um arquivo sensível, procurar os testes que o cobrem e ler a função chamadora e a chamada seguinte do pipeline.

---

## 10. TESTES E VALIDAÇÃO

Use o Python da `.venv` quando disponível:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

### Estratégia mínima

1. Verificar `git status --short` antes de editar.
2. Executar `py_compile` nos arquivos Python alterados.
3. Rodar os testes diretamente relacionados à mudança.
4. Rodar a suíte completa antes de PR ou entrega ampla, quando o ambiente permitir.
5. Gerar pelo menos um plano real quando a mudança atingir calendário, PDF, metodologia ou DOCX.
6. Renderizar e inspecionar o DOCX quando a mudança afetar tabelas, mesclagem, paginação ou ordem visual.

Validação estrutural ou textual não equivale a revisão visual. Só afirmar que o documento foi revisado visualmente depois de renderizar todas as páginas com sucesso.

### Snapshot confirmado em 27/07/2026

Uma suíte direcionada aos fluxos de EJA, cadastro, higienização, revisão final, palavras-chave, qualidade metodológica, Orientação de Estudos e limpeza do DOCX terminou com:

```text
113 passed
```

Isso não substitui uma nova execução da suíte completa depois de futuras alterações.

### Testes prioritários por área

- EJA e rotas: `tests/test_eja_rotas.py`, `tests/test_eja_metodologia.py`.
- Cadastro e banco: `tests/test_cadastro_professores_db.py`, `tests/test_config_database_integracao.py`, `tests/unit/test_database_pragmas.py`.
- Orientação de Estudos/DOCX: `tests/test_orientacao_estudos_referencias.py`, `tests/test_referencias_docx_padrao.py`.
- Higienização: `tests/test_higienizador_pedagogico.py`.
- Revisão e score: `tests/test_revisao_final.py`.
- Palavras-chave: `tests/test_extracao_palavras_chave_pdf.py`.
- Word final: `tests/test_docx_final_cleanup.py`.
- Calendário: `tests/test_calendario_escolar.py`.

---

## 11. ESTADO DAS CORREÇÕES DA AUDITORIA ANTERIOR

As orientações antigas que ainda marcavam tudo como “pendente” estavam desatualizadas. No código atual foram confirmados:

- fallback genérico de Língua Portuguesa em `geral_nao_jornalistica`;
- somente um ramo ativo `elif perfil == "arte"` no motor principal;
- `pratica_oral` separado corretamente entre Português EF e EM;
- `consolidar_quatro_etapas(..., perfil=...)` implementado;
- regras regex do higienizador pré-compiladas;
- penalização de aderência sem teto fixo duplicado;
- extração de palavras-chave com flag `extracao_palavras_chave_ok` e aviso explícito;
- chamadas locais de geração usando a assinatura atual de `montar_resultado_aula_local()`;
- limites naturais de 300/350 caracteres sem corte bruto;
- aliases de EJA e prevenção de duplicidade de cadastro;
- limpeza efetiva do estado da tela;
- ordenação do plano quando existe uma linha de Português sem PDF.

Ao encontrar documentação ou comentário contraditório, trate o código e os testes atuais como fonte técnica de verdade e atualize a documentação junto com a correção.

---

## 12. GIT E ENTREGA

- Antes de editar: `git status --short` e `git diff`.
- Não sobrescrever mudanças locais do usuário.
- Fazer commits pequenos, com mensagem que descreva o resultado.
- Não fazer push, merge, rebase ou abrir PR sem pedido do usuário.
- Antes de informar que o GitHub está atualizado, conferir branch, remoto, commits locais e resultado do push.
- Arquivos pedagógicos de `PLANOS_LUAN_DADOS`, bancos locais e documentos gerados não devem ser adicionados ao Git por acidente.
- Ao concluir, informar arquivos alterados, testes realizados e o que ainda depende de teste manual.

---

## 13. CHECKLIST ANTES DE CONCLUIR UMA ALTERAÇÃO

- [ ] O pedido foi atendido sem ampliar o escopo?
- [ ] O estado local do Git foi preservado?
- [ ] A definição ativa, e não uma função antiga ou wrapper, foi alterada?
- [ ] A modalidade e o perfil disciplinar corretos foram considerados?
- [ ] Rotas externas de PDF/DOCX continuam apontando para `PLANOS_LUAN_DADOS`?
- [ ] Cadastros equivalentes não foram duplicados?
- [ ] Data, horário, ordem e aulas previstas continuam coerentes?
- [ ] Metodologia continua como `list[dict]` com `titulo` e `texto`?
- [ ] Os testes direcionados passaram?
- [ ] Se houve mudança visual no Word, todas as páginas foram renderizadas e revisadas?
- [ ] O usuário recebeu um resumo claro do resultado e das limitações da validação?

---

*AGENTS.md — Planos Luan v1.2.13 | Atualizado em 27/07/2026*
