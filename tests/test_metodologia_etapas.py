from core.lib.metodologia import _etapas_por_perfil


def test_etapas_educacao_financeira_continuidade_sao_mantidas():
    assert _etapas_por_perfil("educacao_financeira", "aula_pratica_continuidade") == [
        ("Para começar", "retomada_conceitual"),
        ("Foco no conteúdo", "contextualizacao_pratica"),
        ("Na prática", "atividade_central"),
        ("Encerramento", "encerramento_reflexivo"),
    ]


def test_etapas_educacao_financeira_com_calculos_sao_mantidas():
    assert _etapas_por_perfil("educacao_financeira", "credito_endividamento") == [
        ("Para começar", "para_comecar"),
        ("Análise de caso", "analise_caso"),
        ("Foco no conteúdo", "foco"),
        ("Pause e responda", "pause"),
        ("Cálculos financeiros", "calculos"),
        ("Na prática", "pratica"),
        ("Encerramento", "encerramento"),
    ]


def test_etapas_educacao_financeira_planejamento_sao_mantidas():
    assert _etapas_por_perfil("educacao_financeira", "orcamento_planejamento") == [
        ("Para começar", "para_comecar"),
        ("Análise de caso", "analise_caso"),
        ("Foco no conteúdo", "foco"),
        ("Pause e responda", "pause"),
        ("Planejamento orçamentário", "planejamento"),
        ("Encerramento", "encerramento"),
    ]
