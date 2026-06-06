from core.disciplinas import (
    BIMESTRES,
    DISCIPLINA_CDP_CICLO_I,
    DISCIPLINA_CDP_FUNDAMENTAL,
    DISCIPLINA_CDP_MEDIO,
    DISCIPLINA_CDP_MULTISSERIADA,
    TURMAS_CDP,
    eh_cdp,
    eh_cdp_contextual,
    eh_cdp_fundamental,
    nomes_disciplinas,
    obter_config,
)


def test_cdp_multisseriada_nao_exige_pdf():
    config = obter_config(DISCIPLINA_CDP_MULTISSERIADA)

    assert eh_cdp(DISCIPLINA_CDP_MULTISSERIADA)
    assert config.exige_pdf is False


def test_cdp_ciclo_i_nao_exige_pdf():
    config = obter_config(DISCIPLINA_CDP_CICLO_I)

    assert eh_cdp(DISCIPLINA_CDP_CICLO_I)
    assert eh_cdp_fundamental(DISCIPLINA_CDP_CICLO_I)
    assert config.exige_pdf is False


def test_cdp_contextual_continua_no_fluxo_pdf():
    config_fundamental = obter_config(DISCIPLINA_CDP_FUNDAMENTAL)
    config_medio = obter_config(DISCIPLINA_CDP_MEDIO)

    assert not eh_cdp(DISCIPLINA_CDP_FUNDAMENTAL)
    assert not eh_cdp(DISCIPLINA_CDP_MEDIO)
    assert eh_cdp_contextual(DISCIPLINA_CDP_FUNDAMENTAL)
    assert eh_cdp_contextual(DISCIPLINA_CDP_MEDIO)
    assert config_fundamental.exige_pdf is True
    assert config_medio.exige_pdf is True


def test_cdp_contextual_aceita_variacoes_simples_de_acentuacao():
    assert eh_cdp_contextual("CDP-ENSINO MEDIO")
    assert eh_cdp_contextual("  cdp-ensino medio  ")


def test_lista_disciplinas_tem_opcoes_principais():
    nomes = nomes_disciplinas()

    assert "Arte" in nomes
    assert "Biologia" in nomes
    assert "Projeto de Vida" in nomes
    assert "Tecnologia e Inovação" in nomes
    assert DISCIPLINA_CDP_MULTISSERIADA in nomes
    assert DISCIPLINA_CDP_FUNDAMENTAL in nomes
    assert DISCIPLINA_CDP_MEDIO in nomes
    assert "Outra" in nomes


def test_opcoes_cabecalho_e_cdp():
    assert len(BIMESTRES) == 4
    assert TURMAS_CDP[0].startswith("MULTISSERIADO 1")
    assert TURMAS_CDP[1].startswith("MULTISSERIADO 4")
    assert any("6" in turma and "7" in turma and "E.F" in turma for turma in TURMAS_CDP)
    assert any("8" in turma and "9" in turma and "E.F" in turma for turma in TURMAS_CDP)
    assert any("1" in turma and "2" in turma and "3" in turma and "E.M" in turma for turma in TURMAS_CDP)
