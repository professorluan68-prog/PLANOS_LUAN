from pathlib import Path

from core.helpers import resolver_pasta_pdfs


def test_resolver_eja_usa_as_subpastas_da_modalidade(tmp_path: Path):
    base = tmp_path / "PDF_AULAS"
    (base / "BIOLOGIA" / "EJA_BIOLOGIA").mkdir(parents=True)
    (base / "LINGUA_INGLESA" / "EJA_EM").mkdir(parents=True)
    (base / "LIDERANCA_E_ORATORIA" / "EJA_EM").mkdir(parents=True)

    assert resolver_pasta_pdfs(
        str(base), "Biologia", "2 termo", "3 bimestre", modalidade_eja=True
    ) == base / "BIOLOGIA" / "EJA_BIOLOGIA"
    assert resolver_pasta_pdfs(
        str(base), "Lingua Inglesa", "1 termo", "3 bimestre", modalidade_eja=True
    ) == base / "LINGUA_INGLESA" / "EJA_EM"
    assert resolver_pasta_pdfs(
        str(base), "Lideranca e Oratoria", "2 ano", "3 bimestre", modalidade_eja=True
    ) == base / "LIDERANCA_E_ORATORIA" / "EJA_EM"


def test_resolver_regular_continua_na_pasta_regular(tmp_path: Path):
    base = tmp_path / "PDF_AULAS"
    regular = base / "BIOLOGIA" / "EM" / "3_BIMESTRE" / "2_ANO"
    eja = base / "BIOLOGIA" / "EJA_BIOLOGIA"
    regular.mkdir(parents=True)
    eja.mkdir(parents=True)

    assert resolver_pasta_pdfs(str(base), "Biologia", "2 ano", "3 bimestre") == regular
