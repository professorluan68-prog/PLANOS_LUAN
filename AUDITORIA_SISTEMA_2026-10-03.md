# Auditoria do Sistema Planos Luan — 03/10/2026

> Auditoria feita antes da atualização da documentação. Nenhum arquivo foi apagado: os itens abaixo são **recomendações** que dependem de decisão do Professor.

## 1. Resumo executivo

| Item | Situação |
|---|---|
| Versão do gerador | `1.2.14` (`core/revisao_final.py`), consistente com a documentação |
| Branch / remoto | `main` → `professorluan68-prog/PLANOS_LUAN` (sincronizado no commit `3bf5763`) |
| Testes | **853 coletados: 828 aprovados, 25 ignorados, 0 falhas** (execução completa em 03/10/2026, 149 s) |
| Arquivos de teste | 122 arquivos `test_*.py` em `tests/` e `tests/unit/` |
| Interface | `planos_luan_app.py` + 14 módulos em `ui/` (modularização concluída em 02/10) |
| Banco | 7 tabelas (`professores`, `professor_turmas`, `professor_dados`, `historico_planos`, `progresso_aulas`, `configuracoes`, `schema_version`), 20 migrações, 11 índices |
| Dados (fora do Git) | `PLANOS_LUAN_DADOS`: banco, `PDF_AULAS`, `Planos feitos`, `historico_docx`, `REFERENCIAS_METODOLOGICAS` |

## 2. O que mudou desde a documentação anterior (23/09/2026)

- Aba **Conferência Mensal** (professor + mês → ✅ feito / ⬜ pendente / ⚠️ registro sem arquivo).
- Regra **"a pasta do mês manda"** para o mês do plano (`_mes_plano_pela_pasta`).
- Modularização do `planos_luan_app.py` em `ui/`.
- Subpastas por mês em `Planos feitos`.
- Memória persistente da última aula (`progresso_aulas`) e detecção pelos DOCX reais.
- Aulas duplas (2 PDFs; 1 PDF + 1 sem PDF; ambas sem PDF) e bloco sem PDF com *Recomposição da Aprendizagem*.
- Feriados com descrição e semanas sem aula preservadas no DOCX (0 aulas previstas).
- Aba **CDP-EF/EM** no menu (o modo `CDP - Ciclo I` ainda existe no código, mas fora do menu).
- Rotas EJA de Língua Inglesa (1º e 2º Termo).

## 3. Achados da auditoria

### 3.1 Críticos
1. **Código-fonte do GitHub Desktop dentro do repositório.** Cerca de 2.460 arquivos não pertencem ao Planos Luan: `app/` (~2.295), `docs/` (60), `vendor/` (57), `script/` (40), `eslint-rules/` (11), `gemoji/`, além de `package.json`, `yarn.lock`, `tsconfig.json`, `.eslintrc.yml`, `.prettierrc.yml`, `.node-version`, `.nvmrc`, `.yarnrc`, `.markdownlint*`, `changelog.json`, `SECURITY.md` e `LICENSE` (`Copyright (c) GitHub, Inc.`). Eles escondem o código real (≈ 263 arquivos `.py`) e tornam o repositório pesado e confuso.
   - **Recomendação:** remover do repositório (`git rm`) em um commit isolado, com backup/branch prévio, e criar um `LICENSE` próprio. **Depende da confirmação do Professor.**
2. **Documentos herdados do GitHub Desktop** — `README.md` e `CODE_OF_CONDUCT.md` eram os do GitHub Desktop (README com instaladores, `opensource@github.com` como contato). **Corrigido nesta atualização.**

### 3.2 Atenção
3. **Arquivos de trabalho soltos na raiz**: `fix_gerador.py`, `inject_final.py`, `inject_improvements.py`, `analisar_metodologias.py`, `scratch_docs.md`, `scratch_docs2.md`, `scratch_test_plan.docx`, `redacao.md`, `estrutura.txt`, `ANDREA_PLANO_OUTUBRO.docx`, `Relatorio_*.docx`. Parecem scripts/relatórios pontuais. Sugestão: mover para uma pasta `scripts/` ou `arquivo/` após o Professor conferir se ainda usa algum.
4. **Pastas de snapshots**: `ESTRUTURAS_SISTEMA_TXT/` (35 arquivos de texto com cópias da estrutura do código) e `Auditoria_Estruturas/` ficam desatualizadas a cada mudança; podem ser regeneradas em vez de mantidas à mão.
5. **Arquivo de escopo** `EM Escopo-sequência 2026 (1).ods` é referenciado por `config.py` (`ESCOPO_PROJETO_VIDA_PATH`) com o nome `EM Escopo-sequencia 2026 (1).ods` (sem acento). Conferir se o nome real do arquivo bate com o configurado, para o Projeto de Vida não cair em fallback.
6. **`PLANOS_LUAN_ENTERPRISE_LITE.md` e `FILA_PRIORIZADA_RELATORIO_V2.md`** são documentos de planejamento de 22/08/2026 (a fila tem caracteres corrompidos por codificação). Mantidos sem alteração; revisar se ainda refletem as prioridades.
7. **`config.py`** ainda define `LEGACY_PLANOS_FEITOS_DIR` (`PLANOS_LUAN\Planos feitos`) e `PASTA_PRINCIPAL_TRABALHO` (`planos_de_junho`). A regra do sistema é não usar fallbacks legados; conferir se ainda são necessários.
8. **Histórico com mês divergente**: 116 registros de `historico_planos` têm `mes_plano` vazio e 3 (Adriana Alda — Educação Financeira) estavam com `2026-09` em arquivos da pasta `NOVEMBRO`. A leitura agora usa a pasta, então a Conferência Mensal funciona; a aba **Histórico** ainda exibe o mês gravado no banco.
9. **Duplicidade de índice**: planos gerados são salvos em `historico_docx` (caminho relativo) e em `Planos feitos` (caminho absoluto); a indexação de `Planos feitos` compara por caminho, podendo criar entradas duplicadas do mesmo plano. Vale monitorar (o hash do arquivo já existe para uma futura deduplicação).

### 3.3 Pontos positivos
- Todas as regras obrigatórias estão cobertas por testes (limites 300/350, CDP sem tecnologia, DOCX de referência, calendário/feriados, histórico).
- Acesso ao banco centralizado em `connection_scope()`/`get_connection()`, WAL e `foreign_keys=ON` preservados, sem `DROP TABLE`.
- Metodologia sempre em `list[dict]` com `titulo` e `texto`.
- Caminhos oficiais centralizados em `config.py`.

## 4. Documentos atualizados nesta rodada

| Arquivo | Ação |
|---|---|
| `AGENTS.md` | Atualizado (modos reais, pastas, regras 5.6–5.9, banco, alerta de repositório) |
| `GEMINI.md` | Reescrito com a arquitetura e as regras atuais |
| `CHANGELOG.md` | Entradas de 24/07 a 03/10/2026 adicionadas |
| `README.md` | Substituído (era o do GitHub Desktop) |
| `CODE_OF_CONDUCT.md` | Adaptado ao projeto (era o do GitHub Desktop) |
| `LEIA-ME_PLANOS_LUAN.md` | Atualizado (caminhos e atalhos corretos) |
| `DOCUMENTACAO_SISTEMA_PLANOS_LUAN.docx` | Atualizado (abas, fluxo, banco, testes, conferência mensal) |
| `DOCUMENTACAO_ESTRUTURA_CORE_PLANOS_LUAN.docx` | Atualizado (tamanhos, novos módulos, `ui/`, `docx_generator/`, testes) |
| `AUDITORIA_SISTEMA_2026-10-03.md` | **Novo** (este arquivo) |

**Não alterados de propósito:** `SECURITY.md`, `changelog.json` e `docs/`, `app/`, `vendor/` (são do GitHub Desktop; ver achado 3.1).

## 5. Próximos passos sugeridos (para decisão do Professor)

1. Autorizar a limpeza do código do GitHub Desktop (achado 3.1) — maior ganho de clareza.
2. Decidir o destino dos arquivos soltos na raiz (achado 3).
3. Aplicar a regra "pasta do mês manda" também à aba **Histórico**.
4. Corrigir (com confirmação) os registros antigos de `mes_plano` divergentes ou vazios.
