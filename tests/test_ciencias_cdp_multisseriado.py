from pathlib import Path
from core.disciplinas import nomes_disciplinas, obter_config, eh_cdp_contextual, TURMAS_CDP
from core.lib.classificador import perfil_disciplina
from core.helpers import resolver_pasta_pdfs
from config import PDF_AULAS_DIR


DISC_PADRAO = "CIÊNCIAS - CDP - EJA - MULTISSERIADO"


def test_disciplinas_ciencias_cdp_multisseriado_no_catalogo():
    nomes = nomes_disciplinas()
    assert DISC_PADRAO in nomes


def test_config_e_perfil_ciencias_cdp_multisseriado():
    cfg = obter_config(DISC_PADRAO)
    assert cfg.habilitado is True
    assert cfg.exige_pdf is True
    assert eh_cdp_contextual(DISC_PADRAO) is True
    assert perfil_disciplina(DISC_PADRAO) == "ciencias_ef"


def test_resolucao_pastas_4_bimestre_ciencias_cdp():
    # Turma C (6º/7º ano) resolve para 6_E_7_ANO
    pasta_c = resolver_pasta_pdfs(PDF_AULAS_DIR, DISC_PADRAO, "C", "4º Bimestre")
    assert pasta_c.name == "6_E_7_ANO"
    assert "4_BIMESTRE" in str(pasta_c)
    assert "CIENCIAS_CDP" in str(pasta_c)
    assert pasta_c.exists()

    # Turma H (8º/9º ano) resolve para 8_E_9_ANO
    pasta_h = resolver_pasta_pdfs(PDF_AULAS_DIR, DISC_PADRAO, "H", "4º Bimestre")
    assert pasta_h.name == "8_E_9_ANO"
    assert "4_BIMESTRE" in str(pasta_h)
    assert "CIENCIAS_CDP" in str(pasta_h)
    assert pasta_h.exists()

    # Turmas J e E no EF também resolvem para 8_E_9_ANO
    pasta_j = resolver_pasta_pdfs(PDF_AULAS_DIR, DISC_PADRAO, "J", "4º Bimestre")
    pasta_e = resolver_pasta_pdfs(PDF_AULAS_DIR, DISC_PADRAO, "E", "4º Bimestre")

    assert pasta_j.name == "8_E_9_ANO"
    assert pasta_j.exists()
    assert pasta_e.name == "8_E_9_ANO"
    assert pasta_e.exists()
