from core import lote


def test_cdp_matematica_detecta_sistema_decimal():
    tipo = lote._tipo_conteudo_cdp(
        "matematica",
        "Sistema de numeração decimal — composição e decomposição (Parte 1)",
        "",
    )
    assert tipo == "decimal_composicao_decomposicao"


def test_cdp_matematica_detecta_ordenacao_naturais():
    tipo = lote._tipo_conteudo_cdp(
        "matematica",
        "Comparação e ordenação de números naturais (Parte 1)",
        "",
    )
    assert tipo == "comparacao_ordenacao_naturais"


def test_cdp_matematica_detecta_numeros_inteiros():
    tipo = lote._tipo_conteudo_cdp(
        "matematica",
        "Adição e subtração com números inteiros",
        "",
    )
    assert tipo == "numeros_inteiros"


def test_cdp_matematica_fundamental_metodologia_sem_lemov():
    tema = "Sistema de numeração decimal — composição e decomposição (Parte 1)"
    texto_pdf = """
    Ensino Fundamental
    Matemática
    Aula 2
    Sistema de numeração decimal — composição e decomposição (Parte 1)
    VIREM E CONVERSEM
    TODO MUNDO ESCREVE
    PAUSE E RESPONDA
    """
    metodologia = " ".join(
        lote._metodologia_cdp_contextual(
            "matematica",
            "",
            tema,
            "composição e decomposição de números naturais",
            texto_pdf=texto_pdf,
            disciplina_base="Matemática",
        )
    ).lower()

    assert "lousa" in metodologia
    assert "caderno" in metodologia
    assert "virem e conversem" not in metodologia
    assert "todo mundo escreve" not in metodologia
    assert "pause e responda" not in metodologia
    assert "com suas palavras" not in metodologia
    assert "internet" not in metodologia
    assert "vídeo" not in metodologia and "video" not in metodologia
    assert "site" not in metodologia
    assert "plataforma" not in metodologia


def test_cdp_matematica_fundamental_acompanhamento_especifico():
    itens = lote._acompanhamento_cdp_contextual(
        "matematica",
        "Sistema de numeração decimal — composição e decomposição (Parte 1)",
        "composição e decomposição de números naturais",
        0,
    )
    texto = " ".join(itens).lower()
    assert "valor posicional" in texto or "ordens" in texto


def test_cdp_matematica_fundamental_acessibilidade_especifica():
    itens = lote._acessibilidade_cdp_contextual(
        "matematica",
        "Resolução de problemas de adição e subtração",
        "adição e subtração com números naturais",
        0,
    )
    texto = " ".join(itens).lower()
    assert "quadro" in texto or "lousa" in texto
    assert "apoio" in texto or "explica" in texto


def test_sanitizar_texto_cdp_estrito():
    from core.qualidade_metodologica import sanitizar_texto_cdp_estrito

    # 1. Test tech removal
    t1 = "Usar o celular para acessar a internet e ver um vídeo online sobre frações no YouTube."
    s1 = sanitizar_texto_cdp_estrito(t1)
    assert "celular" not in s1.lower()
    assert "internet" not in s1.lower()
    assert "vídeo" not in s1.lower()
    assert "material impresso" in s1.lower()

    # 2. Test Lemov removal
    t2 = "Aplicar a técnica Virem e conversem para discutir o problema com o colega."
    s2 = sanitizar_texto_cdp_estrito(t2)
    assert "virem e conversem" not in s2.lower()
    assert "colega" not in s2.lower()
    assert "individualmente" in s2.lower()
