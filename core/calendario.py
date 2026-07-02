from datetime import date, timedelta


DATAS_SEM_AULA_FIXAS = {
    date(2026, 8, 6),
}


def data_pascoa(ano: int) -> date:
    """Calcula a data da Pascoa pelo algoritmo gregoriano."""
    a = ano % 19
    b = ano // 100
    c = ano % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return date(ano, mes, dia)


def feriados_nacionais_brasil(ano: int) -> set[date]:
    pascoa = data_pascoa(ano)
    return {
        date(ano, 1, 1),
        pascoa - timedelta(days=48),
        pascoa - timedelta(days=47),
        pascoa - timedelta(days=2),
        date(ano, 4, 21),
        date(ano, 5, 1),
        pascoa + timedelta(days=60),
        date(ano, 9, 7),
        date(ano, 10, 12),
        date(ano, 11, 2),
        date(ano, 11, 15),
        date(ano, 11, 20),
        date(ano, 12, 25),
    }


def datas_sem_aula_fixadas(ano: int) -> set[date]:
    return {data_aula for data_aula in DATAS_SEM_AULA_FIXAS if data_aula.year == ano}


def datas_sem_aula_calendario(ano: int) -> set[date]:
    return feriados_nacionais_brasil(ano) | datas_sem_aula_fixadas(ano)


def rotulo_data_sem_aula(data_aula: date) -> str:
    dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"]
    return f"{data_aula.strftime('%d/%m/%Y')} ({dias[data_aula.weekday()]})"


def datas_sem_aula_padrao(itens: list[dict]) -> list[date]:
    if not itens:
        return []
    feriados = datas_sem_aula_calendario(next(iter(itens))["data"].year)
    datas = []
    for item in itens:
        data_aula = item.get("data")
        if data_aula in feriados and data_aula not in datas:
            datas.append(data_aula)
    return datas


def datas_feriado_padrao(datas_base: list[date]) -> list[date]:
    if not datas_base:
        return []
    feriados = datas_sem_aula_calendario(datas_base[0].year)
    return [data_aula for data_aula in datas_base if data_aula in feriados]


def filtrar_datas_sem_aula(itens: list[dict], datas_sem_aula: list[date] | set[date] | None) -> list[dict]:
    if not itens:
        return []
    bloqueadas = set(datas_sem_aula or [])
    if not bloqueadas:
        return list(itens)
    return [item for item in itens if item.get("data") not in bloqueadas]


def ultimo_dia_do_mes(ano: int, mes: int) -> date:
    if mes == 12:
        return date(ano + 1, 1, 1) - timedelta(days=1)
    return date(ano, mes + 1, 1) - timedelta(days=1)


def inicio_periodo_mes_com_antecipacao(ano: int, mes: int, antecipacao: int = 0) -> date:
    """
    antecipacao:
    0 = iniciar no primeiro dia do mes
    1 = incluir a semana letiva que antecede o inicio do mes, abrindo o
        periodo na segunda-feira da semana em que cai o dia 1
    """
    primeiro = date(ano, mes, 1)
    if antecipacao <= 0:
        return primeiro
    return primeiro - timedelta(days=primeiro.weekday() + (7 * (antecipacao - 1)))


def fim_periodo_mes_com_extensao(ano: int, mes: int, extensao: int = 0) -> date:
    """
    extensao:
    0 = somente o mes
    1 = completar a ultima semana util que cruza o fim do mes
    2 = completar a ultima semana util + 1 semana adicional
    3 = completar a ultima semana util + 2 semanas adicionais
    """
    ultimo = ultimo_dia_do_mes(ano, mes)
    if extensao <= 0:
        return ultimo
    dias_ate_sexta = max(4 - ultimo.weekday(), 0)
    return ultimo + timedelta(days=dias_ate_sexta + (7 * (extensao - 1)))


def datas_por_dia_ate_limite(inicio: date, fim: date, dia_semana: int) -> list[date]:
    atual = inicio
    datas = []
    while atual <= fim:
        if atual.weekday() == dia_semana:
            datas.append(atual)
        atual += timedelta(days=1)
    return datas


def datas_do_periodo(inicio: date, fim: date) -> list[date]:
    atual = inicio
    datas = []
    while atual <= fim:
        datas.append(atual)
        atual += timedelta(days=1)
    return datas
