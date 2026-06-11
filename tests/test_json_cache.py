import json
from pathlib import Path
from core.lote import _aula_por_pdf

def test_aula_por_pdf_loads_pre_generated_json(tmp_path):
    # Setup temporary PDF and JSON file next to it
    pdf_file = tmp_path / "AULA_TESTE.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 dummy contents")

    json_file = tmp_path / "AULA_TESTE.json"
    json_data = {
        "disciplina": "Matemática",
        "tema": "Frações Equivalentes Teste",
        "material": "AULA_TESTE.pdf",
        "numero_aula": "5",
        "aprendizagem": "Identificar frações equivalentes com apoio visual.",
        "metodologia": [
            {"titulo": "Para começar", "texto": "Discussão inicial sobre partes de um todo."},
            {"titulo": "Foco no conteúdo", "texto": "Exposição do conceito de equivalência."},
            {"titulo": "Na prática", "texto": "Resolução de exercícios práticos."}
        ],
        "acompanhamento": [
            "Observação durante as resoluções de problemas.",
            "Feedback imediato."
        ],
        "acessibilidade": [
            "Uso de frações coloridas em blocos.",
            "Tempo estendido para exercícios."
        ],
        "ia_usada": True,
        "ia_provedor": "Gemini",
        "ia_erro": ""
    }
    
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    # Call _aula_por_pdf with the path of the dummy PDF
    resultado = _aula_por_pdf(
        caminho_pdf=str(pdf_file),
        disciplina="Matemática",
        turma="6º ANO A",
        bimestre="2º Bimestre",
        usar_ia=False,
        provedor_ia=""
    )

    # Check that it returns the data loaded from the JSON
    assert resultado["tema"] == "Frações Equivalentes Teste"
    assert resultado["numero_aula"] == "5"
    assert resultado["aprendizagem"] == "Identificar frações equivalentes com apoio visual."
    assert len(resultado["metodologia"]) == 3
    assert resultado["metodologia"][0]["titulo"] == "Para começar"
    assert resultado["acompanhamento"][0] == "Observação durante as resoluções de problemas."
    assert resultado["acessibilidade"][0] == "Uso de frações coloridas em blocos."
    assert resultado["ia_usada"] is True
    assert resultado["ia_provedor"] == "Gemini"
