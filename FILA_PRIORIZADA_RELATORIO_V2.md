# FILA PRIORIZADA — RELATÓRIO V2

Objetivo: transformar o restante do `RELATÓRIO DE ANÁLISE V2` em uma fila curta, baseada no código atual do projeto, sem repetir itens que já foram corrigidos.

## 1. O que do relatório já está resolvido hoje

Estes pontos apareceram no relatório, mas no código atual já estão atendidos:

- Retry da OpenAI e do Gemini em `core/ia.py`
- Correção do texto de Física e das entradas financeiras em `core/lib/acessibilidade.py`
- Validação do `.docx` gerado em `docx_generator/preencher.py`
- Regex pré-compilados em `core/qualidade_metodologica.py`
- Base de testes já existente no projeto (há dezenas de arquivos em `tests/`)

Observação: esses itens não entram na fila para evitar retrabalho.

## 2. Fila recomendada

### Prioridade 1 — corrigir o fallback de `extrator_pdf.py`

Arquivo principal:
- `core/lib/extrator_pdf.py`

Problema real:
- hoje, se o `pdfplumber` falha por arquivo corrompido, senha ou estrutura inválida, o sistema ainda tenta abrir o PDF como texto puro;
- isso pode deixar lixo binário entrar na pipeline e gerar plano ruim sem aviso claro.

Correção sugerida:
- manter o fallback de leitura direta apenas para ambiente de teste;
- em produção, subir erro claro para o usuário informando que o PDF não pôde ser lido.

Risco:
- baixo.

Ganho:
- alto, porque evita plano contaminado por conteúdo inválido.

Como implementar:
1. Ajustar `extrair_texto_pdf()` para só usar fallback textual quando houver uma flag de teste.
2. Criar teste dedicado para PDF inválido/corrompido.

### Prioridade 2 — separar regra de negócio de `obter_ultima_aula_gerada_sistema()`

Arquivo principal:
- `core/database.py`

Problema real:
- a função mistura acesso ao banco com leitura de `.docx`, regex e regra pedagógica de detecção de aula;
- quando ela falha, o diagnóstico fica confuso porque parece erro de banco, mas muitas vezes é erro de parsing.

Correção sugerida:
- mover a lógica de detecção da última aula para um módulo novo, por exemplo `core/gestao_aulas.py`;
- deixar `database.py` responsável apenas por buscar os bytes do histórico e dados brutos.

Risco:
- médio.

Ganho:
- médio/alto, porque melhora manutenção e facilita testes isolados.

Como implementar:
1. Extrair helpers privados para leitura do `.docx`.
2. Manter a assinatura pública atual para não quebrar o restante do sistema.
3. Cobrir com testes de regressão antes de remover lógica duplicada.

### Prioridade 3 — adicionar política de retenção do histórico de DOCX

Arquivo principal:
- `core/database.py`

Problema real:
- o histórico com BLOB continua crescendo;
- isso não é bug imediato, mas vira custo de manutenção e degradação gradual do SQLite.

Correção sugerida:
- criar rotina de limpeza por retenção;
- manter sempre um conjunto mínimo recente por professor/turma/disciplina.

Risco:
- médio, porque envolve dados salvos.

Ganho:
- médio, com efeito importante no longo prazo.

Como implementar:
1. Criar função separada de limpeza, sem executar automaticamente no primeiro passo.
2. Testar em banco temporário.
3. Só depois decidir se ela entra no fluxo normal ou fica como manutenção manual.

### Prioridade 4 — logging nos módulos mais críticos fora de `ia.py` e `lote.py`

Arquivos principais:
- `core/database.py`
- `core/lib/extrator_pdf.py`
- `docx_generator/preencher.py`

Problema real:
- hoje o projeto já tem logging em alguns pontos, mas esses módulos ainda estão mais silenciosos do que deveriam;
- isso dificulta entender falhas de produção e casos de template ruim ou PDF inválido.

Correção sugerida:
- adicionar `logger = logging.getLogger(__name__)`;
- registrar eventos importantes sem poluir demais o log.

Risco:
- baixo.

Ganho:
- médio.

Como implementar:
1. Inserir logging mínimo.
2. Logar só pontos de entrada, falha e fallback.
3. Evitar logar conteúdo sensível ou textos grandes dos professores.

### Prioridade 5 — fatiar `core/lote.py` aos poucos

Arquivo principal:
- `core/lote.py` (145133 bytes)

Problema real:
- continua sendo o maior ponto de risco para manutenção;
- qualquer ajuste pequeno ali tem grande chance de efeito colateral.

Correção sugerida:
- extrair grupos fechados de funções para módulos menores, sem reescrever o fluxo inteiro.

Risco:
- médio/alto.

Ganho:
- alto, mas estrutural.

Como implementar:
1. Começar pelas funções de Matemática ou por blocos mais isolados.
2. Copiar para módulo novo.
3. Substituir por import.
4. Rodar testes antes de remover definições antigas.

### Prioridade 6 — iniciar migração gradual de `core/lib/metodologia.py`

Arquivo principal:
- `core/lib/metodologia.py` (184560 bytes)

Problema real:
- o arquivo cresceu muito e tende a acumular mais condicionais por perfil e tipo;
- isso não é um erro imediato, mas aumenta o custo de cada nova melhoria.

Correção sugerida:
- migrar um perfil por vez para geradores separados;
- manter fallback no código atual durante a transição.

Risco:
- médio/alto.

Ganho:
- alto no longo prazo.

Como implementar:
1. Escolher um único perfil para piloto.
2. Criar módulo separado.
3. Validar que o texto final continua no mesmo padrão pedagógico.

## 3. Ordem prática que recomendo seguir

1. `core/lib/extrator_pdf.py`
2. `core/database.py` — separar `obter_ultima_aula_gerada_sistema()`
3. `core/database.py` — retenção do histórico
4. logging em `database.py`, `extrator_pdf.py` e `preencher.py`
5. refatoração gradual de `core/lote.py`
6. refatoração gradual de `core/lib/metodologia.py`

## 4. Próximo passo recomendado

Se formos seguir pela rota mais segura e com maior retorno imediato, o próximo passo deve ser:

- corrigir `core/lib/extrator_pdf.py`;
- criar teste específico para PDF inválido/corrompido;
- validar que o sistema passa a falhar de forma clara, sem contaminar a geração do plano.
