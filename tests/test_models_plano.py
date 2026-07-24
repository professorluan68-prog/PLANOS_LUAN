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
    assert dados["metodologia"][1]["texto"] == "Síntese final livre"

    sidecar = plano.to_sidecar_dict(
        "D:/PDF novos/HISTORIA/AULA_1.pdf",
        "hash-teste",
        lambda valor: str(valor),
    )
    assert sidecar["tema"] == "Revolução Francesa"
    assert sidecar["hash_pdf"] == "hash-teste"
    assert sidecar["material"] == "AULA_1.pdf"
    assert sidecar["confidence_score"] == 92


def test_plano_completo_normaliza_campos_textuais_preservando_titulos():
    plano = PlanoCompleto.from_any(
        {
            "disciplina": "Orientação de Estudos",
            "metodologia": (
                "Para começar: Retomar as estratégias usadas na aula anterior.\n\n"
                "Foco no conteúdo: Analisar as fontes e registrar as conclusões."
            ),
            "acompanhamento_aprendizagem": (
                "• Verificar os registros.\n• Observar a argumentação.\n• Retomar dúvidas."
            ),
            "acessibilidade": (
                "☑ Realizar leitura orientada.\n"
                "☑ Disponibilizar apoio visual.\n"
                "☑ Permitir resposta oral mediada."
            ),
        }
    )

    dados = plano.to_dict()
    assert [etapa["titulo"] for etapa in dados["metodologia"]] == [
        "Para começar",
        "Foco no conteúdo",
    ]
    assert len(dados["acompanhamento"]) == 3
    assert dados["acompanhamento"][0] == "Verificar os registros."
    assert len(dados["acessibilidade"]) == 3
    assert dados["acessibilidade"][0].startswith("☑")
