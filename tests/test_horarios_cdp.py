from core.constantes import (
    HORARIOS_CDP_MANHA,
    HORARIOS_CDP_TARDE,
    TURNOS_CDP_AULAS,
    TURNOS_AULAS_ESPECIAIS,
    HORARIOS_AULA,
)
from ui.shared import (
    _aulas_disponiveis_turno,
    _defaults_grade_horarios,
    _montar_horario_flexivel,
    _sugerir_horario_cadastrado,
    _turno_e_aulas_de_horario,
    _indice_horario,
)
from docx_generator.preencher import (
    _quantidade_aulas_por_horario,
    _formatar_horario_modelo,
)


def test_turnos_cdp_disponiveis_e_aulas():
    assert "CDP - Manhã" in TURNOS_AULAS_ESPECIAIS
    assert "CDP - Tarde" in TURNOS_AULAS_ESPECIAIS
    assert _aulas_disponiveis_turno("CDP - Manhã") == [1, 2, 3, 4, 5]
    assert _aulas_disponiveis_turno("CDP - Tarde") == [1, 2, 3, 4, 5]


def test_turnos_cdp_horarios_base_manha():
    manha = TURNOS_CDP_AULAS["CDP - Manhã"]
    # 45 min por aula, intervalo de 15 min entre 3ª e 4ª aula
    assert manha[1] == ("07h30", "08h15")
    assert manha[2] == ("08h15", "09h")
    assert manha[3] == ("09h", "09h45")
    # Intervalo 9h45 - 10h
    assert manha[4] == ("10h", "10h45")
    assert manha[5] == ("10h45", "11h30")


def test_turnos_cdp_horarios_base_tarde():
    tarde = TURNOS_CDP_AULAS["CDP - Tarde"]
    # 45 min por aula, intervalo de 15 min entre 3ª e 4ª aula
    assert tarde[1] == ("13h", "13h45")
    assert tarde[2] == ("13h45", "14h30")
    assert tarde[3] == ("14h30", "15h15")
    # Intervalo 15h15 - 15h30
    assert tarde[4] == ("15h30", "16h15")
    assert tarde[5] == ("16h15", "17h")


def test_montar_horario_flexivel_cdp_manha():
    # Aulas simples
    assert _montar_horario_flexivel("CDP - Manhã", ["1ª"]) == ("07h30", "1ª aula")
    assert _montar_horario_flexivel("CDP - Manhã", ["2ª"]) == ("08h15", "2ª aula")
    assert _montar_horario_flexivel("CDP - Manhã", ["3ª"]) == ("09h", "3ª aula")
    assert _montar_horario_flexivel("CDP - Manhã", ["4ª"]) == ("10h", "4ª aula")
    assert _montar_horario_flexivel("CDP - Manhã", ["5ª"]) == ("10h45", "5ª aula")

    # Aulas duplas consecutivas
    assert _montar_horario_flexivel("CDP - Manhã", ["1ª", "2ª"]) == ("07h30 - 09h", "1ª e 2ª aula")
    assert _montar_horario_flexivel("CDP - Manhã", ["2ª", "3ª"]) == ("08h15 - 09h45", "2ª e 3ª aula")
    assert _montar_horario_flexivel("CDP - Manhã", ["3ª", "4ª"]) == ("09h - 10h45", "3ª e 4ª aula")
    assert _montar_horario_flexivel("CDP - Manhã", ["4ª", "5ª"]) == ("10h - 11h30", "4ª e 5ª aula")

    # Aulas triplas / maiores
    assert _montar_horario_flexivel("CDP - Manhã", ["1ª", "2ª", "3ª"]) == ("07h30 - 09h45", "1ª, 2ª e 3ª aula")
    assert _montar_horario_flexivel("CDP - Manhã", ["3ª", "4ª", "5ª"]) == ("09h - 11h30", "3ª, 4ª e 5ª aula")
    assert _montar_horario_flexivel("CDP - Manhã", ["1ª", "2ª", "3ª", "4ª", "5ª"]) == ("07h30 - 11h30", "1ª, 2ª, 3ª, 4ª e 5ª aula")

    # Aulas não consecutivas
    assert _montar_horario_flexivel("CDP - Manhã", ["1ª", "4ª"]) == ("07h30 - 08h15 | 10h - 10h45", "1ª e 4ª aula")


def test_montar_horario_flexivel_cdp_tarde():
    # Aulas simples
    assert _montar_horario_flexivel("CDP - Tarde", ["1ª"]) == ("13h", "1ª aula")
    assert _montar_horario_flexivel("CDP - Tarde", ["2ª"]) == ("13h45", "2ª aula")
    assert _montar_horario_flexivel("CDP - Tarde", ["3ª"]) == ("14h30", "3ª aula")
    assert _montar_horario_flexivel("CDP - Tarde", ["4ª"]) == ("15h30", "4ª aula")
    assert _montar_horario_flexivel("CDP - Tarde", ["5ª"]) == ("16h15", "5ª aula")

    # Aulas duplas consecutivas
    assert _montar_horario_flexivel("CDP - Tarde", ["1ª", "2ª"]) == ("13h - 14h30", "1ª e 2ª aula")
    assert _montar_horario_flexivel("CDP - Tarde", ["2ª", "3ª"]) == ("13h45 - 15h15", "2ª e 3ª aula")
    assert _montar_horario_flexivel("CDP - Tarde", ["3ª", "4ª"]) == ("14h30 - 16h15", "3ª e 4ª aula")
    assert _montar_horario_flexivel("CDP - Tarde", ["4ª", "5ª"]) == ("15h30 - 17h", "4ª e 5ª aula")

    # Aulas triplas / maiores
    assert _montar_horario_flexivel("CDP - Tarde", ["1ª", "2ª", "3ª"]) == ("13h - 15h15", "1ª, 2ª e 3ª aula")
    assert _montar_horario_flexivel("CDP - Tarde", ["3ª", "4ª", "5ª"]) == ("14h30 - 17h", "3ª, 4ª e 5ª aula")
    assert _montar_horario_flexivel("CDP - Tarde", ["1ª", "2ª", "3ª", "4ª", "5ª"]) == ("13h - 17h", "1ª, 2ª, 3ª, 4ª e 5ª aula")


def test_reconhecimento_e_defaults_grade_cdp():
    # Manhã
    defaults_m = _defaults_grade_horarios("Segunda", "07h30 - 09h - 1ª e 2ª aula")
    assert defaults_m["Segunda"]["turno"] == "CDP - Manhã"
    assert defaults_m["Segunda"]["aulas"] == ["1ª", "2ª"]

    defaults_m34 = _defaults_grade_horarios("Quarta", "09h - 10h45 - 3ª e 4ª aula")
    assert defaults_m34["Quarta"]["turno"] == "CDP - Manhã"
    assert defaults_m34["Quarta"]["aulas"] == ["3ª", "4ª"]

    # Tarde
    defaults_t = _defaults_grade_horarios("Terça", "15h30 - 4ª aula")
    assert defaults_t["Terça"]["turno"] == "CDP - Tarde"
    assert defaults_t["Terça"]["aulas"] == ["4ª"]

    defaults_t45 = _defaults_grade_horarios("Quinta", "15h30 - 17h - 4ª e 5ª aula")
    assert defaults_t45["Quinta"]["turno"] == "CDP - Tarde"
    assert defaults_t45["Quinta"]["aulas"] == ["4ª", "5ª"]


def test_sugestao_horarios_cdp():
    assert _sugerir_horario_cadastrado("07h30 - 1ª aula") == ("07h30", "1ª aula")
    assert _sugerir_horario_cadastrado("08h15 - 2ª aula") == ("08h15", "2ª aula")
    assert _sugerir_horario_cadastrado("13h45 - 2ª aula") == ("13h45", "2ª aula")
    assert _sugerir_horario_cadastrado("15h30 - 4ª aula") == ("15h30", "4ª aula")
    assert _sugerir_horario_cadastrado("16h15 - 5ª aula") == ("16h15", "5ª aula")


def test_quantidade_aulas_por_horario_cdp():
    assert _quantidade_aulas_por_horario("07h30 - 1ª aula") == 1
    assert _quantidade_aulas_por_horario("07h30 - 09h - 1ª e 2ª aula") == 2
    assert _quantidade_aulas_por_horario("08h15 - 09h45 - 2ª e 3ª aula") == 2
    assert _quantidade_aulas_por_horario("09h - 10h45 - 3ª e 4ª aula") == 2
    assert _quantidade_aulas_por_horario("10h - 11h30 - 4ª e 5ª aula") == 2
    assert _quantidade_aulas_por_horario("07h30 - 09h45 - 1ª, 2ª e 3ª aula") == 3
    assert _quantidade_aulas_por_horario("07h30 - 11h30 - 1ª a 5ª aula") == 5

    assert _quantidade_aulas_por_horario("13h - 14h30 - 1ª e 2ª aula") == 2
    assert _quantidade_aulas_por_horario("13h45 - 15h15 - 2ª e 3ª aula") == 2
    assert _quantidade_aulas_por_horario("14h30 - 16h15 - 3ª e 4ª aula") == 2
    assert _quantidade_aulas_por_horario("15h30 - 17h - 4ª e 5ª aula") == 2
    assert _quantidade_aulas_por_horario("13h - 15h15 - 1ª, 2ª e 3ª aula") == 3
    assert _quantidade_aulas_por_horario("13h - 17h - 1ª a 5ª aula") == 5


def test_formatacao_modelo_docx_cdp():
    assert _formatar_horario_modelo("07h30 - 09h") == "7h30 – 9h"
    assert _formatar_horario_modelo("08h15 - 09h45") == "8h15 – 9h45"
    assert _formatar_horario_modelo("13h45 - 15h15") == "13h45 – 15h15"
    assert _formatar_horario_modelo("15h30 - 17h") == "15h30 – 17h"


def test_ordenacao_cronologica_cdp():
    # 07h30 deve vir antes de 08h15
    idx_1 = _indice_horario(("07h30", "1ª aula"))
    idx_2 = _indice_horario(("08h15", "2ª aula"))
    assert idx_1 < idx_2

    # 13h deve vir antes de 13h45
    idx_t1 = _indice_horario(("13h", "1ª aula"))
    idx_t2 = _indice_horario(("13h45", "2ª aula"))
    assert idx_t1 < idx_t2
