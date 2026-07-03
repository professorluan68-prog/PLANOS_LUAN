import pytest
import os
import tempfile
from core.lib.extrator_pdf import (
    extrair_texto_pdf,
    _avaliar_qualidade_docx_texto,
    _extrair_texto_via_pdf2docx,
)

def test_avaliar_qualidade_docx_texto():
    # Caso 1: Texto de boa qualidade
    texto_bom = "Este é um parágrafo longo o suficiente para passar no teste de qualidade.\n" * 5
    paragraphs_bom = [p.strip() for p in texto_bom.split("\n") if p.strip()]
    assert _avaliar_qualidade_docx_texto(texto_bom, paragraphs_bom) is True

    # Caso 2: Texto muito curto (menos de 200 caracteres)
    texto_curto = "Texto curto."
    paragraphs_curto = [texto_curto]
    assert _avaliar_qualidade_docx_texto(texto_curto, paragraphs_curto) is False

    # Caso 3: Poucos parágrafos (menos de 3)
    texto_pouco_p = "Este é um parágrafo bem longo que atinge mais de duzentos caracteres para tentar enganar a métrica de tamanho total do texto. Porém ele falhará na quantidade mínima de parágrafos estruturados."
    paragraphs_pouco_p = [texto_pouco_p]
    assert _avaliar_qualidade_docx_texto(texto_pouco_p, paragraphs_pouco_p) is False

    # Caso 4: Parágrafos muito curtos (média < 25 caracteres)
    texto_fragmentado = "A\nB\nC\nD\nE\nF\nG\nH\nI\nJ"
    paragraphs_fragmentados = [p.strip() for p in texto_fragmentado.split("\n") if p.strip()]
    assert _avaliar_qualidade_docx_texto(texto_fragmentado, paragraphs_fragmentados) is False


def test_extrair_texto_pdf_real_com_pdf2docx():
    # Usa um dos arquivos reais da pasta de história para validar a conversão
    caminho_real = r"D:\PDF novos\HISTORIA\AF\2_BIMESTRE\6_ANO\AULA 1.pdf"
    if not os.path.exists(caminho_real):
        pytest.skip(f"Arquivo de teste real não encontrado em {caminho_real}")

    # Deve extrair com sucesso e conter a habilidade
    texto = extrair_texto_pdf(caminho_real)
    assert len(texto) > 1000
    assert "EF06HI05" in texto or "História" in texto


def test_extrair_texto_pdf_fallback_quando_pdf2docx_falha():
    # Cria um arquivo simulado que não é um PDF válido
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False, mode="w", encoding="utf-8") as temp_file:
        temp_file.write("Conteúdo de texto plano simulando arquivo PDF corrompido para testar o fallback.")
        temp_path = temp_file.name

    try:
        # Quando pdf2docx falhar (porque não é um PDF válido), ele deve cair no fallback do pdfplumber
        # e no fim ler o texto plano se a flag permitir_fallback_teste for True
        texto = extrair_texto_pdf(temp_path, permitir_fallback_teste=True)
        assert "Conteúdo de texto plano" in texto
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
