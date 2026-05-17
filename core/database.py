import json
import os
import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "planos_luan.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS professores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS professor_turmas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                professor_id INTEGER,
                disciplina TEXT,
                turma TEXT,
                dia_semana TEXT,
                horario TEXT,
                aulas_semana TEXT,
                arquivo_modelo TEXT,
                componente_curricular TEXT,
                FOREIGN KEY(professor_id) REFERENCES professores(id) ON DELETE CASCADE
            )
            """
        )
        cursor.execute("PRAGMA table_info(professor_turmas)")
        colunas_prof_turmas = {row[1] for row in cursor.fetchall()}
        if "arquivo_modelo" not in colunas_prof_turmas:
            cursor.execute("ALTER TABLE professor_turmas ADD COLUMN arquivo_modelo TEXT")
        if "componente_curricular" not in colunas_prof_turmas:
            cursor.execute("ALTER TABLE professor_turmas ADD COLUMN componente_curricular TEXT")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS historico_planos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                professor_nome TEXT,
                disciplina TEXT,
                turma TEXT,
                data_geracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                arquivo_nome TEXT,
                arquivo_docx BLOB
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS configuracoes (
                chave TEXT PRIMARY KEY,
                valor TEXT
            )
            """
        )
        conn.commit()


def migrar_json_para_sqlite():
    json_path = Path(__file__).resolve().parent.parent / "professores.json"
    if not json_path.exists():
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            dados = json.load(f)

        with get_connection() as conn:
            cursor = conn.cursor()
            for professor, info in dados.items():
                cursor.execute("INSERT OR IGNORE INTO professores (nome) VALUES (?)", (professor,))
                cursor.execute("SELECT id FROM professores WHERE nome = ?", (professor,))
                prof_id = cursor.fetchone()[0]

                for d in info.get("disciplinas", []):
                    cursor.execute(
                        """
                        SELECT id FROM professor_turmas
                        WHERE professor_id = ? AND disciplina = ? AND turma = ?
                        """,
                        (prof_id, d.get("disciplina"), d.get("turma")),
                    )
                    if not cursor.fetchone():
                        cursor.execute(
                            """
                            INSERT INTO professor_turmas
                            (professor_id, disciplina, turma, dia_semana, horario, aulas_semana, arquivo_modelo, componente_curricular)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                prof_id,
                                d.get("disciplina"),
                                d.get("turma"),
                                d.get("dia_semana"),
                                d.get("horario"),
                                d.get("aulas_semana"),
                                d.get("arquivo_modelo") or d.get("arquivo") or "",
                                d.get("componente_curricular") or "",
                            ),
                        )
            conn.commit()

        os.rename(json_path, json_path.with_suffix(".json.backup"))
    except Exception as e:
        print(f"Erro na migracao do JSON: {e}")


def obter_professores_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT p.nome, t.disciplina, t.turma, t.dia_semana, t.horario, t.aulas_semana, t.arquivo_modelo, t.componente_curricular
            FROM professores p
            LEFT JOIN professor_turmas t ON p.id = t.professor_id
            ORDER BY
                p.nome,
                CASE
                    WHEN COALESCE(t.dia_semana, '') <> ''
                     AND COALESCE(t.horario, '') <> ''
                     AND COALESCE(t.aulas_semana, '') <> '' THEN 0
                    ELSE 1
                END,
                t.disciplina,
                t.turma
            """
        )

        resultado = {}
        for row in cursor.fetchall():
            nome = row[0]
            if nome not in resultado:
                resultado[nome] = {"disciplinas": []}
            if row[1] and row[2]:
                resultado[nome]["disciplinas"].append(
                    {
                        "disciplina": row[1],
                        "turma": row[2],
                        "dia_semana": row[3] or "",
                        "horario": row[4] or "",
                        "aulas_semana": row[5] or "",
                        "arquivo": row[6] or "",
                        "componente_curricular": row[7] or "",
                        "origem": "banco",
                    }
                )
        return resultado


def salvar_professor_turma(nome, disciplina, turma, dia_semana, horario, aulas_semana, arquivo_modelo="", componente_curricular=""):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO professores (nome) VALUES (?)", (nome,))
        cursor.execute("SELECT id FROM professores WHERE nome = ?", (nome,))
        prof_id = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT id FROM professor_turmas
            WHERE professor_id = ? AND disciplina = ? AND turma = ?
            ORDER BY id
            LIMIT 1
            """,
            (prof_id, disciplina, turma),
        )
        existente = cursor.fetchone()

        if existente:
            cursor.execute(
                """
                UPDATE professor_turmas
                SET dia_semana = ?, horario = ?, aulas_semana = ?, arquivo_modelo = ?, componente_curricular = ?
                WHERE id = ?
                """,
                (dia_semana, horario, aulas_semana, arquivo_modelo, componente_curricular, existente[0]),
            )
        else:
            cursor.execute(
                """
                INSERT INTO professor_turmas
                (professor_id, disciplina, turma, dia_semana, horario, aulas_semana, arquivo_modelo, componente_curricular)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (prof_id, disciplina, turma, dia_semana, horario, aulas_semana, arquivo_modelo, componente_curricular),
            )
        conn.commit()


def salvar_historico_plano(professor_nome, disciplina, turma, arquivo_nome, arquivo_docx_bytes):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO historico_planos (professor_nome, disciplina, turma, arquivo_nome, arquivo_docx)
            VALUES (?, ?, ?, ?, ?)
            """,
            (professor_nome, disciplina, turma, arquivo_nome, arquivo_docx_bytes),
        )
        conn.commit()


def listar_historico_planos():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, professor_nome, disciplina, turma, data_geracao, arquivo_nome
            FROM historico_planos
            ORDER BY data_geracao DESC
            LIMIT 50
            """
        )
        return cursor.fetchall()


def obter_arquivo_historico(plano_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT arquivo_nome, arquivo_docx FROM historico_planos WHERE id = ?", (plano_id,))
        return cursor.fetchone()
