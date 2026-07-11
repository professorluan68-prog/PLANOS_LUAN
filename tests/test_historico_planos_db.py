from core import database


def _preparar_banco(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "planos_teste.db")
    monkeypatch.setattr(database, "HISTORICO_DOCX_DIR", tmp_path / "historico_docx")
    database.init_db()


def test_init_db_cria_indices_e_remove_historico_incompleto(monkeypatch, tmp_path):
    _preparar_banco(monkeypatch, tmp_path)

    with database.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO historico_planos
            (professor_nome, disciplina, turma, data_geracao, arquivo_nome, arquivo_path)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("ANA", "Matematica", "6 ANO A", "2026-06-05 10:00:00", "valido.docx", "valido.docx"),
        )
        cursor.execute(
            """
            INSERT INTO historico_planos
            (professor_nome, disciplina, turma, data_geracao, arquivo_nome, arquivo_path)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("ANA", "Matematica", "6 ANO A", "2026-06-05 10:00:01", "", "sem_nome.docx"),
        )
        cursor.execute(
            """
            INSERT INTO historico_planos
            (professor_nome, disciplina, turma, data_geracao, arquivo_nome, arquivo_path)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("ANA", "Matematica", "6 ANO A", "2026-06-05 10:00:02", "sem_path.docx", ""),
        )
        conn.commit()

    database.init_db()

    with database.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA index_list(historico_planos)")
        indices = {row[1] for row in cursor.fetchall()}
        cursor.execute("SELECT arquivo_nome FROM historico_planos ORDER BY id")
        arquivos = [row[0] for row in cursor.fetchall()]

    assert "idx_historico_planos_data_id" in indices
    assert "idx_historico_planos_contexto_data" in indices
    assert arquivos == ["valido.docx"]


def test_listar_historico_planos_tem_ordem_estavel_por_id(monkeypatch, tmp_path):
    _preparar_banco(monkeypatch, tmp_path)

    with database.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO historico_planos
            (professor_nome, disciplina, turma, data_geracao, arquivo_nome, arquivo_path)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("ANA", "Matematica", "6 ANO A", "2026-06-05 10:00:00", "primeiro.docx", "primeiro.docx"),
        )
        cursor.execute(
            """
            INSERT INTO historico_planos
            (professor_nome, disciplina, turma, data_geracao, arquivo_nome, arquivo_path)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("ANA", "Matematica", "6 ANO A", "2026-06-05 10:00:00", "segundo.docx", "segundo.docx"),
        )
        conn.commit()

    historico = database.listar_historico_planos(limite=2)

    assert [row[5] for row in historico] == ["segundo.docx", "primeiro.docx"]


def test_salvar_historico_plano_normaliza_metadados(monkeypatch, tmp_path):
    _preparar_banco(monkeypatch, tmp_path)

    database.salvar_historico_plano(
        " ANA ",
        " Matematica ",
        " 6 ANO A ",
        " plano.docx ",
        b"docx",
        bimestre=" 3o BIMESTRE ",
    )

    with database.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT professor_nome, disciplina, turma, bimestre, arquivo_nome, arquivo_path FROM historico_planos"
        )
        row = cursor.fetchone()

    assert row[0:5] == ("ANA", "Matematica", "6 ANO A", "3o BIMESTRE", "plano.docx")
    assert row[5] != ""
    assert (tmp_path / "historico_docx" / row[5]).exists()
    assert (tmp_path / "historico_docx" / row[5]).read_bytes() == b"docx"


def test_salvar_historico_plano_retencao_limite(monkeypatch, tmp_path):
    _preparar_banco(monkeypatch, tmp_path)

    for i in range(1, 8):
        database.salvar_historico_plano(
            "ANA",
            "Matematica",
            "6 ANO A",
            f"plano_{i}.docx",
            f"conteudo_{i}".encode("utf-8"),
            limite_retencao=5,
            bimestre="3o BIMESTRE",
        )

    with database.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT arquivo_nome, arquivo_path FROM historico_planos ORDER BY id")
        rows = cursor.fetchall()

    arquivos = [row[0] for row in rows]

    assert len(arquivos) == 5
    assert arquivos == [
        "plano_3.docx",
        "plano_4.docx",
        "plano_5.docx",
        "plano_6.docx",
        "plano_7.docx",
    ]

    for i in range(1, 3):
        exists = any(f"plano_{i}.docx" in f.name for f in (tmp_path / "historico_docx").glob("*"))
        assert not exists

    for i in range(3, 8):
        exists = any(f"plano_{i}.docx" in f.name for f in (tmp_path / "historico_docx").glob("*"))
        assert exists


def test_salvar_historico_plano_retencao_respeita_bimestre(monkeypatch, tmp_path):
    _preparar_banco(monkeypatch, tmp_path)

    for i in range(1, 4):
        database.salvar_historico_plano(
            "ANA",
            "Matematica",
            "6 ANO A",
            f"plano_3b_{i}.docx",
            f"conteudo_3b_{i}".encode("utf-8"),
            limite_retencao=2,
            bimestre="3o BIMESTRE",
        )
    for i in range(1, 3):
        database.salvar_historico_plano(
            "ANA",
            "Matematica",
            "6 ANO A",
            f"plano_4b_{i}.docx",
            f"conteudo_4b_{i}".encode("utf-8"),
            limite_retencao=2,
            bimestre="4o BIMESTRE",
        )

    with database.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT bimestre, arquivo_nome FROM historico_planos ORDER BY id")
        registros = cursor.fetchall()

    assert registros == [
        ("3o BIMESTRE", "plano_3b_2.docx"),
        ("3o BIMESTRE", "plano_3b_3.docx"),
        ("4o BIMESTRE", "plano_4b_1.docx"),
        ("4o BIMESTRE", "plano_4b_2.docx"),
    ]


def test_verificar_plano_gerado_por_outro_professor_filtra_bimestre(monkeypatch, tmp_path):
    _preparar_banco(monkeypatch, tmp_path)

    database.salvar_historico_plano(
        "CARLA",
        "Historia",
        "8 ANO A",
        "hist_3b.docx",
        b"docx",
        bimestre="3o BIMESTRE",
    )
    database.salvar_historico_plano(
        "CARLA",
        "Historia",
        "8 ANO A",
        "hist_4b.docx",
        b"docx",
        bimestre="4o BIMESTRE",
    )

    outros = database.verificar_plano_gerado_por_outro_professor(
        "BIA",
        "Historia",
        "8 ANO A",
        "3o BIMESTRE",
    )

    assert len(outros) == 1
    assert outros[0]["professor_nome"] == "CARLA"
    assert outros[0]["arquivo_nome"] == "hist_3b.docx"
    assert outros[0]["bimestre"] == "3o BIMESTRE"


def test_listar_ultimos_planos_por_contexto_filtra_bimestre_e_pega_mais_recente(monkeypatch, tmp_path):
    _preparar_banco(monkeypatch, tmp_path)

    database.salvar_historico_plano(
        "ANA",
        "Matematica",
        "6 ANO A",
        "mat_3b_antigo.docx",
        b"docx-1",
        bimestre="3o BIMESTRE",
    )
    database.salvar_historico_plano(
        "ANA",
        "Matematica",
        "6 ANO A",
        "mat_3b_novo.docx",
        b"docx-2",
        bimestre="3o BIMESTRE",
    )
    database.salvar_historico_plano(
        "ANA",
        "Matematica",
        "6 ANO A",
        "mat_4b.docx",
        b"docx-3",
        bimestre="4o BIMESTRE",
    )
    database.salvar_historico_plano(
        "BIA",
        "Historia",
        "7 ANO B",
        "hist_3b.docx",
        b"docx-4",
        bimestre="3o BIMESTRE",
    )

    registros_3b = database.listar_ultimos_planos_por_contexto("3o BIMESTRE")

    assert [
        (item["professor_nome"], item["disciplina"], item["turma"], item["arquivo_nome"], item["bimestre"])
        for item in registros_3b
    ] == [
        ("ANA", "Matematica", "6 ANO A", "mat_3b_novo.docx", "3o BIMESTRE"),
        ("BIA", "Historia", "7 ANO B", "hist_3b.docx", "3o BIMESTRE"),
    ]

    registros_todos = database.listar_ultimos_planos_por_contexto()

    assert [
        (item["professor_nome"], item["disciplina"], item["turma"], item["arquivo_nome"], item["bimestre"])
        for item in registros_todos
    ] == [
        ("ANA", "Matematica", "6 ANO A", "mat_3b_novo.docx", "3o BIMESTRE"),
        ("ANA", "Matematica", "6 ANO A", "mat_4b.docx", "4o BIMESTRE"),
        ("BIA", "Historia", "7 ANO B", "hist_3b.docx", "3o BIMESTRE"),
    ]


def test_sincronizar_historico_planos_com_planos_feitos_indexa_arquivos(monkeypatch, tmp_path):
    _preparar_banco(monkeypatch, tmp_path)
    monkeypatch.setattr(database, "PLANOS_FEITOS_DIR", tmp_path / "PLANOS_FEITOS")

    pasta = tmp_path / "PLANOS_FEITOS" / "HELOISA_MORAES_DELFINO" / "LINGUA_PORTUGUESA"
    pasta.mkdir(parents=True)
    arquivo = pasta / "Plano_6o_ANO_A_Lingua_Portuguesa.docx"
    arquivo.write_bytes(b"docx-real")

    with database.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO professores (nome) VALUES (?)", ("HELOISA MORAES DELFINO",))
        conn.commit()

    inseridos = database.sincronizar_historico_planos_com_planos_feitos()
    resultados = database.buscar_historico_planos("HELOISA MORAES DELFINO")

    assert inseridos == 1
    assert len(resultados) == 1
    assert resultados[0]["disciplina"] == "LINGUA PORTUGUESA"
    assert resultados[0]["turma"] == "6O ANO A"
    assert resultados[0]["arquivo_nome"] == "Plano_6o_ANO_A_Lingua_Portuguesa.docx"


def test_obter_arquivo_historico_aceita_caminho_absoluto(monkeypatch, tmp_path):
    _preparar_banco(monkeypatch, tmp_path)

    arquivo = tmp_path / "externo.docx"
    arquivo.write_bytes(b"conteudo-externo")

    with database.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO historico_planos
            (professor_nome, disciplina, turma, data_geracao, arquivo_nome, arquivo_path)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "ANA",
                "Matematica",
                "6 ANO A",
                "2026-06-05 10:00:00",
                "externo.docx",
                str(arquivo),
            ),
        )
        plano_id = int(cursor.lastrowid)
        conn.commit()

    nome, conteudo = database.obter_arquivo_historico(plano_id)

    assert nome == "externo.docx"
    assert conteudo == b"conteudo-externo"
