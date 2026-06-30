from core import database


def _preparar_banco(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "planos_teste.db")
    database.init_db()


def test_init_db_cria_indices_e_remove_historico_incompleto(monkeypatch, tmp_path):
    _preparar_banco(monkeypatch, tmp_path)

    with database.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO historico_planos
            (professor_nome, disciplina, turma, data_geracao, arquivo_nome, arquivo_docx)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("ANA", "Matematica", "6 ANO A", "2026-06-05 10:00:00", "valido.docx", b"ok"),
        )
        cursor.execute(
            """
            INSERT INTO historico_planos
            (professor_nome, disciplina, turma, data_geracao, arquivo_nome, arquivo_docx)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("ANA", "Matematica", "6 ANO A", "2026-06-05 10:00:01", "", b"ok"),
        )
        cursor.execute(
            """
            INSERT INTO historico_planos
            (professor_nome, disciplina, turma, data_geracao, arquivo_nome, arquivo_docx)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("ANA", "Matematica", "6 ANO A", "2026-06-05 10:00:02", "sem_blob.docx", b""),
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
            (professor_nome, disciplina, turma, data_geracao, arquivo_nome, arquivo_docx)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("ANA", "Matematica", "6 ANO A", "2026-06-05 10:00:00", "primeiro.docx", b"1"),
        )
        cursor.execute(
            """
            INSERT INTO historico_planos
            (professor_nome, disciplina, turma, data_geracao, arquivo_nome, arquivo_docx)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("ANA", "Matematica", "6 ANO A", "2026-06-05 10:00:00", "segundo.docx", b"2"),
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
        bimestre=" 3º BIMESTRE ",
    )

    with database.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT professor_nome, disciplina, turma, bimestre, arquivo_nome, LENGTH(arquivo_docx) FROM historico_planos"
        )
        row = cursor.fetchone()

    assert row == ("ANA", "Matematica", "6 ANO A", "3º BIMESTRE", "plano.docx", 4)


def test_salvar_historico_plano_retencao_limite(monkeypatch, tmp_path):
    _preparar_banco(monkeypatch, tmp_path)

    # Inserir 7 planos para o mesmo professor/turma/disciplina com limite de 5
    for i in range(1, 8):
        database.salvar_historico_plano(
            "ANA",
            "Matematica",
            "6 ANO A",
            f"plano_{i}.docx",
            f"conteudo_{i}".encode("utf-8"),
            limite_retencao=5,
            bimestre="3º BIMESTRE",
        )

    # Listar todos os planos no banco
    with database.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT arquivo_nome FROM historico_planos ORDER BY id")
        arquivos = [row[0] for row in cursor.fetchall()]

    # Deve conter exatamente 5 arquivos, os mais recentes (plano_3 a plano_7)
    assert len(arquivos) == 5
    assert arquivos == ["plano_3.docx", "plano_4.docx", "plano_5.docx", "plano_6.docx", "plano_7.docx"]


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
            bimestre="3º BIMESTRE",
        )
    for i in range(1, 3):
        database.salvar_historico_plano(
            "ANA",
            "Matematica",
            "6 ANO A",
            f"plano_4b_{i}.docx",
            f"conteudo_4b_{i}".encode("utf-8"),
            limite_retencao=2,
            bimestre="4º BIMESTRE",
        )

    with database.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT bimestre, arquivo_nome FROM historico_planos ORDER BY id"
        )
        registros = cursor.fetchall()

    assert registros == [
        ("3º BIMESTRE", "plano_3b_2.docx"),
        ("3º BIMESTRE", "plano_3b_3.docx"),
        ("4º BIMESTRE", "plano_4b_1.docx"),
        ("4º BIMESTRE", "plano_4b_2.docx"),
    ]


def test_verificar_plano_gerado_por_outro_professor_filtra_bimestre(monkeypatch, tmp_path):
    _preparar_banco(monkeypatch, tmp_path)

    database.salvar_historico_plano(
        "CARLA",
        "Historia",
        "8 ANO A",
        "hist_3b.docx",
        b"docx",
        bimestre="3º BIMESTRE",
    )
    database.salvar_historico_plano(
        "CARLA",
        "Historia",
        "8 ANO A",
        "hist_4b.docx",
        b"docx",
        bimestre="4º BIMESTRE",
    )

    outros = database.verificar_plano_gerado_por_outro_professor(
        "BIA",
        "Historia",
        "8 ANO A",
        bimestre="3º BIMESTRE",
    )

    assert len(outros) == 1
    assert outros[0]["professor_nome"] == "CARLA"
    assert outros[0]["arquivo_nome"] == "hist_3b.docx"
    assert outros[0]["bimestre"] == "3º BIMESTRE"
