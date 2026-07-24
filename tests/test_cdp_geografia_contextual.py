from core import lote
from core.cdp.gerador_cdp import titulo_cdp_por_caminho
from core.resultados_aula import _normalizar_metodologia_cdp


def _texto_geografia(tema: str, conceito: str = "", indice: int = 0) -> str:
    return lote._metodologia_cdp_contextual(
        "geografia",
        "",
        tema,
        conceito,
        indice,
    )[0]


def test_geografia_cdp_classifica_subtipos_centrais():
    assert (
        lote._tipo_conteudo_cdp(
            "geografia",
            "Mapas qualitativos e quantitativos",
            "cartografia temática, legenda e representação cartográfica",
        )
        == "geografia_cartografia_tematica"
    )
    assert (
        lote._tipo_conteudo_cdp(
            "geografia",
            "Distribuição espacial da população brasileira",
            "densidade demográfica e desigualdade regional",
        )
        == "geografia_dados_espaciais"
    )
    assert (
        lote._tipo_conteudo_cdp(
            "geografia",
            "Produzir mapa temático",
            "mapa-base com título, legenda e simbologia",
        )
        == "geografia_cartografia_tematica"
    )


def test_geografia_cartografia_cdp_usa_metodologia_contextual():
    texto = _texto_geografia(
        "Mapas qualitativos e quantitativos",
        "cartografia temática, legenda, simbologia e valores de percepção",
    ).lower()

    assert "mapa" in texto
    assert "legenda" in texto
    assert "qualitativo" in texto or "quantitativo" in texto
    assert "caderno" in texto or "quadro" in texto or "lousa" in texto

    proibidas = [
        "virem e conversem",
        "todo mundo escreve",
        "com suas palavras",
        "projete",
        "projetor",
        "slide",
        "internet",
        "vídeo",
        "aplicativo",
        "recurso digital",
        "encontre um colega",
        "estimule a análise crítica",
        "provoque a turma",
    ]
    assert not [termo for termo in proibidas if termo in texto]


def test_geografia_cdp_acompanhamento_e_acessibilidade_especificos():
    acompanhamento = lote._acompanhamento_cdp_contextual(
        "geografia",
        "Mapas qualitativos e quantitativos",
        "cartografia temática, legenda e simbologia",
    )
    acessibilidade = lote._acessibilidade_cdp_contextual(
        "geografia",
        "Produzir mapa temático",
        "mapa-base com título, legenda e simbologia",
    )

    assert any("mapa qualitativo" in item or "mapa quantitativo" in item for item in acompanhamento)
    assert any("legenda" in item or "simbologia" in item or "valores numéricos" in item for item in acompanhamento)
    assert any("mapa" in item or "símbolos" in item for item in acessibilidade)


def test_geografia_cdp_limpa_expressoes_inadequadas():
    texto = lote._limpar_texto_cdp_contextual(
        "Projete o slide e acesse o link. VIREM E CONVERSEM. "
        "Estimule a análise crítica e encontre um colega."
    ).lower()

    assert "projete" not in texto
    assert "slide" not in texto
    assert "acesse" not in texto
    assert "virem e conversem" not in texto
    assert "estimule a análise crítica" not in texto
    assert "encontre um colega" not in texto


def test_geografia_cdp_titulo_usa_nome_limpo_do_pdf():
    assert titulo_cdp_por_caminho(
        r"C:\pdf\02 - ATIVIDADE 2 - Construção de mapas a legenda.pdf"
    ) == "Construção de mapas a legenda"
    assert titulo_cdp_por_caminho(r"C:\pdf\GEOGRAFIA EM VOL 1.pdf") == ""


def test_geografia_cdp_metodologia_e_encurtada_e_sem_agrupamentos():
    metodologia = _normalizar_metodologia_cdp([
        {"titulo": "Na prática", "texto": "Analisar o mapa em duplas. " + "Explicar a legenda. " * 80},
        {"titulo": "Encerramento", "texto": "Registrar a síntese no caderno."},
    ])
    assert sum(len(item["texto"]) for item in metodologia) <= 1200
    texto = " ".join(item["texto"] for item in metodologia).lower()
    assert "duplas" not in texto
