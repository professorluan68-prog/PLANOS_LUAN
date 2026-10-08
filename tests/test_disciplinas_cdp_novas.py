from core.disciplinas import (
    nomes_disciplinas,
    TURMAS_CDP,
    DISCIPLINAS_CDP_PADRONIZADAS,
    obter_config,
    MODO_PDF,
    eh_cdp_contextual,
)


def test_disciplinas_cdp_padronizadas():
    disciplinas = nomes_disciplinas()
    for disc in DISCIPLINAS_CDP_PADRONIZADAS:
        assert disc in disciplinas, f"Disciplina {disc} não encontrada nas disciplinas ativas"
        config = obter_config(disc)
        assert config.modo == MODO_PDF, f"Disciplina {disc} deveria usar MODO_PDF (fluxo contextual com PDFs)"
        assert config.exige_pdf is True
        assert eh_cdp_contextual(disc) is True


def test_turmas_cdp_padronizadas():
    assert TURMAS_CDP == ["C", "H", "J", "E"]
