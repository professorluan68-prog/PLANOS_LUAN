from core import database as db


def _plano(pid, disciplina, turma, caminho):
    return {
        "id": pid,
        "professor_nome": "Prof Teste",
        "disciplina": disciplina,
        "turma": turma,
        "bimestre": "",
        "data_geracao": "2026-10-01 10:00:00",
        "arquivo_nome": f"plano{pid}.docx",
        "arquivo_path": caminho,
        "mes_plano": "2026-10",
    }


def test_conferencia_mensal_exige_docx_e_agrupa_horarios(monkeypatch, tmp_path):
    existente = tmp_path / "ok.docx"
    existente.write_bytes(b"x")

    vinculos = [
        {"professor": "Prof Teste", "disciplina": "Biologia", "turma": "1º A"},
        {"professor": "Prof Teste", "disciplina": "Biologia", "turma": "1º A"},  # outro horário
        {"professor": "Prof Teste", "disciplina": "Inglês", "turma": "2º B"},
        {"professor": "Prof Teste", "disciplina": "Física", "turma": "3º C"},
        {"professor": "Outro", "disciplina": "Artes", "turma": "1º A"},
    ]
    planos = [
        _plano(1, "Biologia", "1º A", "ok.docx"),
        _plano(2, "Inglês", "2º B", "sumiu.docx"),
    ]
    monkeypatch.setattr(db, "listar_vinculos_professores", lambda: vinculos)
    monkeypatch.setattr(db, "buscar_historico_planos", lambda p, m="": planos)
    monkeypatch.setattr(db, "_resolver_caminho_arquivo_historico", lambda c: tmp_path / c)

    itens = {i["disciplina"]: i for i in db.obter_conferencia_mensal("Prof Teste", "2026-10")}

    assert set(itens) == {"Biologia", "Inglês", "Física"}
    assert itens["Biologia"]["feito"] is True
    assert itens["Inglês"]["feito"] is False and itens["Inglês"]["registro_sem_arquivo"] is True
    assert itens["Física"]["feito"] is False and itens["Física"]["registro_sem_arquivo"] is False


def test_conferencia_mensal_sem_parametros():
    assert db.obter_conferencia_mensal("", "2026-10") == []
    assert db.obter_conferencia_mensal("Prof", "") == []


def test_mes_pela_pasta_ignora_data_de_geracao(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "PLANOS_FEITOS_DIR", tmp_path)
    arq = tmp_path / "PROF" / "DISC" / "NOVEMBRO" / "Plano_8o_ANO_A.docx"
    # gerado em outubro, mas a pasta diz NOVEMBRO
    assert db._mes_plano_pela_pasta(str(arq), "2026-10-02 17:19:15") == "2026-11"
    # virada de ano: plano de JANEIRO gerado em dezembro
    arq2 = tmp_path / "PROF" / "DISC" / "JANEIRO" / "Plano.docx"
    assert db._mes_plano_pela_pasta(str(arq2), "2026-12-20 10:00:00") == "2027-01"
    # fora da estrutura de pastas: sem infer�ncia
    assert db._mes_plano_pela_pasta(str(tmp_path / "solto.docx"), "2026-10-02") == ""
    plano = {"arquivo_path": str(arq), "data_geracao": "2026-10-02 17:19:15", "mes_plano": "2026-09"}
    assert db._mes_efetivo_plano(plano) == "2026-11"
