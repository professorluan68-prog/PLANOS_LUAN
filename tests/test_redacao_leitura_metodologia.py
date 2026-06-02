from core.lote import _montar_etapas_metodologia


def _titulos(metodologia):
    return [item["titulo"] for item in metodologia]


def _corpo(metodologia):
    return " ".join(item["texto"] for item in metodologia).lower()


def test_redacao_leitura_devolutiva_usa_quadro_autoral():
    texto = (
        "AULA 8 - Devolutiva da producao textual\n"
        "Pratica de linguagem: Producao de textos\n"
        "Quadro de analise autoral\n"
        "o que esta bom\n"
        "o que precisa melhorar\n"
        "o que vou fazer para melhorar\n"
    )

    metodologia = _montar_etapas_metodologia(
        texto,
        "Redacao e Leitura",
        "9o ano",
        "Devolutiva da producao textual",
    )

    assert _titulos(metodologia) == [
        "Disparo inicial / contextualizacao",
        "Leitura ou exploracao inicial",
        "Analise guiada",
        "Sistematizacao",
        "Producao textual",
        "Revisao e fechamento",
    ]
    corpo = _corpo(metodologia)
    assert "julgamento final" in corpo
    assert "orientacao de melhoria" in corpo
    assert "quadro de analise autoral" in corpo
    assert "o que esta bom" in corpo
    assert "o que precisa melhorar" in corpo
    assert "o que vou fazer para melhorar" in corpo


def test_redacao_leitura_planejamento_conta_realista_reforca_roteiro():
    texto = (
        "AULA 10 - Planejamento do conto realista\n"
        "Pratica de linguagem: Producao de textos\n"
        "Planejamento no caderno\n"
        "Roteiro orientador\n"
    )

    metodologia = _montar_etapas_metodologia(
        texto,
        "Redacao e Leitura",
        "9o ano",
        "Planejamento do conto realista",
    )

    corpo = _corpo(metodologia)
    assert "situacao-problema" in corpo
    assert "ponto de virada" in corpo
    assert "desfecho verossimil" in corpo
    assert "projeto de texto" in corpo


def test_redacao_leitura_em_citacoes_trata_leitura_como_argumento():
    texto = (
        "AULA 5 - Leitura e citacoes\n"
        "EM13LP09 EM13LP10 EM13LP13\n"
        "Citar nao e copiar trecho\n"
        "tese repertorio sociocultural argumentacao\n"
    )

    metodologia = _montar_etapas_metodologia(
        texto,
        "Redacao e Leitura",
        "3o ano",
        "Leitura e citacoes",
    )

    corpo = _corpo(metodologia)
    assert "dialogar com o texto" in corpo
    assert "citacoes" in corpo
    assert "repertorio sociocultural" in corpo
    assert "tese" in corpo
