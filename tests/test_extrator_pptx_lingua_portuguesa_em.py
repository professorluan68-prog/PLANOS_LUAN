from pathlib import Path

import pytest

import core.lote as lote
from core.lib.extrator_pptx import (
    eh_cenario_piloto_pptx,
    encontrar_pptx_correspondente,
    extrair_estrutura_pptx,
    estrutura_pptx_para_dados_aula,
)
from core.qualidade_metodologica import normalizar_texto

pptx = pytest.importorskip("pptx")


def _criar_pptx_exemplo(caminho: Path) -> Path:
    apresentacao = pptx.Presentation()

    slide = apresentacao.slides.add_slide(apresentacao.slide_layouts[6])
    caixa = slide.shapes.add_textbox(0, 0, 5000000, 800000)
    caixa.text_frame.text = "Lingua Portuguesa"
    caixa = slide.shapes.add_textbox(0, 900000, 5000000, 800000)
    caixa.text_frame.text = "1a Serie"
    caixa = slide.shapes.add_textbox(0, 1800000, 7000000, 800000)
    caixa.text_frame.text = "3o bimestre"
    caixa = slide.shapes.add_textbox(0, 2700000, 7000000, 1000000)
    caixa.text_frame.text = "Aula 1"
    caixa = slide.shapes.add_textbox(0, 3600000, 9000000, 1200000)
    caixa.text_frame.text = "A literatura medieval portuguesa e suas influencias"

    slide = apresentacao.slides.add_slide(apresentacao.slide_layouts[6])
    caixa = slide.shapes.add_textbox(0, 0, 5000000, 800000)
    caixa.text_frame.text = "Conteudos"
    for texto in [
        "A Idade Media em Portugal e a influencia galego-portuguesa",
        "Flexao verbal em textos do trovadorismo",
    ]:
        caixa = slide.shapes.add_textbox(0, 900000, 9000000, 800000)
        caixa.text_frame.text = texto

    slide = apresentacao.slides.add_slide(apresentacao.slide_layouts[6])
    caixa = slide.shapes.add_textbox(0, 0, 5000000, 800000)
    caixa.text_frame.text = "Objetivos"
    objetivos = [
        "Conhecer o contexto historico da Idade Media em Portugal.",
        "Compreender a influencia galego-portuguesa nas cantigas trovadorescas.",
        "Relacionar elementos do trovadorismo com a leitura orientada do texto.",
    ]
    for texto in objetivos:
        caixa = slide.shapes.add_textbox(0, 900000, 9000000, 800000)
        caixa.text_frame.text = texto

    slide = apresentacao.slides.add_slide(apresentacao.slide_layouts[6])
    for linha in [
        "Para comecar",
        "Com suas palavras",
        "Observar a iluminura e levantar hipoteses sobre o contexto medieval.",
        "Foco no conteudo",
        "Ler trechos sobre a cultura galego-portuguesa e identificar marcas do trovadorismo.",
        "Na pratica",
        "Analisar cantigas e registrar caracteristicas no caderno.",
        "Encerramento",
        "Sistematizar as influencias medievais na literatura portuguesa.",
    ]:
        caixa = slide.shapes.add_textbox(0, 0, 9000000, 800000)
        caixa.text_frame.text = linha

    apresentacao.save(caminho)
    return caminho


def test_extrator_pptx_lingua_portuguesa_em_le_titulo_e_blocos(tmp_path):
    caminho_pptx = _criar_pptx_exemplo(tmp_path / "1220955.pptx")

    estrutura = extrair_estrutura_pptx(str(caminho_pptx))

    assert estrutura["fonte"] == "pptx"
    assert "aula 1" not in normalizar_texto(estrutura["titulo"])
    assert "literatura medieval portuguesa" in normalizar_texto(estrutura["titulo"])
    assert any("idade media" in normalizar_texto(item) for item in estrutura["conteudos"])
    assert any("trovador" in normalizar_texto(item) for item in estrutura["objetivos"])
    assert "Para comecar" in estrutura["blocos"]
    assert "Na pratica" in estrutura["blocos"]


def test_fluxo_piloto_prefere_pptx_e_nao_usa_nome_do_pdf_como_tema(tmp_path, monkeypatch):
    caminho_pdf = tmp_path / "AULA 1.pdf"
    caminho_pdf.write_text("PDF generico sem estrutura boa", encoding="utf-8")
    _criar_pptx_exemplo(tmp_path / "1220955.pptx")

    monkeypatch.setattr(lote, "_extrair_texto_pdf", lambda caminho: "AULA 1.pdf\nMaterial Digital\n")

    contexto = lote._preparar_contexto_aula_pdf(
        caminho_pdf=str(caminho_pdf),
        disciplina="Lingua Portuguesa",
        turma="1 ANO A",
        bimestre="3o Bimestre",
        indice_aula=0,
        modalidade_eja=False,
    )

    assert eh_cenario_piloto_pptx("Lingua Portuguesa", "1 ANO A") is True
    assert encontrar_pptx_correspondente(str(caminho_pdf), "Lingua Portuguesa", "1 ANO A")
    assert contexto["fonte_extracao"] == "pptx"
    assert "literatura medieval portuguesa" in normalizar_texto(contexto["tema"])
    assert "aula 1 pdf" not in normalizar_texto(contexto["tema"])

    aula = lote._aula_por_pdf(
        caminho_pdf=str(caminho_pdf),
        disciplina="Lingua Portuguesa",
        turma="1 ANO A",
        bimestre="3o Bimestre",
        usar_ia=False,
        provedor_ia="",
    )

    assert aula["fonte_extracao"] == "pptx"
    assert "literatura medieval portuguesa" in normalizar_texto(aula["tema"])
    assert "aula 1 pdf" not in normalizar_texto(aula["tema"])
    textos_metodologia = " ".join(item["texto"] for item in aula["metodologia"] if isinstance(item, dict))
    assert "trovador" in normalizar_texto(textos_metodologia) or "idade media" in normalizar_texto(textos_metodologia)


def test_estrutura_pptx_para_dados_aula_monta_texto_base(tmp_path):
    caminho_pptx = _criar_pptx_exemplo(tmp_path / "AULA 1.pptx")
    estrutura = extrair_estrutura_pptx(str(caminho_pptx))

    dados = estrutura_pptx_para_dados_aula(estrutura)

    assert dados["fonte_extracao"] == "pptx"
    assert "objetivos da aula" in normalizar_texto(dados["texto_base"])
    assert "para comecar" in normalizar_texto(dados["texto_base"])
    assert "foco no conteudo" in normalizar_texto(dados["texto_base"])
