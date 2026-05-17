from core.lote import _material_digital_por_texto, _montar_etapas_metodologia, _variar_linguagem_metodologia
from docx_generator.preencher import _titulo_aula


def test_material_digital_usa_numero_real_do_pdf():
    texto = (
        "Educacao Financeira\n"
        "Por que poupamos? - Parte 1\n"
        "2o bimestre Ensino Fundamental:\n"
        "Aula 06 Anos Finais\n"
        "Reserva de emergencia; Explicar o que e uma reserva\n"
    )

    material = _material_digital_por_texto(
        texto,
        r"D:\PLANOS DE JUNHO\ADRIANA ALDA PALOS\PDF_AULAS\EDUCACAO FINANCEIRA\AULA06_7ANO.pdf",
        "Educacao Financeira",
    )

    assert material == "AULA 06 - Por que poupamos? - Parte 1"


def test_material_digital_preserva_titulo_multilinha_da_capa():
    texto = (
        "Educacao Financeira\n"
        "Por que poupamos?\n"
        "- Parte 2\n"
        "2o bimestre Ensino Fundamental:\n"
        "Aula 7 Anos Finais\n"
    )

    material = _material_digital_por_texto(texto, "AULA07_7ANO.pdf", "Educacao Financeira")

    assert material == "AULA 7 - Por que poupamos? - Parte 2"


def test_preenchimento_docx_prefere_material_extraido_do_pdf():
    aula = {
        "material": "AULA 06 - Por que poupamos? - Parte 1",
        "tema": "Tema ajustado pela IA",
    }

    assert _titulo_aula(aula, 2) == "AULA 06 - Por que poupamos? - Parte 1"


def test_desenvolvimento_coloca_titulo_entre_aspas():
    metodologia = [
        {
            "titulo": "Para comecar",
            "texto": "Retomar a aula anterior sobre Por que poupamos? - Parte 1 e conectar os registros.",
        }
    ]

    ajustada = _variar_linguagem_metodologia(
        metodologia,
        "Educacao Financeira",
        "7 ano B",
        "Por que poupamos? - Parte 1",
    )

    assert '"Por que poupamos? - Parte 1"' in ajustada[0]["texto"]


def test_metodologia_ignora_rotulo_de_bimestre_como_conceito():
    etapas = _montar_etapas_metodologia(
        texto=(
            "Biologia\n"
            "2o bimestre Ensino\n"
            "Polinizacao e controle biologico\n"
            "Foco no conteudo\n"
            "Abelhas e polinizacao em ecossistemas.\n"
        ),
        disciplina="Biologia",
        turma="2 ano C",
        tema="Polinizacao e controle biologico",
    )

    texto = " ".join(etapa["texto"] for etapa in etapas)
    assert "2o bimestre" not in texto.lower()
    assert "bimestre ensino" not in texto.lower()
    assert "Polinizacao e controle biologico" in texto
