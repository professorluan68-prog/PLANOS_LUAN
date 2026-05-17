from core import lote


def _texto_ciencias(tema: str, conceito: str = "", indice: int = 0) -> str:
    return lote._metodologia_cdp_contextual(
        "ciencias_ef",
        "",
        tema,
        conceito,
        indice,
    )[0]


def test_ciencias_cdp_classifica_conteudos_centrais():
    assert (
        lote._tipo_conteudo_cdp(
            "ciencias_ef",
            "Montagem de cardápio semanal",
            "alimentação balanceada e grupos alimentares",
        )
        == "ciencias_alimentacao"
    )
    assert (
        lote._tipo_conteudo_cdp("ciencias_ef", "Processo de digestão dos alimentos", "")
        == "ciencias_digestao"
    )
    assert (
        lote._tipo_conteudo_cdp(
            "ciencias_ef",
            "Sistema nervoso e sistema endócrino no desenvolvimento humano",
            "",
        )
        == "ciencias_nervoso_endocrino"
    )


def test_ciencias_alimentacao_cdp_usa_metodologia_contextual():
    texto = _texto_ciencias(
        "Montagem de cardápio semanal",
        "alimentação balanceada, grupos alimentares e alimentos ultraprocessados",
    ).lower()

    assert "cardápio" in texto
    assert "grupos alimentares" in texto or "alimentos" in texto
    assert "caderno" in texto or "lousa" in texto or "quadro" in texto

    proibidas = [
        "virem e conversem",
        "todo mundo escreve",
        "com suas palavras",
        "pause e responda",
        "veja no livro",
        "livro didático",
        "internet",
        "vídeo",
        "simulador",
        "na escola",
        "sua escola",
        "compartilhe com os seus colegas",
        "use sua criatividade",
    ]
    assert not [termo for termo in proibidas if termo in texto]


def test_ciencias_alimentacao_cdp_acompanhamento_e_acessibilidade():
    acompanhamento = lote._acompanhamento_cdp_contextual(
        "ciencias_ef",
        "Montagem de cardápio semanal",
        "alimentação balanceada e grupos alimentares",
    )
    acessibilidade = lote._acessibilidade_cdp_contextual(
        "ciencias_ef",
        "Montagem de cardápio semanal",
        "alimentação balanceada e grupos alimentares",
    )

    assert any("grupos alimentares" in item or "cardápio" in item for item in acompanhamento)
    assert any("tabela de cardápio" in item or "lista de alimentos" in item for item in acessibilidade)


def test_ciencias_cdp_limpa_expressoes_inadequadas():
    texto = lote._limpar_texto_cdp_contextual(
        "Veja no livro! Use sua criatividade e compartilhe com os seus colegas na escola. "
        "Acesse o simulador pela internet."
    ).lower()

    assert "veja no livro" not in texto
    assert "use sua criatividade" not in texto
    assert "compartilhe com os seus colegas" not in texto
    assert "na escola" not in texto
    assert "simulador" not in texto
    assert "internet" not in texto
