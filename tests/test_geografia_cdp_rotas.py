from pathlib import Path
from core.helpers import resolver_pasta_pdfs, resolver_raiz_disciplina_pdfs
from core.disciplinas import nomes_disciplinas


DISC_PADRAO = "GEOGRAFIA - CDP - EJA - MULTISSERIADO"


def test_geografia_cdp_disciplinas_cadastradas():
    disciplinas = nomes_disciplinas()
    assert DISC_PADRAO in disciplinas


def test_geografia_cdp_4_bimestre_resolucao(tmp_path):
    raiz_falsa = tmp_path / "PDF_AULAS"
    pasta_geo_cdp_4b = raiz_falsa / "GEOGRAFIA_CDP" / "EM" / "4_BIMESTRE"
    pasta_geo_cdp_4b.mkdir(parents=True)
    (pasta_geo_cdp_4b / "AULA_02.pdf").write_bytes(b"%PDF-1.4 test")

    pasta_geo_regular_4b_1ano = raiz_falsa / "GEOGRAFIA" / "EM" / "4_BIMESTRE" / "1_ANO"
    pasta_geo_regular_4b_1ano.mkdir(parents=True)
    (pasta_geo_regular_4b_1ano / "AULA_01.pdf").write_bytes(b"%PDF-1.4 test")

    # 1. Disciplina padronizada GEOGRAFIA - CDP - EJA - MULTISSERIADO + Turma J
    res1 = resolver_pasta_pdfs(
        base_dir=str(raiz_falsa),
        disciplina=DISC_PADRAO,
        turma="J",
        bimestre="4º Bimestre",
    )
    assert res1 == pasta_geo_cdp_4b

    # 2. Disciplina padronizada + Turma E
    res2 = resolver_pasta_pdfs(
        base_dir=str(raiz_falsa),
        disciplina=DISC_PADRAO,
        turma="E",
        bimestre="4º Bimestre",
    )
    assert res2 == pasta_geo_cdp_4b

    # 3. Geografia regular continua indo para a pasta regular
    res_regular = resolver_pasta_pdfs(
        base_dir=str(raiz_falsa),
        disciplina="GEOGRAFIA",
        turma="1º ANO A",
        bimestre="4º Bimestre",
    )
    assert res_regular == pasta_geo_regular_4b_1ano
