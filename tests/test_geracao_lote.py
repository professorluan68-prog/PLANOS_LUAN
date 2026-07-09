from ui.geracao_lote import (
    _nome_arquivo_plano_lote,
    _proxima_aula_cdp_lote,
    _quantidade_aulas_lote_regular,
)


def test_quantidade_aulas_lote_regular_limita_pasta_parcial():
    assert _quantidade_aulas_lote_regular(total_datas=8, total_pdfs=3) == 3
    assert _quantidade_aulas_lote_regular(total_datas=0, total_pdfs=3) == 3


def test_quantidade_aulas_lote_regular_reutiliza_pdf_unico_em_orientacao():
    assert _quantidade_aulas_lote_regular(total_datas=6, total_pdfs=1, reutilizar_pdf_unico=True) == 6


def test_proxima_aula_cdp_lote_continua_do_historico():
    assert _proxima_aula_cdp_lote(0) == 1
    assert _proxima_aula_cdp_lote(4) == 5


def test_nome_arquivo_plano_lote_inclui_professor_e_mes():
    nome = _nome_arquivo_plano_lote(
        professor="Ana Maria",
        turma="7º ANO A",
        disciplina="Matemática",
        mes="JUNHO",
        ia_usada=True,
    )

    assert nome.endswith(".docx")
    assert "Ana_Maria" in nome
    assert "JUNHO" in nome
    assert "Plano_7o_ANO_A_Matematica_In" in nome
