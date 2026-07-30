import pytest

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


@pytest.mark.parametrize(
    ("perfil", "tipo", "contexto", "chaves_esperadas"),
    [
        (
            "ingles",
            "listening",
            None,
            [
                "para_comecar_virem_e_conversem",
                "vocabulario_pre_escuta",
                "listening_atividade",
                "foco_conteudo",
                "pause_e_responda",
                "pratica_adicional",
                "encerramento_com_suas_palavras",
            ],
        ),
        (
            "lingua_portuguesa_ef",
            "resumo_retextualizacao",
            None,
            [
                "para_comecar",
                "hora_leitura",
                "foco",
                "de_olho_modelo",
                "todo_mundo_escreve",
                "pratica",
                "revisao_colega",
                "encerramento",
            ],
        ),
        (
            "lingua_portuguesa_em",
            "pratica_oral",
            None,
            [
                "relembre",
                "foco",
                "planejamento_oral",
                "pratica",
                "socializacao",
                "encerramento",
            ],
        ),
        (
            "lingua_portuguesa_ef",
            "leitura_jornalistica",
            {"tipo_aula": "dupla"},
            [
                "para_comecar",
                "hora_leitura",
                "foco",
                "pratica",
                "socializacao",
                "encerramento",
            ],
        ),
        (
            "ciencias_ef",
            "modelagem_cientifica",
            None,
            [
                "relembre",
                "observacao_inicial",
                "mao_na_massa",
                "socializacao",
                "correcao_dialogada",
                "encerramento",
            ],
        ),
        (
            "biologia",
            "aula_desafio",
            None,
            [
                "desafio",
                "entendendo_problema",
                "solucao_acao",
                "hora_verdade",
                "encerramento",
            ],
        ),
        (
            "projeto_de_vida",
            "producao_coletiva",
            None,
            [
                "relembre",
                "foco_no_tema",
                "producao_em_grupos",
                "apresentacao",
                "encerramento",
            ],
        ),
        ("historia", "fonte_historica", None, ["para_comecar", "foco", "pause", "pratica", "encerramento"]),
        ("geografia", "analise_geografica", None, ["para_comecar", "leitura", "foco", "pause", "pratica", "encerramento"]),
    ],
)
def test_etapas_por_perfil_preservam_o_contrato_por_disciplina(
    perfil,
    tipo,
    contexto,
    chaves_esperadas,
):
    etapas = _etapas_por_perfil(perfil, tipo, contexto)

    assert [chave for _, chave in etapas] == chaves_esperadas
