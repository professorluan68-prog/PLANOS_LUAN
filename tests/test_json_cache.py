import json
from pathlib import Path
from core.lote import _aula_por_pdf
from core.revisao_final import VERSAO_GERADOR_ATUAL, calcular_sha256
from core.variacao_metodologica import montar_fingerprint_contexto, selecionar_perfil_metodologico

def test_aula_por_pdf_loads_pre_generated_json(tmp_path):
    # Setup temporary PDF and JSON file next to it
    pdf_file = tmp_path / "AULA_TESTE.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 dummy contents")

    hash_pdf = calcular_sha256(str(pdf_file))
    turma = "6\u00ba ANO A"
    disciplina = "Matem\u00e1tica"
    bimestre = "2\u00ba Bimestre"
    perfil_metodologico = selecionar_perfil_metodologico("", turma, disciplina, bimestre)
    fingerprint_contexto = montar_fingerprint_contexto(
        hash_pdf=f"{hash_pdf}|modalidade:regular",
        versao_gerador=VERSAO_GERADOR_ATUAL,
        professor_nome="",
        turma=turma,
        disciplina=disciplina,
        bimestre=bimestre,
        tipo_aula="simples",
        perfil_metodologico=perfil_metodologico,
    )

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
        "ia_erro": "",
        "hash_pdf": hash_pdf,
        "versao_gerador": VERSAO_GERADOR_ATUAL,
        "fingerprint_contexto": fingerprint_contexto,
    }
    
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    # Call _aula_por_pdf with the path of the dummy PDF
    resultado = _aula_por_pdf(
        caminho_pdf=str(pdf_file),
        disciplina="Matemática",
        turma="6º ANO A",
        bimestre="2º Bimestre",
        usar_ia=True,
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


def test_aula_por_pdf_ignora_cache_com_versao_antiga(tmp_path):
    pdf_file = tmp_path / "AULA_TESTE.pdf"
    pdf_file.write_text("Conteudo novo do pdf", encoding="utf-8")

    json_file = tmp_path / "AULA_TESTE.json"
    json_data = {
        "disciplina": "Lingua Portuguesa",
        "tema": "Tema antigo em cache",
        "material": "AULA_TESTE.pdf",
        "numero_aula": "10",
        "aprendizagem": "Aprendizagem antiga.",
        "metodologia": [{"titulo": "Para comecar", "texto": "Texto antigo."}],
        "acompanhamento": ["Item antigo 1", "Item antigo 2", "Item antigo 3"],
        "acessibilidade": ["Item antigo 1", "Item antigo 2", "Item antigo 3"],
        "versao_gerador": "1.0.0",
    }

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    resultado = _aula_por_pdf(
        caminho_pdf=str(pdf_file),
        disciplina="Lingua Portuguesa",
        turma="1 ANO",
        bimestre="3o Bimestre",
        usar_ia=False,
        provedor_ia="",
    )

    assert resultado["tema"] != "Tema antigo em cache"
