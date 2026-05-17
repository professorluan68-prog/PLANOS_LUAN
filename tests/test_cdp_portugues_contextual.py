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


def test_portugues_cdp_nao_usa_termos_inadequados():
    texto = " ".join(
        [
            _texto_portugues("Por dentro da crônica - Parte 1"),
            _texto_portugues("Por dentro da crônica - Parte 2", "modo subjuntivo", 1),
            _texto_portugues("Vocabulário no texto", "palavras e expressões pelo contexto", 1),
            _texto_portugues("Produção textual", "escrita de crônica"),
        ]
    ).lower()
    proibidas = [
        "virem e conversem",
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
