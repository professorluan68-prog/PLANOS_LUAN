from __future__ import annotations

import csv
import json
from pathlib import Path

from core.models import PlanoCompleto
from core.validador_plano import validar_aula_final

_DIRETORIOS_IGNORADOS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
}

_CAMPOS_MINIMOS = {
    "tema",
    "aprendizagem",
    "metodologia",
    "acompanhamento",
    "acessibilidade",
}


def _parece_sidecar_plano(dados) -> bool:
    return isinstance(dados, dict) and _CAMPOS_MINIMOS.issubset(set(dados.keys()))


def iterar_sidecars(base_dir: str | Path):
    base_path = Path(base_dir)
    for caminho in base_path.rglob("*.json"):
        if any(parte in _DIRETORIOS_IGNORADOS for parte in caminho.parts):
            continue
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except Exception:
            continue
        if _parece_sidecar_plano(dados):
            yield caminho, dados


def avaliar_sidecar(caminho_json: str | Path, dados: dict) -> dict:
    plano = PlanoCompleto.from_any(dados)
    aula = plano.to_dict()
    avisos_recalculados = validar_aula_final(aula) or []
    avisos_salvos = [str(aviso).strip() for aviso in plano.avisos_validacao if str(aviso).strip()]
    return {
        "arquivo_json": str(caminho_json),
        "disciplina": plano.disciplina,
        "tema": plano.tema,
        "perfil": plano.perfil,
        "confidence_score_salvo": plano.confidence_score,
        "qtd_avisos_salvos": len(avisos_salvos),
        "qtd_avisos_recalculados": len(avisos_recalculados),
        "avisos_salvos": " | ".join(avisos_salvos),
        "avisos_recalculados": " | ".join(avisos_recalculados),
        "status": "ATENCAO" if (avisos_salvos or avisos_recalculados) else "OK",
    }


def exportar_relatorio_validacao_sidecars(
    base_dir: str | Path,
    saida_csv: str | Path,
) -> int:
    linhas = [
        avaliar_sidecar(caminho_json, dados)
        for caminho_json, dados in iterar_sidecars(base_dir)
    ]
    saida_path = Path(saida_csv)
    saida_path.parent.mkdir(parents=True, exist_ok=True)
    campos = [
        "arquivo_json",
        "disciplina",
        "tema",
        "perfil",
        "confidence_score_salvo",
        "qtd_avisos_salvos",
        "qtd_avisos_recalculados",
        "avisos_salvos",
        "avisos_recalculados",
        "status",
    ]
    with saida_path.open("w", encoding="utf-8-sig", newline="") as arquivo_csv:
        writer = csv.DictWriter(arquivo_csv, fieldnames=campos)
        writer.writeheader()
        writer.writerows(linhas)
    return len(linhas)
