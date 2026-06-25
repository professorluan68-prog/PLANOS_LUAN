from docx import Document
from core.referencias_ciencias import (
    localizar_docx_referencia_ciencias,
    referencia_ciencias_por_pdf,
    titulos_referencia_ciencias_por_docx,
)


def _criar_docx_referencia_ciencias(caminho, incluir_aula_3: bool = True):
    doc = Document()
    doc.add_paragraph("AULA 01 — A célula")
    doc.add_paragraph("Metodologia")
    doc.add_paragraph("Para começar: Conversa inicial sobre células.")
    doc.add_paragraph("Foco no conteúdo: Teoria celular e microscopia.")
    doc.add_paragraph("Na prática: Atividades práticas.")
    doc.add_paragraph("Encerramento: Quiz e revisão.")
    doc.add_paragraph("Acompanhamento da aprendizagem")
    doc.add_paragraph("☑ Observar se os estudantes compreendem a teoria celular.")
    doc.add_paragraph("☑ Verificar a realização dos registros no caderno.")
    doc.add_paragraph("☑ Conferir as respostas da atividade escrita.")
    doc.add_paragraph("Acessibilidade")
    doc.add_paragraph("☑ Utilizar imagens ampliadas da célula.")
    doc.add_paragraph("☑ Fornecer banco de palavras-chave.")
    doc.add_paragraph("☑ Permitir respostas em formatos diversos.")

    doc.add_paragraph("AULA 02 — Desenvolvimento da microscopia")
    doc.add_paragraph("Metodologia")
    doc.add_paragraph("Para começar: Retomar microscópios antigos.")
    doc.add_paragraph("Acompanhamento da aprendizagem")
    doc.add_paragraph("☑ Verificar se reconhece o papel do microscópio.")
    doc.add_paragraph("☑ Observar a participação na discussão.")
    doc.add_paragraph("☑ Conferir o registro de pneumonia.")
    doc.add_paragraph("Acessibilidade")
    doc.add_paragraph("☑ Usar imagem simplificada.")
    doc.add_paragraph("☑ Disponibilizar roteiro.")
    doc.add_paragraph("☑ Apoiar resposta oral.")

    if incluir_aula_3:
        doc.add_paragraph("AULA 03 — Aula fictícia")
        doc.add_paragraph("Metodologia")
        doc.add_paragraph("Para começar: Texto da aula 3.")
        doc.add_paragraph("Acompanhamento da aprendizagem")
        doc.add_paragraph("☑ Verificar um registro.")
        doc.add_paragraph("☑ Observar uma fala.")
        doc.add_paragraph("☑ Conferir uma resposta.")
        doc.add_paragraph("Acessibilidade")
        doc.add_paragraph("☑ Apoiar com palavras-chave.")
        doc.add_paragraph("☑ Apoiar com perguntas.")
        doc.add_paragraph("☑ Apoiar com resposta oral.")

    doc.add_paragraph("AULA 04 — Seres procariontes")
    doc.add_paragraph("Metodologia")
    doc.add_paragraph("Para começar: Diferenças básicas de núcleo.")
    doc.add_paragraph("Acompanhamento da aprendizagem")
    doc.add_paragraph("☑ Verificar se diferencia eucarionte de procarionte.")
    doc.add_paragraph("☑ Observar justificativas apresentadas na conversa.")
    doc.add_paragraph("☑ Conferir o registro das cores coloridas.")
    doc.add_paragraph("Acessibilidade")
    doc.add_paragraph("☑ Oferecer imagens ampliadas.")
    doc.add_paragraph("☑ Registrar palavras-chave no quadro.")
    doc.add_paragraph("☑ Permitir resposta oral.")
    doc.save(caminho)


def test_referencia_ciencias_le_docx_da_pasta_do_pdf(tmp_path):
    caminho_docx = tmp_path / "Metodologias_Ciencias_6_Ano.docx"
    caminho_pdf = tmp_path / "AULA_01 - A célula.pdf"
    _criar_docx_referencia_ciencias(caminho_docx)
    caminho_pdf.write_bytes(b"%PDF-1.4\n")

    referencia = referencia_ciencias_por_pdf(caminho_pdf, "1")

    assert referencia is not None
    assert referencia["titulo"] == "A célula"
    assert [etapa["titulo"] for etapa in referencia["metodologia"]][:3] == [
        "Para começar",
        "Foco no conteúdo",
        "Na prática",
    ]
    assert len(referencia["acompanhamento"]) == 3
    assert len(referencia["acessibilidade"]) == 3


def test_titulos_ciencias_6ano_permitem_salto_da_aula_3(tmp_path):
    caminho_docx = tmp_path / "Metodologias_Ciencias_6_Ano.docx"
    _criar_docx_referencia_ciencias(caminho_docx, incluir_aula_3=False)

    titulos = titulos_referencia_ciencias_por_docx(caminho_docx)

    assert titulos == {
        1: "A célula",
        2: "Desenvolvimento da microscopia",
        4: "Seres procariontes",
    }


def test_referencia_ciencias_localiza_docx_do_ano(tmp_path):
    caminho_docx = tmp_path / "Metodologias_Ciencias_6_Ano.docx"
    caminho_pdf = tmp_path / "AULA_02 - Microscopia.pdf"
    _criar_docx_referencia_ciencias(caminho_docx)

    caminho_localizado = localizar_docx_referencia_ciencias(caminho_pdf)
    assert caminho_localizado is not None
    assert caminho_localizado.name == "Metodologias_Ciencias_6_Ano.docx"
