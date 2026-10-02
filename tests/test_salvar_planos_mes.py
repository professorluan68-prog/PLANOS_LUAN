import io
from pathlib import Path
from planos_luan_app import (
    _resolver_caminho_professor_disciplina,
    _salvar_planos_na_pasta_finalizados,
)


def test_resolver_caminho_cria_subpasta_do_mes(monkeypatch, tmp_path):
    monkeypatch.setattr("planos_luan_app.PLANOS_FEITOS_DIR", tmp_path / "Planos_feitos")
    
    caminho_setembro = _resolver_caminho_professor_disciplina("Adriana Alda", "Educacao Financeira", mes="SETEMBRO")
    caminho_novembro = _resolver_caminho_professor_disciplina("Adriana Alda", "Educacao Financeira", mes="NOVEMBRO")
    
    assert caminho_setembro.name == "SETEMBRO"
    assert caminho_novembro.name == "NOVEMBRO"
    assert caminho_setembro.parent == caminho_novembro.parent
    assert caminho_setembro.exists()
    assert caminho_novembro.exists()


def test_salvar_planos_meses_diferentes_nao_se_substituem(monkeypatch, tmp_path):
    monkeypatch.setattr("planos_luan_app.PLANOS_FEITOS_DIR", tmp_path / "Planos_feitos")
    
    # 1. Gera plano de setembro
    plano_set = [{
        "turma": "7o ANO B",
        "docx_bytes": io.BytesIO(b"conteudo de setembro"),
        "ia_usada": False,
    }]
    salvos_set = _salvar_planos_na_pasta_finalizados(plano_set, "Educacao Financeira", "Adriana Alda", mes="SETEMBRO")
    
    # 2. Gera plano de novembro para a mesma turma e disciplina
    plano_nov = [{
        "turma": "7o ANO B",
        "docx_bytes": io.BytesIO(b"conteudo de novembro"),
        "ia_usada": False,
    }]
    salvos_nov = _salvar_planos_na_pasta_finalizados(plano_nov, "Educacao Financeira", "Adriana Alda", mes="NOVEMBRO")
    
    arq_set = Path(salvos_set[0])
    arq_nov = Path(salvos_nov[0])
    
    # Verifica que estao em pastas de meses diferentes
    assert arq_set.parent.name == "SETEMBRO"
    assert arq_nov.parent.name == "NOVEMBRO"
    
    # Verifica que ambos existem e possuem seus respectivos conteudos preservados
    assert arq_set.exists()
    assert arq_nov.exists()
    assert arq_set.read_bytes() == b"conteudo de setembro"
    assert arq_nov.read_bytes() == b"conteudo de novembro"
