import pytest
import os
import tempfile
from core.lib.extrator_pdf import extrair_texto_pdf

def test_extrair_texto_pdf_sem_fallback_falha_para_invalido():
    # Cria um arquivo temporário simulando um PDF corrompido (apenas texto plano)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False, mode="w", encoding="utf-8") as temp_file:
        temp_file.write("Este nao eh um PDF valido, eh apenas texto plano.")
        temp_path = temp_file.name

    try:
        # Por padrão, permitir_fallback_teste é False, deve lançar RuntimeError ao falhar em pdfplumber.open()
        with pytest.raises(RuntimeError) as exc_info:
            extrair_texto_pdf(temp_path, permitir_fallback_teste=False)
        assert "Nao foi possivel extrair texto do PDF" in str(exc_info.value)
        
        # Se permitir_fallback_teste for True, ele deve ler o conteúdo com fallback
        conteudo = extrair_texto_pdf(temp_path, permitir_fallback_teste=True)
        assert "Este nao eh um PDF valido" in conteudo
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except PermissionError:
                pass

