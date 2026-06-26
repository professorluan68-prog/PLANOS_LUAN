# tests/unit/test_database_pragmas.py
import pytest

from core.database import connection_scope, get_connection


def test_pragmas_applied(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode;")
    mode = cur.fetchone()[0]
    cur.execute("PRAGMA synchronous;")
    sync = cur.fetchone()[0]
    conn.close()
    assert mode.lower() == "wal"
    assert sync is not None


def test_connection_scope_commit(tmp_path):
    db_path = str(tmp_path / "commit.db")
    with connection_scope(db_path) as conn:
        cur = conn.cursor()
        cur.execute("CREATE TABLE exemplo (id INTEGER PRIMARY KEY, nome TEXT)")
        cur.execute("INSERT INTO exemplo (nome) VALUES ('ok')")

    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM exemplo")
        total = cur.fetchone()[0]
    assert total == 1


def test_connection_scope_rollback(tmp_path):
    db_path = str(tmp_path / "rollback.db")
    with get_connection(db_path) as conn:
        conn.execute("CREATE TABLE exemplo (id INTEGER PRIMARY KEY, nome TEXT)")
        conn.commit()

    with pytest.raises(RuntimeError):
        with connection_scope(db_path) as conn:
            conn.execute("INSERT INTO exemplo (nome) VALUES ('falha')")
            raise RuntimeError("forcar rollback")

    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM exemplo")
        total = cur.fetchone()[0]
    assert total == 0
