import pytest

from core.seguranca_upload import (
    ArquivoPDFInvalido,
    limpar_upload_temporario,
    nome_pdf_upload_temporario,
    nomes_pdf_original_possiveis,
    salvar_pdf_upload_temporario,
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


def test_upload_temporario_remove_pdf_e_sidecar(tmp_path):
    caminho_pdf = salvar_pdf_upload_temporario(
        b"%PDF-1.7",
        "AULA 1.pdf",
        raiz_temporaria=tmp_path,
        contador_paginas=lambda _: 1,
    )
    caminho_json = caminho_pdf.with_suffix(".json")
    caminho_json.write_text('{"texto_fonte": "conteudo"}', encoding="utf-8")

    assert caminho_pdf.exists()
    assert caminho_json.exists()
    assert limpar_upload_temporario(
        caminho_pdf,
        raiz_temporaria=tmp_path,
    )
    assert not caminho_pdf.parent.exists()


def test_limpeza_temporaria_nao_remove_arquivo_fora_do_diretorio_exclusivo(tmp_path):
    arquivo = tmp_path / "aula.pdf"
    arquivo.write_bytes(b"%PDF-1.7")

    assert not limpar_upload_temporario(
        arquivo,
        raiz_temporaria=tmp_path,
    )
    assert arquivo.exists()
