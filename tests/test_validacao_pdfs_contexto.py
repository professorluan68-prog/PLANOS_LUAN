from pathlib import Path

from core import validacao_pdfs_contexto as validacao


def test_validar_pdf_contexto_sem_ia_aprova_pdf_coerente():
    resultado = validacao.validar_pdf_contexto_sem_ia(
        Path("AULA_001__POTENCIA_MEDIA__FISICA__EM__B3__1_ANO.pdf"),
        disciplina="Física",
        turma="1º ANO A",
        bimestre="3º Bimestre",
        texto_pdf="Física Potência média ou instantânea 3o bimestre Ensino Médio",
    )

    assert resultado.valido is True
    assert resultado.motivos == ()


def test_validar_pdf_contexto_sem_ia_bloqueia_outra_disciplina():
    resultado = validacao.validar_pdf_contexto_sem_ia(
        Path("AULA_002__REVOLUCAO_INDUSTRIAL__HISTORIA__EM__B3__1_ANO.pdf"),
        disciplina="Física",
        turma="1º ANO A",
        bimestre="3º Bimestre",
        texto_pdf="História Revolução Industrial 3o bimestre Ensino Médio",
    )

    assert resultado.valido is False
    assert "disciplina do PDF nao confere com o cadastro" in resultado.motivos


def test_validar_pdf_contexto_sem_ia_bloqueia_bimestre_errado():
    resultado = validacao.validar_pdf_contexto_sem_ia(
        Path("AULA_003__ENERGIA__FISICA__EM__B2__1_ANO.pdf"),
        disciplina="Física",
        turma="1º ANO A",
        bimestre="3º Bimestre",
        texto_pdf="Física Energia 2o bimestre Ensino Médio",
    )

    assert resultado.valido is False
    assert "bimestre do PDF nao confere com o selecionado" in resultado.motivos


def test_validar_pdf_contexto_sem_ia_nao_bloqueia_aula_valida_fora_do_mes():
    resultado = validacao.validar_pdf_contexto_sem_ia(
        Path("AULA_004__PARTICIPACAO_DA_POPULACAO_NEGRA__HISTORIA__EF_AF__B3__8_ANO.pdf"),
        disciplina="História",
        turma="8º ANO A",
        bimestre="3º Bimestre",
        texto_pdf="História 3o bimestre 8 ano Participação da população negra e indígena",
    )

    assert resultado.valido is True
    assert resultado.motivos == ()


def test_validar_pdf_contexto_sem_ia_bloqueia_titulo_fora_da_referencia(monkeypatch):
    monkeypatch.setattr(
        validacao,
        "referencia_docx_por_perfil",
        lambda *args, **kwargs: {"titulo": "Potência média ou instantânea", "habilidade": ""},
    )

    resultado = validacao.validar_pdf_contexto_sem_ia(
        Path("AULA_001__FISICA.pdf"),
        disciplina="Física",
        turma="",
        bimestre="",
        texto_pdf="Física Sistemas isolados",
    )

    assert resultado.valido is False
    assert "titulo da aula nao aparece no PDF" in resultado.motivos


def test_validar_lote_pdfs_contexto_sem_ia_separa_validos_e_suspeitos(monkeypatch):
    textos = {
        "AULA_001__FISICA__EM__B3__1_ANO.pdf": "Física 3o bimestre Ensino Médio",
        "AULA_002__HISTORIA__EM__B3__1_ANO.pdf": "História 3o bimestre Ensino Médio",
    }
    monkeypatch.setattr(
        validacao,
        "_extrair_amostra_texto_pdf",
        lambda caminho: textos.get(Path(caminho).name, ""),
    )

    resultado = validacao.validar_lote_pdfs_contexto_sem_ia(
        [Path(nome) for nome in textos],
        disciplina="Física",
        turma="1º ANO A",
        bimestre="3º Bimestre",
    )

    assert [item.caminho.name for item in resultado.validos] == [
        "AULA_001__FISICA__EM__B3__1_ANO.pdf"
    ]
    assert [item.caminho.name for item in resultado.suspeitos] == [
        "AULA_002__HISTORIA__EM__B3__1_ANO.pdf"
    ]
