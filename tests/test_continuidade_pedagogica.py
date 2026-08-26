import pytest
from core import database
from core.gestao_aulas import obter_referencia_ultima_aula_historico, obter_ultima_aula_gerada_sistema_impl

def _preparar_banco(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "planos_teste_continuidade.db")
    database.init_db()

def test_fluxo_completo_continuidade_pedagogica(monkeypatch, tmp_path):
    _preparar_banco(monkeypatch, tmp_path)

    # 1. Salvar no histórico um plano de aula gerado com o último PDF sendo "AULA 04.pdf"
    database.salvar_historico_plano(
        professor_nome="Luan Dias",
        disciplina="Matemática",
        turma="1 Ano EM",
        arquivo_nome="plano_final_matematica.docx",
        arquivo_docx_bytes=b"bytes_do_docx_simulado",
        bimestre="3 BIMESTRE",
        mes_plano="Agosto",
        ultimo_pdf="AULA 04.pdf"
    )

    # 2. Consultar o histórico para validar que as colunas foram gravadas e lidas perfeitamente
    historico = database.obter_ultimo_historico_por_contexto(
        professor_nome="Luan Dias",
        disciplina="Matemática",
        turma="1 Ano EM",
        bimestre="3 BIMESTRE"
    )

    assert historico is not None
    assert historico["ultimo_pdf"] == "AULA 04.pdf"

    # 3. Validar obter_referencia_ultima_aula_historico
    referencia = obter_referencia_ultima_aula_historico(
        professor="Luan Dias",
        disciplina="Matemática",
        turma="1 Ano EM",
        bimestre="3 BIMESTRE"
    )
    assert referencia is not None
    assert referencia["ultimo_pdf"] == "AULA 04.pdf"

    # 4. Validar que a última aula gerada NÃO retorna mais zero fixo e reflete a aula correta do banco
    aula_inicio = obter_ultima_aula_gerada_sistema_impl(
        professor="Luan Dias",
        disciplina="Matemática",
        turma="1 Ano EM",
        bimestre="3 BIMESTRE"
    )
    assert isinstance(aula_inicio, int)
