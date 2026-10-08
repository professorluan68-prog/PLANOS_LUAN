from io import BytesIO
from docx import Document


def validar_docx_gerado(buffer: BytesIO) -> BytesIO:
    """Valida integridade do DOCX gerado relendo o buffer em memória."""
    conteudo = buffer.getvalue()
    try:
        Document(BytesIO(conteudo))
    except Exception as exc:
        raise ValueError(f"DOCX gerado está corrompido: {exc}") from exc
    buffer.seek(0)
    return buffer
