from io import BytesIO

from docx import Document

from docx_generator.preencher import preencher_documento


def _modelo_com_semanas(semanas):
    doc = Document()
    for semana in semanas:
        cabecalho = doc.add_table(rows=4, cols=9)
        cabecalho.rows[0].cells[0].text = "PLANO DE AULAS"
        cabecalho.rows[1].cells[2].text = "PROFESSOR"
        cabecalho.rows[1].cells[3].text = "COMPONENTE CURRICULAR"
        cabecalho.rows[1].cells[6].text = "TURMA"
        cabecalho.rows[1].cells[7].text = "MÊS"
        cabecalho.rows[1].cells[8].text = "BIMESTRE"
        cabecalho.rows[3].cells[0].text = "SEMANA"
        cabecalho.rows[3].cells[1].text = semana
        cabecalho.rows[3].cells[2].text = "AULAS PREVISTAS NA SEMANA"

        aulas = doc.add_table(rows=2, cols=6)
        aulas.rows[0].cells[0].text = "AULA SEMANAL (Data e Horário)"
        aulas.rows[0].cells[1].text = "NÚMERO E TÍTULO DO MATERIAL DIGITAL"
        aulas.rows[0].cells[2].text = "APRENDIZAGEM ESSENCIAL*"
        aulas.rows[0].cells[3].text = "DESENVOLVIMENTO"
        aulas.rows[0].cells[4].text = "ACOMPANHAMENTO DA APRENDIZAGEM"
        aulas.rows[0].cells[5].text = "ACESSIBILIDADE"

    saida = BytesIO()
    doc.save(saida)
    saida.seek(0)
    return saida


def _aula(data, tema="Tema da aula"):
    return {
        "data": data,
        "horario": "14h40 - 16h40",
        "material": f"AULA 5 - {tema}",
        "aprendizagem": "Habilidade: manter BNCC como veio.",
        "metodologia": [
            {
                "titulo": "Para começar",
                "texto": (
                    "Retomar registros ja construidos, analisando consequencias possiveis, "
                    "sistematizacao, servico e preco."
                ),
            }
        ],
        "acompanhamento": ["Observar registros da aula."],
        "acessibilidade": ["Oferecer apoio visual."],
    }


def _gerar(aulas):
    modelo = _modelo_com_semanas(
        ["01/06 a 05/06", "08/06 a 12/06", "15/06 a 19/06", "22/06 a 26/06", "29/06 a 03/07"]
    )
    return Document(
        preencher_documento(
            modelo,
            aulas,
            professor="ADRIANA",
            disciplina="Educação Financeira",
            turma="7º ANO A",
            mes="JUNHO",
            bimestre="2º Bimestre",
            aulas_previstas_manual="2",
        )
    )


def test_remove_apenas_semana_final_vazia():
    doc = _gerar([_aula("05/06"), _aula("12/06"), _aula("19/06"), _aula("26/06")])

    texto = "\n".join(cell.text for table in doc.tables for row in table.rows for cell in row.cells)

    assert len(doc.tables) == 8
    assert "22/06 a 26/06" in texto
    assert "29/06 a 03/07" not in texto


def test_preserva_semana_vazia_no_meio_quando_ha_aula_depois():
    doc = _gerar([_aula("05/06"), _aula("19/06"), _aula("03/07")])

    texto = "\n".join(cell.text for table in doc.tables for row in table.rows for cell in row.cells)

    assert len(doc.tables) == 10
    assert "08/06 a 12/06" in texto
    assert "29/06 a 03/07" in texto
    assert "03/07" in texto


def test_polimento_corrige_acentos_observados():
    doc = _gerar([_aula("05/06")])

    texto = "\n".join(cell.text for table in doc.tables for row in table.rows for cell in row.cells)

    assert "já construídos" in texto
    assert "consequências possíveis" in texto
    assert "sistematização" in texto
    assert "serviço" in texto
    assert "preço" in texto

