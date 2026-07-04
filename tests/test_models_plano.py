from core.models import PlanoCompleto


def test_plano_completo_normaliza_metodologia_e_sidecar():
    plano = PlanoCompleto.from_any(
        {
            "disciplina": "História",
            "tema": "Revolução Francesa",
            "aprendizagem": "Compreender causas e consequências.",
            "metodologia": [
                {"titulo": "Para começar", "texto": "Retomar conhecimentos prévios."},
                "Síntese final livre",
            ],
            "acompanhamento": ["☑ Observar a participação."],
            "acessibilidade": ["☑ Oferecer glossário visual."],
            "confidence_score": 92,
            "avisos_validacao": ["Atenção em um item."],
        }
    )

    dados = plano.to_dict()
    assert dados["metodologia"][0]["titulo"] == "Para começar"
    assert dados["metodologia"][1] == "Síntese final livre"

    sidecar = plano.to_sidecar_dict(
        "D:/PDF novos/HISTORIA/AULA_1.pdf",
        "hash-teste",
        lambda valor: str(valor),
    )
    assert sidecar["tema"] == "Revolução Francesa"
    assert sidecar["hash_pdf"] == "hash-teste"
    assert sidecar["material"] == "AULA_1.pdf"
    assert sidecar["confidence_score"] == 92
