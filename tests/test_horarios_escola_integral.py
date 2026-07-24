from core.constantes import ESCOLA_PERSONALIZADA, ESCOLAS, HORARIOS_INTEGRAIS
from ui.shared import (
    _aulas_disponiveis_turno,
    _defaults_grade_horarios,
    _montar_horario_flexivel,
    _sugerir_horario_cadastrado,
    TURNO_HORARIO_PERSONALIZADO,
)


TURNO_INTEGRAL = "Integral - José Theodoro"


def test_nova_escola_e_horarios_integrais_estao_disponiveis():
    assert "E.E. JOSÉ THEODORO DE MORAES" in ESCOLAS
    assert ESCOLA_PERSONALIZADA == "Outra escola (digitar)"
    assert _aulas_disponiveis_turno(TURNO_INTEGRAL) == list(range(3, 10))
    assert HORARIOS_INTEGRAIS[:7] == [
        ("08h40 - 09h30", "3ª aula"),
        ("09h45 - 10h35", "4ª aula"),
        ("10h35 - 11h25", "5ª aula"),
        ("12h25 - 13h15", "6ª aula"),
        ("13h15 - 14h05", "7ª aula"),
        ("14h20 - 15h10", "8ª aula"),
        ("15h10 - 16h", "9ª aula"),
    ]


def test_grade_integral_monta_aulas_simples_e_duplas_com_intervalo_completo():
    assert _montar_horario_flexivel(TURNO_INTEGRAL, ["6ª"]) == (
        "12h25 - 13h15",
        "6ª aula",
    )
    assert _montar_horario_flexivel(TURNO_INTEGRAL, ["6ª", "7ª"]) == (
        "12h25 - 14h05",
        "6ª e 7ª aula",
    )
    assert _montar_horario_flexivel(TURNO_INTEGRAL, ["8ª", "9ª"]) == (
        "14h20 - 16h",
        "8ª e 9ª aula",
    )


def test_horario_escrito_como_no_plano_e_reconhecido_como_integral():
    horario = _sugerir_horario_cadastrado(
        "6ª e 7ª aulas | 12:25 a 13:15 HS | 13:15 a 14:05 HS"
    )
    assert horario == ("12h25 - 14h05", "6ª e 7ª aula")

    defaults = _defaults_grade_horarios(
        "Quarta",
        "12h25 - 14h05 - 6ª e 7ª aula",
    )
    assert defaults["Quarta"] == {
        "turno": TURNO_INTEGRAL,
        "aulas": ["6ª", "7ª"],
    }


def test_horario_antigo_da_terceira_aula_continua_no_turno_da_manha():
    horario = _sugerir_horario_cadastrado("08h40 - 3ª aula")
    assert horario == ("08h40", "3ª aula")

    defaults = _defaults_grade_horarios("Segunda", "08h40 - 3ª aula")
    assert defaults["Segunda"] == {
        "turno": "Manhã",
        "aulas": ["3ª"],
    }


def test_horario_personalizado_pode_ser_salvo_reaberto_e_removido():
    horario = _sugerir_horario_cadastrado(
        "Personalizado: 6ª aula - 12:30 a 13:20"
    )
    assert horario == (
        "6ª aula - 12:30 a 13:20",
        "Horário personalizado",
    )

    defaults = _defaults_grade_horarios(
        "Quarta",
        "Personalizado: 6ª aula - 12:30 a 13:20",
    )
    assert defaults["Quarta"] == {
        "turno": TURNO_HORARIO_PERSONALIZADO,
        "aulas": ["6ª"],
        "horario_personalizado": "6ª aula - 12:30 a 13:20",
    }

    assert _sugerir_horario_cadastrado("Personalizado:") is None
