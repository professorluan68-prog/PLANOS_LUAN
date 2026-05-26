from core.disciplinas import (
    BIMESTRES,
    TURMAS_CDP,
    eh_cdp,
    eh_cdp_contextual,
    eh_cdp_fundamental,
    nomes_disciplinas,
    obter_config,
)


def test_cdp_nao_exige_pdf():
    config = obter_config("CDP- Multisseriada")

    assert eh_cdp("CDP- Multisseriada")
    assert config.exige_pdf is False


def test_cdp_fundamental_nao_exige_pdf():
    config = obter_config("CDP - Ciclo I")

    assert eh_cdp("CDP - Ciclo I")
    assert eh_cdp_fundamental("CDP - Ciclo I")
    assert config.exige_pdf is False


def test_cdp_ensino_fundamental_em_planos_gerais_usa_pdf():
    config = obter_config("CDP-ENSINO FUNDAMENTAL")

    assert not eh_cdp("CDP-ENSINO FUNDAMENTAL")
    assert eh_cdp_contextual("CDP-ENSINO FUNDAMENTAL")
    assert config.exige_pdf is True


def test_cdp_ensino_medio_em_planos_gerais_usa_pdf():
    config = obter_config("CDP-ENSINO MÉDIO")

    assert not eh_cdp("CDP-ENSINO MÉDIO")
    assert eh_cdp_contextual("CDP-ENSINO MÉDIO")
    assert config.exige_pdf is True


def test_lista_disciplinas_tem_opcoes_principais():
    nomes = nomes_disciplinas()

    assert "Arte" in nomes
    assert "Biologia" in nomes
    assert "Projeto de Vida" in nomes
    assert "Tecnologia e Inovação" in nomes
    assert "CDP- Multisseriada" in nomes
    assert "CDP-ENSINO FUNDAMENTAL" in nomes
    assert "CDP-ENSINO MÉDIO" in nomes
    assert "Outra" in nomes


def test_opcoes_cabecalho_e_cdp():
    assert len(BIMESTRES) == 4
    assert TURMAS_CDP[0].startswith("MULTISSERIADO 1")
    assert TURMAS_CDP[1].startswith("MULTISSERIADO 4")
    assert any("6" in turma and "7" in turma and "E.F" in turma for turma in TURMAS_CDP)
    assert any("8" in turma and "9" in turma and "E.F" in turma for turma in TURMAS_CDP)
    assert any("1" in turma and "2" in turma and "3" in turma and "E.M" in turma for turma in TURMAS_CDP)
