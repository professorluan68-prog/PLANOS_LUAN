from core.turmas import chave_serie_turma, letra_turma, turmas_espelho_mesma_serie


def test_filtra_turma_espelho_apenas_mesma_serie_com_letra_diferente():
    candidatas = turmas_espelho_mesma_serie(
        "7º ANO A",
        ["7º ANO A", "7º ANO B", "8º ANO A", "7º ANO C", "7º ANO"],
    )

    assert candidatas == ["7º ANO B", "7º ANO C"]


def test_filtra_turma_espelho_preserva_ordem_e_remove_duplicadas():
    candidatas = turmas_espelho_mesma_serie(
        "7o ANO A",
        ["7º ANO C", "7º ANO B", "7º ANO C", "6º ANO B"],
    )

    assert candidatas == ["7º ANO C", "7º ANO B"]


def test_filtra_turma_espelho_para_ensino_medio_com_serie():
    candidatas = turmas_espelho_mesma_serie(
        "1ª SÉRIE A",
        ["1ª SÉRIE B", "1ª SÉRIE C", "2ª SÉRIE A", "1º ANO B"],
    )

    assert candidatas == ["1ª SÉRIE B", "1ª SÉRIE C"]


def test_chave_e_letra_da_turma():
    assert chave_serie_turma("7º ANO A") == "ANO:7"
    assert chave_serie_turma("1ª SÉRIE B") == "SERIE:1"
    assert letra_turma("7º ANO A") == "A"


def test_sem_turma_principal_valida_nao_oferece_espelho():
    assert turmas_espelho_mesma_serie("", ["7º ANO B"]) == []
    assert turmas_espelho_mesma_serie("Turma livre", ["7º ANO B"]) == []
