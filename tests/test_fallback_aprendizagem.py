from core.ia import _aprendizagem_fallback_por_perfil


def test_fallback_aprendizagem_nao_herda_enunciado_bruto_de_slide():
    tema_bruto = (
        "Observe duas obras que foram criadas durante o periodo historico do "
        "Renascimento e responda as perguntas propostas no material."
    )

    aprendizagem = _aprendizagem_fallback_por_perfil(
        "lingua_portuguesa_em",
        tema_bruto,
        "(EM13LGG601)",
    )

    assert "Observe duas obras" not in aprendizagem
    assert "o tema da aula" in aprendizagem
