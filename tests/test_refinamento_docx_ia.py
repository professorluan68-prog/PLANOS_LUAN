import pytest

from core.ia import _serializar_rascunho_base
from core.lote import _montar_resultado_aula_ia


def test_serializar_rascunho_base_inclui_acompanhamento_acessibilidade():
    rascunho = {
        "tema": "Historia do Brasil",
        "aprendizagem": "Analisar fontes historicas",
        "metodologia": [
            {"titulo": "Abertura", "texto": "Discussao inicial sobre fontes."}
        ],
        "acompanhamento": ["Observar a participacao", "Checar registros"],
        "acessibilidade": ["Oferecer lupa para leitura", "Tempo extra"],
    }
    saida = _serializar_rascunho_base(rascunho)
    assert "Historia do Brasil" in saida
    assert "Acompanhamento da aprendizagem base:" in saida
    assert "- Observar a participacao" in saida
    assert "Acessibilidade base:" in saida
    assert "- Tempo extra" in saida


def test_montar_resultado_aula_ia_com_docx_usa_referencia_exata(monkeypatch):
    import core.lote as lote

    monkeypatch.setattr(
        lote._extrator_lib,
        "extrair",
        lambda *args, **kwargs: {
            "habilidade": "HAB123",
            "conceito_extraido": "Conceito de teste",
            "recursos_detectados": ["Quadro", "Caderno"],
        },
    )

    plano_ia = {
        "tema": "Tema Refinado IA",
        "aprendizagem": "Aprendizagem Refinada IA",
        "metodologia": [
            {"titulo": "Relembre", "texto": "Texto da IA."},
        ],
        "acompanhamento": ["IA 1", "IA 2", "IA 3"],
        "acessibilidade": ["Acesso 1", "Acesso 2", "Acesso 3"],
    }

    referencia_docx = {
        "titulo": "Tema DOCX Cru",
        "metodologia": [{"titulo": "Etapa 1", "texto": "Texto DOCX antigo."}],
        "acompanhamento": ["Item DOCX Antigo 1", "Item DOCX Antigo 2", "Item DOCX Antigo 3"],
        "acessibilidade": ["Acesso DOCX Antigo 1", "Acesso DOCX Antigo 2", "Acesso DOCX Antigo 3"],
        "fonte": "referencia.docx",
    }

    monkeypatch.setattr(lote, "_referencia_docx_por_perfil", lambda *args, **kwargs: referencia_docx)

    resultado = _montar_resultado_aula_ia(
        texto="Texto da aula",
        tema=plano_ia["tema"],
        material_digital="AULA 1",
        numero_aula="1",
        disciplina_base="Historia",
        turma="6 ANO A",
        provedor_ia="openai",
        perfil="historia",
        contexto_metodologico="regular",
        indice_aula=0,
        total_aulas=1,
        modalidade_eja_ativa=False,
        plano_ia=plano_ia,
        metodologia_fixa_pdf=[],
        aprendizagem_pv="",
        objetivos_orientacao=[],
        aprendizagem_orientacao="",
        caminho_pdf="dummy.pdf",
    )

    assert resultado["tema"] == "Tema Refinado IA"
    assert "Tema Refinado IA" in resultado["aprendizagem"]
    assert resultado["metodologia"][0]["texto"] == "Texto DOCX antigo."
    assert resultado["acompanhamento"] == [
        "Item DOCX Antigo 1",
        "Item DOCX Antigo 2",
        "Item DOCX Antigo 3",
    ]
    assert resultado["acessibilidade"] == [
        "Acesso DOCX Antigo 1",
        "Acesso DOCX Antigo 2",
        "Acesso DOCX Antigo 3",
    ]
    assert resultado["ia_usada"] is False
