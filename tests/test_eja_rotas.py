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


def test_resolver_biologia_eja_1_termo_4_bimestre(tmp_path: Path):
    base = tmp_path / "PDF_AULAS"
    termo_1 = base / "BIOLOGIA_EJA" / "EM" / "4_BIMESTRE" / "1_TERMO"
    termo_1.mkdir(parents=True)
    (termo_1 / "AULA_01.pdf").write_bytes(b"%PDF-fake")

    # Testa com várias grafias comuns de 1º Termo (com e sem espaço)
    for turma in ["1ºTermo", "1º Termo", "1_TERMO", "1 Termo"]:
        assert resolver_pasta_pdfs(
            str(base), "Biologia_EJA", turma, "4º Bimestre", modalidade_eja=True
        ) == termo_1
        assert resolver_pasta_pdfs(
            str(base), "Biologia", turma, "4º Bimestre", modalidade_eja=True
        ) == termo_1


def test_resolver_lingua_inglesa_eja_1_e_2_termo_4_bimestre(tmp_path: Path):
    base = tmp_path / "PDF_AULAS"
    termo_1 = base / "LINGUA_INGLESA_EJA" / "EM" / "4_BIMESTRE" / "1_TERMO"
    termo_2 = base / "LINGUA_INGLESA_EJA" / "EM" / "4_BIMESTRE" / "2_TERMO"
    termo_1.mkdir(parents=True)
    termo_2.mkdir(parents=True)
    (termo_1 / "AULA_01.pdf").write_bytes(b"%PDF-fake")
    (termo_2 / "AULA_01.pdf").write_bytes(b"%PDF-fake")

    for disc in ["Língua Inglesa", "Língua Inglesa EJA", "Inglês", "Inglês EJA"]:
        for turma in ["1ºTermo", "1º Termo", "1_TERMO", "1 Termo"]:
            assert resolver_pasta_pdfs(
                str(base), disc, turma, "4º Bimestre", modalidade_eja=True
            ) == termo_1
        for turma in ["2ºTermo", "2º Termo", "2_TERMO", "2 Termo"]:
            assert resolver_pasta_pdfs(
                str(base), disc, turma, "4º Bimestre", modalidade_eja=True
            ) == termo_2


