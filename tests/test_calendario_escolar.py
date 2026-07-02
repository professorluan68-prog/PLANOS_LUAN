from datetime import date

from core.calendario import (
    datas_sem_aula_calendario,
    datas_do_periodo,
    datas_feriado_padrao,
    datas_por_dia_ate_limite,
    datas_sem_aula_padrao,
    feriados_nacionais_brasil,
    filtrar_datas_sem_aula,
    fim_periodo_mes_com_extensao,
    inicio_periodo_mes_com_antecipacao,
)


def test_feriados_nacionais_detecta_corpus_christi_2026():
    feriados = feriados_nacionais_brasil(2026)

    assert date(2026, 6, 4) in feriados


def test_datas_sem_aula_padrao_marca_feriado_nacional_presente_na_agenda():
    agenda = [
        {"data": date(2026, 6, 4), "horario": "13h - 14h40"},
        {"data": date(2026, 6, 5), "horario": "13h - 14h40"},
        {"data": date(2026, 6, 11), "horario": "13h - 14h40"},
    ]

    assert datas_sem_aula_padrao(agenda) == [date(2026, 6, 4)]


def test_filtrar_datas_sem_aula_remove_feriado_e_ponto_facultativo():
    agenda = [
        {"data": date(2026, 6, 4), "horario": "13h - 14h40"},
        {"data": date(2026, 6, 5), "horario": "13h - 14h40"},
        {"data": date(2026, 6, 11), "horario": "13h - 14h40"},
    ]

    filtrada = filtrar_datas_sem_aula(agenda, [date(2026, 6, 4), date(2026, 6, 5)])

    assert [item["data"] for item in filtrada] == [date(2026, 6, 11)]


def test_extensao_mes_completa_ultima_semana_que_avanca_no_mes_seguinte():
    assert fim_periodo_mes_com_extensao(2026, 6, 1) == date(2026, 7, 3)


def test_datas_por_dia_ate_limite_inclui_inicio_do_mes_seguinte_quando_extendido():
    datas = datas_por_dia_ate_limite(date(2026, 6, 1), fim_periodo_mes_com_extensao(2026, 6, 1), 3)

    assert datas[-1] == date(2026, 7, 2)


def test_inicio_periodo_mes_com_antecipacao_inclui_semana_anterior_quando_mes_comeca_no_fim_de_semana():
    assert inicio_periodo_mes_com_antecipacao(2026, 8, 1) == date(2026, 7, 27)


def test_datas_do_periodo_de_junho_incluem_feriado_e_ponte():
    datas = datas_do_periodo(date(2026, 6, 1), date(2026, 6, 30))

    assert date(2026, 6, 4) in datas
    assert date(2026, 6, 5) in datas


def test_datas_feriado_padrao_marca_corpus_christi_no_periodo():
    datas = datas_do_periodo(date(2026, 6, 1), date(2026, 6, 30))

    assert date(2026, 6, 4) in datas_feriado_padrao(datas)


def test_datas_sem_aula_padrao_inclui_feriados_escolares_de_agosto_2026():
    datas = datas_do_periodo(date(2026, 8, 1), date(2026, 8, 31))

    assert date(2026, 8, 6) in datas_sem_aula_calendario(2026)
    assert date(2026, 8, 7) in datas_sem_aula_calendario(2026)
    assert date(2026, 8, 6) in datas_feriado_padrao(datas)
    assert date(2026, 8, 7) in datas_feriado_padrao(datas)


def test_filtrar_datas_sem_aula_remove_apenas_data_especifica_nao_dia_da_semana():
    """Regressão: remover uma quinta-feira feriado não deve sumir com as outras quintas."""
    # Simula agenda com quintas-feiras de junho (4 quintas)
    quintas_junho = [
        date(2026, 6, 4),   # quinta - Corpus Christi (feriado)
        date(2026, 6, 11),
        date(2026, 6, 18),
        date(2026, 6, 25),
    ]
    agenda = [{"data": d, "horario": "13h - 14h40"} for d in quintas_junho]

    # Remove apenas o feriado (1ª quinta)
    filtrada = filtrar_datas_sem_aula(agenda, [date(2026, 6, 4)])
    datas_restantes = [item["data"] for item in filtrada]

    # As demais quintas devem permanecer intactas
    assert date(2026, 6, 11) in datas_restantes
    assert date(2026, 6, 18) in datas_restantes
    assert date(2026, 6, 25) in datas_restantes
    assert date(2026, 6, 4) not in datas_restantes
