import pytest
from ui.shared import _montar_horario_flexivel, _sugerir_horario_cadastrado, _padroes_horario_config, _defaults_grade_horarios

def test_montar_horario_flexivel_consecutivos():
    # Consecutivos no turno Tarde: 1ª e 2ª aula -> "13h - 14h40"
    horario = _montar_horario_flexivel("Tarde", ["1a", "2a"])
    assert horario is not None
    assert horario[0] == "13h - 14h40"

def test_montar_horario_flexivel_nao_consecutivos():
    # Não consecutivos no turno Tarde: 2ª e 5ª aula
    # slots de Tarde = ["13h", "13h50", "14h40", "15h50", "16h40", "17h30", "18h20", "19h10", "20h00", "20h50"]
    # 2ª aula = "13h50 - 14h40"
    # 5ª aula = "16h40 - 17h30"
    horario = _montar_horario_flexivel("Tarde", ["2a", "5a"])
    assert horario is not None
    assert horario[0] == "13h50 - 14h40 | 16h40 - 17h30"

def test_sugerir_horario_cadastrado_desmembrado():
    # Deve sugerir uma lista de horários desmembrados para o caso legando da Adriana Carvalho
    sugestao = _sugerir_horario_cadastrado("10h40 - 14h00 - 5º e 9º aula", "1º ANO B")
    assert isinstance(sugestao, list)
    assert len(sugestao) == 2
    assert sugestao[0][0] == "10h40"
    assert sugestao[1][0] == "14h00"

def test_padroes_horario_config_desmembrado():
    config = {
        "dia_semana": "Quinta",
        "horario": "10h40 - 14h00 - 5º e 9º aula",
        "aulas_semana": "2"
    }
    padroes = _padroes_horario_config(config, "1º ANO B")
    # Quinta-feira é dia 3. Deve gerar dois padrões para o dia 3.
    assert len(padroes) == 2
    assert padroes[0]["dia"] == 3
    assert padroes[0]["horario"][0] == "10h40"
    assert padroes[1]["dia"] == 3
    assert padroes[1]["horario"][0] == "14h00"

def test_defaults_grade_horarios_desmembrado():
    defaults = _defaults_grade_horarios("Quinta", "10h40 - 14h00 - 5º e 9º aula", "1º ANO B")
    quinta_def = defaults.get("Quinta")
    assert quinta_def is not None
    # Deve preencher as duas aulas
    assert "5ª" in quinta_def["aulas"]
    assert "9ª" in quinta_def["aulas"]
