from pathlib import Path
from core.helpers import resolver_pasta_pdfs, resolver_raiz_disciplina_pdfs
from core.disciplinas import nomes_disciplinas, TURMAS_CDP, TURMAS_CDP_MULTISSERIADA


DISC_PADRAO = "SOCIOLOGIA - CDP - EJA - MULTISSERIADO"


def test_sociologia_cdp_multisseriado_disciplina_e_turmas_cadastradas():
    disciplinas = nomes_disciplinas()
    assert DISC_PADRAO in disciplinas
    for t in ["C", "H", "J", "E"]:
        assert t in TURMAS_CDP
        assert t in TURMAS_CDP_MULTISSERIADA


def test_sociologia_cdp_multisseriado_raiz_resolvida(tmp_path):
    raiz_falsa = tmp_path / "PDF_AULAS"
    pasta_soc = raiz_falsa / "SOCIOLOGIA_CDP_MULTISSERIADO"
    pasta_soc.mkdir(parents=True)

    resolvida = resolver_raiz_disciplina_pdfs(raiz_falsa, DISC_PADRAO)
    assert resolvida == pasta_soc


def test_sociologia_cdp_multisseriado_4_bimestre_turmas(tmp_path):
    raiz_falsa = tmp_path / "PDF_AULAS"
    pasta_4b = raiz_falsa / "SOCIOLOGIA_CDP_MULTISSERIADO" / "EM" / "4_BIMESTRE"
    pasta_4b.mkdir(parents=True)
    (pasta_4b / "AULA_01.pdf").write_bytes(b"%PDF-1.4 test")

    pasta_3b = raiz_falsa / "SOCIOLOGIA_CDP_MULTISSERIADO" / "EM" / "3_BIMESTRE" / "1_ANO_2_ANO_3_ANO"
    pasta_3b.mkdir(parents=True)
    (pasta_3b / "AULA_08.pdf").write_bytes(b"%PDF-1.4 test")

    turmas_teste = [
        "J",
        "E",
    ]

    for turma in turmas_teste:
        resultado = resolver_pasta_pdfs(
            base_dir=str(raiz_falsa),
            disciplina=DISC_PADRAO,
            turma=turma,
            bimestre="4º Bimestre",
        )
        assert resultado == pasta_4b, f"Falha para turma {turma}: esperado {pasta_4b}, obtido {resultado}"
