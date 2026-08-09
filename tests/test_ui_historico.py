from ui.historico import _formatar_mes_plano, _formatar_resumo_aulas, _formatar_turma


def test_formatar_turma_multisseriada_ensino_fundamental():
    assert _formatar_turma("8O 9O E F") == "8º/9º E.F."
    assert _formatar_turma("6O 7O E F") == "6º/7º E.F."


def test_formatar_turma_multisseriada_ensino_medio():
    assert _formatar_turma("1O 2O 3O E M") == "1º/2º/3º E.M."


def test_formatar_turma_regular():
    assert _formatar_turma("8O ANO C") == "8º ANO C"


def test_formatar_resumo_aulas():
    assert _formatar_resumo_aulas(9, 8) == "Aulas: 1-9 (8)"
    assert _formatar_resumo_aulas(0, 0) == ""


def test_formatar_mes_plano():
    assert _formatar_mes_plano("2026-09") == "Setembro/2026"
    assert _formatar_mes_plano("") == ""
