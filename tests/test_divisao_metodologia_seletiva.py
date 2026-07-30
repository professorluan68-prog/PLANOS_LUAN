from core import lote
from core.divisor_metodologia import processar_pdf_e_dividir_metodologia


def test_processar_varios_pdfs_divide_apenas_os_pdfs_marcados(monkeypatch):
    def fake_aula_por_pdf(caminho, disciplina, turma, bimestre, usar_ia, provedor_ia, modelo_ia, indice_aula=0, total_aulas=1, modalidade_eja=False):
        return {
            "tema": f"Tema {indice_aula + 1}",
            "material": f"AULA {indice_aula + 1}",
            "aprendizagem": "Aprendizagem exemplo completa.",
            "metodologia": [{"titulo": "Para comecar", "texto": f"Metodologia base {indice_aula + 1}."}],
            "acompanhamento": ["Item 1", "Item 2"],
            "acessibilidade": ["Item 1", "Item 2"],
        }

    monkeypatch.setattr(lote, "_aula_por_pdf", fake_aula_por_pdf)
    monkeypatch.setattr(
        lote,
        "processar_pdf_e_dividir_metodologia",
        lambda texto: ("Para comecar:\nParte 1", "Encerramento:\nParte 2"),
    )
    monkeypatch.setattr(
        lote,
        "_metodologia_em_blocos_por_texto",
        lambda texto: [{"titulo": texto.split(":")[0], "texto": texto.split("\n", 1)[1]}],
    )

    aulas = lote.processar_varios_pdfs(
        ["a.pdf", "b.pdf", "c.pdf"],
        disciplina="Matematica",
        turma="1 ano B",
        dividir_metodologia=True,
        dividir_por_pdf=[False, True, False],
    )

    assert [aula["tema"] for aula in aulas] == [
        "Tema 1",
        "Tema 2",
        "Tema 2 - continuidade",
        "Tema 3",
    ]


def test_segunda_parte_do_mesmo_pdf_mantem_retomada_propria():
    metodologia = (
        "Para comecar:\nLer a reportagem.\n\n"
        "Foco no conteudo:\nAnalisar as ideias principais.\n\n"
        "Na pratica:\nResponder as questoes propostas.\n\n"
        "Encerramento:\nRegistrar uma sintese."
    )

    _, segunda_parte = processar_pdf_e_dividir_metodologia(metodologia)

    assert "Retomar brevemente os conceitos explorados na aula anterior" in segunda_parte
