import json
import os
import sqlite3
import logging
import re
import unicodedata
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime

from config import DB_PATH, REGISTRO_PROXIMA_GERACAO_PATH, HISTORICO_DOCX_DIR, PLANOS_FEITOS_DIR
from core.lib.classificador import normalizar_texto

logger = logging.getLogger(__name__)


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


def get_connection(db_path=None):
    """
    Retorna uma nova conexão SQLite configurada para concorrência (WAL).
    Cada worker/thread deve abrir sua própria conexão via esta função.
    """
    db_path = DB_PATH if db_path is None else db_path
    conn = sqlite3.connect(db_path, timeout=30, check_same_thread=False)
    # Pragmas aplicadas por conexão para garantir comportamento consistente
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA busy_timeout=10000;")
    return SafeConnectionWrapper(conn)


@contextmanager
def connection_scope(db_path=None):
    """
    Context manager para uso de conexão com commit/rollback automático.
    Uso recomendado: with connection_scope() as conn: ...
    """
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def _normalizar_campo(valor):
    return str(valor or "").strip()


def _normalizar_campo_chave(valor):
    return _normalizar_campo(valor).upper()


def _resolver_caminho_arquivo_historico(arquivo_path: str) -> Path:
    caminho = Path(str(arquivo_path or "").strip())
    if not str(caminho):
        return Path()
    return caminho if caminho.is_absolute() else Path(HISTORICO_DOCX_DIR) / caminho


def _chave_caminho_historico(arquivo_path: str) -> str:
    caminho = _resolver_caminho_arquivo_historico(arquivo_path)
    if not str(caminho):
        return ""
    try:
        return str(caminho.resolve()).upper()
    except OSError:
        return str(caminho).upper()


def _normalizar_nome_pasta_historico(valor: str) -> str:
    texto = str(valor or "").replace("_", " ").strip()
    return re.sub(r"\s+", " ", normalizar_texto(texto)).strip().upper()


def _slug_nome_arquivo_historico(texto: str) -> str:
    texto = str(texto or "").replace("º", "o").replace("°", "o").replace("ª", "a")
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"[^A-Za-z0-9_-]+", "_", texto).strip("_")


def _inferir_turma_por_nome_arquivo(arquivo_nome: str, disciplina: str) -> str:
    stem = Path(str(arquivo_nome or "")).stem
    if stem.lower().startswith("plano_"):
        stem = stem[6:]
    if stem.lower().endswith("_in"):
        stem = stem[:-3]

    disciplina_slug = _slug_nome_arquivo_historico(disciplina)
    sufixo_disciplina = f"_{disciplina_slug.lower()}" if disciplina_slug else ""
    if sufixo_disciplina and stem.lower().endswith(sufixo_disciplina):
        stem = stem[: -len(sufixo_disciplina)]

    turma = re.sub(r"\s+", " ", stem.replace("_", " ")).strip()
    return turma.upper()


def _resolver_nome_professor_por_pasta(nome_pasta: str, nomes_professores: list[str]) -> str:
    chave_pasta = _normalizar_nome_pasta_historico(nome_pasta)
    for nome in nomes_professores:
        if _normalizar_nome_pasta_historico(nome) == chave_pasta:
            return str(nome or "").strip()
    return re.sub(r"\s+", " ", str(nome_pasta or "").replace("_", " ")).strip().upper()


def _buscar_id_historico_por_caminho(cursor, arquivo_path: str) -> int | None:
    alvo = _chave_caminho_historico(arquivo_path)
    if not alvo:
        return None

    cursor.execute(
        """
        SELECT id, arquivo_path
        FROM historico_planos
        WHERE COALESCE(TRIM(arquivo_path), '') <> ''
        """
    )
    for row in cursor.fetchall():
        if _chave_caminho_historico(row[1]) == alvo:
            return int(row[0])
    return None


def _existe_historico_mesmo_contexto_arquivo(
    cursor,
    professor_nome: str,
    disciplina: str,
    turma: str,
    arquivo_nome: str,
) -> bool:
    cursor.execute(
        """
        SELECT 1
        FROM historico_planos
        WHERE UPPER(TRIM(professor_nome)) = UPPER(TRIM(?))
          AND UPPER(TRIM(disciplina)) = UPPER(TRIM(?))
          AND UPPER(TRIM(turma)) = UPPER(TRIM(?))
          AND UPPER(TRIM(arquivo_nome)) = UPPER(TRIM(?))
        LIMIT 1
        """,
        (professor_nome, disciplina, turma, arquivo_nome),
    )
    return bool(cursor.fetchone())


def sincronizar_historico_planos_com_planos_feitos() -> int:
    pasta_planos = Path(PLANOS_FEITOS_DIR)
    if not pasta_planos.exists():
        return 0

    arquivos_docx = [
        caminho
        for caminho in pasta_planos.rglob("*.docx")
        if caminho.is_file() and not caminho.name.startswith("~$")
    ]
    if not arquivos_docx:
        return 0

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nome FROM professores ORDER BY nome")
        nomes_professores = [row[0] for row in cursor.fetchall()]

        inseridos = 0
        for caminho in arquivos_docx:
            try:
                relativo = caminho.relative_to(pasta_planos)
            except ValueError:
                continue
            partes = relativo.parts
            if len(partes) < 3:
                continue

            professor_nome = _resolver_nome_professor_por_pasta(partes[0], nomes_professores)
            disciplina = str(partes[1] or "").replace("_", " ").strip()
            arquivo_nome = caminho.name
            turma = _inferir_turma_por_nome_arquivo(arquivo_nome, disciplina)
            if not professor_nome or not disciplina or not turma:
                continue

            caminho_str = str(caminho.resolve())
            if _buscar_id_historico_por_caminho(cursor, caminho_str) is not None:
                continue
            if _existe_historico_mesmo_contexto_arquivo(
                cursor,
                professor_nome,
                disciplina,
                turma,
                arquivo_nome,
            ):
                continue

            data_geracao = datetime.fromtimestamp(caminho.stat().st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            cursor.execute(
                """
                INSERT INTO historico_planos
                (professor_nome, disciplina, turma, bimestre, data_geracao, arquivo_nome, arquivo_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    professor_nome,
                    disciplina,
                    turma,
                    "",
                    data_geracao,
                    arquivo_nome,
                    caminho_str,
                ),
            )
            inseridos += 1

        conn.commit()
        return inseridos


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
        CREATE INDEX IF NOT EXISTS idx_historico_planos_contexto_bimestre_data
        ON historico_planos (professor_nome, disciplina, turma, bimestre, data_geracao DESC, id DESC)
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
        WHERE arquivo_path IS NULL
           OR COALESCE(TRIM(arquivo_path), '') = ''
           OR COALESCE(TRIM(arquivo_nome), '') = ''
        """
    )


def _normalizar_limite_historico(limite) -> int:
    try:
        valor = int(limite)
    except (TypeError, ValueError):
        valor = HISTORICO_PLANOS_LIMITE_PADRAO
    return max(1, min(valor, HISTORICO_PLANOS_LIMITE_MAXIMO))
# ---------- Sistema de migrações versionadas ----------
MIGRACOES = [
    # Versão 1
    "ALTER TABLE professor_turmas ADD COLUMN arquivo_modelo TEXT",
    # Versão 2
    "ALTER TABLE professor_turmas ADD COLUMN template_id TEXT",
    # Versão 3
    "ALTER TABLE professor_turmas ADD COLUMN componente_curricular TEXT",
    # Versão 4
    "ALTER TABLE historico_planos ADD COLUMN bimestre TEXT",
]


def _aplicar_migracoes(cursor):
    """Aplica migrações pendentes de schema com controle de versão."""
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS schema_version (versao INTEGER PRIMARY KEY)"
    )
    cursor.execute("SELECT COALESCE(MAX(versao), 0) FROM schema_version")
    versao_atual = cursor.fetchone()[0]

    for i, sql in enumerate(MIGRACOES[versao_atual:], start=versao_atual + 1):
        try:
            cursor.execute(sql)
            cursor.execute("INSERT OR IGNORE INTO schema_version VALUES (?)", (i,))
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                cursor.execute("INSERT OR IGNORE INTO schema_version VALUES (?)", (i,))
            else:
                raise RuntimeError(f"Falha na migração {i}: {e}") from e


def _migrar_blob_para_path(conn) -> None:
    """
    Verifica se a tabela historico_planos tem a coluna antiga 'arquivo_docx' (BLOB).
    Se sim, migra os blobs para arquivos físicos em HISTORICO_DOCX_DIR,
    salva a referência do caminho relativo em uma nova tabela e substitui a antiga.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='historico_planos'")
    if not cursor.fetchone():
        return

    cursor.execute("PRAGMA table_info(historico_planos)")
    colunas = [row[1] for row in cursor.fetchall()]
    if "arquivo_docx" not in colunas:
        return

    logger.info("Iniciando migração de BLOBs do SQLite para arquivos físicos...")
    cursor.execute("SELECT id, professor_nome, disciplina, turma, bimestre, data_geracao, arquivo_nome, arquivo_docx FROM historico_planos")
    registros = cursor.fetchall()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS historico_planos_nova (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            professor_nome TEXT,
            disciplina TEXT,
            turma TEXT,
            bimestre TEXT,
            data_geracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            arquivo_nome TEXT,
            arquivo_path TEXT
        )
        """
    )

    os.makedirs(HISTORICO_DOCX_DIR, exist_ok=True)
    from core.lib.classificador import normalizar_texto

    for reg in registros:
        r_id, prof, disc, turma, bim, data_gen, arq_nome, blob = reg
        if not arq_nome:
            arq_nome = f"plano_{r_id}.docx"

        stem = Path(arq_nome).stem
        ext = Path(arq_nome).suffix or ".docx"

        prof_clean = normalizar_texto(prof).replace(" ", "_")
        disc_clean = normalizar_texto(disc).replace(" ", "_")
        turma_clean = normalizar_texto(turma).replace(" ", "_")

        unique_name = f"{prof_clean}_{disc_clean}_{turma_clean}_{r_id}_{stem}{ext}"
        filepath = Path(HISTORICO_DOCX_DIR) / unique_name

        if blob:
            try:
                filepath.write_bytes(blob)
            except Exception as e:
                logger.error(f"Erro ao salvar arquivo fisico na migracao: {e}")
                raise RuntimeError(f"Abortando migração: erro ao gravar arquivo {filepath}") from e

        cursor.execute(
            """
            INSERT INTO historico_planos_nova (id, professor_nome, disciplina, turma, bimestre, data_geracao, arquivo_nome, arquivo_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (r_id, prof, disc, turma, bim, data_gen, arq_nome, unique_name),
        )

    cursor.execute("DROP TABLE historico_planos")
    cursor.execute("ALTER TABLE historico_planos_nova RENAME TO historico_planos")
    logger.info("Migração concluída com sucesso!")


def init_db():
    with get_connection() as conn:
        _migrar_blob_para_path(conn)
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
        
        

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS historico_planos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                professor_nome TEXT,
                disciplina TEXT,
                turma TEXT,
                bimestre TEXT,
                data_geracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                arquivo_nome TEXT,
                arquivo_path TEXT
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
        _aplicar_migracoes(cursor)
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


def salvar_historico_plano(
    professor_nome,
    disciplina,
    turma,
    arquivo_nome,
    arquivo_docx_bytes,
    limite_retencao: int = 5,
    bimestre: str = "",
):
    professor_nome = _normalizar_campo(professor_nome)
    disciplina = _normalizar_campo(disciplina)
    turma = _normalizar_campo(turma)
    bimestre = _normalizar_campo(bimestre)
    arquivo_nome = _normalizar_campo(arquivo_nome)
    arquivo_docx_bytes = bytes(arquivo_docx_bytes or b"")

    # Gera um nome físico único para salvar no disco
    from core.lib.classificador import normalizar_texto
    import uuid
    prof_clean = normalizar_texto(professor_nome).replace(" ", "_")
    disc_clean = normalizar_texto(disciplina).replace(" ", "_")
    turma_clean = normalizar_texto(turma).replace(" ", "_")
    ts = uuid.uuid4().hex[:8]
    
    unique_filename = f"{prof_clean}_{disc_clean}_{turma_clean}_{ts}_{arquivo_nome.strip()}"
    filepath = Path(HISTORICO_DOCX_DIR) / unique_filename

    try:
        os.makedirs(HISTORICO_DOCX_DIR, exist_ok=True)
        filepath.write_bytes(arquivo_docx_bytes)
    except Exception as e:
        logger.error(f"Erro ao salvar arquivo fisico de historico: {e}")
        return

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO historico_planos (professor_nome, disciplina, turma, bimestre, arquivo_nome, arquivo_path)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                professor_nome,
                disciplina,
                turma,
                bimestre,
                arquivo_nome,
                unique_filename,
            ),
        )
        
        # Aplicar política de retenção
        if limite_retencao > 0:
            cursor.execute(
                """
                SELECT arquivo_path FROM historico_planos
                WHERE UPPER(TRIM(professor_nome)) = UPPER(TRIM(?))
                  AND UPPER(TRIM(disciplina)) = UPPER(TRIM(?))
                  AND UPPER(TRIM(turma)) = UPPER(TRIM(?))
                  AND UPPER(TRIM(COALESCE(bimestre, ''))) = UPPER(TRIM(?))
                  AND id NOT IN (
                      SELECT id FROM historico_planos
                      WHERE UPPER(TRIM(professor_nome)) = UPPER(TRIM(?))
                        AND UPPER(TRIM(disciplina)) = UPPER(TRIM(?))
                        AND UPPER(TRIM(turma)) = UPPER(TRIM(?))
                        AND UPPER(TRIM(COALESCE(bimestre, ''))) = UPPER(TRIM(?))
                      ORDER BY data_geracao DESC, id DESC
                      LIMIT ?
                  )
                """,
                (
                    professor_nome,
                    disciplina,
                    turma,
                    bimestre,
                    professor_nome,
                    disciplina,
                    turma,
                    bimestre,
                    limite_retencao,
                ),
            )
            caminhos_remover = [row[0] for row in cursor.fetchall()]
            for p_rel in caminhos_remover:
                if p_rel:
                    try:
                        p_abs = Path(HISTORICO_DOCX_DIR) / p_rel
                        if p_abs.exists():
                            p_abs.unlink()
                    except Exception as e:
                        logger.error(f"Erro ao remover arquivo fisico do historico: {e}")

            cursor.execute(
                """
                DELETE FROM historico_planos
                WHERE UPPER(TRIM(professor_nome)) = UPPER(TRIM(?))
                  AND UPPER(TRIM(disciplina)) = UPPER(TRIM(?))
                  AND UPPER(TRIM(turma)) = UPPER(TRIM(?))
                  AND UPPER(TRIM(COALESCE(bimestre, ''))) = UPPER(TRIM(?))
                  AND id NOT IN (
                      SELECT id FROM historico_planos
                      WHERE UPPER(TRIM(professor_nome)) = UPPER(TRIM(?))
                        AND UPPER(TRIM(disciplina)) = UPPER(TRIM(?))
                        AND UPPER(TRIM(turma)) = UPPER(TRIM(?))
                        AND UPPER(TRIM(COALESCE(bimestre, ''))) = UPPER(TRIM(?))
                      ORDER BY data_geracao DESC, id DESC
                      LIMIT ?
                  )
                """,
                (
                    professor_nome,
                    disciplina,
                    turma,
                    bimestre,
                    professor_nome,
                    disciplina,
                    turma,
                    bimestre,
                    limite_retencao,
                ),
            )
            deletados = cursor.rowcount
            if deletados > 0:
                logger.info(
                    "Politica de retencao aplicada: %d planos antigos removidos para %s - %s - %s - %s",
                    deletados,
                    professor_nome,
                    disciplina,
                    turma,
                    bimestre,
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


def listar_ultimos_planos_por_contexto(bimestre: str = "") -> list[dict]:
    bimestre = _normalizar_campo(bimestre)

    with get_connection() as conn:
        cursor = conn.cursor()
        if bimestre:
            cursor.execute(
                """
                SELECT
                    h.id,
                    h.professor_nome,
                    h.disciplina,
                    h.turma,
                    COALESCE(h.bimestre, ''),
                    h.data_geracao,
                    h.arquivo_nome
                FROM historico_planos h
                JOIN (
                    SELECT
                        UPPER(TRIM(professor_nome)) AS professor_chave,
                        UPPER(TRIM(disciplina)) AS disciplina_chave,
                        UPPER(TRIM(turma)) AS turma_chave,
                        UPPER(TRIM(COALESCE(bimestre, ''))) AS bimestre_chave,
                        MAX(id) AS ultimo_id
                    FROM historico_planos
                    WHERE UPPER(TRIM(COALESCE(bimestre, ''))) = UPPER(TRIM(?))
                    GROUP BY
                        UPPER(TRIM(professor_nome)),
                        UPPER(TRIM(disciplina)),
                        UPPER(TRIM(turma)),
                        UPPER(TRIM(COALESCE(bimestre, '')))
                ) ultimos
                    ON h.id = ultimos.ultimo_id
                ORDER BY
                    UPPER(TRIM(h.professor_nome)),
                    UPPER(TRIM(h.disciplina)),
                    UPPER(TRIM(h.turma)),
                    h.data_geracao DESC,
                    h.id DESC
                """,
                (bimestre,),
            )
        else:
            cursor.execute(
                """
                SELECT
                    h.id,
                    h.professor_nome,
                    h.disciplina,
                    h.turma,
                    COALESCE(h.bimestre, ''),
                    h.data_geracao,
                    h.arquivo_nome
                FROM historico_planos h
                JOIN (
                    SELECT
                        UPPER(TRIM(professor_nome)) AS professor_chave,
                        UPPER(TRIM(disciplina)) AS disciplina_chave,
                        UPPER(TRIM(turma)) AS turma_chave,
                        UPPER(TRIM(COALESCE(bimestre, ''))) AS bimestre_chave,
                        MAX(id) AS ultimo_id
                    FROM historico_planos
                    GROUP BY
                        UPPER(TRIM(professor_nome)),
                        UPPER(TRIM(disciplina)),
                        UPPER(TRIM(turma)),
                        UPPER(TRIM(COALESCE(bimestre, '')))
                ) ultimos
                    ON h.id = ultimos.ultimo_id
                ORDER BY
                    UPPER(TRIM(h.professor_nome)),
                    UPPER(TRIM(h.disciplina)),
                    UPPER(TRIM(h.turma)),
                    UPPER(TRIM(COALESCE(h.bimestre, ''))),
                    h.data_geracao DESC,
                    h.id DESC
                """
            )

        return [
            {
                "id": int(row[0]),
                "professor_nome": row[1] or "",
                "disciplina": row[2] or "",
                "turma": row[3] or "",
                "bimestre": row[4] or "",
                "data_geracao": row[5] or "",
                "arquivo_nome": row[6] or "",
            }
            for row in cursor.fetchall()
        ]


def obter_meses_historico_planos() -> list[str]:
    """Retorna uma lista de anos-meses (YYYY-MM) disponíveis no histórico."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT strftime('%Y-%m', data_geracao) as mes
            FROM historico_planos
            WHERE data_geracao IS NOT NULL
            ORDER BY mes DESC
            """
        )
        return [row[0] for row in cursor.fetchall() if row[0]]


def buscar_historico_planos(professor_nome: str, mes: str = "") -> list[dict]:
    """Busca os planos gerados por um professor, filtrando opcionalmente por mês (YYYY-MM)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT id, professor_nome, disciplina, turma, bimestre, data_geracao, arquivo_nome, arquivo_path
            FROM historico_planos
            WHERE UPPER(TRIM(professor_nome)) = UPPER(TRIM(?))
        """
        params = [professor_nome]
        
        if mes:
            query += " AND strftime('%Y-%m', data_geracao) = ?"
            params.append(mes)
            
        query += " ORDER BY data_geracao DESC, id DESC"
        
        cursor.execute(query, params)
        return [
            {
                "id": int(row[0]),
                "professor_nome": row[1] or "",
                "disciplina": row[2] or "",
                "turma": row[3] or "",
                "bimestre": row[4] or "",
                "data_geracao": row[5] or "",
                "arquivo_nome": row[6] or "",
                "arquivo_path": row[7] or "",
            }
            for row in cursor.fetchall()
        ]



def obter_arquivo_historico(plano_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT arquivo_nome, arquivo_path FROM historico_planos WHERE id = ?", (plano_id,))
        row = cursor.fetchone()
        if not row:
            return None
        nome, path_rel = row
        bytes_content = b""
        if path_rel:
            p_abs = _resolver_caminho_arquivo_historico(path_rel)
            if p_abs.exists():
                try:
                    bytes_content = p_abs.read_bytes()
                except Exception as e:
                    logger.error(f"Erro ao ler arquivo fisico do historico: {e}")
        return nome, bytes_content



def obter_ultimo_plano_docx(professor_nome: str, disciplina: str, turma: str) -> bytes | None:
    professor_nome = _normalizar_campo(professor_nome)
    disciplina = _normalizar_campo(disciplina)
    turma = _normalizar_campo(turma)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT arquivo_path FROM historico_planos
            WHERE UPPER(TRIM(professor_nome)) = UPPER(TRIM(?))
              AND UPPER(TRIM(disciplina)) = UPPER(TRIM(?))
              AND UPPER(TRIM(turma)) = UPPER(TRIM(?))
            ORDER BY data_geracao DESC, id DESC
            LIMIT 1
            """,
            (professor_nome, disciplina, turma),
        )
        row = cursor.fetchone()
        if row and row[0]:
            p_abs = _resolver_caminho_arquivo_historico(row[0])
            if p_abs.exists():
                try:
                    return p_abs.read_bytes()
                except Exception as e:
                    logger.error(f"Erro ao ler ultimo arquivo docx: {e}")
        return None



def obter_ultima_aula_gerada_sistema(professor: str, disciplina: str, turma: str, bimestre: str = "") -> int:
    from core.gestao_aulas import obter_ultima_aula_gerada_sistema_impl
    return obter_ultima_aula_gerada_sistema_impl(professor, disciplina, turma, bimestre)


def verificar_plano_gerado_por_outro_professor(
    professor_nome: str,
    disciplina: str,
    turma: str,
    bimestre: str = "",
) -> list[dict]:
    """
    Retorna lista de registros do historico onde a mesma disciplina e turma
    foram geradas para um professor diferente do atual.
    """
    professor_nome = _normalizar_campo(professor_nome)
    disciplina = _normalizar_campo(disciplina)
    turma = _normalizar_campo(turma)
    bimestre = _normalizar_campo(bimestre)

    if not professor_nome or not disciplina or not turma:
        return []

    with get_connection() as conn:
        cursor = conn.cursor()
        if bimestre:
            cursor.execute(
                """
                SELECT DISTINCT professor_nome, data_geracao, arquivo_nome, bimestre
                FROM historico_planos
                WHERE UPPER(TRIM(professor_nome)) <> UPPER(TRIM(?))
                  AND UPPER(TRIM(disciplina)) = UPPER(TRIM(?))
                  AND UPPER(TRIM(turma)) = UPPER(TRIM(?))
                  AND UPPER(TRIM(COALESCE(bimestre, ''))) = UPPER(TRIM(?))
                ORDER BY data_geracao DESC
                """,
                (professor_nome, disciplina, turma, bimestre),
            )
        else:
            cursor.execute(
                """
                SELECT DISTINCT professor_nome, data_geracao, arquivo_nome, bimestre
                FROM historico_planos
                WHERE UPPER(TRIM(professor_nome)) <> UPPER(TRIM(?))
                  AND UPPER(TRIM(disciplina)) = UPPER(TRIM(?))
                  AND UPPER(TRIM(turma)) = UPPER(TRIM(?))
                ORDER BY data_geracao DESC
                """,
                (professor_nome, disciplina, turma),
            )
        return [
            {
                "professor_nome": row[0],
                "data_geracao": row[1],
                "arquivo_nome": row[2],
                "bimestre": row[3],
            }
            for row in cursor.fetchall()
        ]

