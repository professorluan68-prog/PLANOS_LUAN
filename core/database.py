import json
import os
import sqlite3
from pathlib import Path

from config import DB_PATH


HISTORICO_PLANOS_LIMITE_PADRAO = 50
HISTORICO_PLANOS_LIMITE_MAXIMO = 500


class SafeConnectionWrapper:
    """
    Wrapper para sqlite3.Connection que garante o fechamento automático da
    conexão ao sair do bloco 'with'.
    """
    def __init__(self, conn):
        self.conn = conn

    def __getattr__(self, name):
        return getattr(self.conn, name)

    def __enter__(self):
        self.conn.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.conn.__exit__(exc_type, exc_val, exc_tb)
        finally:
            self.conn.close()


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return SafeConnectionWrapper(conn)


def _normalizar_campo(valor):
    return str(valor or "").strip()


def _normalizar_campo_chave(valor):
    return _normalizar_campo(valor).upper()


def _obter_ou_criar_professor(cursor, nome: str) -> int:
    nome = _normalizar_campo(nome).upper()
    cursor.execute("INSERT OR IGNORE INTO professores (nome) VALUES (?)", (nome,))
    cursor.execute("SELECT id FROM professores WHERE nome = ?", (nome,))
    row = cursor.fetchone()
    if not row:
        raise ValueError("Nao foi possivel localizar ou criar o professor.")
    return int(row[0])


def _remover_professor_sem_turmas(cursor, professor_id: int) -> None:
    cursor.execute("SELECT COUNT(*) FROM professor_turmas WHERE professor_id = ?", (professor_id,))
    total = int(cursor.fetchone()[0] or 0)
    if total == 0:
        cursor.execute("DELETE FROM professores WHERE id = ?", (professor_id,))


def _criar_indices_banco(cursor) -> None:
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_historico_planos_data_id
        ON historico_planos (data_geracao DESC, id DESC)
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_historico_planos_contexto_data
        ON historico_planos (professor_nome, disciplina, turma, data_geracao DESC, id DESC)
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_professor_turmas_prof_id
        ON professor_turmas (professor_id)
        """
    )


def _limpar_historico_planos_incompletos(cursor) -> None:
    cursor.execute(
        """
        DELETE FROM historico_planos
        WHERE arquivo_docx IS NULL
           OR LENGTH(arquivo_docx) = 0
           OR COALESCE(TRIM(arquivo_nome), '') = ''
        """
    )


def _normalizar_limite_historico(limite) -> int:
    try:
        valor = int(limite)
    except (TypeError, ValueError):
        valor = HISTORICO_PLANOS_LIMITE_PADRAO
    return max(1, min(valor, HISTORICO_PLANOS_LIMITE_MAXIMO))


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
                template_id TEXT,
                componente_curricular TEXT,
                FOREIGN KEY(professor_id) REFERENCES professores(id) ON DELETE CASCADE
            )
            """
        )
        cursor.execute("PRAGMA table_info(professor_turmas)")
        colunas_prof_turmas = {row[1] for row in cursor.fetchall()}
        if "arquivo_modelo" not in colunas_prof_turmas:
            cursor.execute("ALTER TABLE professor_turmas ADD COLUMN arquivo_modelo TEXT")
        if "template_id" not in colunas_prof_turmas:
            cursor.execute("ALTER TABLE professor_turmas ADD COLUMN template_id TEXT")
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
        _criar_indices_banco(cursor)
        _limpar_historico_planos_incompletos(cursor)
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
                    componente = _normalizar_campo_chave(d.get("componente_curricular"))
                    cursor.execute(
                        """
                        SELECT id FROM professor_turmas
                        WHERE professor_id = ? AND disciplina = ? AND turma = ? AND UPPER(COALESCE(componente_curricular, '')) = ?
                        """,
                        (prof_id, d.get("disciplina"), d.get("turma"), componente),
                    )
                    if not cursor.fetchone():
                        cursor.execute(
                            """
                            INSERT INTO professor_turmas
                            (professor_id, disciplina, turma, dia_semana, horario, aulas_semana, arquivo_modelo, template_id, componente_curricular)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                prof_id,
                                d.get("disciplina"),
                                d.get("turma"),
                                d.get("dia_semana"),
                                d.get("horario"),
                                d.get("aulas_semana"),
                                d.get("arquivo_modelo") or d.get("arquivo") or "",
                                d.get("template_id") or "",
                                d.get("componente_curricular") or "",
                            ),
                        )
            conn.commit()

        os.rename(json_path, json_path.with_suffix(".json.backup"))
    except Exception as e:
        print(f"Erro na migracao do JSON: {e}")


def obter_professor_id_por_nome(nome: str) -> int | None:
    """Retorna o ID do professor pelo nome cadastrado (sem criar se não existir)."""
    if not nome or not isinstance(nome, str):
        return None
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            nome_norm = _normalizar_campo(nome).upper()
            cursor.execute("SELECT id FROM professores WHERE nome = ?", (nome_norm,))
            row = cursor.fetchone()
            if row:
                return int(row[0])
    except Exception:
        pass
    return None


def obter_professores_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT p.nome, t.disciplina, t.turma, t.dia_semana, t.horario, t.aulas_semana, t.arquivo_modelo, t.template_id, t.componente_curricular
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
                , COALESCE(t.componente_curricular, '')
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
                        "arquivo_modelo": row[6] or "",
                        "template_id": row[7] or "",
                        "componente_curricular": row[8] or "",
                        "origem": "banco",
                    }
                )
        return resultado


def salvar_professor_turma(
    nome,
    disciplina,
    turma,
    dia_semana,
    horario,
    aulas_semana,
    arquivo_modelo="",
    componente_curricular="",
    template_id="",
):
    with get_connection() as conn:
        cursor = conn.cursor()
        prof_id = _obter_ou_criar_professor(cursor, nome)
        disciplina = _normalizar_campo(disciplina)
        turma = _normalizar_campo(turma)
        dia_semana = _normalizar_campo(dia_semana)
        horario = _normalizar_campo(horario)
        aulas_semana = _normalizar_campo(aulas_semana)
        arquivo_modelo = _normalizar_campo(arquivo_modelo)
        template_id = _normalizar_campo(template_id)
        componente_curricular = _normalizar_campo(componente_curricular)
        componente_chave = _normalizar_campo_chave(componente_curricular)

        cursor.execute(
            """
            SELECT id FROM professor_turmas
            WHERE professor_id = ? AND disciplina = ? AND turma = ? AND UPPER(COALESCE(componente_curricular, '')) = ?
            ORDER BY id
            LIMIT 1
            """,
            (prof_id, disciplina, turma, componente_chave),
        )
        existente = cursor.fetchone()

        if existente:
            cursor.execute(
                """
                UPDATE professor_turmas
                SET dia_semana = ?, horario = ?, aulas_semana = ?, arquivo_modelo = ?, template_id = ?, componente_curricular = ?
                WHERE id = ?
                """,
                (dia_semana, horario, aulas_semana, arquivo_modelo, template_id, componente_curricular, existente[0]),
            )
        else:
            cursor.execute(
                """
                INSERT INTO professor_turmas
                (professor_id, disciplina, turma, dia_semana, horario, aulas_semana, arquivo_modelo, template_id, componente_curricular)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (prof_id, disciplina, turma, dia_semana, horario, aulas_semana, arquivo_modelo, template_id, componente_curricular),
            )
        conn.commit()


def listar_vinculos_professores():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                t.id,
                p.id,
                p.nome,
                t.disciplina,
                t.turma,
                t.dia_semana,
                t.horario,
                t.aulas_semana,
                t.arquivo_modelo,
                t.template_id,
                t.componente_curricular
            FROM professor_turmas t
            JOIN professores p ON p.id = t.professor_id
            ORDER BY p.nome, t.disciplina, t.turma, t.id
                     , COALESCE(t.componente_curricular, '')
            """
        )
        return [
            {
                "id": row[0],
                "professor_id": row[1],
                "professor": row[2] or "",
                "disciplina": row[3] or "",
                "turma": row[4] or "",
                "dia_semana": row[5] or "",
                "horario": row[6] or "",
                "aulas_semana": row[7] or "",
                "arquivo": row[8] or "",
                "arquivo_modelo": row[8] or "",
                "template_id": row[9] or "",
                "componente_curricular": row[10] or "",
                "origem": "banco",
            }
            for row in cursor.fetchall()
        ]


def obter_vinculo_professor(vinculo_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                t.id,
                p.id,
                p.nome,
                t.disciplina,
                t.turma,
                t.dia_semana,
                t.horario,
                t.aulas_semana,
                t.arquivo_modelo,
                t.template_id,
                t.componente_curricular
            FROM professor_turmas t
            JOIN professores p ON p.id = t.professor_id
            WHERE t.id = ?
            """,
            (vinculo_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "professor_id": row[1],
            "professor": row[2] or "",
            "disciplina": row[3] or "",
            "turma": row[4] or "",
            "dia_semana": row[5] or "",
            "horario": row[6] or "",
            "aulas_semana": row[7] or "",
            "arquivo": row[8] or "",
            "arquivo_modelo": row[8] or "",
            "template_id": row[9] or "",
            "componente_curricular": row[10] or "",
            "origem": "banco",
        }


def atualizar_vinculo_professor(
    vinculo_id,
    nome,
    disciplina,
    turma,
    dia_semana,
    horario,
    aulas_semana,
    arquivo_modelo="",
    componente_curricular="",
    template_id="",
):
    nome = _normalizar_campo(nome).upper()
    disciplina = _normalizar_campo(disciplina)
    turma = _normalizar_campo(turma)
    if not nome or not disciplina or not turma:
        raise ValueError("Professor, disciplina e turma sao obrigatorios.")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT professor_id FROM professor_turmas WHERE id = ?", (vinculo_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError("Cadastro nao encontrado.")
        professor_antigo_id = int(row[0])
        professor_id = _obter_ou_criar_professor(cursor, nome)
        cursor.execute(
            """
            UPDATE professor_turmas
            SET professor_id = ?,
                disciplina = ?,
                turma = ?,
                dia_semana = ?,
                horario = ?,
                aulas_semana = ?,
                arquivo_modelo = ?,
                template_id = ?,
                componente_curricular = ?
            WHERE id = ?
            """,
            (
                professor_id,
                disciplina,
                turma,
                _normalizar_campo(dia_semana),
                _normalizar_campo(horario),
                _normalizar_campo(aulas_semana),
                _normalizar_campo(arquivo_modelo),
                _normalizar_campo(template_id),
                _normalizar_campo(componente_curricular),
                vinculo_id,
            ),
        )
        if professor_antigo_id != professor_id:
            _remover_professor_sem_turmas(cursor, professor_antigo_id)
        conn.commit()
    return obter_vinculo_professor(vinculo_id)


def excluir_vinculo_professor(vinculo_id) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT professor_id FROM professor_turmas WHERE id = ?", (vinculo_id,))
        row = cursor.fetchone()
        if not row:
            return False
        professor_id = int(row[0])
        cursor.execute("DELETE FROM professor_turmas WHERE id = ?", (vinculo_id,))
        _remover_professor_sem_turmas(cursor, professor_id)
        conn.commit()
    return True


def duplicar_vinculo_professor(
    vinculo_id,
    nome=None,
    disciplina=None,
    turma=None,
    dia_semana=None,
    horario=None,
    aulas_semana=None,
    arquivo_modelo=None,
    componente_curricular=None,
    template_id=None,
) -> int:
    original = obter_vinculo_professor(vinculo_id)
    if not original:
        raise ValueError("Cadastro original nao encontrado.")

    with get_connection() as conn:
        cursor = conn.cursor()
        professor_id = _obter_ou_criar_professor(cursor, nome or original["professor"])
        cursor.execute(
            """
            INSERT INTO professor_turmas
            (professor_id, disciplina, turma, dia_semana, horario, aulas_semana, arquivo_modelo, template_id, componente_curricular)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                professor_id,
                _normalizar_campo(disciplina if disciplina is not None else original["disciplina"]),
                _normalizar_campo(turma if turma is not None else original["turma"]),
                _normalizar_campo(dia_semana if dia_semana is not None else original["dia_semana"]),
                _normalizar_campo(horario if horario is not None else original["horario"]),
                _normalizar_campo(aulas_semana if aulas_semana is not None else original["aulas_semana"]),
                _normalizar_campo(arquivo_modelo if arquivo_modelo is not None else original["arquivo_modelo"]),
                _normalizar_campo(template_id if template_id is not None else original["template_id"]),
                _normalizar_campo(
                    componente_curricular
                    if componente_curricular is not None
                    else original["componente_curricular"]
                ),
            ),
        )
        novo_id = int(cursor.lastrowid)
        conn.commit()
    return novo_id


def salvar_historico_plano(professor_nome, disciplina, turma, arquivo_nome, arquivo_docx_bytes):
    professor_nome = _normalizar_campo(professor_nome)
    disciplina = _normalizar_campo(disciplina)
    turma = _normalizar_campo(turma)
    arquivo_nome = _normalizar_campo(arquivo_nome)
    arquivo_docx_bytes = bytes(arquivo_docx_bytes or b"")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO historico_planos (professor_nome, disciplina, turma, arquivo_nome, arquivo_docx)
            VALUES (?, ?, ?, ?, ?)
            """,
            (professor_nome, disciplina, turma, arquivo_nome, sqlite3.Binary(arquivo_docx_bytes)),
        )
        conn.commit()


def listar_historico_planos(limite=HISTORICO_PLANOS_LIMITE_PADRAO):
    limite = _normalizar_limite_historico(limite)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, professor_nome, disciplina, turma, data_geracao, arquivo_nome
            FROM historico_planos
            ORDER BY data_geracao DESC, id DESC
            LIMIT ?
            """,
            (limite,),
        )
        return cursor.fetchall()


def obter_arquivo_historico(plano_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT arquivo_nome, arquivo_docx FROM historico_planos WHERE id = ?", (plano_id,))
        return cursor.fetchone()


def obter_ultimo_plano_docx(professor_nome: str, disciplina: str, turma: str) -> bytes | None:
    professor_nome = _normalizar_campo(professor_nome)
    disciplina = _normalizar_campo(disciplina)
    turma = _normalizar_campo(turma)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT arquivo_docx FROM historico_planos
            WHERE UPPER(TRIM(professor_nome)) = UPPER(TRIM(?))
              AND UPPER(TRIM(disciplina)) = UPPER(TRIM(?))
              AND UPPER(TRIM(turma)) = UPPER(TRIM(?))
            ORDER BY data_geracao DESC, id DESC
            LIMIT 1
            """,
            (professor_nome, disciplina, turma),
        )
        row = cursor.fetchone()
        return row[0] if row else None


def obter_ultima_aula_gerada_sistema(professor: str, disciplina: str, turma: str, bimestre: str = "") -> int:
    from io import BytesIO
    from docx import Document
    import re
    import json
    
    prof_upper = str(professor or "").strip().upper()
    disc_upper = str(disciplina or "").strip().upper()
    turma_upper = str(turma or "").strip().upper()

    # 1. Tentar obter do historico no banco de dados
    try:
        docx_bytes = obter_ultimo_plano_docx(professor, disciplina, turma)
        if docx_bytes:
            # Se um bimestre foi informado, verificar se o plano do histórico pertence a esse mesmo bimestre
            if bimestre:
                try:
                    doc_temp = Document(BytesIO(docx_bytes))
                    outro_bimestre_detectado = False
                    for table in doc_temp.tables:
                        contem_palavra_bimestre = False
                        textos_celulas = []
                        for row in table.rows:
                            for cell in row.cells:
                                txt = cell.text.strip()
                                textos_celulas.append(txt)
                                if "BIMESTRE" in txt.upper():
                                    contem_palavra_bimestre = True
                        
                        if contem_palavra_bimestre:
                            from core.disciplinas import BIMESTRES
                            for b in BIMESTRES:
                                if b.lower() != bimestre.lower():
                                    if any(b.lower() in tc.lower() for tc in textos_celulas):
                                        outro_bimestre_detectado = True
                                        break
                            if outro_bimestre_detectado:
                                break
                    
                    if outro_bimestre_detectado:
                        # O último plano gerado pertence a outro bimestre, então zeramos a contagem para o bimestre atual
                        return 0
                except Exception:
                    pass

            doc = Document(BytesIO(docx_bytes))
            total_linhas = 0
            aulas_detectadas = []
            for t in doc.tables:
                if len(t.rows) > 0:
                    textos_cab = [c.text.upper() for c in t.rows[0].cells]
                    if any('AULA' in tc for tc in textos_cab) and any('APRENDIZAGEM' in tc for tc in textos_cab):
                        for row in t.rows[1:]:
                            total_linhas += 1
                            if len(row.cells) >= 2:
                                txt_col2 = row.cells[1].text
                                match = re.search(r'(?i)Aula\s*(\d+)', txt_col2)
                                if match:
                                    aulas_detectadas.append(int(match.group(1)))
            if aulas_detectadas:
                return max(aulas_detectadas)
            if total_linhas > 0:
                return total_linhas
    except Exception:
        pass

    # 2. Tentar obter do arquivo JSON de mapeamento
    try:
        json_path = Path("D:\\registro_proxima_geracao.json")
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as fj:
                dados = json.load(fj)
                for item in dados:
                    if (str(item.get("professor") or "").strip().upper() == prof_upper and
                        str(item.get("disciplina") or "").strip().upper() == disc_upper and
                        str(item.get("turma") or "").strip().upper() == turma_upper):
                        if bimestre and item.get("bimestre"):
                            if str(item.get("bimestre")).strip().lower() != bimestre.strip().lower():
                                continue
                        return int(item.get("aula_parada") or 0)
    except Exception:
        pass

    return 0
