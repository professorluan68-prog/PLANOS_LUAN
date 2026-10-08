# -*- coding: utf-8 -*-
from pathlib import Path
import pytest
from config import PDF_AULAS_DIR
from core.disciplinas import (
    nomes_disciplinas,
    TURMAS_CDP,
    componentes_curriculares_por_disciplina,
    obter_config,
    MODO_PDF,
)
from core.helpers import resolver_pasta_pdfs


DISC_PADRAO = "MATEMÁTICA - CDP - EJA - MULTISSERIADO"


def test_catalogo_matematica_cdp():
    disciplinas = nomes_disciplinas()
    assert DISC_PADRAO in disciplinas

    for t in ["C", "H", "J", "E"]:
        assert t in TURMAS_CDP

    componentes = componentes_curriculares_por_disciplina(DISC_PADRAO)
    assert DISC_PADRAO in componentes

    cfg = obter_config(DISC_PADRAO)
    assert cfg.modo == MODO_PDF
    assert cfg.exige_pdf is True


def test_resolver_pasta_pdfs_matematica_cdp_disco_real():
    pasta_em_esperada = Path(PDF_AULAS_DIR) / "MATEMATICA-CDP" / "EM" / "4_BIMESTRE" / "1_2_E_3_ANO_MULTISSERIADO"
    
    # Com a disciplina padronizada e turma J
    pasta_j = resolver_pasta_pdfs(
        PDF_AULAS_DIR,
        DISC_PADRAO,
        "J",
        "4º Bimestre",
    )
    assert pasta_j == pasta_em_esperada

    # Com turma E
    pasta_e = resolver_pasta_pdfs(
        PDF_AULAS_DIR,
        DISC_PADRAO,
        "E",
        "4º Bimestre",
    )
    assert pasta_e == pasta_em_esperada

    # Com turma C (EF 6/7)
    pasta_c = resolver_pasta_pdfs(
        PDF_AULAS_DIR,
        DISC_PADRAO,
        "C",
        "4º Bimestre",
    )
    pasta_c_esperada = Path(PDF_AULAS_DIR) / "MATEMATICA-CDP" / "AF" / "4_BIMESTRE" / "6_E_7_ANO"
    assert pasta_c == pasta_c_esperada

    # Com turma H (EF 8/9)
    pasta_h = resolver_pasta_pdfs(
        PDF_AULAS_DIR,
        DISC_PADRAO,
        "H",
        "4º Bimestre",
    )
    pasta_h_esperada = Path(PDF_AULAS_DIR) / "MATEMATICA-CDP" / "AF" / "4_BIMESTRE" / "8_E_9_ANO"
    assert pasta_h == pasta_h_esperada
