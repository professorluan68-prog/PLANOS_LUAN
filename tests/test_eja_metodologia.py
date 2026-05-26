import core.lote as lote
from core.ia import _montar_prompt


TEXTO_BIOLOGIA_EJA = """
Biologia
Metabolismo energetico: fotossintese
2o bimestre Ensino
Aula 1 Medio
Relembre
VIREM E CONVERSEM
Link para video
A reacao da fotossintese
Pause e responda
TODO MUNDO ESCREVE
Questao do ENEM
"""


def test_biologia_eja_sem_ia_usa_blocos_e_linguagem_contextualizada(monkeypatch):
    monkeypatch.setattr(lote, "_extrair_texto_pdf", lambda caminho: TEXTO_BIOLOGIA_EJA)

    aula = lote._aula_por_pdf(
        "aula_fotossintese.pdf",
        "Biologia",
        "EJA - 2 termo",
        "2o bimestre",
        usar_ia=False,
        provedor_ia="",
        modalidade_eja=True,
    )

    titulos = [item["titulo"] for item in aula["metodologia"]]
    texto = " ".join(item["texto"] for item in aula["metodologia"])

    assert titulos == ["Para comecar", "Foco no conteudo", "Pause e responda", "Encerramento"]
    assert "jovens e adultos" in texto.lower()
    assert "linguagem acessivel e adulta" in texto.lower()
    assert "VIREM E CONVERSEM" in texto
    assert "TODO MUNDO ESCREVE" in texto
    assert "video indicado" in texto.lower()


def test_ingles_eja_sem_ia_prioriza_uso_funcional(monkeypatch):
    monkeypatch.setattr(
        lote,
        "_extrair_texto_pdf",
        lambda caminho: "Ingles\nAt the restaurant\nLISTEN AND REPEAT\nWRITE AND SHARE\nDialogue practice\n",
    )

    aula = lote._aula_por_pdf(
        "aula_ingles.pdf",
        "Ingles",
        "EJA - 1 termo",
        "2o bimestre",
        usar_ia=False,
        provedor_ia="",
        modalidade_eja=True,
    )

    texto = " ".join(item["texto"] for item in aula["metodologia"]).lower()

    assert [item["titulo"] for item in aula["metodologia"]] == [
        "Para comecar",
        "Foco no conteudo",
        "Pause e responda",
        "Encerramento",
    ]
    assert "pronuncia orientada" in texto
    assert "situacoes reais de comunicacao" in texto


def test_prompt_ia_inclui_orientacao_eja_quando_selecionado():
    prompt = _montar_prompt(TEXTO_BIOLOGIA_EJA, "Biologia", "2 termo", modalidade_eja=True)

    assert "MODALIDADE EJA" in prompt
    assert "linguagem acessivel, adulta" in prompt
    assert "Para comecar" in prompt


def test_prompt_cdp_com_ia_bloqueia_tecnicas_lemov_explicitas():
    prompt = _montar_prompt(
        "Tema: leitura e interpretacao",
        "Português",
        "MULTISSERIADO 1º, 2º e 3º ano",
        modalidade_eja=True,
        permitir_tecnicas_explicitamente=False,
    )

    assert "Nao cite tecnicas LEMOV" in prompt
    assert "cite o nome da tecnica em maiusculas" not in prompt
