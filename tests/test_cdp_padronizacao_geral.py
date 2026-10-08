from pathlib import Path
import pytest
from config import PDF_AULAS_DIR
from core.disciplinas import (
    nomes_disciplinas,
    TURMAS_CDP,
    DISCIPLINAS_CDP_PADRONIZADAS,
    componentes_curriculares_por_disciplina,
    obter_config,
    eh_cdp_contextual,
)
from core.helpers import resolver_pasta_pdfs


def test_catalogo_e_configuracoes_cdp_padronizado():
    disciplinas = nomes_disciplinas()
    assert TURMAS_CDP == ["C", "H", "J", "E"]

    for disc in DISCIPLINAS_CDP_PADRONIZADAS:
        assert disc in disciplinas
        assert eh_cdp_contextual(disc) is True
        assert obter_config(disc).exige_pdf is True
        comp = componentes_curriculares_por_disciplina(disc)
        assert disc in comp


def test_resolucao_pastas_todas_disciplinas_cdp_reais():
    base_dir = PDF_AULAS_DIR
    bimestre = "4º Bimestre"

    # 1. HISTÓRIA
    disc_hist = "HISTÓRIA - CDP - EJA - MULTISSERIADO"
    pasta_hist_e = resolver_pasta_pdfs(base_dir, disc_hist, "E", bimestre)
    assert pasta_hist_e.exists()
    assert "HISTORIA_CDP" in str(pasta_hist_e)
    assert "4_BIMESTRE" in str(pasta_hist_e)

    pasta_hist_c = resolver_pasta_pdfs(base_dir, disc_hist, "C", bimestre)
    assert pasta_hist_c.exists()
    assert "HISTORIA_CDP" in str(pasta_hist_c)
    assert "6_E_7_ANO" in str(pasta_hist_c)

    pasta_hist_h = resolver_pasta_pdfs(base_dir, disc_hist, "H", bimestre)
    assert pasta_hist_h.exists()
    assert "HISTORIA_CDP" in str(pasta_hist_h)

    # 2. CIÊNCIAS
    disc_cie = "CIÊNCIAS - CDP - EJA - MULTISSERIADO"
    pasta_cie_c = resolver_pasta_pdfs(base_dir, disc_cie, "C", bimestre)
    assert pasta_cie_c.exists()
    assert "CIENCIAS_CDP" in str(pasta_cie_c)
    assert "6_E_7_ANO" in str(pasta_cie_c)

    pasta_cie_j = resolver_pasta_pdfs(base_dir, disc_cie, "J", bimestre)
    assert pasta_cie_j.exists()
    assert "CIENCIAS_CDP" in str(pasta_cie_j)
    assert "8_E_9_ANO" in str(pasta_cie_j)

    # 3. MATEMÁTICA
    disc_mat = "MATEMÁTICA - CDP - EJA - MULTISSERIADO"
    pasta_mat_j = resolver_pasta_pdfs(base_dir, disc_mat, "J", bimestre)
    assert pasta_mat_j.exists()
    assert "MATEMATICA-CDP" in str(pasta_mat_j)
    assert "1_2_E_3_ANO_MULTISSERIADO" in str(pasta_mat_j)

    pasta_mat_c = resolver_pasta_pdfs(base_dir, disc_mat, "C", bimestre)
    assert pasta_mat_c.exists()
    assert "MATEMATICA-CDP" in str(pasta_mat_c)
    assert "6_E_7_ANO" in str(pasta_mat_c)

    # 4. GEOGRAFIA
    disc_geo = "GEOGRAFIA - CDP - EJA - MULTISSERIADO"
    pasta_geo_j = resolver_pasta_pdfs(base_dir, disc_geo, "J", bimestre)
    assert pasta_geo_j.exists()
    assert "GEOGRAFIA_CDP" in str(pasta_geo_j)
    assert "4_BIMESTRE" in str(pasta_geo_j)

    pasta_geo_e = resolver_pasta_pdfs(base_dir, disc_geo, "E", bimestre)
    assert pasta_geo_e.exists()
    assert "GEOGRAFIA_CDP" in str(pasta_geo_e)
    assert "4_BIMESTRE" in str(pasta_geo_e)

    # 5. SOCIOLOGIA
    disc_soc = "SOCIOLOGIA - CDP - EJA - MULTISSERIADO"
    pasta_soc_j = resolver_pasta_pdfs(base_dir, disc_soc, "J", bimestre)
    assert pasta_soc_j.exists()
    assert "SOCIOLOGIA_CDP" in str(pasta_soc_j)
    assert "4_BIMESTRE" in str(pasta_soc_j)

    pasta_soc_e = resolver_pasta_pdfs(base_dir, disc_soc, "E", bimestre)
    assert pasta_soc_e.exists()
    assert "SOCIOLOGIA_CDP" in str(pasta_soc_e)
    assert "4_BIMESTRE" in str(pasta_soc_e)

    # 6. LIDERANÇA E ORATÓRIA
    disc_lid = "LIDERANÇA E ORATÓRIA - CDP - EJA - MULTISSERIADO"
    pasta_lid_j = resolver_pasta_pdfs(base_dir, disc_lid, "J", bimestre)
    assert pasta_lid_j.exists()
    assert "LIDERANCA" in str(pasta_lid_j).upper()
    assert "4_BIMESTRE" in str(pasta_lid_j)
