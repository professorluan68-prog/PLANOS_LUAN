from core import lote


def _texto_matematica(tema: str, conceito: str = "", indice: int = 0) -> str:
    return lote._metodologia_cdp_contextual(
        "matematica",
        "",
        tema,
        conceito,
        indice,
    )[0]


def test_matematica_cdp_fracoes_ganha_metodologia_mais_densa():
    texto = _texto_matematica(
        "Adicao e subtracao com fracoes",
        "adicao e subtracao de fracoes",
    ).lower()

    assert "denominadores diferentes" in texto
    assert "fracoes equivalentes" in texto
    assert "caderno" in texto
    assert "correcao coletiva" in texto


def test_matematica_cdp_geometria_mantem_tom_contextual():
    texto = _texto_matematica(
        "Giros e angulos",
        "classificacao de angulos",
        1,
    ).lower()

    assert "quadro" in texto or "lousa" in texto
    assert "caderno" in texto
    assert "correcao coletiva" in texto

    proibidas = [
        "internet",
        "video",
        "aplicativo",
        "em grupos",
        "em duplas",
    ]
    assert not [termo for termo in proibidas if termo in texto]


def test_matematica_cdp_algebra_variavel_fica_mais_humana_e_multisseriada():
    texto = _texto_matematica(
        "Letras para representar numeros",
        "variavel e expressao algebrica",
    ).lower()

    assert "quadro" in texto
    assert "caderno" in texto
    assert "atividades graduais" in texto or "niveis" in texto
    assert "correcao coletiva" in texto
    assert "professor inicia" not in texto
    assert "a aula começa" not in texto


def test_matematica_cdp_equacao_primeiro_grau_tem_operacoes_inversas_e_apoio():
    texto = _texto_matematica(
        "Equacoes do 1 grau",
        "equacao de primeiro grau",
        1,
    ).lower()
    acompanhamento = lote._acompanhamento_cdp_contextual(
        "matematica",
        "Equacoes do 1 grau",
        "equacao de primeiro grau",
    )
    acessibilidade = lote._acessibilidade_cdp_contextual(
        "matematica",
        "Equacoes do 1 grau",
        "equacao de primeiro grau",
    )

    assert "operacoes inversas" in texto
    assert "sentenca matematica" in texto or "incognita" in texto
    assert any("equacao" in item.lower() or "incognita" in item.lower() for item in acompanhamento)
    assert any("operacoes inversas" in item.lower() or "etapas curtas" in item.lower() for item in acessibilidade)


def test_matematica_cdp_pitagoras_fica_ligado_ao_conteudo_real():
    texto = _texto_matematica(
        "Teorema de Pitagoras",
        "triangulo retangulo, catetos e hipotenusa",
    ).lower()
    acompanhamento = lote._acompanhamento_cdp_contextual(
        "matematica",
        "Teorema de Pitagoras",
        "triangulo retangulo, catetos e hipotenusa",
    )
    acessibilidade = lote._acessibilidade_cdp_contextual(
        "matematica",
        "Teorema de Pitagoras",
        "triangulo retangulo, catetos e hipotenusa",
    )

    assert "triangulo retangulo" in texto
    assert "catetos" in texto
    assert "hipotenusa" in texto
    assert any("hipotenusa" in item.lower() or "catetos" in item.lower() for item in acompanhamento)
    assert any("marcacoes" in item.lower() or "formula" in item.lower() for item in acessibilidade)


def test_matematica_cdp_em_funcao_algebrica_fica_especifica():
    texto = _texto_matematica(
        "Relação entre grandezas: representação algébrica",
        "EM13MAT501 função polinomial do 1º grau e generalização algébrica",
    ).lower()

    assert "tabela" in texto
    assert "expressão algébrica" in texto
    assert "grandezas" in texto
    assert "correção coletiva" in texto


def test_matematica_cdp_em_funcao_logaritmica_fica_contextualizada():
    texto = _texto_matematica(
        "Função logarítmica",
        "relação entre potência, logaritmo e variação em escala",
    ).lower()
    acompanhamento = lote._acompanhamento_cdp_contextual(
        "matematica",
        "Função logarítmica",
        "relação entre potência, logaritmo e variação em escala",
    )

    assert "potência" in texto
    assert "logaritmo" in texto
    assert any("logaritmo" in item.lower() or "potência" in item.lower() for item in acompanhamento)


def test_matematica_cdp_ef_reta_numerica_fica_especifica():
    texto = _texto_matematica(
        "Números racionais na reta numérica",
        "frações, decimais e comparação de valores",
    ).lower()
    acompanhamento = lote._acompanhamento_cdp_contextual(
        "matematica",
        "Números racionais na reta numérica",
        "frações, decimais e comparação de valores",
    )
    acessibilidade = lote._acessibilidade_cdp_contextual(
        "matematica",
        "Números racionais na reta numérica",
        "frações, decimais e comparação de valores",
    )

    assert "reta numérica" in texto
    assert "frações" in texto or "decimais" in texto
    assert any("reta numérica" in item.lower() or "fraç" in item.lower() for item in acompanhamento)
    assert any("reta numérica" in item.lower() or "fraç" in item.lower() for item in acessibilidade)
