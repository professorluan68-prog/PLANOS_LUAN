import pytest
from core.ia import _serializar_rascunho_base
from core.lote import _montar_resultado_aula_ia


def test_serializar_rascunho_base_inclui_acompanhamento_acessibilidade():
    rascunho = {
        "tema": "História do Brasil",
        "aprendizagem": "Analisar fontes históricas",
        "metodologia": [
            {"titulo": "Abertura", "texto": "Discussão inicial sobre fontes."}
        ],
        "acompanhamento": ["Observar a participação", "Checar registros"],
        "acessibilidade": ["Oferecer lupa para leitura", "Tempo extra"]
    }
    saida = _serializar_rascunho_base(rascunho)
    assert "História do Brasil" in saida
    assert "Acompanhamento da aprendizagem base:" in saida
    assert "- Observar a participação" in saida
    assert "Acessibilidade base:" in saida
    assert "- Tempo extra" in saida


def test_montar_resultado_aula_ia_preserva_refinamento_ia(monkeypatch):
    # Mock extrator to return basic values
    import core.lote as lote
    monkeypatch.setattr(lote._extrator_lib, "extrair", lambda *args, **kwargs: {
        "habilidade": "HAB123",
        "conceito_extraido": "Conceito de teste",
        "recursos_detectados": ["Quadro", "Caderno"]
    })

    plano_ia = {
        "tema": "Tema Refinado IA",
        "aprendizagem": "Aprendizagem Refinada IA",
        "metodologia": [
            {"titulo": "Relembre", "texto": "O professor faz uma introdução com a turma no caderno sobre História."},
            {"titulo": "Foco no conteudo", "texto": "Os estudantes leem e resolvem no caderno."},
            {"titulo": "Na pratica", "texto": "Os estudantes resolvem atividades em duplas."}
        ],
        "acompanhamento": [
            "Checar se a turma escreveu no caderno",
            "Apoiar os estudantes durante a leitura compartilhada",
            "Orientar a autoavaliação ao final"
        ],
        "acessibilidade": [
            "Prover materiais impressos adaptados",
            "Garantir tempo adicional para a resolução no caderno",
            "Oferecer apoio individualizado nas duplas"
        ]
    }

    referencia_docx = {
        "titulo": "Tema DOCX Cru",
        "metodologia": [{"titulo": "Etapa 1", "texto": "Texto DOCX antigo."}],
        "acompanhamento": ["Item DOCX Antigo 1", "Item DOCX Antigo 2"],
        "acessibilidade": ["Acesso DOCX Antigo 1", "Acesso DOCX Antigo 2"],
        "fonte": "referencia.docx"
    }

    monkeypatch.setattr(lote, "_referencia_docx_por_perfil", lambda *args, **kwargs: referencia_docx)

    resultado = _montar_resultado_aula_ia(
        texto="Texto da aula",
        tema=plano_ia["tema"],
        material_digital="AULA 1",
        numero_aula="1",
        disciplina_base="História",
        turma="6º ANO A",
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
        caminho_pdf="dummy.pdf"
    )

    # Verify that the final result uses the IA's refined content and NOT the raw docx!
    assert resultado["tema"] == "Tema Refinado IA"
    assert "Tema Refinado IA" in resultado["aprendizagem"]

    # Assert that the methodology has the IA's text (sanitized/naturalized)
    texto_metodologia = "".join(m["texto"] for m in resultado["metodologia"])
    assert "professor" in texto_metodologia
    assert "DOCX antigo" not in texto_metodologia

    # Assert that acompanhamento has IA items (and not docx ancient ones)
    assert any("escreveu no caderno" in item for item in resultado["acompanhamento"])
    assert not any("DOCX Antigo" in item for item in resultado["acompanhamento"])

    # Assert that acessibilidade has IA items
    assert any("tempo adicional" in item for item in resultado["acessibilidade"])
    assert not any("DOCX Antigo" in item for item in resultado["acessibilidade"])
