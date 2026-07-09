from pathlib import Path

from core import seletor_referencias


def test_itens_referencia_docx_normaliza_e_limita_tres():
    referencia = {
        "acompanhamento": ["Item 1", "☑ Item 2", "", "Item 4"],
    }

    itens = seletor_referencias.itens_referencia_docx(referencia, "acompanhamento")

    assert itens == ["☑ Item 1", "☑ Item 2"]


def test_sobrescrever_listas_pedagogicas_com_referencia_exige_tres_itens():
    referencia = {
        "acompanhamento": ["Item 1", "Item 2", "Item 3"],
        "acessibilidade": ["Apoio 1", "Apoio 2"],
    }

    acompanhamento, acessibilidade = (
        seletor_referencias.sobrescrever_listas_pedagogicas_com_referencia(
            referencia,
            ["Base 1"],
            ["Base A"],
        )
    )

    assert acompanhamento == ["☑ Item 1", "☑ Item 2", "☑ Item 3"]
    assert acessibilidade == ["Base A"]


def test_assinatura_docx_referencia_usa_docx_localizado(monkeypatch, tmp_path):
    caminho_pdf = tmp_path / "AULA_1.pdf"
    caminho_pdf.write_bytes(b"%PDF-1.4")
    caminho_docx = tmp_path / "referencia.docx"
    caminho_docx.write_bytes(b"docx")

    monkeypatch.setattr(
        seletor_referencias,
        "localizar_docx_referencia_por_perfil",
        lambda *args, **kwargs: caminho_docx,
    )

    assinatura = seletor_referencias.assinatura_docx_referencia(
        str(caminho_pdf),
        "Matematica",
        "1 ANO A",
    )

    assert assinatura.startswith("referencia.docx|")


def test_deve_aplicar_referencia_docx_no_resultado_ia_respeita_perfil():
    assert seletor_referencias.deve_aplicar_referencia_docx_no_resultado_ia(
        "lingua_portuguesa_ef",
        {"metodologia": [{"titulo": "Etapa", "texto": "Texto IA"}]},
    )
    assert not seletor_referencias.deve_aplicar_referencia_docx_no_resultado_ia(
        "historia",
        {"metodologia": [{"titulo": "Etapa", "texto": "Texto IA"}]},
    )
    assert seletor_referencias.deve_aplicar_referencia_docx_no_resultado_ia(
        "historia",
        {"metodologia": []},
    )


def test_perfil_prioriza_docx_sobre_cache_json_para_perfis_com_referencia():
    assert seletor_referencias.perfil_prioriza_docx_sobre_cache_json("historia")
    assert seletor_referencias.perfil_prioriza_docx_sobre_cache_json("arte")
    assert seletor_referencias.perfil_prioriza_docx_sobre_cache_json("lingua_portuguesa_ef")
    assert not seletor_referencias.perfil_prioriza_docx_sobre_cache_json("filosofia")


def test_material_aula_com_titulo_monta_rotulo_padrao():
    assert (
        seletor_referencias.material_aula_com_titulo("AULA 7", "Equacoes")
        == "AULA 7 - Equacoes"
    )
