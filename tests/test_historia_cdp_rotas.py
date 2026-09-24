from pathlib import Path
from core.helpers import resolver_pasta_pdfs, resolver_raiz_disciplina_pdfs
from core.disciplinas import nomes_disciplinas


DISC_PADRAO = "HISTÓRIA - CDP - EJA - MULTISSERIADO"


def test_historia_cdp_disciplinas_cadastradas():
    disciplinas = nomes_disciplinas()
    assert DISC_PADRAO in disciplinas


def test_historia_cdp_4_bimestre_resolucao(tmp_path):
    raiz_falsa = tmp_path / "PDF_AULAS"
    pasta_hist_cdp_4b = raiz_falsa / "HISTORIA_CDP" / "EM" / "4_BIMESTRE" / "1_ANO_2_ANO_3_ANO"
    pasta_hist_cdp_4b.mkdir(parents=True)
    (pasta_hist_cdp_4b / "AULA_01.pdf").write_bytes(b"%PDF-1.4 test")

    pasta_hist_cdp_4b_ef_8_9 = raiz_falsa / "HISTORIA_CDP" / "EF" / "4_BIMESTRE" / "8_E_9_ANO_MULTISSERIADO"
    pasta_hist_cdp_4b_ef_8_9.mkdir(parents=True)
    (pasta_hist_cdp_4b_ef_8_9 / "AULA_01.pdf").write_bytes(b"%PDF-1.4 test")

    pasta_hist_cdp_4b_ef_6_7 = raiz_falsa / "HISTORIA_CDP" / "EF" / "4_BIMESTRE" / "6_E_7_ANO_MULTISSERIADO"
    pasta_hist_cdp_4b_ef_6_7.mkdir(parents=True)
    (pasta_hist_cdp_4b_ef_6_7 / "AULA_01.pdf").write_bytes(b"%PDF-1.4 test")

    pasta_hist_regular_4b_1ano = raiz_falsa / "HISTORIA" / "EM" / "4_BIMESTRE" / "1_ANO"
    pasta_hist_regular_4b_1ano.mkdir(parents=True)
    (pasta_hist_regular_4b_1ano / "AULA_01.pdf").write_bytes(b"%PDF-1.4 test")

    # 1. EM - Turmas E e J
    res1 = resolver_pasta_pdfs(
        base_dir=str(raiz_falsa),
        disciplina=DISC_PADRAO,
        turma="E",
        bimestre="4º Bimestre",
    )
    assert res1 == pasta_hist_cdp_4b

    # 2. EF 8/9 - Turma H
    res_ef_h = resolver_pasta_pdfs(
        base_dir=str(raiz_falsa),
        disciplina=DISC_PADRAO,
        turma="H",
        bimestre="4º Bimestre",
    )
    assert res_ef_h == pasta_hist_cdp_4b_ef_8_9 or res_ef_h == pasta_hist_cdp_4b_ef_6_7

    # 3. EF 6/7 - Turma C
    res_ef_c = resolver_pasta_pdfs(
        base_dir=str(raiz_falsa),
        disciplina=DISC_PADRAO,
        turma="C",
        bimestre="4º Bimestre",
    )
    assert res_ef_c == pasta_hist_cdp_4b_ef_6_7

    # 4. Regular
    res_regular = resolver_pasta_pdfs(
        base_dir=str(raiz_falsa),
        disciplina="HISTORIA",
        turma="1º ANO A",
        bimestre="4º Bimestre",
    )
    assert res_regular == pasta_hist_regular_4b_1ano
