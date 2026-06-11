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

    database.salvar_historico_plano(" ANA ", " Matematica ", " 6 ANO A ", " plano.docx ", b"docx")

    with database.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT professor_nome, disciplina, turma, arquivo_nome, LENGTH(arquivo_docx) FROM historico_planos"
        )
        row = cursor.fetchone()

    assert row == ("ANA", "Matematica", "6 ANO A", "plano.docx", 4)
