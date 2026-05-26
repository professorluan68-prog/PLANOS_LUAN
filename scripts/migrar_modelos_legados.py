from __future__ import annotations

import csv
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import MODELOS_LEGADOS_QUARENTENA_DIR, PASTA_PLANOS_PROFESSORES
from core.database import get_connection, init_db, listar_vinculos_professores
from core.modelos_docx import template_id_por_contexto
from core.professores_planos import extrair_info_plano


def _destino_unico(destino: Path) -> Path:
    if not destino.exists():
        return destino
    indice = 2
    while True:
        candidato = destino.with_name(f"{destino.stem} ({indice}){destino.suffix}")
        if not candidato.exists():
            return candidato
        indice += 1


def _esta_na_quarentena(caminho: Path) -> bool:
    try:
        caminho.resolve().relative_to(MODELOS_LEGADOS_QUARENTENA_DIR.resolve())
        return True
    except ValueError:
        return False


def _subpasta_professor(vinculo: dict, origem: Path) -> str:
    try:
        rel = origem.resolve().relative_to(PASTA_PLANOS_PROFESSORES.resolve())
        if len(rel.parts) > 1:
            return rel.parts[0]
    except ValueError:
        pass
    return str(vinculo.get("professor") or origem.parent.name or "SEM_PROFESSOR").strip() or "SEM_PROFESSOR"


def migrar_modelos_legados() -> Path:
    init_db()
    MODELOS_LEGADOS_QUARENTENA_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    relatorio = MODELOS_LEGADOS_QUARENTENA_DIR / f"relatorio_migracao_modelos_{timestamp}.csv"
    linhas = []

    with get_connection() as conn:
        cursor = conn.cursor()
        for vinculo in listar_vinculos_professores():
            origem_texto = str(vinculo.get("arquivo_modelo") or vinculo.get("arquivo") or "").strip()
            if not origem_texto:
                linhas.append(_linha_relatorio(vinculo, "", "", "", "sem arquivo_modelo no banco"))
                continue

            origem = Path(origem_texto)
            template_id = template_id_por_contexto(
                disciplina=vinculo.get("disciplina", ""),
                componente_curricular=vinculo.get("componente_curricular", ""),
                arquivo_modelo=origem_texto,
            )

            if _esta_na_quarentena(origem):
                novo_caminho = origem
                status = "ja estava na quarentena"
            elif not origem.exists():
                novo_caminho = origem
                status = "arquivo original nao encontrado; banco atualizado apenas com template_id"
            else:
                info = {}
                try:
                    info = extrair_info_plano(origem, origem.parent.name)
                except Exception:
                    info = {}

                pasta_destino = MODELOS_LEGADOS_QUARENTENA_DIR / _subpasta_professor(vinculo, origem)
                pasta_destino.mkdir(parents=True, exist_ok=True)
                novo_caminho = _destino_unico(pasta_destino / origem.name)
                shutil.move(str(origem), str(novo_caminho))
                status = "movido"

                vinculo = _completar_vinculo(vinculo, info)

            cursor.execute(
                """
                UPDATE professor_turmas
                SET dia_semana = ?,
                    horario = ?,
                    aulas_semana = ?,
                    arquivo_modelo = ?,
                    template_id = ?,
                    componente_curricular = ?
                WHERE id = ?
                """,
                (
                    str(vinculo.get("dia_semana") or ""),
                    str(vinculo.get("horario") or ""),
                    str(vinculo.get("aulas_semana") or ""),
                    str(novo_caminho),
                    template_id,
                    str(vinculo.get("componente_curricular") or vinculo.get("disciplina") or ""),
                    vinculo["id"],
                ),
            )
            linhas.append(_linha_relatorio(vinculo, origem_texto, str(novo_caminho), template_id, status))
        conn.commit()

    with relatorio.open("w", newline="", encoding="utf-8-sig") as arquivo:
        campos = ["id", "professor", "disciplina", "turma", "arquivo_original", "novo_local", "template_id", "status"]
        writer = csv.DictWriter(arquivo, fieldnames=campos, delimiter=";")
        writer.writeheader()
        writer.writerows(linhas)
    return relatorio


def _completar_vinculo(vinculo: dict, info: dict) -> dict:
    atualizado = dict(vinculo)
    for campo in ("dia_semana", "horario", "aulas_semana", "componente_curricular"):
        if not str(atualizado.get(campo) or "").strip() and info.get(campo):
            atualizado[campo] = info[campo]
    return atualizado


def _linha_relatorio(vinculo: dict, original: str, novo: str, template_id: str, status: str) -> dict:
    return {
        "id": vinculo.get("id", ""),
        "professor": vinculo.get("professor", ""),
        "disciplina": vinculo.get("disciplina", ""),
        "turma": vinculo.get("turma", ""),
        "arquivo_original": original,
        "novo_local": novo,
        "template_id": template_id,
        "status": status,
    }


if __name__ == "__main__":
    print(migrar_modelos_legados())
