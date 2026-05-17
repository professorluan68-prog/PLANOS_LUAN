from core import lote


def _metodologia_historia(tema: str, conceito: str = "", indice: int = 0) -> str:
    return lote._metodologia_cdp_contextual(
        "historia",
        "",
        tema,
        conceito,
        indice,
    )[0]


def test_historia_cdp_classifica_tipos_centrais():
    assert (
        lote._tipo_conteudo_cdp("historia", "Monarquias Nacionais e centralização do poder", "")
        == "historia_poder_politico"
    )
    assert (
        lote._tipo_conteudo_cdp("historia", "Guerra Russo-Japonesa", "")
        == "historia_conflito"
    )
    assert (
        lote._tipo_conteudo_cdp("historia", "Independências na América Espanhola", "")
        == "historia_independencia_revolucao"
    )
    assert (
        lote._tipo_conteudo_cdp("historia", "Sociedade colonial e classes sociais", "")
        == "historia_sociedade_desigualdade"
    )
    assert (
        lote._tipo_conteudo_cdp("historia", "Carta de Bolívar: análise de fonte histórica", "")
        == "historia_fonte"
    )


def test_historia_cdp_nao_usa_termos_inadequados():
    texto = " ".join(
        [
            _metodologia_historia("Monarquias Nacionais e centralização do poder"),
            _metodologia_historia("Guerra Russo-Japonesa", indice=1),
            _metodologia_historia("Independências na América Espanhola", indice=1),
            _metodologia_historia("Carta de Bolívar: análise de fonte histórica", indice=2),
        ]
    ).lower()
    proibidas = [
        "vídeo",
        "filme",
        "youtube",
        "internet",
        "celular",
        "projetor",
        "datashow",
        "virem e conversem",
        "todo mundo escreve",
        "com suas palavras",
        "hora da leitura",
        "de olho no modelo",
        "veja no livro",
    ]
    assert not [termo for termo in proibidas if termo in texto]


def test_historia_cdp_acompanhamento_e_acessibilidade_especificos():
    acompanhamento = lote._acompanhamento_cdp_contextual(
        "historia",
        "Carta de Bolívar: análise de fonte histórica",
        "",
    )
    acessibilidade = lote._acessibilidade_cdp_contextual(
        "historia",
        "Carta de Bolívar: análise de fonte histórica",
        "",
    )

    assert any("fonte histórica" in item or "documento" in item for item in acompanhamento)
    assert any("roteiro de análise" in item or "Ler a fonte" in item for item in acessibilidade)
