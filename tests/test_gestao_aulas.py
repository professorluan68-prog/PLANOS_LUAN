from core import database, gestao_aulas


def test_obter_ultima_aula_gerada_sistema_impl_reinicia_da_primeira_aula(monkeypatch):
    monkeypatch.setattr(database, "obter_ultimo_plano_docx", lambda *args, **kwargs: b"docx_antigo")
    monkeypatch.setattr(gestao_aulas, "detectar_ultima_aula_de_docx_bytes", lambda *args, **kwargs: 9)
    monkeypatch.setattr(gestao_aulas, "obter_aula_parada_do_json", lambda *args, **kwargs: 7)

    ultima_aula = gestao_aulas.obter_ultima_aula_gerada_sistema_impl(
        "ANA",
        "Ciências",
        "6 ANO A",
        "3º BIMESTRE",
    )

    assert ultima_aula == 0
