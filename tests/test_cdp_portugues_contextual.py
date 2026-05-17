from core import lote


def _texto_portugues(tema: str, conceito: str = "", indice: int = 0) -> str:
    return lote._metodologia_cdp_contextual(
        "lingua_portuguesa_ef",
        "",
        tema,
        conceito,
        indice,
    )[0]


def test_portugues_cdp_classifica_conceitos_centrais():
    assert (
        lote._tipo_conteudo_cdp("lingua_portuguesa_ef", "Por dentro da crônica - Parte 1", "")
        == "genero_textual"
    )
    assert (
        lote._conceito_cdp_contextual("lingua_portuguesa_ef", "Por dentro da crônica - Parte 2", "modo subjuntivo")
        == "modo subjuntivo em textos literários"
    )
    assert (
        lote._tipo_conteudo_cdp("lingua_portuguesa_ef", "Produção textual", "escrita de crônica")
        == "producao_textual"
    )
    assert (
        lote._tipo_conteudo_cdp(
            "lingua_portuguesa_em",
            "Textos contemporâneos na construção da opinião - Parte 3",
            "artigo de opinião: estrutura, fato, opinião e conectivos",
        )
        == "lp_artigo_opiniao"
    )
    assert (
        lote._tipo_conteudo_cdp(
            "lingua_portuguesa_em",
            "Relações lógico-discursivas no artigo de opinião",
            "conectivos, causa, oposição e concessão",
        )
        == "lp_relacoes_logico_discursivas"
    )


def test_portugues_cdp_nao_usa_termos_inadequados():
    texto = " ".join(
        [
            _texto_portugues("Por dentro da crônica - Parte 1"),
            _texto_portugues("Por dentro da crônica - Parte 2", "modo subjuntivo", 1),
            _texto_portugues("Vocabulário no texto", "palavras e expressões pelo contexto", 1),
            _texto_portugues("Produção textual", "escrita de crônica"),
            lote._metodologia_cdp_contextual(
                "lingua_portuguesa_em",
                "",
                "Textos contemporâneos na construção da opinião - Parte 3",
                "artigo de opinião: estrutura, fato, opinião e conectivos",
                0,
            )[0],
        ]
    ).lower()
    proibidas = [
        "virem e conversem",
        "veja no livro",
        "pnld",
        "resposta pessoal",
        "você concorda",
        "todo mundo escreve",
        "hora da leitura",
        "pause e responda",
        "com suas palavras",
        "um passo de cada vez",
        "internet",
        "vídeo",
        "celular",
        "em duplas",
        "em grupos",
    ]
    assert not [termo for termo in proibidas if termo in texto]


def test_portugues_cdp_acompanhamento_e_acessibilidade_especificos():
    acompanhamento = lote._acompanhamento_cdp_contextual(
        "lingua_portuguesa_ef",
        "Por dentro da crônica - Parte 2",
        "modo subjuntivo",
    )
    acessibilidade = lote._acessibilidade_cdp_contextual(
        "lingua_portuguesa_ef",
        "Por dentro da crônica - Parte 2",
        "modo subjuntivo",
    )

    assert any("recurso linguístico" in item or "sentido" in item for item in acompanhamento)
    assert any("conceito gramatical" in item or "exemplos no quadro" in item for item in acessibilidade)


def test_portugues_em_cdp_artigo_opiniao_e_conectivos():
    metodologia = lote._metodologia_cdp_contextual(
        "lingua_portuguesa_em",
        "",
        "Textos contemporâneos na construção da opinião - Parte 3",
        "artigo de opinião: estrutura, fato, opinião e conectivos",
        0,
    )[0]
    acompanhamento = lote._acompanhamento_cdp_contextual(
        "lingua_portuguesa_em",
        "Textos contemporâneos na construção da opinião - Parte 3",
        "artigo de opinião: estrutura, fato, opinião e conectivos",
    )
    acessibilidade = lote._acessibilidade_cdp_contextual(
        "lingua_portuguesa_em",
        "Relações lógico-discursivas no artigo de opinião",
        "conectivos, causa, oposição e concessão",
    )

    assert "artigo de opinião" in metodologia
    assert "fato e opinião" in metodologia
    assert "resposta" in metodologia
    assert any("tese" in item or "fato" in item for item in acompanhamento)
    assert any("tabela de conectivos" in item or "conectivos" in item for item in acessibilidade)
