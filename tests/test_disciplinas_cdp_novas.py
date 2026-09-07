from core.disciplinas import nomes_disciplinas, TURMAS_CDP, obter_config, MODO_CDP


def test_novas_disciplinas_cdp_cadastradas():
    disciplinas = nomes_disciplinas()
    novas_esperadas = [
        "História_EF-CDP",
        "História_EM-CDP",
        "Geografia_EM-CDP",
        "Sociologia-CDP",
        "Liderança-CDP",
        "Matemática_EM-CDP",
        "Matemática_EF-CDP",
    ]
    for disc in novas_esperadas:
        assert disc in disciplinas, f"Disciplina {disc} não encontrada nas disciplinas ativas"
        config = obter_config(disc)
        assert config.modo == MODO_CDP, f"Disciplina {disc} deveria ter modo MODO_CDP"
        assert config.exige_pdf is False, f"Disciplina {disc} não deveria exigir PDF obrigatoriamente"

    assert "Matemática-CDP" not in disciplinas, "Matemática-CDP antiga deveria ter sido removida/substituída"


def test_novas_turmas_cdp_cadastradas():
    turmas_novas = [
        "6º/7ºANO-TURMA C",
        "6º/7ºANO-TURMA H",
        "8º/9°ANO-TURMA J",
        "8º/9°ANO-TURMA E",
        "1°/2°/3°-TURMA J",
        "1°/2°/3°-TURMA E",
    ]
    for t in turmas_novas:
        assert t in TURMAS_CDP, f"Turma {t} não encontrada em TURMAS_CDP"

    assert "6º/7º E.F/ C" not in TURMAS_CDP, "Turma antiga 6º/7º E.F/ C não deveria estar presente"
    assert "8º/9º E.F/ H" not in TURMAS_CDP, "Turma antiga 8º/9º E.F/ H não deveria estar presente"
