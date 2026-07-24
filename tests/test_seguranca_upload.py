import pytest

from core.seguranca_upload import (
    ArquivoPDFInvalido,
    nome_pdf_upload_temporario,
    nomes_pdf_original_possiveis,
    validar_pdf_bytes,
)


def test_nome_temporario_preserva_nome_original():
    nome = nome_pdf_upload_temporario("1 Jornada 07 — Etapa 1.pdf", "AbC1")

    assert nome.startswith("planos_luan_upload_AbC1__")
    assert nomes_pdf_original_possiveis(nome)[1] == "1 Jornada 07 — Etapa 1.pdf"


def test_validar_pdf_rejeita_assinatura_invalida():
    with pytest.raises(ArquivoPDFInvalido, match="assinatura PDF"):
        validar_pdf_bytes(
            b"not-a-pdf",
            "aula.pdf",
            contador_paginas=lambda _: 1,
        )


def test_validar_pdf_rejeita_excesso_de_paginas():
    with pytest.raises(ArquivoPDFInvalido, match="ultrapassa o limite"):
        validar_pdf_bytes(
            b"%PDF-1.7",
            "aula.pdf",
            limite_paginas=2,
            contador_paginas=lambda _: 3,
        )
